# -*- coding: utf-8 -*-
"""Generate a small synthetic zhihu.db matching zhihu_schema.sql,
for end-to-end smoke tests while the real dataset is unavailable."""

import sqlite3
from pathlib import Path

import numpy as np

TOPICS = [
    "生活", "历史", "电影", "心理学", "互联网", "编程", "音乐", "法律",
    "政治", "健康", "美食", "旅行", "教育", "经济", "文学", "游戏",
]


def generate(db_path, n_users=2000, seed=0):
    rng = np.random.default_rng(seed)
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    schema = Path(__file__).resolve().parent.parent / "zhihu_schema.sql"
    conn.executescript(schema.read_text())

    urls = [f"user-{i}" for i in range(n_users)]
    # Heavy-tailed profile counts.
    follower = rng.zipf(2.2, n_users)
    followee = rng.zipf(2.6, n_users)
    answer = rng.zipf(2.4, n_users)
    agree = follower * rng.integers(1, 5, n_users)
    thanks = (agree * rng.uniform(0.1, 0.4, n_users)).astype(int)
    layers = rng.choice([0, 1, 2], size=n_users, p=[0.001, 0.05, 0.949])

    conn.executemany(
        "insert into User (user_url, user_id, followee_num, follower_num, answer_num,"
        " agree_num, thanks_num, layer, is_crawled) values (?,?,?,?,?,?,?,?,1)",
        [
            (urls[i], f"用户{i}", int(followee[i]), int(follower[i]), int(answer[i]),
             int(agree[i]), int(thanks[i]), int(layers[i]))
            for i in range(n_users)
        ],
    )

    # Preferential attachment-ish edges; some point outside the crawled set.
    p_attach = follower / follower.sum()
    edges = set()
    for i in range(n_users):
        k = min(int(followee[i]), 50)
        for j in rng.choice(n_users, size=k, p=p_attach):
            if i != j:
                edges.add((urls[i], urls[int(j)]))
    external = {(urls[int(i)], f"external-{rng.integers(5000)}")
                for i in rng.integers(0, n_users, size=n_users)}
    conn.executemany(
        "insert into Following (user_url, followee_url) values (?,?)", sorted(edges | external)
    )

    # Questions with Zipf topics; users answer questions.
    n_q = n_users * 5
    q_ids = [f"q{i}" for i in range(n_q)]
    q_topics = [TOPICS[min(rng.zipf(1.5) - 1, len(TOPICS) - 1)] for _ in range(n_q)]
    conn.executemany("insert into Question (question_id, topic) values (?,?)", zip(q_ids, q_topics))

    uq, ut = set(), set()
    for i in range(n_users):
        for q in rng.integers(0, n_q, size=min(int(answer[i]), 30)):
            uq.add((urls[i], q_ids[q]))
            ut.add((urls[i], q_topics[q]))
    conn.executemany("insert into UserQuestion (user_url, question_id) values (?,?)", sorted(uq))
    conn.executemany("insert into UserTopic (user_url, topic) values (?,?)", sorted(ut))

    conn.commit()
    conn.close()
    return db_path
