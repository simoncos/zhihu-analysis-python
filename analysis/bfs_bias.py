# -*- coding: utf-8 -*-
"""Project 1 (T1.3): quantify the bias of a 2-layer BFS crawl.

Mimics the 2015 crawl on a synthetic directed graph with power-law degrees:
seed user -> followees (layer 1) -> their followees (layer 2). Compares three
estimates of the in-degree distribution:

  1. ground truth over the whole graph;
  2. "profile counts": true degrees of the sampled nodes only
     (analogous to follower_num read off each crawled user's profile);
  3. induced-subgraph degrees among sampled nodes
     (analogous to degrees inside the 26k-user "blue circle").

This experiment needs no real data and directly supports the claim that
profile counts and induced degrees carry different biases.
"""

import numpy as np
import pandas as pd

from .powerlaw_fit import _fit


def draw_balanced_degree_sequences(n, alpha_in, alpha_out, rng, base_out=48):
    """Draw equal-sum directed degree sequences without flattening the tail.

    Out-degree follows the shifted distribution used to obtain a realistic BFS
    expansion. In-degree *propensities* are power-law distributed; the exact
    number of incoming stubs is then allocated multinomially. This preserves
    the heavy-tailed target propensity while satisfying the directed graph's
    equal-stub constraint. It deliberately does not claim every realized
    in-degree is an exact draw from an unshifted zeta distribution.
    """
    attractiveness = np.minimum(rng.zipf(alpha_in, n), n - 1).astype(float)
    dout = np.minimum(base_out + rng.zipf(alpha_out, n), n - 1).astype(np.int64)
    din = rng.multinomial(int(dout.sum()), attractiveness / attractiveness.sum())
    return din.astype(np.int64), dout


def make_directed_powerlaw_graph(n, alpha_in, alpha_out, rng, base_out=48):
    """Build and simplify a directed configuration-model graph."""
    import igraph as ig

    din, dout = draw_balanced_degree_sequences(n, alpha_in, alpha_out, rng, base_out)
    g = ig.Graph.Degree_Sequence(list(map(int, dout)), list(map(int, din)), method="configuration")
    g.simplify(multiple=True, loops=True)
    return g


def bfs_two_layers(g, seed):
    """Crawl order of the 2015 crawler: follow OUT-edges, two layers deep."""
    layer0 = {seed}
    layer1 = set(g.successors(seed)) - layer0
    layer2 = set()
    for v in layer1:
        layer2.update(g.successors(v))
    layer2 -= layer0 | layer1
    return sorted(layer0 | layer1 | layer2)


def _mean_ci(values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return np.nan, np.nan, np.nan
    mean = float(values.mean())
    if len(values) == 1:
        return mean, np.nan, np.nan
    from scipy.stats import t

    half = float(t.ppf(0.975, len(values) - 1)) * float(values.std(ddof=1)) / np.sqrt(len(values))
    return mean, mean - half, mean + half


def run_experiment(
    n=100_000,
    alpha_in=2.3,
    alpha_out=2.6,
    n_graphs=5,
    seeds_per_graph=2,
    seed=7,
    base_out=48,
):
    """Repeat the crawl over independent graphs, then aggregate by graph."""
    rows = []
    graph_rows = []
    last_g, last_true_in = None, None
    for graph_id, child_seed in enumerate(np.random.SeedSequence(seed).spawn(n_graphs)):
        rng = np.random.default_rng(child_seed)
        g = make_directed_powerlaw_graph(n, alpha_in, alpha_out, rng, base_out)
        true_in = np.array(g.degree(mode="in"))
        fit_true = _fit(true_in[true_in > 0])
        true_alpha = float(fit_true.power_law.alpha)
        graph_rows.append(
            {"graph_id": graph_id, "n_edges": g.ecount(), "alpha_true": true_alpha}
        )

        # Seeds mimic an active but non-hub account. Multiple seeds within one
        # graph are not treated as independent graph replicates.
        dout = np.array(g.degree(mode="out"))
        candidates = np.where((dout >= 100) & (dout <= 400))[0]
        if len(candidates) < seeds_per_graph:
            candidates = np.where(dout >= np.quantile(dout, 0.9))[0]
        take = min(seeds_per_graph, len(candidates))
        for s in rng.choice(candidates, size=take, replace=False):
            sampled = bfs_two_layers(g, int(s))
            if len(sampled) < min(500, max(50, n // 200)):
                continue
            profile_in = true_in[sampled]
            induced = g.induced_subgraph(sampled)
            induced_in = np.array(induced.degree(mode="in"))

            fit_profile = _fit(profile_in[profile_in > 0])
            fit_induced = _fit(induced_in[induced_in > 0])
            rows.append(
                {
                    "graph_id": graph_id,
                    "seed": int(s),
                    "n_sampled": len(sampled),
                    "frac_sampled": len(sampled) / n,
                    "alpha_true": true_alpha,
                    "alpha_profile": fit_profile.power_law.alpha,
                    "alpha_induced": fit_induced.power_law.alpha,
                    "bias_profile": fit_profile.power_law.alpha - true_alpha,
                    "bias_induced": fit_induced.power_law.alpha - true_alpha,
                    "mean_true_in_sampled": profile_in.mean(),
                    "mean_true_in_all": true_in.mean(),
                }
            )
        last_g, last_true_in = g, true_in

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("no valid BFS samples; adjust graph size or seed criteria")
    graph_df = pd.DataFrame(graph_rows)
    graph_bias = df.groupby("graph_id")[["bias_profile", "bias_induced"]].mean()
    profile_bias, profile_low, profile_high = _mean_ci(graph_bias["bias_profile"])
    induced_bias, induced_low, induced_high = _mean_ci(graph_bias["bias_induced"])
    summary = {
        "n_nodes": n,
        "n_edges_mean": float(graph_df["n_edges"].mean()),
        "alpha_in_propensity": alpha_in,
        "alpha_true_fitted": float(graph_df["alpha_true"].mean()),
        "alpha_true_fitted_std": float(graph_df["alpha_true"].std()),
        "alpha_profile_mean": df["alpha_profile"].mean(),
        "alpha_profile_std": df["alpha_profile"].std(),
        "alpha_induced_mean": df["alpha_induced"].mean(),
        "alpha_induced_std": df["alpha_induced"].std(),
        "bias_profile_graph_mean": profile_bias,
        "bias_profile_graph_ci95": [profile_low, profile_high],
        "bias_induced_graph_mean": induced_bias,
        "bias_induced_graph_ci95": [induced_low, induced_high],
        "oversampling_of_degree": (df["mean_true_in_sampled"] / df["mean_true_in_all"]).mean(),
        "n_graphs": n_graphs,
        "n_valid_graphs": int(df["graph_id"].nunique()),
        "seeds_per_graph": seeds_per_graph,
        "n_valid_seeds": len(df),
    }
    return summary, df, last_g, last_true_in


def report_markdown(summary, df):
    lines = [
        "# BFS 两层采样偏差模拟 (T1.3)",
        "",
        f"每张合成有向图：{summary['n_nodes']:,} 节点 / 平均 {summary['n_edges_mean']:,.0f} 边；"
        f"入度目标倾向权重指数 α = {summary['alpha_in_propensity']}",
        f"独立图重复：{summary['n_graphs']}；每图种子：{summary['seeds_per_graph']}",
        "",
        "| 估计方式 | 拟合 α (mean ± std) |",
        "|---|---|",
        f"| 全图真实入度 | {summary['alpha_true_fitted']:.3f} ± {summary['alpha_true_fitted_std']:.3f} |",
        f"| 被采样节点的画像计数 | {summary['alpha_profile_mean']:.3f} ± {summary['alpha_profile_std']:.3f} |",
        f"| 诱导子图入度 | {summary['alpha_induced_mean']:.3f} ± {summary['alpha_induced_std']:.3f} |",
        "",
        f"- 被采样节点的平均真实入度是全图平均的 **{summary['oversampling_of_degree']:.1f} 倍**"
        "（BFS 偏向高度数节点，Kurant et al. 2010 的效应）",
        f"- profile α 偏差（先按图聚合）的 95% CI：{summary['bias_profile_graph_ci95'][0]:.3f} 至 {summary['bias_profile_graph_ci95'][1]:.3f}",
        f"- induced α 偏差（先按图聚合）的 95% CI：{summary['bias_induced_graph_ci95'][0]:.3f} 至 {summary['bias_induced_graph_ci95'][1]:.3f}",
        f"- 有效图/种子数：{summary['n_valid_graphs']}/{summary['n_valid_seeds']}；同一图内种子不作为独立图重复",
        "",
        "注：幂律参数描述目标吸引力权重，而非声称每个实现入度都是未经变换的精确 zeta 抽样。"
        "所有偏差均相对于每张图简化后的实际全图拟合计算。",
        "",
        "## 每个种子的结果",
        "",
        df.round(3).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines)
