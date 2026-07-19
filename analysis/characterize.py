# -*- coding: utf-8 -*-
"""Canonical dataset characterization.

Combines the scalable igraph implementation with the contribution-
concentration and Lorenz-curve metrics from the literature-review branch.
It covers induced-graph structure, the topic layer, a follow-edge homophily
experiment, and the 90-9-1 concentration hypothesis.

Usage: python -m analysis.characterize --parquet results/parquet --out results
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data_io import build_induced_graph, load_parquet


def gini(values):
    values = np.sort(np.asarray(values, dtype=float))
    if len(values) == 0 or values.sum() == 0:
        return 0.0
    cumulative = np.cumsum(values)
    return float((len(values) + 1 - 2 * (cumulative / cumulative[-1]).sum()) / len(values))


def concentration_shares(values):
    """Return the top-1%, next-9%, and bottom-90% shares."""
    values = np.sort(np.asarray(values, dtype=float))[::-1]
    if len(values) == 0 or values.sum() == 0:
        return {"top_1pct": 0.0, "next_9pct": 0.0, "bottom_90pct": 0.0}
    top_1_end = max(1, len(values) // 100)
    top_10_end = max(1, len(values) // 10)
    top_1 = values[:top_1_end].sum() / values.sum()
    top_10 = values[:top_10_end].sum() / values.sum()
    return {
        "top_1pct": float(top_1),
        "next_9pct": float(top_10 - top_1),
        "bottom_90pct": float(1 - top_10),
    }


def sampled_path_stats(g, rng, n_path_samples=500, mode="all"):
    """Sample source-to-target distances without materializing a dense matrix."""
    if g.vcount() <= 1:
        return {"mean": 0.0, "diameter_lower_bound": 0, "n_sources": g.vcount()}

    sources = rng.choice(g.vcount(), size=min(n_path_samples, g.vcount()), replace=False)
    distance_sum = 0.0
    distance_count = 0
    diameter_lower_bound = 0
    for source in sources:
        distances = np.asarray(g.distances(source=[int(source)], mode=mode)[0], dtype=float)
        distances = distances[np.isfinite(distances) & (distances > 0)]
        if len(distances):
            distance_sum += float(distances.sum())
            distance_count += len(distances)
            diameter_lower_bound = max(diameter_lower_bound, int(distances.max()))

    return {
        "mean": float(distance_sum / distance_count) if distance_count else 0.0,
        "diameter_lower_bound": diameter_lower_bound,
        "n_sources": len(sources),
    }


def graph_structure(g, rng, n_path_samples=500, wcc_rng=None):
    undirected = g.as_undirected(mode="collapse")
    assortativity_directed = g.assortativity_degree(directed=True)
    stats = {
        "nodes": g.vcount(),
        "edges": g.ecount(),
        "density": g.density(),
        "reciprocity": g.reciprocity(),
        "clustering_global_undirected": undirected.transitivity_undirected(),
        # Preserve the original key while making its directed semantics clear.
        "assortativity_degree": assortativity_directed,
        "assortativity_degree_directed": assortativity_directed,
        "assortativity_degree_undirected": undirected.assortativity_degree(directed=False),
        "max_k_core_undirected": max(undirected.coreness()),
    }
    wcc_obj = g.connected_components(mode="weak")
    wcc = wcc_obj.sizes()
    scc_obj = g.connected_components(mode="strong")
    scc = sorted(scc_obj.sizes(), reverse=True)
    stats["n_wcc"] = len(wcc)
    stats["giant_wcc_frac"] = max(wcc) / g.vcount()
    stats["n_scc"] = len(scc)
    stats["giant_scc_size"] = scc[0]
    stats["giant_scc_frac"] = scc[0] / g.vcount()

    scc_paths = sampled_path_stats(scc_obj.giant(), rng, n_path_samples, mode="out")
    stats["avg_shortest_path_giant_scc_sampled"] = scc_paths["mean"]
    stats["n_path_samples"] = scc_paths["n_sources"]

    # The literature-review branch used an undirected giant-WCC baseline. Keep
    # it alongside, rather than silently replacing the directed SCC measure.
    giant_wcc = wcc_obj.giant().as_undirected(mode="collapse")
    wcc_rng = wcc_rng or np.random.default_rng(2016)
    wcc_paths = sampled_path_stats(giant_wcc, wcc_rng, n_path_samples, mode="all")
    stats["avg_shortest_path_giant_wcc_undirected_sampled"] = wcc_paths["mean"]
    stats["diameter_lower_bound_giant_wcc_undirected"] = wcc_paths["diameter_lower_bound"]
    stats["n_path_samples_giant_wcc_undirected"] = wcc_paths["n_sources"]
    return stats


def topic_side(ut, user):
    per_user = ut.groupby("user_url").agg(rows=("topic", "size"), distinct=("topic", "nunique"))
    topic_freq = ut["topic"].value_counts()
    topic_user_sizes = ut.groupby("topic")["user_url"].nunique()
    return {
        "rows": len(ut),
        "distinct_topics": int(ut["topic"].nunique()),
        "users_with_topics": len(per_user),
        "topics_per_user_median": float(per_user["distinct"].median()),
        "topics_per_user_mean": float(per_user["distinct"].mean()),
        "topic_freq_top20": topic_freq.head(20).to_dict(),
        "topic_freq_median": float(topic_freq.median()),
        "topic_user_size_gini": gini(topic_user_sizes.values),
        "topic_user_size_median": float(topic_user_sizes.median()),
        "topic_user_size_mean": float(topic_user_sizes.mean()),
        "topics_with_at_least_20_users": int((topic_user_sizes >= 20).sum()),
        "largest_topic_user_count": int(topic_user_sizes.max()),
        "topic_freq_gini_like_top1pct_share": float(
            topic_freq.head(max(1, len(topic_freq) // 100)).sum() / topic_freq.sum()
        ),
    }


def contribution_concentration(g, user):
    """Quantify the 90-9-1 pattern for activity, audience, and graph degree."""
    in_degree = pd.Series(g.degree(mode="in"), index=g.vs["name"])
    aligned_in_degree = in_degree.reindex(user["user_url"]).fillna(0).to_numpy()
    series = {
        "answers": user["answer_num"],
        "agrees": user["agree_num"],
        "thanks": user["thanks_num"],
        "followers_platform_wide": user["follower_num"],
        "in_degree_induced": aligned_in_degree,
    }
    return {
        name: {"gini": gini(values), **concentration_shares(values)}
        for name, values in series.items()
    }


def plot_lorenz_curves(g, user, out_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    in_degree = pd.Series(g.degree(mode="in"), index=g.vs["name"])
    aligned_in_degree = in_degree.reindex(user["user_url"]).fillna(0).to_numpy()
    series = {
        "agrees": user["agree_num"],
        "answers": user["answer_num"],
        "in-degree": aligned_in_degree,
    }
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for label, values in series.items():
        values = np.sort(np.asarray(values, dtype=float))
        cumulative = np.cumsum(values)
        if cumulative[-1] == 0:
            continue
        ax.plot(
            np.linspace(0, 1, len(values)),
            cumulative / cumulative[-1],
            label=f"{label} (Gini {gini(values):.2f})",
        )
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="perfect equality")
    ax.set_xlabel("cumulative share of users (lowest first)")
    ax.set_ylabel("cumulative share of total")
    ax.set_title("Lorenz curves, 2015 Zhihu snapshot")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


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
    # Keep the added WCC baseline on an independent stream so it cannot alter
    # the existing SCC and homophily samples for the canonical seed.
    wcc_rng = np.random.default_rng(2016)

    user = load_parquet(args.parquet, "User")
    following = load_parquet(args.parquet, "Following")
    ut = load_parquet(args.parquet, "UserTopic")
    g, _ = build_induced_graph(user, following)

    out = {}
    print("graph structure ...")
    out["graph"] = graph_structure(g, rng, wcc_rng=wcc_rng)
    print(json.dumps(out["graph"], indent=2))
    print("topic side ...")
    out["topics"] = topic_side(ut, user)
    print("contribution concentration ...")
    out["concentration"] = contribution_concentration(g, user)
    print("homophily experiment ...")
    out["homophily"] = homophily(g, ut, rng)
    print(json.dumps(out["homophily"], indent=2))

    # seed discrepancy check
    seed_row = user[user["layer"] == 0].iloc[0]
    out["seed_check"] = {
        "seed_followee_num": int(seed_row["followee_num"]),
        "layer1_crawled": int((user["layer"] == 1).sum()),
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_lorenz_curves(g, user, out_dir / "lorenz_curves.png")
    Path(out_dir, "characterization.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str)
    )
    print(f"done -> {args.out}/characterization.json")


if __name__ == "__main__":
    main()
