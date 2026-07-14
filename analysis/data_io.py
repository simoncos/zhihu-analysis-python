# -*- coding: utf-8 -*-
"""Phase 0: data access layer. SQLite -> pandas/parquet -> igraph."""

import sqlite3
from pathlib import Path

import igraph as ig
import pandas as pd

TABLES = ["User", "Following", "Question", "UserQuestion", "UserTopic"]

# Record counts reported in the 2015 project report (section 3.3), used as
# sanity anchors by the health check. Approximate by design.
EXPECTED_COUNTS = {
    "User": 26_000,
    "Following": 4_600_000,
    "Question": 2_200_000,
    "UserQuestion": 1_700_000,
    "UserTopic": 5_400_000,
}

USER_FEATURES = ["followee_num", "follower_num", "answer_num", "agree_num", "thanks_num"]


def load_table(db_path, table):
    if table not in TABLES:
        raise ValueError(f"unknown table {table}")
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(f"select * from {table}", conn)


def export_parquet(db_path, out_dir):
    """One-shot SQLite -> parquet export; downstream analysis never touches SQLite."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for table in TABLES:
        df = load_table(db_path, table)
        path = out_dir / f"{table}.parquet"
        df.to_parquet(path, index=False)
        paths[table] = path
    return paths


def load_parquet(out_dir, table):
    return pd.read_parquet(Path(out_dir) / f"{table}.parquet")


def build_induced_graph(user_df, following_df):
    """Directed graph induced on crawled users.

    Only edges whose both endpoints are in the User table are kept: this is
    the fully-observed part of the crawl (the "blue circle" of the report).
    Returns (graph, info dict).
    """
    crawled = set(user_df["user_url"])
    mask = following_df["user_url"].isin(crawled) & following_df["followee_url"].isin(crawled)
    induced = following_df.loc[mask, ["user_url", "followee_url"]].drop_duplicates()

    g = ig.Graph.TupleList(induced.itertuples(index=False), directed=True)
    # Isolated crawled users still belong to the graph.
    missing = crawled - set(g.vs["name"])
    if missing:
        g.add_vertices(sorted(missing))

    info = {
        "n_users": len(crawled),
        "n_edges_total": len(following_df),
        "n_edges_induced": len(induced),
        "frac_edges_induced": len(induced) / max(len(following_df), 1),
    }
    return g, info


def induced_degree_frame(g):
    """Per-user in/out degree inside the induced subgraph."""
    return pd.DataFrame(
        {
            "user_url": g.vs["name"],
            "induced_in_degree": g.degree(mode="in"),
            "induced_out_degree": g.degree(mode="out"),
        }
    )
