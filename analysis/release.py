# -*- coding: utf-8 -*-
"""Build the pseudonymized Zhihu2015 release candidate.

The public tables are written atomically. Raw-to-pseudonym mappings go to a
separate, permission-restricted directory that is never nested beneath the
public upload root.

Usage:
    python -m analysis.release --db zhihu.db --out release_build \
        --private-out /secure/location/zhihu2015-mappings
"""

import argparse
import csv
import hashlib
import json
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .atomic_io import atomic_directory
from .data_io import USER_FEATURES, iter_table, load_table


PUBLIC_SCHEMAS = {
    "users": ["uid", *USER_FEATURES, "layer"],
    "edges": ["src", "dst"],
    "questions": ["qid", "topic"],
    "user_questions": ["uid", "qid"],
    "user_topics": ["uid", "topic"],
}
PUBLIC_ID_COLUMNS = {
    "users": ["uid"],
    "edges": ["src", "dst"],
    "questions": ["qid"],
    "user_questions": ["uid", "qid"],
    "user_topics": ["uid"],
}
FORBIDDEN_PUBLIC_COLUMNS = {"user_url", "user_id", "followee_url", "question_id"}


def _sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pseudonymize(values, rng):
    """Stable random-integer mapping independent of set/dict iteration order."""
    unique = sorted(set(values), key=lambda value: (type(value).__name__, str(value)))
    perm = rng.permutation(len(unique))
    return dict(zip(unique, perm.tolist()))


def _collect_ids(db_path, specs, chunksize):
    values = set()
    for table, column in specs:
        for chunk in iter_table(
            db_path, table, columns=[column], chunksize=chunksize
        ):
            if chunk[column].isna().any():
                raise ValueError(f"{table}.{column} contains null identifiers")
            values.update(chunk[column].tolist())
    return values


def _iter_query(db_path, query, chunksize):
    with sqlite3.connect(db_path) as conn:
        yield from pd.read_sql_query(query, conn, chunksize=chunksize)


def _validate_public_chunk(name, frame):
    expected = PUBLIC_SCHEMAS[name]
    if list(frame.columns) != expected:
        raise ValueError(f"{name}: expected columns {expected}, got {list(frame.columns)}")
    leaked = FORBIDDEN_PUBLIC_COLUMNS.intersection(frame.columns)
    if leaked:
        raise ValueError(f"{name}: forbidden raw columns present: {sorted(leaked)}")
    for column in PUBLIC_ID_COLUMNS[name]:
        if frame[column].isna().any():
            raise ValueError(f"{name}.{column}: unmapped/null pseudonym")
        if not pd.api.types.is_integer_dtype(frame[column]):
            raise ValueError(f"{name}.{column}: pseudonyms must have integer dtype")


def _write_parquet(path, name, chunks):
    writer = None
    rows = 0
    try:
        for frame in chunks:
            _validate_public_chunk(name, frame)
            arrow = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(path, arrow.schema)
            writer.write_table(arrow)
            rows += len(frame)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise ValueError(f"{name}: release table is empty")
    return rows


def _write_private_mapping(path, mapping, pseudonym_name):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["raw_id", pseudonym_name])
        for raw_id, pseudonym in sorted(mapping.items(), key=lambda item: item[1]):
            writer.writerow([raw_id, pseudonym])
    os.chmod(path, 0o600)


def build_release(
    db_path,
    out_dir,
    private_dir=None,
    seed=20151201,
    chunksize=100_000,
):
    out_dir = Path(out_dir)
    pub_dir = out_dir / "public"
    private_dir = Path(private_dir) if private_dir else out_dir.with_name(f"{out_dir.name}_private")
    if (
        pub_dir == private_dir
        or pub_dir in private_dir.parents
        or private_dir in pub_dir.parents
    ):
        raise ValueError("private mappings must not be inside the public upload directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    private_dir.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    uid_specs = [
        ("User", "user_url"),
        ("Following", "user_url"),
        ("Following", "followee_url"),
        ("UserQuestion", "user_url"),
        ("UserTopic", "user_url"),
    ]
    qid_specs = [("Question", "question_id"), ("UserQuestion", "question_id")]
    uid_map = _pseudonymize(_collect_ids(db_path, uid_specs, chunksize), rng)
    qid_map = _pseudonymize(_collect_ids(db_path, qid_specs, chunksize), rng)

    user = load_table(db_path, "User", columns=["user_url", *USER_FEATURES, "layer"])
    users_pub = pd.DataFrame({"uid": user["user_url"].map(uid_map)})
    for feature in USER_FEATURES:
        users_pub[feature] = user[feature]
    users_pub["layer"] = user["layer"]
    users_pub = users_pub.sort_values("uid").reset_index(drop=True)
    crawled_uids = set(users_pub["uid"])

    n_edges_induced = 0
    distinct_topics = set()

    def users_chunks():
        yield users_pub

    def edge_chunks():
        nonlocal n_edges_induced
        query = "select distinct user_url, followee_url from Following order by user_url, followee_url"
        for chunk in _iter_query(db_path, query, chunksize):
            frame = pd.DataFrame(
                {"src": chunk["user_url"].map(uid_map), "dst": chunk["followee_url"].map(uid_map)}
            )
            n_edges_induced += int(
                (frame["src"].isin(crawled_uids) & frame["dst"].isin(crawled_uids)).sum()
            )
            yield frame

    def question_chunks():
        query = "select distinct question_id, topic from Question order by question_id, topic"
        for chunk in _iter_query(db_path, query, chunksize):
            yield pd.DataFrame(
                {"qid": chunk["question_id"].map(qid_map), "topic": chunk["topic"]}
            )

    def user_question_chunks():
        query = "select distinct user_url, question_id from UserQuestion order by user_url, question_id"
        for chunk in _iter_query(db_path, query, chunksize):
            yield pd.DataFrame(
                {"uid": chunk["user_url"].map(uid_map), "qid": chunk["question_id"].map(qid_map)}
            )

    def user_topic_chunks():
        query = "select user_url, topic from UserTopic order by user_url, topic"
        for chunk in _iter_query(db_path, query, chunksize):
            distinct_topics.update(chunk["topic"].dropna().tolist())
            yield pd.DataFrame(
                {"uid": chunk["user_url"].map(uid_map), "topic": chunk["topic"]}
            )

    with atomic_directory(private_dir) as private_stage, atomic_directory(pub_dir) as public_stage:
        os.chmod(private_stage, 0o700)
        _write_private_mapping(private_stage / "mapping_users.csv", uid_map, "uid")
        _write_private_mapping(private_stage / "mapping_questions.csv", qid_map, "qid")
        private_manifest = private_stage / "mapping_manifest.json"
        private_manifest.write_text(json.dumps({"pseudonymization_seed": seed}, indent=2))
        os.chmod(private_manifest, 0o600)

        counts = {
            "users": _write_parquet(public_stage / "users.parquet", "users", users_chunks()),
            "edges": _write_parquet(public_stage / "edges.parquet", "edges", edge_chunks()),
            "questions": _write_parquet(
                public_stage / "questions.parquet", "questions", question_chunks()
            ),
            "user_questions": _write_parquet(
                public_stage / "user_questions.parquet",
                "user_questions",
                user_question_chunks(),
            ),
            "user_topics": _write_parquet(
                public_stage / "user_topics.parquet", "user_topics", user_topic_chunks()
            ),
        }
        checksums = {
            f"{name}.parquet": _sha256(public_stage / f"{name}.parquet")
            for name in PUBLIC_SCHEMAS
        }
        stats = {
            "n_users_crawled": counts["users"],
            "n_users_referenced": len(uid_map),
            "n_edges": counts["edges"],
            "n_edges_induced": n_edges_induced,
            "n_questions": counts["questions"],
            "n_user_questions": counts["user_questions"],
            "n_user_topics": counts["user_topics"],
            "n_distinct_topics": len(distinct_topics),
            "feature_summary": {
                feature: {
                    "mean": float(users_pub[feature].mean()),
                    "median": float(users_pub[feature].median()),
                    "max": int(users_pub[feature].max()),
                }
                for feature in USER_FEATURES
            },
            "sha256": checksums,
        }
        (public_stage / "stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2)
        )
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="zhihu.db")
    parser.add_argument("--out", default="release_build")
    parser.add_argument(
        "--private-out",
        help="separate secure directory; defaults to <out>_private beside the release root",
    )
    parser.add_argument("--seed", type=int, default=20151201)
    parser.add_argument("--chunksize", type=int, default=100_000)
    args = parser.parse_args()
    stats = build_release(
        args.db,
        args.out,
        private_dir=args.private_out,
        seed=args.seed,
        chunksize=args.chunksize,
    )
    print(json.dumps({key: value for key, value in stats.items() if key != "sha256"}, ensure_ascii=False, indent=2))
    private_path = args.private_out or f"{args.out}_private"
    print(f"\npublic artifacts -> {args.out}/public/ ; PRIVATE mappings -> {private_path}/")


if __name__ == "__main__":
    main()
