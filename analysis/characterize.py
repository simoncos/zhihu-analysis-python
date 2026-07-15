# -*- coding: utf-8 -*-
"""Dataset-paper characterization: induced-graph structure, topic side,
and a follow-edge topic-homophily experiment.

Usage: python -m analysis.characterize --parquet results/parquet --out results
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data_io import build_induced_graph, load_parquet


def graph_structure(g, rng, n_path_samples=500):
    stats = {
        "nodes": g.vcount(),
        "edges": g.ecount(),
        "density": g.density(),
        "reciprocity": g.reciprocity(),
        "clustering_global_undirected": g.as_undirected(mode="collapse").transitivity_undirected(),
        "assortativity_degree": g.assortativity_degree(directed=True),
    }
    wcc = g.connected_components(mode="weak").sizes()
    scc_obj = g.connected_components(mode="strong")
    scc = sorted(scc_obj.sizes(), reverse=True)
    stats["n_wcc"] = len(wcc)
    stats["giant_wcc_frac"] = max(wcc) / g.vcount()
    stats["n_scc"] = len(scc)
    stats["giant_scc_size"] = scc[0]
    stats["giant_scc_frac"] = scc[0] / g.vcount()

    giant = g.induced_subgraph(scc_obj.giant().vs.indices if hasattr(scc_obj, "giant") else None) \
        if False else scc_obj.giant()
    sources = rng.choice(giant.vcount(), size=min(n_path_samples, giant.vcount()), replace=False)
    dists = []
    for s in sources:
        d = giant.distances(source=[int(s)], mode="out")[0]
        d = [x for x in d if np.isfinite(x) and x > 0]
        dists.append(np.mean(d))
    stats["avg_shortest_path_giant_scc_sampled"] = float(np.mean(dists))
    stats["n_path_samples"] = len(sources)
    return stats


def topic_side(ut, user):
    per_user = ut.groupby("user_url").agg(rows=("topic", "size"), distinct=("topic", "nunique"))
    topic_freq = ut["topic"].value_counts()
    return {
        "rows": len(ut),
        "distinct_topics": int(ut["topic"].nunique()),
        "users_with_topics": len(per_user),
        "topics_per_user_median": float(per_user["distinct"].median()),
        "topics_per_user_mean": float(per_user["distinct"].mean()),
        "topic_freq_top20": topic_freq.head(20).to_dict(),
        "topic_freq_median": float(topic_freq.median()),
        "topic_freq_gini_like_top1pct_share": float(
            topic_freq.head(max(1, len(topic_freq) // 100)).sum() / topic_freq.sum()
        ),
    }


def homophily(g, ut, rng, n_samples=100_000):
    """Topic-set Jaccard for connected pairs vs random pairs (both crawled,
    both with topic records)."""
    topic_sets = ut.groupby("user_url")["topic"].agg(set)
    name_of = np.array(g.vs["name"])
    has_topics = pd.Series(name_of).isin(topic_sets.index).values

    edges = np.array(g.get_edgelist())
    mask = has_topics[edges[:, 0]] & has_topics[edges[:, 1]]
    eligible_edges = edges[mask]
    idx = rng.choice(len(eligible_edges), size=min(n_samples, len(eligible_edges)), replace=False)

    def jaccard(a, b):
        u = len(a | b)
        return len(a & b) / u if u else 0.0

    edge_j = [
        jaccard(topic_sets[name_of[s]], topic_sets[name_of[t]]) for s, t in eligible_edges[idx]
    ]

    eligible_nodes = np.where(has_topics)[0]
    pairs = rng.choice(eligible_nodes, size=(len(idx), 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    rand_j = [jaccard(topic_sets[name_of[s]], topic_sets[name_of[t]]) for s, t in pairs]

    return {
        "n_edge_pairs": len(edge_j),
        "n_random_pairs": len(rand_j),
        "jaccard_followed_mean": float(np.mean(edge_j)),
        "jaccard_random_mean": float(np.mean(rand_j)),
        "ratio": float(np.mean(edge_j) / np.mean(rand_j)),
        "nonzero_overlap_followed": float(np.mean([j > 0 for j in edge_j])),
        "nonzero_overlap_random": float(np.mean([j > 0 for j in rand_j])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="results/parquet")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    rng = np.random.default_rng(2015)

    user = load_parquet(args.parquet, "User")
    following = load_parquet(args.parquet, "Following")
    ut = load_parquet(args.parquet, "UserTopic")
    g, _ = build_induced_graph(user, following)

    out = {}
    print("graph structure ...")
    out["graph"] = graph_structure(g, rng)
    print(json.dumps(out["graph"], indent=2))
    print("topic side ...")
    out["topics"] = topic_side(ut, user)
    print("homophily experiment ...")
    out["homophily"] = homophily(g, ut, rng)
    print(json.dumps(out["homophily"], indent=2))

    # seed discrepancy check
    seed_row = user[user["layer"] == 0].iloc[0]
    out["seed_check"] = {
        "seed_followee_num": int(seed_row["followee_num"]),
        "layer1_crawled": int((user["layer"] == 1).sum()),
    }

    Path(args.out, "characterization.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str)
    )
    print(f"done -> {args.out}/characterization.json")


if __name__ == "__main__":
    main()
