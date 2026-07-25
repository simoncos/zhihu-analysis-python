# -*- coding: utf-8 -*-
"""Phase 0.3: data health check. Produces a markdown report."""

import gc

import pandas as pd
import pyarrow.parquet as pq

from .data_io import EXPECTED_COUNTS, TABLES, load_parquet


def run_health_check(parquet_dir):
    lines = ["# 数据体检报告 (Phase 0.3)", ""]

    lines += ["## 记录数 vs 2015 报告", "", "| 表 | 实际 | 报告值(约) | 比例 |", "|---|---|---|---|"]
    for t in TABLES:
        n = pq.ParquetFile(f"{parquet_dir}/{t}.parquet").metadata.num_rows
        exp = EXPECTED_COUNTS[t]
        lines.append(f"| {t} | {n:,} | {exp:,} | {n / exp:.2f} |")

    user = load_parquet(
        parquet_dir,
        "User",
        columns=[
            "user_url",
            "followee_num",
            "follower_num",
            "answer_num",
            "agree_num",
            "thanks_num",
            "layer",
        ],
    )
    following = load_parquet(
        parquet_dir, "Following", columns=["user_url", "followee_url"]
    )

    dup_user = user["user_url"].duplicated().sum()
    dup_edge = following.duplicated(subset=["user_url", "followee_url"]).sum()
    self_loops = (following["user_url"] == following["followee_url"]).sum()
    lines += ["", "## 完整性", ""]
    lines.append(f"- User 表重复 user_url：{dup_user}")
    lines.append(f"- Following 重复边：{dup_edge}")
    lines.append(f"- 自环：{self_loops}")

    crawled = set(user["user_url"])
    dangling = (~following["followee_url"].isin(crawled)).mean()
    lines.append(f"- Following 中指向 User 表外的边占比（悬挂引用）：{dangling:.1%}")
    lines.append("  - 这是预期现象：只有 User 表内节点间的诱导子图是完整观测的采样框")

    if "layer" in user.columns:
        layer_counts = user["layer"].value_counts(dropna=False).sort_index()
        lines += ["", "## layer 分布", ""]
        for k, v in layer_counts.items():
            lines.append(f"- layer={k}: {v:,}")

    del following
    gc.collect()

    q = load_parquet(parquet_dir, "Question", columns=["question_id"])
    uq = load_parquet(parquet_dir, "UserQuestion", columns=["question_id"])
    q_known = uq["question_id"].isin(set(q["question_id"])).mean()
    del q, uq
    gc.collect()

    ut = load_parquet(parquet_dir, "UserTopic", columns=["user_url", "topic"])
    users_with_topic = user["user_url"].isin(set(ut["user_url"])).mean()
    lines += ["", "## 话题覆盖（当年已知的 topic 爬漏问题）", ""]
    lines.append(f"- UserQuestion 中 question_id 能在 Question 表找到话题的比例：{q_known:.1%}")
    lines.append(f"- 至少有一条 UserTopic 记录的用户比例：{users_with_topic:.1%}")
    lines.append(f"- 不同话题标签数：{ut['topic'].nunique():,}")

    na_topics = ut["topic"].isna().sum() + (ut["topic"].astype(str).str.strip() == "").sum()
    lines.append(f"- 空/空白话题标签：{na_topics}")
    del ut
    gc.collect()

    zero_feature_users = (user[["followee_num", "follower_num"]].sum(axis=1) == 0).mean()
    lines += ["", "## 特征字段", ""]
    lines.append(f"- followee_num+follower_num 均为 0 的用户比例：{zero_feature_users:.1%}")
    desc = user[["followee_num", "follower_num", "answer_num", "agree_num", "thanks_num"]].describe()
    lines += ["", "```", desc.to_string(), "```", ""]

    return "\n".join(lines)
