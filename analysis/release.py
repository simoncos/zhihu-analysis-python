# -*- coding: utf-8 -*-
"""Build the anonymized public release of the Zhihu2015 dataset.

Privacy design:
- user_url / user_id (display name) are replaced by random integer ids;
  the mapping is written locally (mapping_*.csv) and MUST NOT be published.
- question_id is also pseudonymized: real ids would let anyone look up the
  answerer list on zhihu.com and re-identify users.
- topic strings are public wiki tags, not personal data: kept as-is.

Usage:
    python -m analysis.release --db zhihu.db --out release_build
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data_io import TABLES, USER_FEATURES, load_table


def _pseudonymize(values, rng):
    """Stable random-integer mapping for a series of identifiers."""
    unique = pd.unique(values)
    perm = rng.permutation(len(unique))
    return dict(zip(unique, perm.tolist()))


def build_release(db_path, out_dir, seed=20151201):
    out_dir = Path(out_dir)
    pub_dir = out_dir / "public"
    priv_dir = out_dir / "private"  # mappings; never publish
    pub_dir.mkdir(parents=True, exist_ok=True)
    priv_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    dfs = {t: load_table(db_path, t) for t in TABLES}
    user, following = dfs["User"], dfs["Following"]
    question, uq, ut = dfs["Question"], dfs["UserQuestion"], dfs["UserTopic"]

    # ids appearing anywhere (crawled users + followees outside the circle)
    all_urls = pd.concat([user["user_url"], following["user_url"], following["followee_url"]])
    uid_map = _pseudonymize(all_urls, rng)
    qid_map = _pseudonymize(pd.concat([question["question_id"], uq["question_id"]]), rng)

    users_pub = pd.DataFrame({"uid": user["user_url"].map(uid_map)})
    for f in USER_FEATURES:
        users_pub[f] = user[f]
    users_pub["layer"] = user.get("layer")
    users_pub = users_pub.sort_values("uid").reset_index(drop=True)

    edges_pub = pd.DataFrame(
        {
            "src": following["user_url"].map(uid_map),
            "dst": following["followee_url"].map(uid_map),
        }
    ).drop_duplicates().sort_values(["src", "dst"]).reset_index(drop=True)

    questions_pub = pd.DataFrame(
        {"qid": question["question_id"].map(qid_map), "topic": question["topic"]}
    ).drop_duplicates().sort_values("qid").reset_index(drop=True)

    uq_pub = pd.DataFrame(
        {"uid": uq["user_url"].map(uid_map), "qid": uq["question_id"].map(qid_map)}
    ).drop_duplicates().sort_values(["uid", "qid"]).reset_index(drop=True)

    ut_pub = pd.DataFrame(
        {"uid": ut["user_url"].map(uid_map), "topic": ut["topic"]}
    ).sort_values(["uid", "topic"]).reset_index(drop=True)  # keep duplicates: they carry counts

    tables = {
        "users": users_pub,
        "edges": edges_pub,
        "questions": questions_pub,
        "user_questions": uq_pub,
        "user_topics": ut_pub,
    }
    checksums = {}
    for name, df in tables.items():
        path = pub_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        checksums[f"{name}.parquet"] = hashlib.sha256(path.read_bytes()).hexdigest()

    # local-only mappings for future linkage by the maintainer
    pd.Series(uid_map).rename("uid").to_csv(priv_dir / "mapping_users.csv")
    pd.Series(qid_map).rename("qid").to_csv(priv_dir / "mapping_questions.csv")

    crawled_uids = set(users_pub["uid"])
    stats = {
        "n_users_crawled": len(users_pub),
        "n_users_referenced": len(uid_map),
        "n_edges": len(edges_pub),
        "n_edges_induced": int(
            (edges_pub["src"].isin(crawled_uids) & edges_pub["dst"].isin(crawled_uids)).sum()
        ),
        "n_questions": len(questions_pub),
        "n_user_questions": len(uq_pub),
        "n_user_topics": len(ut_pub),
        "n_distinct_topics": int(ut_pub["topic"].nunique()),
        "feature_summary": {
            f: {
                "mean": float(users_pub[f].mean()),
                "median": float(users_pub[f].median()),
                "max": int(users_pub[f].max()),
            }
            for f in USER_FEATURES
        },
        "sha256": checksums,
    }
    (pub_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="zhihu.db")
    ap.add_argument("--out", default="release_build")
    args = ap.parse_args()
    stats = build_release(args.db, args.out)
    print(json.dumps({k: v for k, v in stats.items() if k != "sha256"}, ensure_ascii=False, indent=2))
    print(f"\npublic artifacts -> {args.out}/public/ ; PRIVATE mappings -> {args.out}/private/ (do not publish)")


if __name__ == "__main__":
    main()
