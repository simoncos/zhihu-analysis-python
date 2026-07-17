# -*- coding: utf-8 -*-
"""
Heterogeneous-network expert finding on the 2015 Zhihu snapshot
(literature review recommendation 6.1, see analysis-report/literature-review-2026.md).

Compares four method generations on the same data and task:
  gen0  2015 toolkit      : in-degree, PageRank, HITS authority (structure-only scores)
  gen1  shallow embedding : DeepWalk (uniform random walks + word2vec) on the following graph
  gen2  homogeneous GNN   : GraphSAGE regression on the following graph
  gen3a hetero embedding  : metapath walks mixing following steps and User-Topic-User steps
  gen3b hetero GNN        : HeteroConv (user-follows-user + user-topic bipartite)

Task: predict expertise = log10(1 + agree_num) from network structure only.
agree/thanks/answer counts are used ONLY as evaluation labels, never as features.
Users are split 60/20/20 train/val/test; all methods are evaluated on the same
test users with Spearman rho, NDCG@100 and Precision@100 (overlap of predicted
vs. actual top-100 test users).

Usage:
    pip install torch torch_geometric gensim scikit-learn pandas scipy
    python expert_finding_analysis.py [path/to/zhihu.db] [--out expert_results]
"""

import argparse
import os
import sqlite3

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import spearmanr

SEED = 42
EMB_DIM = 64
WALKS_PER_NODE = 10
WALK_LEN = 40
TOPIC_MIN_USERS = 20


# ---------------------------------------------------------------- data loading

def load_graph(db_path):
    conn = sqlite3.connect(db_path)
    users = pd.read_sql('select user_url, agree_num from User', conn)
    edges = pd.read_sql(
        'select user_url, followee_url from Following '
        'where user_url in (select user_url from User) '
        'and followee_url in (select user_url from User)', conn)
    ut = pd.read_sql(
        'select user_url, topic from UserTopic '
        'where user_url in (select user_url from User)', conn)
    conn.close()

    uid = {u: i for i, u in enumerate(users.user_url)}
    n = len(uid)
    src = edges.user_url.map(uid).values
    dst = edges.followee_url.map(uid).values

    topic_counts = ut.groupby('topic').user_url.nunique()
    keep = set(topic_counts[topic_counts >= TOPIC_MIN_USERS].index)
    ut = ut[ut.topic.isin(keep)]
    tid = {t: i for i, t in enumerate(sorted(keep))}
    t_u = ut.user_url.map(uid).values
    t_t = ut.topic.map(tid).values

    y = np.log10(1 + users.agree_num.values.astype(float))
    print('users=%d follow_edges=%d topics=%d user_topic_pairs=%d'
          % (n, len(src), len(tid), len(t_u)))
    return n, src, dst, len(tid), t_u, t_t, y


def split_users(n, rng):
    idx = rng.permutation(n)
    n_tr, n_va = int(0.6 * n), int(0.2 * n)
    return idx[:n_tr], idx[n_tr:n_tr + n_va], idx[n_tr + n_va:]


# ----------------------------------------------------------------- evaluation

def ndcg_at_k(y_true, y_score, k=100):
    order = np.argsort(-y_score)[:k]
    gains = (2 ** y_true[order] - 1) / np.log2(np.arange(2, k + 2))
    ideal_order = np.argsort(-y_true)[:k]
    ideal = (2 ** y_true[ideal_order] - 1) / np.log2(np.arange(2, k + 2))
    return gains.sum() / ideal.sum()


def precision_at_k(y_true, y_score, k=100):
    return len(set(np.argsort(-y_score)[:k]) & set(np.argsort(-y_true)[:k])) / k


def evaluate(name, y_test, score_test, results):
    rho = spearmanr(y_test, score_test).statistic
    row = {'method': name, 'spearman': rho,
           'ndcg@100': ndcg_at_k(y_test, score_test),
           'p@100': precision_at_k(y_test, score_test)}
    results.append(row)
    print('%-28s spearman=%.3f ndcg@100=%.3f p@100=%.2f'
          % (name, row['spearman'], row['ndcg@100'], row['p@100']))


def ridge_scores(emb, y, train, val, test):
    """Fit ridge on train embeddings, choose alpha on val, score test."""
    from sklearn.linear_model import Ridge
    best, best_rho = None, -2
    for alpha in [0.1, 1.0, 10.0, 100.0]:
        m = Ridge(alpha=alpha).fit(emb[train], y[train])
        rho = spearmanr(y[val], m.predict(emb[val])).statistic
        if rho > best_rho:
            best, best_rho = m, rho
    return best.predict(emb[test])


# ------------------------------------------------------- gen0: 2015 toolkit

def toolkit_scores(n, src, dst):
    A = sp.csr_matrix((np.ones(len(src)), (src, dst)), shape=(n, n))
    in_deg = np.asarray(A.sum(0)).ravel()
    out_deg = np.asarray(A.sum(1)).ravel()

    # PageRank by power iteration on the column-stochastic matrix
    d = 0.85
    P = sp.csr_matrix((np.ones(len(src)) / np.maximum(out_deg[src], 1), (dst, src)), shape=(n, n))
    pr = np.ones(n) / n
    dangling = out_deg == 0
    for _ in range(100):
        new = (1 - d) / n + d * (P @ pr + pr[dangling].sum() / n)
        if np.abs(new - pr).sum() < 1e-10:
            break
        pr = new

    # HITS by power iteration
    auth = np.ones(n)
    for _ in range(100):
        hub = A @ auth
        hub /= np.linalg.norm(hub) or 1
        auth = A.T @ hub
        auth /= np.linalg.norm(auth) or 1
    return in_deg, out_deg, pr, auth


# ---------------------------------------------- random walks (gen1 and gen3a)

def build_csr_neighbors(n, src, dst):
    und = sp.csr_matrix((np.ones(len(src) * 2), (np.r_[src, dst], np.r_[dst, src])), shape=(n, n))
    und.sum_duplicates()
    return und.indptr, und.indices


def deepwalk_walks(n, indptr, indices, rng):
    walks = []
    for _ in range(WALKS_PER_NODE):
        for start in rng.permutation(n):
            walk, cur = [start], start
            for _ in range(WALK_LEN - 1):
                lo, hi = indptr[cur], indptr[cur + 1]
                if lo == hi:
                    break
                cur = indices[lo + rng.integers(hi - lo)]
                walk.append(cur)
            walks.append(['u%d' % w for w in walk])
    return walks


def metapath_walks(n, indptr, indices, t_u, t_t, n_topic, rng):
    """Walks alternating: follow-step (prob .5) or user->topic->user hop (prob .5)."""
    ut = sp.csr_matrix((np.ones(len(t_u)), (t_u, t_t)), shape=(n, n_topic))
    tu = ut.T.tocsr()
    walks = []
    for _ in range(WALKS_PER_NODE):
        for start in rng.permutation(n):
            walk, cur = [('u', start)], start
            for _ in range(WALK_LEN - 1):
                use_topic = rng.random() < 0.5
                if use_topic and ut.indptr[cur] < ut.indptr[cur + 1]:
                    lo, hi = ut.indptr[cur], ut.indptr[cur + 1]
                    topic = ut.indices[lo + rng.integers(hi - lo)]
                    walk.append(('t', topic))
                    lo, hi = tu.indptr[topic], tu.indptr[topic + 1]
                    cur = tu.indices[lo + rng.integers(hi - lo)]
                else:
                    lo, hi = indptr[cur], indptr[cur + 1]
                    if lo == hi:
                        break
                    cur = indices[lo + rng.integers(hi - lo)]
                walk.append(('u', cur))
            walks.append(['%s%d' % w for w in walk])
    return walks


def word2vec_embeddings(walks, n, prefix='u'):
    from gensim.models import Word2Vec
    model = Word2Vec(walks, vector_size=EMB_DIM, window=5, min_count=0,
                     sg=1, workers=os.cpu_count() or 4, epochs=3, seed=SEED)
    emb = np.zeros((n, EMB_DIM))
    for i in range(n):
        key = '%s%d' % (prefix, i)
        if key in model.wv:
            emb[i] = model.wv[key]
    return emb


# ------------------------------------------------------------ gen2/gen3b: GNN

def structural_features(in_deg, out_deg):
    f = np.c_[np.log10(1 + in_deg), np.log10(1 + out_deg)]
    return (f - f.mean(0)) / (f.std(0) + 1e-9)


def train_gnn(feat, y, src, dst, train, val, test, hetero=None):
    import torch
    from torch_geometric.nn import SAGEConv, HeteroConv
    torch.manual_seed(SEED)

    y_t = torch.tensor(y, dtype=torch.float32)
    tr = torch.tensor(train)
    va = torch.tensor(val)
    te = torch.tensor(test)

    if hetero is None:
        edge_index = torch.tensor(np.r_['0,2', np.r_[src, dst], np.r_[dst, src]], dtype=torch.long)
        x = torch.tensor(feat, dtype=torch.float32)

        class Net(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.c1 = SAGEConv(feat.shape[1], EMB_DIM)
                self.c2 = SAGEConv(EMB_DIM, EMB_DIM)
                self.head = torch.nn.Linear(EMB_DIM, 1)

            def forward(self):
                h = self.c1(x, edge_index).relu()
                h = self.c2(h, edge_index).relu()
                return self.head(h).squeeze(-1)
    else:
        t_u, t_t, n_topic = hetero
        data_x = {'user': torch.tensor(feat, dtype=torch.float32),
                  'topic': torch.ones(n_topic, 1)}
        eis = {
            ('user', 'follows', 'user'): torch.tensor(np.r_['0,2', src, dst], dtype=torch.long),
            ('user', 'rev_follows', 'user'): torch.tensor(np.r_['0,2', dst, src], dtype=torch.long),
            ('user', 'likes', 'topic'): torch.tensor(np.r_['0,2', t_u, t_t], dtype=torch.long),
            ('topic', 'rev_likes', 'user'): torch.tensor(np.r_['0,2', t_t, t_u], dtype=torch.long),
        }

        class Net(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.c1 = HeteroConv({k: SAGEConv((-1, -1), EMB_DIM) for k in eis})
                self.c2 = HeteroConv({k: SAGEConv((-1, -1), EMB_DIM) for k in eis})
                self.head = torch.nn.Linear(EMB_DIM, 1)

            def forward(self):
                h = self.c1(data_x, eis)
                h = {k: v.relu() for k, v in h.items()}
                h = self.c2(h, eis)
                return self.head(h['user'].relu()).squeeze(-1)

    model = Net()
    opt = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    best_state, best_rho, patience = None, -2, 0
    for epoch in range(200):
        model.train()
        opt.zero_grad()
        out = model()
        loss = torch.nn.functional.mse_loss(out[tr], y_t[tr])
        loss.backward()
        opt.step()
        if epoch % 5 == 0:
            model.eval()
            with torch.no_grad():
                rho = spearmanr(y[val], model()[va].numpy()).statistic
            if rho > best_rho:
                best_rho, best_state, patience = rho, {k: v.clone() for k, v in model.state_dict().items()}, 0
            else:
                patience += 1
                if patience >= 6:
                    break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        return model()[te].numpy()


# ------------------------------------------------------------------------ main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db', nargs='?', default='zhihu.db')
    parser.add_argument('--out', default='expert_results')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(SEED)

    n, src, dst, n_topic, t_u, t_t, y = load_graph(args.db)
    train, val, test = split_users(n, rng)
    y_test = y[test]
    results = []

    print('\n--- gen0: 2015 toolkit (unsupervised structural scores) ---')
    in_deg, out_deg, pr, auth = toolkit_scores(n, src, dst)
    evaluate('in-degree', y_test, in_deg[test], results)
    evaluate('PageRank', y_test, pr[test], results)
    evaluate('HITS authority', y_test, auth[test], results)

    print('\n--- gen1: DeepWalk + ridge ---')
    indptr, indices = build_csr_neighbors(n, src, dst)
    emb_dw = word2vec_embeddings(deepwalk_walks(n, indptr, indices, rng), n)
    np.save(os.path.join(args.out, 'emb_deepwalk.npy'), emb_dw)
    evaluate('DeepWalk + ridge', y_test, ridge_scores(emb_dw, y, train, val, test), results)

    print('\n--- gen2: GraphSAGE (following graph) ---')
    feat = structural_features(in_deg, out_deg)
    evaluate('GraphSAGE', y_test, train_gnn(feat, y, src, dst, train, val, test), results)

    print('\n--- gen3a: metapath (user-topic) walks + ridge ---')
    emb_mp = word2vec_embeddings(
        metapath_walks(n, indptr, indices, t_u, t_t, n_topic, rng), n)
    np.save(os.path.join(args.out, 'emb_metapath.npy'), emb_mp)
    evaluate('Metapath walks + ridge', y_test, ridge_scores(emb_mp, y, train, val, test), results)

    print('\n--- gen3b: Heterogeneous GraphSAGE (following + user-topic) ---')
    evaluate('Hetero-GraphSAGE', y_test,
             train_gnn(feat, y, src, dst, train, val, test, hetero=(t_u, t_t, n_topic)), results)

    df = pd.DataFrame(results)
    df.to_csv(os.path.join(args.out, 'expert_finding_results.csv'), index=False)
    md = ['| method | Spearman ρ | NDCG@100 | P@100 |', '|---|---|---|---|']
    md += ['| %s | %.3f | %.3f | %.2f |' % (r['method'], r['spearman'], r['ndcg@100'], r['p@100'])
           for r in results]
    with open(os.path.join(args.out, 'expert_finding_results.md'), 'w') as f:
        f.write('# Expert finding on the 2015 Zhihu snapshot: four method generations\n\n')
        f.write('Task: predict log10(1+agree_num) from network structure only; '
                'test split of %d users.\n\n' % len(test))
        f.write('\n'.join(md) + '\n')
    print('\n' + '\n'.join(md))


if __name__ == '__main__':
    main()
