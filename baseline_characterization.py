# -*- coding: utf-8 -*-
"""
Dual-baseline structural characterization of the 2015 Zhihu snapshot
(literature review recommendation 6.4, see analysis-report/literature-review-2026.md).

The 2015 dataset predates both Zhihu's monetization era (Zhihu Live launched
May 2016) and the generative-AI era, making it a "pre-everything" baseline.
This script characterizes the snapshot so later states of the platform (e.g.
ZhihuRec 2021 aggregates, or a future re-crawl) can be compared against it:

  1. Global following-network topology: density, reciprocity, clustering,
     assortativity, k-core depth, connected-component structure, path lengths
     (sampled) — the small-world profile claimed for Zhihu Live interaction
     networks (Tu & Xin, WHICEB 2020).
  2. Contribution concentration: Gini coefficients and top-1% / next-9% /
     bottom-90% shares for answers, agrees, thanks and internal in-degree —
     a direct 2015 test of the "90-9-1 pyramid" characterization
     (涂艳等, 北京理工大学学报(社科版) 2022).
  3. Topic layer: topic-size distribution of the user-topic bipartite graph.

Usage:
    python baseline_characterization.py [path/to/zhihu.db] [--out baseline_results]
"""

import argparse
import os
import sqlite3

import numpy as np
import pandas as pd
import scipy.sparse as sp

SEED = 42


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def shares(x):
    """Return (top 1%, next 9%, bottom 90%) shares of the total of x."""
    x = np.sort(np.asarray(x, dtype=float))[::-1]
    n, total = len(x), x.sum()
    if total == 0:
        return 0.0, 0.0, 0.0
    p1 = x[:max(1, n // 100)].sum() / total
    p10 = x[:max(1, n // 10)].sum() / total
    return float(p1), float(p10 - p1), float(1 - p10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db', nargs='?', default='zhihu.db')
    parser.add_argument('--out', default='baseline_results')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(SEED)

    conn = sqlite3.connect(args.db)
    users = pd.read_sql('select user_url, followee_num, follower_num, answer_num,'
                        ' agree_num, thanks_num from User', conn)
    edges = pd.read_sql(
        'select user_url, followee_url from Following '
        'where user_url in (select user_url from User) '
        'and followee_url in (select user_url from User)', conn)
    topic_sizes = pd.read_sql(
        'select topic, count(distinct user_url) sz from UserTopic group by topic', conn)
    conn.close()

    uid = {u: i for i, u in enumerate(users.user_url)}
    n = len(uid)
    src = edges.user_url.map(uid).values
    dst = edges.followee_url.map(uid).values
    m = len(src)

    A = sp.csr_matrix((np.ones(m), (src, dst)), shape=(n, n))
    A.data[:] = 1
    in_deg = np.asarray(A.sum(0)).ravel()
    out_deg = np.asarray(A.sum(1)).ravel()

    lines = ['# Structural baseline of the 2015 Zhihu snapshot (pre-monetization, pre-AI)', '']

    # ---- 1. global topology -------------------------------------------------
    density = m / (n * (n - 1))
    recip = (A.multiply(A.T)).nnz / m  # fraction of edges whose reverse also exists

    und = ((A + A.T) > 0).astype(np.int8)
    und.setdiag(0)
    und.eliminate_zeros()
    # global clustering (transitivity) via sparse triangle counting
    deg_u = np.asarray(und.sum(1)).ravel()
    triangles = (und @ und).multiply(und).sum() / 6
    triads = (deg_u * (deg_u - 1)).sum() / 2
    transitivity = 3 * triangles / triads if triads else 0.0

    # degree assortativity (undirected, Pearson over edge endpoint degrees)
    eu, ev = und.nonzero()
    assort = float(np.corrcoef(deg_u[eu], deg_u[ev])[0, 1])

    # k-core depth
    import networkx as nx
    Gu = nx.from_scipy_sparse_array(und)
    core = nx.core_number(Gu)
    max_core = max(core.values())

    # components
    n_wcc, wcc_labels = sp.csgraph.connected_components(und, directed=False)
    wcc_sizes = np.bincount(wcc_labels)
    n_scc, scc_labels = sp.csgraph.connected_components(A, directed=True, connection='strong')
    scc_sizes = np.bincount(scc_labels)

    # sampled shortest paths within the giant WCC (undirected)
    giant = np.flatnonzero(wcc_labels == wcc_sizes.argmax())
    sample = rng.choice(giant, size=min(200, len(giant)), replace=False)
    dists = []
    for s in sample:
        d = sp.csgraph.shortest_path(und, method='BF', unweighted=True, indices=s)
        d = d[giant]
        dists.append(d[np.isfinite(d) & (d > 0)])
    dists = np.concatenate(dists)
    avg_path, diam_lb = float(dists.mean()), int(dists.max())

    lines += [
        '## 1. Following-network topology (intra-snapshot edges)', '',
        '| metric | value |', '|---|---|',
        '| users | %d |' % n,
        '| following edges (within snapshot) | %d |' % m,
        '| density | %.5f |' % density,
        '| reciprocity (mutual-edge fraction) | %.3f |' % recip,
        '| global clustering (transitivity) | %.3f |' % transitivity,
        '| degree assortativity (undirected) | %.3f |' % assort,
        '| max k-core | %d |' % max_core,
        '| weakly connected components | %d (giant: %d users, %.1f%%) |'
        % (n_wcc, wcc_sizes.max(), 100 * wcc_sizes.max() / n),
        '| strongly connected components | %d (giant: %d users, %.1f%%) |'
        % (n_scc, scc_sizes.max(), 100 * scc_sizes.max() / n),
        '| avg shortest path (sampled, giant WCC) | %.2f |' % avg_path,
        '| diameter (lower bound from sample) | %d |' % diam_lb,
        '',
        'Small-world check: avg path %.2f with clustering %.3f at density %.5f '
        '(random-graph clustering would be ~density) -> clustering is %.0fx the '
        'random expectation, i.e. a small-world profile already present in 2015.'
        % (avg_path, transitivity, density, transitivity / density),
        '',
    ]

    # ---- 2. contribution concentration -------------------------------------
    lines += ['## 2. Contribution concentration (90-9-1 pyramid test)', '',
              '| feature | Gini | top 1% share | next 9% | bottom 90% |',
              '|---|---|---|---|---|']
    conc_rows = {}
    for label, x in [('answers', users.answer_num), ('agrees', users.agree_num),
                     ('thanks', users.thanks_num),
                     ('followers (platform-wide)', users.follower_num),
                     ('in-degree (within snapshot)', in_deg)]:
        g = gini(x)
        p1, p9, p90 = shares(x)
        conc_rows[label] = (g, p1, p9, p90)
        lines.append('| %s | %.3f | %.1f%% | %.1f%% | %.1f%% |'
                     % (label, g, 100 * p1, 100 * p9, 100 * p90))
    lines += ['',
              'The 90-9-1 rule (涂艳等 2022) posits ~1%% of users dominate contribution. '
              'On this 2015 snapshot the top 1%% of users already hold %.0f%% of agrees '
              'and %.0f%% of answers.' % (100 * conc_rows['agrees'][1],
                                          100 * conc_rows['answers'][1]),
              '']

    # ---- 3. topic layer ------------------------------------------------------
    sz = topic_sizes.sz.values
    lines += ['## 3. Topic layer (user-topic bipartite)', '',
              '| metric | value |', '|---|---|',
              '| distinct topics | %d |' % len(sz),
              '| topics with >= 20 users | %d |' % (sz >= 20).sum(),
              '| median / mean topic size | %d / %.1f |' % (int(np.median(sz)), sz.mean()),
              '| largest topic size | %d |' % sz.max(),
              '| topic-size Gini | %.3f |' % gini(sz),
              '']

    # ---- plots ---------------------------------------------------------------
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for label, x in [('agrees', users.agree_num), ('answers', users.answer_num),
                     ('in-degree', in_deg)]:
        xs = np.sort(np.asarray(x, float))
        cum = np.cumsum(xs) / xs.sum()
        ax.plot(np.linspace(0, 1, len(xs)), cum, label='%s (Gini %.2f)' % (label, gini(x)))
    ax.plot([0, 1], [0, 1], 'k--', lw=0.8, label='perfect equality')
    ax.set_xlabel('cumulative share of users (poorest first)')
    ax.set_ylabel('cumulative share of total')
    ax.set_title('Lorenz curves, 2015 Zhihu snapshot')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, 'lorenz_curves.png'), dpi=150)
    plt.close(fig)

    out_md = os.path.join(args.out, 'baseline_characterization.md')
    with open(out_md, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print('\nwrote %s and lorenz_curves.png' % out_md)


if __name__ == '__main__':
    main()
