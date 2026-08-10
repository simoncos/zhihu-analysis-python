import json
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from zhihu_database import ImportContractError, build_database


class DatabaseImportTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        source = root / "data"
        (source / "topic").mkdir(parents=True)
        (source / "user_Process-2").write_text(
            "u1\tO'Connor\t2\t3\t2\t4\t5\t0\n"
            "u2\tSynthetic User\t1\t2\t1\t3\t4\t1\n",
            encoding="utf-8",
        )
        (source / "followee_Process-2").write_text(
            "u1\tu2\tu3\n" "u2\tu1\n", encoding="utf-8"
        )
        (source / "question_Process-2").write_text(
            "u1\tq1\tq2\n" "u2\tq2\tq-without-topic\n", encoding="utf-8"
        )
        (source / "topic" / "topic_Process-2").write_text(
            "q1\t生活\t历史\n" "q2\t生活\n", encoding="utf-8"
        )
        return source

    def test_builds_crawler_tsv_and_derives_user_topics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            database = root / "zhihu.db"

            summary = build_database(source, database)

            self.assertEqual(summary["users"], 2)
            self.assertEqual(summary["follow_edges"], 3)
            self.assertEqual(summary["question_topics"], 3)
            self.assertEqual(summary["user_questions"], 4)
            self.assertEqual(summary["user_topics"], 4)
            self.assertEqual(summary["followee_ids_without_profiles"], 1)
            self.assertEqual(summary["user_questions_without_topics"], 1)
            self.assertEqual(len(summary["source_sha256"]), 64)
            self.assertEqual(len(summary["schema_sha256"]), 64)
            self.assertEqual(stat.S_IMODE(database.stat().st_mode), 0o600)

            with sqlite3.connect(database) as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT user_id FROM User WHERE user_url = ?", ("u1",)
                    ).fetchone()[0],
                    "O'Connor",
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM UserTopic "
                        "WHERE user_url = ? AND topic = ?",
                        ("u1", "生活"),
                    ).fetchone()[0],
                    2,
                )
                self.assertEqual(
                    connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )

    def test_malformed_input_does_not_replace_existing_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            database = root / "zhihu.db"
            original = b"existing-private-database"
            database.write_bytes(original)
            (source / "user_Process-2").write_text(
                "u1\ttoo-few-fields\n", encoding="utf-8"
            )

            with self.assertRaises(ImportContractError):
                build_database(source, database, replace=True)

            self.assertEqual(database.read_bytes(), original)
            self.assertEqual(list(root.glob(".zhihu.db.*")), [])

    def test_missing_input_group_creates_no_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            (source / "topic" / "topic_Process-2").unlink()
            database = root / "zhihu.db"

            with self.assertRaises(ImportContractError):
                build_database(source, database)

            self.assertFalse(database.exists())

    def test_existing_destination_requires_explicit_replace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            database = root / "zhihu.db"
            database.write_bytes(b"do-not-overwrite")

            with self.assertRaises(FileExistsError):
                build_database(source, database)

            self.assertEqual(database.read_bytes(), b"do-not-overwrite")

    def test_explicit_replace_installs_complete_private_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            database = root / "zhihu.db"
            database.write_bytes(b"old")

            summary = build_database(source, database, replace=True)

            self.assertEqual(summary["users"], 2)
            self.assertEqual(stat.S_IMODE(database.stat().st_mode), 0o600)
            with sqlite3.connect(database) as connection:
                self.assertEqual(
                    connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )

    def test_symbolic_link_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            real_database = root / "real.db"
            real_database.write_bytes(b"keep")
            linked_database = root / "linked.db"
            linked_database.symlink_to(real_database)

            with self.assertRaisesRegex(ImportContractError, "symbolic link"):
                build_database(source, linked_database, replace=True)

            self.assertTrue(linked_database.is_symlink())
            self.assertEqual(real_database.read_bytes(), b"keep")

    def test_conflicting_duplicate_user_fails_without_installing_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            (source / "user_Process-3").write_text(
                "u1\tChanged Name\t2\t3\t2\t4\t5\t0\n", encoding="utf-8"
            )
            database = root / "zhihu.db"

            with self.assertRaisesRegex(
                ImportContractError, "conflicting duplicate user record"
            ):
                build_database(source, database)

            self.assertFalse(database.exists())

    def test_format_error_does_not_echo_private_field_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            private_value = "private-invalid-count"
            (source / "user_Process-2").write_text(
                f"u1\tSynthetic User\t{private_value}\t3\t2\t4\t5\t0\n",
                encoding="utf-8",
            )

            with self.assertRaises(ImportContractError) as raised:
                build_database(source, root / "zhihu.db")

            self.assertNotIn(private_value, str(raised.exception))

    def test_invalid_utf8_fails_without_echoing_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            (source / "user_Process-2").write_bytes(b"private-\xff-value\n")

            with self.assertRaisesRegex(ImportContractError, "not valid UTF-8") as raised:
                build_database(source, root / "zhihu.db")

            self.assertNotIn("private", str(raised.exception))
            self.assertFalse((root / "zhihu.db").exists())

    def test_cli_builds_database_and_emits_aggregate_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._fixture(root)
            database = root / "zhihu.db"
            script = Path(__file__).resolve().parents[1] / "zhihu_database.py"

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--source",
                    str(source),
                    "--db",
                    str(database),
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["users"], 2)
            self.assertEqual(summary["user_questions_without_topics"], 1)
            self.assertNotIn("u1", result.stdout)
            self.assertTrue(database.exists())


if __name__ == "__main__":
    unittest.main()
