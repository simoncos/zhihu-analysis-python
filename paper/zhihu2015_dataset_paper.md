# Zhihu2015: A Follow-Network Snapshot of China's Largest Q&A Community

> Dataset paper draft v0.2 — target venue: ICWSM dataset track (alt.:
> NeurIPS D&B, Scientific Data, CSCW). The real-data artifacts in §6 predate
> the canonical direct TPL-vs-lognormal comparison and must be regenerated
> before submission. Dataset publication and DOI metadata are also pending.

## Abstract

We prepare Zhihu2015, a December-2015 snapshot of the follow network of
Zhihu, then and now the largest Chinese community question answering (CQA)
platform. The dataset covers 26,161 users with complete profile
counts, 4.61M directed follow edges (459K distinct accounts; 3.13M edges
form a fully-observed induced subgraph), and 5.41M user-topic
activity records spanning 2.25M questions and 46.6K topic tags. To our knowledge it is the
largest and most fully documented public snapshot of Zhihu's social graph:
the official ZhihuRec dataset exposes recommendation logs but no follow
relations, prior graph releases are two orders of magnitude smaller, and
today's anti-crawling measures make the graph impossible to re-collect. Alongside
the data we contribute (i) a reproducible re-analysis design for its degree
and activity distributions using likelihood-based model comparison and a
Monte Carlo-calibrated goodness-of-fit test; and (ii) a sensitivity-analysis
framework for the bias induced by the crawl's 2-layer BFS design, separating
profile-count and induced-subgraph estimators. Numerical claims from both
analyses remain withheld until the corrected canonical pipeline is rerun on
the private database. We document pseudonymization,
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

This paper documents a release candidate collected in December 2015,
when Zhihu had roughly 30M registered users. The snapshot originates from a
2015 course project; we publish it a decade later because its value has
inverted: no longer current, it is now unreproducible history — login
walls and anti-crawling infrastructure have made large-scale collection of
Zhihu's follow graph infeasible, and the 2015 "golden era" community it
captures no longer exists in that form.

Contributions:
1. **The dataset release package**: five pseudonymized tables (users, edges,
   questions, user-questions, user-topics), a datasheet and publication
   tooling. Zenodo/Hugging Face publication and final license metadata remain
   pending.
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
- **The CANE/CENE "Zhihu" benchmark** (Sun et al. 2016; Tu et al. 2017):
  a 10K-user follow-edge dataset with topic-description texts, widely
  reused in textual network embedding papers. It is the closest existing
  release; Zhihu2015 differs in scale (26K fully-profiled users, 459K
  referenced accounts, 4.6M edges vs ~44K), in carrying complete profile
  counts, BFS-layer provenance and the question/topic bipartite layer,
  and in documented collection methodology and bias analysis.
- **Event-scoped Zhihu data**: a multimodal dataset around a single viral
  event (Goldbach-conjecture claim; Fu et al. 2021) — temporal but not a
  platform-scale graph snapshot.
- **Other CQA graphs**: Stack Exchange dumps (interaction, not follow,
  graphs); Quora has no public graph data. Historical follow-graph
  snapshots exist for Twitter (Kwak et al. 2010) and have proven durably
  valuable; Zhihu2015 plays that role for the Chinese knowledge community.

Positioning: to our knowledge Zhihu2015 is the largest and most fully
documented public snapshot of Zhihu's follow network, and the only one
that couples the social graph with question/topic activity at this scale.

## 3. Collection Methodology (2015)

Two-stage multiprocess crawler over public profile pages (modified
zhihu-python), December 2015:
- **Stage 1** — from seed user *(pseudonymized)*, BFS along followee
  (out-link) lists, two layers deep; for each visited user: profile counts
  (followee/follower/answer/agree/thanks), followee list, answered
  question ids.
- **Stage 2** — topics of all collected question ids.
- Layer sizes: layer 0 = 1, layer 1 = 146, layer 2 = 26,014. (The seed's
  profile listed 149 followees; 3 accounts were deleted or failed to crawl
  — a measured example of the crawl's small losses.)
- Data quality (measured): 99.3% of answered-question ids resolve to at
  least one topic tag; at user level, 68.3% of users have topic records —
  13.6% of users answered nothing (no topics expected) and 18.2% answered
  questions but lack topic rows (stage-2 gap). Integrity checks: zero
  duplicate users, duplicate edges, or self-loops.

Only publicly visible information was collected; no text content.

## 4. Dataset Description

| table | rows | contents |
|---|---|---|
| users | 26,161 | 5 profile counts + BFS layer |
| edges | 4,612,110 | directed follows; 3,132,527 (67.9%) inside the crawled set |
| questions | 2,245,143 | question → topic tag |
| user_questions | 1,655,411 | who answered what |
| user_topics | 5,414,129 | user → topic activity (46,647 distinct tags) |

Profile counts (mean / median / max): followees 176.3 / 67 / 43,949;
followers 3,620.0 / 112 / 921,940; answers 68.9 / 17 / 10,807;
agrees 3,858.4 / 96 / 1,515,417; thanks 865.3 / 28 / 275,044.
All means and medians reproduce the original 2015 report exactly,
confirming the artifact's integrity across a decade of storage.

Observation model: profile counts are exact platform-global values for the
crawled users; the follow graph is completely observed only on the induced
subgraph of crawled users. Edges to 433,041 referenced-but-uncrawled
pseudonymous accounts are included for completeness. Contrary to the 2015
report's own analysis — which examined only elite subgraphs of ≤1,896
users — the full induced subgraph is large and dense (3.13M edges over
26K users, mean total degree ≈ 240), enabling graph analyses the original
project could not attempt.

## 5. Anonymization and Ethics

User URL slugs and display names are replaced by random integers. Question
ids are likewise pseudonymized — with raw ids, the public answerer list of
a question would re-identify users. Topic tags (public wiki labels) are
kept verbatim. Mapping tables remain with the maintainer; takedown requests
are honored via versioned re-release. Residual risk: count signatures of
extreme accounts could in principle be matched against 2015-era public
records; we assess this as low and document it in the datasheet.
We verified the risk concretely: the maximum follower count in the data
(921,940) is attributable to the publicly known most-followed Zhihu
account of late 2015. We accept and disclose this: affected accounts are
public figures, the exposed fields are aggregate counts that their
profiles displayed publicly, and no username or content is released.

## 6. Statistical Characterization

We fit each of the five profile-count distributions and the induced
subgraph's in/out-degree distributions with the CSN framework
(`powerlaw`: MLE α, KS-optimal x_min) and compare the power-law model
against lognormal, exponential, and truncated power law via normalized
Vuong likelihood-ratio tests. The primary reported verdict controls the
false-discovery rate across the seven GOF tests and, separately, across the
model-comparison family; unadjusted verdicts remain a sensitivity column.

**Canonical result status:** no publication-grade headline is currently
claimed. The archived table in `results/` is a 100-replicate run produced before the
canonical direct TPL-vs-lognormal comparison, deterministic bootstrap stream,
Monte Carlo correction, and exact-source manifest were implemented. It must
be replaced by an exact-commit run with at least 2,000 bootstrap replicates.

[TODO: insert the manifested canonical table after the private-database rerun.]

The canonical output will report corrected
Monte Carlo p-values, 95% simulation intervals, full sample accounting and an
explicit status when GOF is not evaluated.

The original 2015 report concluded from log-log scatter plots that all five
profile counts "show a significant power law". The archival likelihood-based
run casts doubt on that blanket claim, but its threshold-adjacent p-values and
100-replicate resolution are insufficient for a final count of rejected
series. The canonical pipeline now performs direct alternative comparison and
reports Monte Carlo uncertainty; final labels will be filled only after the
real-data rerun. Fits are explicitly conditional on positive observations,
not models of the full zero-inclusive count distribution.

CCDF plots for all seven series with fitted overlays:
`results/figures/` [TODO: select 2–3 for the paper].

### 6.2 Structure of the induced follow graph

The fully-observed induced subgraph (26,161 nodes, 3.13M edges) is a
single weak component containing a giant strongly connected component of
25,635 nodes (98.0%; 524 SCCs in total). Sampled average shortest path
length inside the giant SCC is 2.62 (500 sources) — descriptively shorter
than the 2015 report's elite-subgraph values of 2.11/1.85, but the difference
cannot be causally attributed to sampling frame or elite status from these
two summaries alone. Density is 4.6×10⁻³; global clustering
(undirected) 0.079; degree assortativity −0.186 (disassortative, typical
of follow networks). Reciprocity is 14.4% — notably lower than the 22.1%
reported for Twitter's early follow graph (Kwak et al. 2010). This descriptive
cross-platform contrast does not by itself identify whether Zhihu follows act
as interest subscriptions rather than social ties.

### 6.3 The topic layer

17,861 crawled users (68.3%) have topic records (plus 53 orphan ids with
topics but no profile row — a documented crawl artifact); the median such
user spans 71 distinct topics (mean 150.5). Tag usage is highly concentrated: the top
1% of the 46,647 tags account for 54.5% of all 5.41M rows. The
full-population top tags (调查类问题, 生活, 心理学, 恋爱, 互联网, 情感,
电影, 历史, …) largely reproduce the 2015 report's list — which was
computed only over a 220-user dominating set — indicating that the old
shortcut introduced little distortion at the top of the ranking, while
the full table now provides calibrated counts at every rank.

### 6.4 A demonstration: topic homophily of the follow relation

As a minimal validation that the two layers interact, the canonical analysis
compares topic-set Jaccard similarity on sampled follow edges with repeated
matched-target permutations. Each observed source is retained while its target
is replaced by a near neighbour matched on in/out-degree, answer activity,
topic-set size and crawl layer. This avoids the degree/activity confounding of
the earlier uniform-user null and reports the full null interval plus a
permutation p-value. Numerical results remain pending the real-data rerun;
community-level alignment remains a natural research use (§8).

## 7. Sampling Bias of the 2-Layer BFS Design

We simulate the historical crawl on independent directed
configuration-model graphs. Out-degree retains the shifted heavy-tailed
distribution needed for realistic two-layer expansion. Incoming stubs are
allocated from power-law-distributed target propensities while enforcing the
equal in/out-stub constraint; the analysis no longer claims that realized
in-degrees are untouched zeta draws. Multiple seeds within one graph are
aggregated before graph-level confidence intervals are computed.

The prior implementation balanced stubs by adding roughly 47 incoming stubs
per node under the default parameters, destroying its stated planted
distribution. Its reported ≈0.6 effect is therefore withdrawn. Corrected
multi-graph estimates and sensitivity analyses over density, seed activity
and degree parameters will be inserted after rerun. The defensible conclusion
at present is qualitative: a single-seed two-layer out-link BFS is a selected
sampling frame, and profile-count and induced-degree estimators need not share
the same bias.

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

Single-seed 2-layer BFS frame (§7); no timestamps; no text; user-level
topic gaps (18.2% of users with answers lack topic rows); 2015 vintage —
none of these are fixable, all are documented.

## 10. Ethics Statement

The data was collected in 2015 by student researchers for coursework,
before Zhihu offered an API, by scraping profile pages that were publicly
visible to any logged-in user; no private messages, drafts, or restricted
content were accessed, and no text content was retained. The collection
predates and was not subject to institutional IRB review; the present
*release* is where the ethical decisions lie, and we make them explicit:
(i) no usernames, URLs, or content are released; (ii) user and question
identifiers are pseudonymized (question ids specifically because public
answerer lists would otherwise re-identify users); (iii) re-identification
risk is measured rather than assumed away — 92.4% of users carry a unique
profile-count signature, which defeats casual identification only, and we
disclose that an adversary holding independent 2015 auxiliary data gains
nothing new from this release (§5); (iv) counts are not perturbed, a
deliberate utility/privacy trade-off we justify by the data's 10-year
staleness and its distributional payload (§6); (v) a takedown channel is
provided via versioned re-release. Automated collection was against the
letter of Zhihu's terms of service, as it is for essentially all
independent social-media research corpora of that era; we believe the
scientific value of preserving an unreproducible snapshot, combined with
the minimization above, justifies publication, and we welcome the
community's scrutiny of that judgement.

## 11. Availability

Planned: a versioned Zenodo DOI (canonical) and a Hugging Face dataset mirror.
The analysis and release-pipeline code is maintained at
github.com/simoncos/zhihu-analysis-python. No anonymous dataset release or
final dataset-license grant should be claimed until the publishing checklist
is complete and the old raw release asset has been removed or restricted.

## References

- Alstott, J., Bullmore, E., & Plenz, D. (2014). powerlaw: A Python
  package for analysis of heavy-tailed distributions. *PLoS ONE*, 9(1).
- Broido, A. D., & Clauset, A. (2019). Scale-free networks are rare.
  *Nature Communications*, 10, 1017.
- Clauset, A., Shalizi, C. R., & Newman, M. E. J. (2009). Power-law
  distributions in empirical data. *SIAM Review*, 51(4), 661–703.
- Fu, S., et al. (2021). Multimodal social network dataset based on the
  Goldbach-conjecture-proved event in Zhihu. (Dataset descriptor.)
- Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H.,
  Daumé III, H., & Crawford, K. (2021). Datasheets for datasets.
  *Communications of the ACM*, 64(12), 86–92.
- Gjoka, M., Kurant, M., Butts, C. T., & Markopoulou, A. (2010). Walking
  in Facebook: A case study of unbiased sampling of OSNs. *INFOCOM*.
- Hao, B., et al. (2021). A large-scale rich context query and
  recommendation dataset in online knowledge-sharing (ZhihuRec).
  arXiv:2106.06467.
- Kurant, M., Markopoulou, A., & Thiran, P. (2010). On the bias of BFS.
  *ITC 22* / arXiv:1004.1729.
- Kwak, H., Lee, C., Park, H., & Moon, S. (2010). What is Twitter, a
  social network or a news media? *WWW*.
- Narayanan, A., & Shmatikov, V. (2009). De-anonymizing social networks.
  *IEEE S&P*.
- Sun, X., Guo, J., Ding, X., & Liu, T. (2016). A general framework for
  content-enhanced network representation learning. arXiv:1610.02906.
- Traag, V. A., Waltman, L., & van Eck, N. J. (2019). From Louvain to
  Leiden: guaranteeing well-connected communities. *Scientific Reports*.
- Tu, C., Liu, H., Liu, Z., & Sun, M. (2017). CANE: Context-aware network
  embedding for relation modeling. *ACL*.
- Voitalov, I., van der Hoorn, P., van der Hofstad, R., & Krioukov, D.
  (2019). Scale-free networks well done. *Physical Review Research*.
- Xu, et al. (2017). A deep learning approach for expert identification
  in question answering communities. arXiv:1711.05350.
- Yuan, S., Zhang, Y., Tang, J., Hall, W., & Cabotà, J. B. (2020). Expert
  finding in community question answering: a review. *Artificial
  Intelligence Review* (survey version: arXiv:1807.05540).
- Zhang, J., Tang, J., & Li, J. (2015). ZhihuRank: A topic-sensitive
  expert finding algorithm in community question answering websites.
  *ICWL*.
