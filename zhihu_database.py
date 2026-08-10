#!/usr/bin/env python3
"""Build a Zhihu SQLite database from the legacy crawler's TSV outputs.

The historical importer read different paths and a different delimiter than the
crawler wrote.  This module keeps the reconstruction boundary deliberately
small: it performs no crawling, accepts only the documented local TSV layout,
and replaces the destination database only after a complete validated build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence


class ImportContractError(ValueError):
    """Raised when local crawler output does not satisfy the TSV contract."""


@dataclass(frozen=True)
class SourceFiles:
    root: Path
    users: tuple[Path, ...]
    followees: tuple[Path, ...]
    user_questions: tuple[Path, ...]
    question_topics: tuple[Path, ...]

    @classmethod
    def discover(cls, source_dir: Path | str) -> "SourceFiles":
        root = Path(source_dir).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"source directory does not exist: {root}")

        def files(pattern: str) -> tuple[Path, ...]:
            return tuple(sorted(path for path in root.glob(pattern) if path.is_file()))

        discovered = cls(
            root=root,
            users=files("user_*"),
            followees=files("followee_*"),
            user_questions=files("question_*"),
            question_topics=files("topic/topic_*"),
        )
        missing = [
            label
            for label, paths in (
                ("user_*", discovered.users),
                ("followee_*", discovered.followees),
                ("question_*", discovered.user_questions),
                ("topic/topic_*", discovered.question_topics),
            )
            if not paths
        ]
        if missing:
            raise ImportContractError(
                "missing required crawler output group(s): " + ", ".join(missing)
            )
        return discovered

    def all(self) -> tuple[Path, ...]:
        return self.users + self.followees + self.user_questions + self.question_topics


def _rows(paths: Sequence[Path], label: str) -> Iterator[tuple[Path, int, list[str]]]:
    for path in paths:
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                for line_number, raw_line in enumerate(handle, 1):
                    line = raw_line.rstrip("\r\n")
                    if not line:
                        continue
                    fields = line.split("\t")
                    if not fields[0]:
                        raise ImportContractError(
                            f"{label} row has an empty leading identifier at "
                            f"{path.name}:{line_number}"
                        )
                    yield path, line_number, fields
        except UnicodeDecodeError as error:
            raise ImportContractError(
                f"{label} file is not valid UTF-8: {path.name}"
            ) from error


def _require_width(
    path: Path, line_number: int, fields: Sequence[str], expected: int, label: str
) -> None:
    if len(fields) != expected:
        raise ImportContractError(
            f"{label} row at {path.name}:{line_number} has {len(fields)} fields; "
            f"expected {expected} tab-separated fields"
        )


def _nonnegative_int(value: str, path: Path, line_number: int, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ImportContractError(
            f"{field} at {path.name}:{line_number} is not an integer"
        ) from exc
    if parsed < 0:
        raise ImportContractError(
            f"{field} at {path.name}:{line_number} must be non-negative"
        )
    return parsed


def _source_fingerprint(sources: SourceFiles) -> str:
    digest = hashlib.sha256()
    for path in sources.all():
        relative = path.relative_to(sources.root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


def _import_users(connection: sqlite3.Connection, paths: Sequence[Path]) -> None:
    statement = """
        INSERT INTO User (
            user_url, user_id, followee_num, follower_num, answer_num,
            agree_num, thanks_num, layer, is_crawled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    seen: dict[str, tuple[str | int, ...]] = {}
    for path, line_number, fields in _rows(paths, "user"):
        _require_width(path, line_number, fields, 8, "user")
        if not fields[1]:
            raise ImportContractError(
                f"user_id is empty at {path.name}:{line_number}"
            )
        numeric = [
            _nonnegative_int(value, path, line_number, field)
            for value, field in zip(
                fields[2:],
                (
                    "followee_num",
                    "follower_num",
                    "answer_num",
                    "agree_num",
                    "thanks_num",
                    "layer",
                ),
            )
        ]
        record = (fields[0], fields[1], *numeric)
        previous = seen.get(fields[0])
        if previous is not None:
            if previous != record:
                raise ImportContractError(
                    f"conflicting duplicate user record at {path.name}:{line_number}"
                )
            continue
        seen[fields[0]] = record
        connection.execute(statement, record)


def _import_pairs(
    connection: sqlite3.Connection,
    paths: Sequence[Path],
    label: str,
    statement: str,
) -> None:
    for path, line_number, fields in _rows(paths, label):
        if len(fields) < 2:
            raise ImportContractError(
                f"{label} row at {path.name}:{line_number} must contain an "
                "identifier and at least one tab-separated value"
            )
        for value in fields[1:]:
            if not value:
                continue
            connection.execute(statement, (fields[0], value))


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _load_database(connection: sqlite3.Connection, sources: SourceFiles) -> dict[str, int]:
    _import_users(connection, sources.users)
    _import_pairs(
        connection,
        sources.followees,
        "followee",
        "INSERT OR IGNORE INTO Following (user_url, followee_url) VALUES (?, ?)",
    )
    _import_pairs(
        connection,
        sources.user_questions,
        "user-question",
        "INSERT OR IGNORE INTO UserQuestion (user_url, question_id) VALUES (?, ?)",
    )
    _import_pairs(
        connection,
        sources.question_topics,
        "question-topic",
        "INSERT OR IGNORE INTO Question (question_id, topic) VALUES (?, ?)",
    )

    # UserTopic is a derived activity table consumed by the legacy analysis.
    # Preserve repeated topics across different answered questions as counts.
    connection.execute("DELETE FROM UserTopic")
    connection.execute(
        """
        INSERT INTO UserTopic (user_url, topic)
        SELECT uq.user_url, q.topic
        FROM UserQuestion AS uq
        JOIN Question AS q ON q.question_id = uq.question_id
        ORDER BY uq.user_url, uq.question_id, q.topic
        """
    )

    counts = {
        "users": _table_count(connection, "User"),
        "follow_edges": _table_count(connection, "Following"),
        "question_topics": _table_count(connection, "Question"),
        "user_questions": _table_count(connection, "UserQuestion"),
        "user_topics": _table_count(connection, "UserTopic"),
    }
    empty = [name for name, count in counts.items() if count == 0]
    if empty:
        raise ImportContractError(
            "database build produced empty required table(s): " + ", ".join(empty)
        )
    # These gaps are expected possibilities in a partial BFS snapshot. Report
    # them explicitly instead of adding foreign keys that would discard the
    # uncrawled boundary or pretending topic coverage is complete.
    counts["followee_ids_without_profiles"] = int(
        connection.execute(
            """
            SELECT COUNT(DISTINCT f.followee_url)
            FROM Following AS f
            LEFT JOIN User AS u ON u.user_url = f.followee_url
            WHERE u.id IS NULL
            """
        ).fetchone()[0]
    )
    counts["user_questions_without_topics"] = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM UserQuestion AS uq
            LEFT JOIN Question AS q ON q.question_id = uq.question_id
            WHERE q.id IS NULL
            """
        ).fetchone()[0]
    )
    return counts


def build_database(
    source_dir: Path | str,
    database_path: Path | str,
    *,
    schema_path: Path | str | None = None,
    replace: bool = False,
) -> dict[str, int | str]:
    """Build and atomically install a database from local crawler output.

    The destination is never opened by SQLite until a complete temporary build
    passes its format, non-empty-table, and integrity checks.  If any step
    fails, an existing destination is left byte-for-byte untouched.
    """

    sources = SourceFiles.discover(source_dir)
    target = Path(database_path).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    target = target.absolute()
    schema = (
        Path(schema_path).resolve()
        if schema_path is not None
        else Path(__file__).with_name("zhihu_schema.sql").resolve()
    )
    if not schema.is_file():
        raise FileNotFoundError(f"schema file does not exist: {schema}")
    if not target.parent.is_dir():
        raise FileNotFoundError(f"database parent directory does not exist: {target.parent}")
    if target.is_symlink():
        raise ImportContractError("destination database must not be a symbolic link")
    if target.exists() and not target.is_file():
        raise ImportContractError("destination database must be a regular file")
    if target.exists() and not replace:
        raise FileExistsError(
            f"destination already exists: {target}; pass --replace for atomic replacement"
        )

    source_fingerprint = _source_fingerprint(sources)
    schema_text = schema.read_text(encoding="utf-8")
    schema_fingerprint = hashlib.sha256(schema_text.encode("utf-8")).hexdigest()

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    os.chmod(temporary, 0o600)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary)
        connection.executescript(schema_text)
        connection.execute("BEGIN IMMEDIATE")
        counts = _load_database(connection, sources)
        if _source_fingerprint(sources) != source_fingerprint:
            raise ImportContractError("source files changed during database construction")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise sqlite3.DatabaseError(f"SQLite integrity check failed: {integrity}")
        connection.commit()
        connection.close()
        connection = None

        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        if connection is not None:
            connection.rollback()
            connection.close()
        temporary.unlink(missing_ok=True)
        raise

    return {
        **counts,
        "schema_sha256": schema_fingerprint,
        "source_files": len(sources.all()),
        "source_sha256": source_fingerprint,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a private SQLite database from legacy local crawler TSV files."
    )
    parser.add_argument(
        "--source", required=True, type=Path, help="crawler data directory"
    )
    parser.add_argument(
        "--db", required=True, type=Path, help="private destination SQLite path"
    )
    parser.add_argument(
        "--schema", type=Path, default=None, help="schema path (defaults to zhihu_schema.sql)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="atomically replace an existing destination after a successful build",
    )
    return parser


def main() -> int:
    parser = _parser()
    arguments = parser.parse_args()
    try:
        summary = build_database(
            arguments.source,
            arguments.db,
            schema_path=arguments.schema,
            replace=arguments.replace,
        )
    except (ImportContractError, OSError, sqlite3.Error) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
