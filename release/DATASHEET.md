# Datasheet: Zhihu2015 Follow Network Dataset

Following the *Datasheets for Datasets* framework (Gebru et al., 2021).
`[TODO]` marks values to fill from the real data after `analysis/release.py` runs.

## Motivation

- **Purpose.** Collected in December 2015 for a course project on social
  network analysis of Zhihu, then the largest Chinese Q&A community
  (~30M registered users at the time). Released a decade later as a
  historical snapshot: to our knowledge no other public dataset captures
  Zhihu's *follow network* structure, and this period ("golden era" Zhihu)
  can no longer be re-crawled.
- **Creators.** Zhao Che and course teammates (CUHK course project, 2015);
  release prepared 2026.

## Composition

- **Instances.** Five tables (Parquet):
  - `users`: [TODO ~26,161] crawled users × 5 profile counts
    (followee/follower/answer/agree/thanks) + BFS layer;
  - `edges`: [TODO ~4.6M] directed follow edges (src follows dst),
    including edges to ~[TODO] referenced-but-not-crawled users;
  - `questions`: [TODO ~2.2M] question → topic tag pairs;
  - `user_questions`: [TODO ~1.7M] who answered which question;
  - `user_topics`: [TODO ~5.4M] user → topic rows (duplicates = counts).
- **Sampling.** NOT a random sample: 2-layer BFS (out-links/followees) from
  a single seed user. The induced subgraph among crawled users is completely
  observed; everything else is partially observed. Known biases are
  quantified in the accompanying paper (BFS oversamples high-degree users;
  simulation shows the fitted in-degree exponent is underestimated by ~0.6).
- **Known quality issues.** A crawler bug caused some question→topic tags to
  be missed; coverage is quantified in the paper ([TODO %]). Counts are
  point-in-time profile values, not aggregates of the crawled content.

## Collection Process

- Crawled Dec 2015 via a modified zhihu-python scraper (multiprocess BFS,
  two stages: user profiles + followees + answered-question ids, then
  question topics). Only information publicly visible on profile pages
  was collected. No answer/question text was collected.

## Preprocessing

- `analysis/release.py`: user identifiers (URL slugs and display names)
  replaced by random integers; question ids likewise pseudonymized (real
  question ids would allow re-identification via public answerer lists).
  Topic tags are public wiki labels and are kept verbatim. De-duplication
  of edges; no other filtering. The id mappings are retained privately by
  the maintainer and are not distributed.

## Uses

- Intended: network-structure research (degree distributions, communities,
  centrality), interest/homophily studies via the user-topic bipartite
  graph, expert-finding benchmarks, historical comparison, initialization
  or calibration of social simulations.
- Not suitable for: content/NLP research (no text), longitudinal claims
  about *current* Zhihu, or any attempt to re-identify individuals.

## Distribution

- Zenodo (DOI, versioned, canonical) + Hugging Face Datasets (mirror,
  discoverability). License: CC BY 4.0 for the compiled dataset; underlying
  profile facts were publicly visible on zhihu.com in 2015.
- Citation: see CITATION.cff / the dataset paper.

## Ethics & Privacy

- All collected fields were public at crawl time; the release removes
  usernames and URL slugs and pseudonymizes question ids.
- Residual risk: users with extreme, publicly known profile counts
  (e.g. a specific follower count in Dec 2015) could in principle be
  re-identified from count signatures; we judge this low-risk because the
  counts are 10+ years stale, but we document it explicitly.
- Takedown: contact the maintainer to have a specific pseudonymized record
  removed in a new version.

## Maintenance

- Maintainer: simoncos (GitHub). Errata and new versions via Zenodo
  versioning; issues via the GitHub repository.
