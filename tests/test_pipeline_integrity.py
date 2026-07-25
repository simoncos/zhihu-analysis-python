import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analysis.atomic_io import atomic_directory
from analysis.data_io import export_parquet
from analysis.release import build_release
from analysis.provenance import build_manifest
from analysis.synth_db import generate


class AtomicDirectoryTests(unittest.TestCase):
    def test_failure_preserves_previous_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "current"
            target.mkdir()
            (target / "old.txt").write_text("old")
            with self.assertRaises(RuntimeError):
                with atomic_directory(target) as staging:
                    (staging / "new.txt").write_text("new")
                    raise RuntimeError("boom")
            self.assertEqual((target / "old.txt").read_text(), "old")
            self.assertFalse((target / "new.txt").exists())

    def test_success_replaces_whole_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "current"
            target.mkdir()
            (target / "old.txt").write_text("old")
            with atomic_directory(target) as staging:
                (staging / "new.txt").write_text("new")
            self.assertFalse((target / "old.txt").exists())
            self.assertEqual((target / "new.txt").read_text(), "new")


class ChunkedExportTests(unittest.TestCase):
    def test_chunked_export_preserves_table_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            db = generate(Path(temp) / "fixture.db", n_users=40)
            parquet = Path(temp) / "parquet"
            export_parquet(db, parquet, chunksize=7)
            with sqlite3.connect(db) as conn:
                expected = conn.execute("select count(*) from UserTopic").fetchone()[0]
            actual = len(pd.read_parquet(parquet / "UserTopic.parquet"))
            self.assertEqual(actual, expected)


class ReleaseIntegrityTests(unittest.TestCase):
    def test_release_mapping_covers_orphan_relation_users(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            db = generate(temp / "fixture.db", n_users=40)
            with sqlite3.connect(db) as conn:
                conn.execute("insert into UserTopic (user_url, topic) values (?, ?)", ("topic-only-user", "历史"))
                conn.execute("insert into UserQuestion (user_url, question_id) values (?, ?)", ("question-only-user", "orphan-question"))
                conn.commit()
            out = temp / "release_build"
            private = temp / "secure_mappings"
            stats = build_release(db, out, private_dir=private, chunksize=11)
            user_topics = pd.read_parquet(out / "public" / "user_topics.parquet")
            user_questions = pd.read_parquet(out / "public" / "user_questions.parquet")
            self.assertFalse(user_topics["uid"].isna().any())
            self.assertFalse(user_questions[["uid", "qid"]].isna().any().any())
            self.assertGreater(stats["n_users_referenced"], stats["n_users_crawled"])
            self.assertNotIn("pseudonymization_seed", stats)
            self.assertFalse((out / "private").exists())
            self.assertTrue((private / "mapping_users.csv").exists())
            self.assertEqual(
                json.loads((private / "mapping_manifest.json").read_text())[
                    "pseudonymization_seed"
                ],
                20151201,
            )
            self.assertEqual(json.loads((out / "public" / "stats.json").read_text())["n_user_topics"], len(user_topics))


class ProvenanceGateTests(unittest.TestCase):
    def test_reproducibility_does_not_claim_publication_readiness(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            db = temp / "fixture.db"
            db.write_bytes(b"fixture")
            (temp / "artifact.txt").write_text("artifact")
            manifest = build_manifest(
                temp,
                db,
                config={
                    "gof_sims": 2500,
                    "homophily_null_reps": 200,
                    "all_powerlaw_evaluated": True,
                    "characterization_completed": True,
                },
                source_state={"commit": "abc", "branch": "test", "dirty": False},
                synthetic=False,
            )
            self.assertTrue(manifest["reproducibility_gate_passed"])
            self.assertFalse(manifest["publication_ready"])


if __name__ == "__main__":
    unittest.main()
