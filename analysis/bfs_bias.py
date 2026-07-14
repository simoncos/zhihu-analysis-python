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


def make_directed_powerlaw_graph(n, alpha_in, alpha_out, rng, base_out=48):
    """Configuration-model style directed graph from zeta-sampled degrees.

    In-degree is pure power law (the quantity under study). Out-degree gets a
    constant base plus a power-law tail so that the mean (~50) is in the same
    regime as real Zhihu followee counts (mean 176 in the 2015 data) — a pure
    zeta out-degree (mean < 2) would make a 2-layer BFS cover almost nothing.
    """
    import igraph as ig

    din = np.minimum(rng.zipf(alpha_in, n), n - 1)
    dout = np.minimum(base_out + rng.zipf(alpha_out, n), n - 1)
    # Directed config model needs equal in/out stubs; trim the surplus at random.
    diff = int(din.sum() - dout.sum())
    target = dout if diff > 0 else din
    surplus = abs(diff)
    while surplus > 0:
        idx = rng.integers(0, n, size=min(surplus * 2, 10 * n))
        for i in idx:
            if surplus == 0:
                break
            target[i] += 1
            surplus -= 1
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


def run_experiment(n=100_000, alpha_in=2.3, alpha_out=2.6, n_seeds=10, seed=7):
    rng = np.random.default_rng(seed)
    g = make_directed_powerlaw_graph(n, alpha_in, alpha_out, rng)
    true_in = np.array(g.degree(mode="in"))

    fit_true = _fit(true_in[true_in > 0])
    rows = []
    # Seeds mimic the real seed user (149 followees): active but not a top hub.
    dout = np.array(g.degree(mode="out"))
    candidates = np.where((dout >= 100) & (dout <= 400))[0]
    if len(candidates) < n_seeds:
        candidates = np.where(dout >= np.quantile(dout, 0.9))[0]
    for s in rng.choice(candidates, size=n_seeds, replace=False):
        sampled = bfs_two_layers(g, int(s))
        if len(sampled) < 500:
            continue
        profile_in = true_in[sampled]
        induced = g.induced_subgraph(sampled)
        induced_in = np.array(induced.degree(mode="in"))

        fit_profile = _fit(profile_in[profile_in > 0])
        fit_induced = _fit(induced_in[induced_in > 0])
        rows.append(
            {
                "seed": int(s),
                "n_sampled": len(sampled),
                "frac_sampled": len(sampled) / n,
                "alpha_profile": fit_profile.power_law.alpha,
                "alpha_induced": fit_induced.power_law.alpha,
                "mean_true_in_sampled": profile_in.mean(),
                "mean_true_in_all": true_in.mean(),
            }
        )
    df = pd.DataFrame(rows)
    summary = {
        "n_nodes": n,
        "n_edges": g.ecount(),
        "alpha_in_planted": alpha_in,
        "alpha_true_fitted": fit_true.power_law.alpha,
        "alpha_profile_mean": df["alpha_profile"].mean(),
        "alpha_profile_std": df["alpha_profile"].std(),
        "alpha_induced_mean": df["alpha_induced"].mean(),
        "alpha_induced_std": df["alpha_induced"].std(),
        "oversampling_of_degree": (df["mean_true_in_sampled"] / df["mean_true_in_all"]).mean(),
        "n_valid_seeds": len(df),
    }
    return summary, df, g, true_in


def report_markdown(summary, df):
    lines = [
        "# BFS 两层采样偏差模拟 (T1.3)",
        "",
        f"合成有向图：{summary['n_nodes']:,} 节点 / {summary['n_edges']:,} 边，"
        f"植入入度幂指数 α = {summary['alpha_in_planted']}",
        "",
        "| 估计方式 | 拟合 α (mean ± std) |",
        "|---|---|",
        f"| 全图真实入度 | {summary['alpha_true_fitted']:.3f} |",
        f"| 被采样节点的画像计数 | {summary['alpha_profile_mean']:.3f} ± {summary['alpha_profile_std']:.3f} |",
        f"| 诱导子图入度 | {summary['alpha_induced_mean']:.3f} ± {summary['alpha_induced_std']:.3f} |",
        "",
        f"- 被采样节点的平均真实入度是全图平均的 **{summary['oversampling_of_degree']:.1f} 倍**"
        "（BFS 偏向高度数节点，Kurant et al. 2010 的效应）",
        f"- 有效种子数：{summary['n_valid_seeds']}（每个种子一次独立 2 层 BFS）",
        "",
        "注：'全图真实入度'的 α 以简化（去重边/自环）后实际生成的图为准，"
        "它与植入参数的差异来自配置模型的重边合并，不影响三种估计方式之间的比较。",
        "",
        "## 每个种子的结果",
        "",
        df.round(3).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines)
