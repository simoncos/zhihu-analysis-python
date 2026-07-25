# -*- coding: utf-8 -*-
"""Phase 0: data access layer. SQLite -> pandas/parquet -> igraph."""

import sqlite3
from pathlib import Path

import igraph as ig
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

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


def _select_sql(table, columns=None):
    if table not in TABLES:
        raise ValueError(f"unknown table {table}")
    columns = list(columns) if columns is not None else None
    if columns is not None and any(not str(c).replace("_", "").isalnum() for c in columns):
        raise ValueError("invalid column name")
    projection = ", ".join(columns) if columns else "*"
    return f"select {projection} from {table}"


def load_table(db_path, table, columns=None):
    """Load one table, optionally projecting only the required columns."""
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(_select_sql(table, columns), conn)


def iter_table(db_path, table, columns=None, chunksize=100_000):
    """Stream a SQLite table as pandas chunks without retaining a connection."""
    with sqlite3.connect(db_path) as conn:
        yield from pd.read_sql_query(
            _select_sql(table, columns), conn, chunksize=chunksize
        )


def export_parquet(db_path, out_dir, chunksize=100_000):
    """Chunked SQLite -> parquet export; downstream analysis avoids SQLite."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for table in TABLES:
        path = out_dir / f"{table}.parquet"
        writer = None
        try:
            for chunk in iter_table(db_path, table, chunksize=chunksize):
                arrow = pa.Table.from_pandas(chunk, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(path, arrow.schema)
                writer.write_table(arrow)
        finally:
            if writer is not None:
                writer.close()
        if writer is None:
            # Preserve a valid empty-table schema if a future fixture contains
            # no rows. Real project tables are non-empty.
            load_table(db_path, table).to_parquet(path, index=False)
        paths[table] = path
    return paths


def load_parquet(out_dir, table, columns=None):
    return pd.read_parquet(Path(out_dir) / f"{table}.parquet", columns=columns)


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
