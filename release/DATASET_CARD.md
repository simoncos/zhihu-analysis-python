---
license: cc-by-4.0
language:
  - zh
tags:
  - social-network
  - graph
  - community-question-answering
  - zhihu
  - network-science
pretty_name: Zhihu2015 Follow Network
size_categories:
  - 1M<n<10M
---

# Zhihu2015: a 2015 Snapshot of the Zhihu Follow Network

A historical (December 2015) snapshot of the follow network and
user-topic activity of Zhihu, the largest Chinese Q&A community.
To our knowledge the only public dataset of Zhihu's *social graph*
(the official ZhihuRec dataset covers recommendation logs, not the
follow network). This period of Zhihu can no longer be re-crawled.

**Canonical version & DOI:** Zenodo `[TODO: DOI]`. This HF repo is a mirror.
**Paper:** `[TODO: link]` · **Code:** https://github.com/simoncos/zhihu-analysis-python

## Files

| file | rows | schema |
|---|---|---|
| `users.parquet` | ~26K | `uid, followee_num, follower_num, answer_num, agree_num, thanks_num, layer` |
| `edges.parquet` | ~4.6M | `src, dst` (directed: src follows dst) |
| `questions.parquet` | ~2.2M | `qid, topic` |
| `user_questions.parquet` | ~1.7M | `uid, qid` |
| `user_topics.parquet` | ~5.4M | `uid, topic` (duplicate rows carry activity counts) |

`uid`/`qid` are random integers (see Privacy). Topic tags are original
Chinese strings. Exact row counts in `stats.json`.

## ⚠️ Read before using

1. **Sampling frame.** 2-layer BFS from a single seed user — not a uniform
   sample of Zhihu. Only the subgraph induced on the ~26K crawled users is
   completely observed. BFS oversamples high-degree users; see the paper's
   bias analysis before fitting distributions.
2. **Known gaps.** Some question→topic tags were missed by the 2015
   crawler (coverage quantified in the paper).
3. **Vintage.** All values are as of December 2015.

## Quick start

```python
import pandas as pd
edges = pd.read_parquet("edges.parquet")
users = pd.read_parquet("users.parquet")
crawled = set(users.uid)
induced = edges[edges.src.isin(crawled) & edges.dst.isin(crawled)]
```

## Privacy

Usernames and profile URLs removed; user and question identifiers replaced
by random integers (question ids are pseudonymized because real ids would
allow re-identification through public answerer lists). Full discussion in
`DATASHEET.md`.

## Citation

```bibtex
[TODO: bibtex after Zenodo DOI / paper acceptance]
```
