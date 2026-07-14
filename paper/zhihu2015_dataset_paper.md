# Zhihu2015: A Follow-Network Snapshot of China's Largest Q&A Community

> Dataset paper draft v0.1 — target venue: ICWSM dataset track (alt.:
> NeurIPS D&B, Scientific Data, CSCW). `[TODO]` = fill after real-data run.
> Numbers in §6 come from `results/powerlaw_results.md`, §7 from
> `results/bfs_bias_simulation.md` (already final).

## Abstract

We release Zhihu2015, a December-2015 snapshot of the follow network of
Zhihu, then and now the largest Chinese community question answering (CQA)
platform. The dataset covers [TODO 26,161] users with complete profile
counts, [TODO 4.6M] directed follow edges, and [TODO 5.4M] user-topic
activity records spanning [TODO 2.2M] questions. To our knowledge it is the
only public dataset of Zhihu's social graph: the official ZhihuRec dataset
exposes recommendation logs but no follow relations, and today's
anti-crawling measures make the graph impossible to re-collect. Alongside
the data we contribute (i) a rigorous re-analysis of its degree and
activity distributions using likelihood-based model comparison, revising
the "power law by visual inspection" claims of the original 2015 report,
and (ii) a simulation-based quantification of the bias induced by the
crawl's 2-layer BFS design, showing that naive use of profile counts
underestimates the in-degree exponent by ≈0.6. We document anonymization,
residual re-identification risk, and intended uses including expert-finding
benchmarks, interest-homophily studies, and calibration of LLM-based social
simulations.

## 1. Introduction

Zhihu occupies a distinctive position among large online social platforms:
a directed follow graph, as on Twitter/Weibo, is interleaved with a
knowledge market — questions, answers, and a curated topic taxonomy. Yet
public structural data about Zhihu has always been scarce. Research on the
platform either uses small purpose-built crawls that are not released, or
the official ZhihuRec recommendation logs, which contain no social graph.

This paper releases and documents a snapshot collected in December 2015,
when Zhihu had roughly 30M registered users. The snapshot originates from a
2015 course project; we publish it a decade later because its value has
inverted: no longer current, it is now unreproducible history — login
walls and anti-crawling infrastructure have made large-scale collection of
Zhihu's follow graph infeasible, and the 2015 "golden era" community it
captures no longer exists in that form.

Contributions:
1. **The dataset**: five tables (users, edges, questions, user-questions,
   user-topics) under CC BY 4.0, pseudonymized, with datasheet, on
   Zenodo (DOI) and Hugging Face.
2. **A rigorous statistical characterization** (§6), replacing the original
   report's visual power-law claims with CSN maximum-likelihood fits and
   model comparison — contributing a Chinese-CQA data point to the
   scale-free-networks debate.
3. **A sampling-bias analysis** (§7): the crawl is a single-seed, 2-layer
   out-link BFS; we quantify on synthetic graphs how this design distorts
   degree-distribution estimates, separating two estimators (profile counts
   vs induced-subgraph degrees) that future users of the data must not
   conflate.

## 2. Related Datasets

- **ZhihuRec** (THUIR × Zhihu, 2021): ~100M recommendation interactions,
  10M+ users; rich impression logs, **no follow edges**. Complementary:
  behavioral vs structural.
- **Zhihu expert-identification pairs** (Xu et al. 2017): 1.2M QA pairs for
  supervised expert finding; no graph.
- **Other CQA graphs**: Stack Exchange dumps (interaction, not follow,
  graphs); Quora has no public graph data. Historical follow-graph
  snapshots exist for Twitter (Kwak et al. 2010) and have proven durably
  valuable; Zhihu2015 plays that role for the Chinese knowledge community.

[TODO: 补充近年是否出现其他知乎结构数据集的最终核查]

## 3. Collection Methodology (2015)

Two-stage multiprocess crawler over public profile pages (modified
zhihu-python), December 2015:
- **Stage 1** — from seed user *(pseudonymized)*, BFS along followee
  (out-link) lists, two layers deep; for each visited user: profile counts
  (followee/follower/answer/agree/thanks), followee list, answered
  question ids.
- **Stage 2** — topics of all collected question ids.
- Layer sizes: layer 0 = 1, layer 1 = [TODO], layer 2 = [TODO].
- Known defect: stage-2 crawler intermittently missed topic tags;
  [TODO %] of user_questions rows have a resolvable topic.

Only publicly visible information was collected; no text content.

## 4. Dataset Description

[TODO: schema table + exact row counts from stats.json + basic stats table
(mean/median/max of the five profile counts) + induced-subgraph edge count]

Observation model: profile counts are exact platform-global values for the
crawled users; the follow graph is completely observed only on the induced
subgraph of crawled users. Edges to referenced-but-uncrawled accounts
([TODO] additional pseudonymous ids) are included for completeness.

## 5. Anonymization and Ethics

User URL slugs and display names are replaced by random integers. Question
ids are likewise pseudonymized — with raw ids, the public answerer list of
a question would re-identify users. Topic tags (public wiki labels) are
kept verbatim. Mapping tables remain with the maintainer; takedown requests
are honored via versioned re-release. Residual risk: count signatures of
extreme accounts could in principle be matched against 2015-era public
records; we assess this as low and document it in the datasheet.
[TODO: describe the celebrity-fingerprint self-check result]

## 6. Statistical Characterization

[TODO — from powerlaw_results.md once real data is in:
- Table: CSN fits for 5 profile counts + induced in/out degree
  (α, xmin, GOF p, LR vs lognormal/exponential/truncated PL, verdict)
- Expected headline: which of the 2015 "significant power law" claims
  survive; likely several downgrade to lognormal-indistinguishable,
  echoing Broido & Clauset (2019)
- CCDF figures
- agree–follower correlation, revisited with rank correlation + partial
  correlation controlling answer_num]

## 7. Sampling Bias of the 2-Layer BFS Design

(Final numbers; independent of the real data.)

We simulate the crawl on directed configuration-model graphs (100K nodes,
~5M edges, planted power-law in-degree; out-degree given a constant base +
power-law tail so that its mean ≈ 50, matching the regime of real followee
counts). Ten independent seeds with realistic out-degree (100–400) each
yield a 2-layer out-link BFS sample (~5–8% of nodes).

| in-degree estimator | fitted α (mean ± std) |
|---|---|
| ground truth, full graph | 2.98 |
| profile counts of sampled nodes | 2.38 ± 0.16 |
| induced-subgraph degrees | 2.63 ± 0.15 |

Two findings with direct consequences for users of this dataset:
1. **Profile counts are individually exact but collectively biased**: BFS
   overselects high-in-degree nodes, thickening the observed tail and
   underestimating α by ≈0.6 (consistent with Kurant et al. 2010).
2. Induced-subgraph degrees combine node overselection with edge
   truncation; the net bias is smaller here but less predictable.

Any distributional claim from this dataset must therefore be stated
relative to the sampling frame; §6's fits are reported for both estimators.

## 8. Intended Uses

1. **Expert finding / question routing benchmarks**: follow graph +
   user-topic bipartite graph in one dataset supports the current
   "social relations × topical expertise" research line.
2. **Interest-structure alignment**: do follow communities coincide with
   interest clusters? (Our follow-up work.)
3. **Historical baseline**: structural comparison target for studies of
   platform evolution and community decay.
4. **Simulation calibration**: real network snapshot for initializing and
   validating LLM-agent social simulations, which currently lack
   ground-truth topologies.

## 9. Limitations

Single-seed 2-layer BFS frame (§7); no timestamps; no text; topic-tag gaps
([TODO %]); 2015 vintage — none of these are fixable, all are documented.

## 10. Availability

Zenodo DOI [TODO] (canonical, versioned) · Hugging Face `simoncos/zhihu2015`
(mirror) · code: github.com/simoncos/zhihu-analysis-python (analysis +
release pipeline, MIT). License CC BY 4.0.

## References

[TODO: Broido & Clauset 2019; Kurant et al. 2010; Gjoka et al. 2010;
Clauset, Shalizi & Newman 2009; Alstott et al. 2014 (powerlaw); ZhihuRec
(Hao et al. 2021); Xu et al. 2017; Kwak et al. 2010; Gebru et al. 2021
(datasheets); survey Yuan et al. 2018 (expert rec in CQA)]
