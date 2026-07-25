# Major Revision tracker

> Review baseline: `codex/canonical-integration@6222c2a`
> Last updated: 2026-07-25
> Decision: **Major Revision — suitable as an engineering integration baseline,
> but not yet ready for paper submission or public dataset release.**

This document preserves the substantive findings from the independent
statistics, reproducibility, and ethics/release reviews. It also records which
findings were addressed in the current remediation and which gates remain open.

## Important scope clarification

The review phrase “rewrite the BFS generation mechanism” refers only to the
**synthetic graph generator used to study BFS sampling bias** in
`analysis/bfs_bias.py`. It does not refer to the historical crawler, does not
propose collecting new data, and cannot change the ten-year-old dataset.

The historical dataset remains a single-seed, two-layer BFS snapshot. Simulation
can characterize sensitivity to that sampling design, but cannot reconstruct an
unbiased population sample or “correct” the old crawl.

## Status summary

| ID | Major Revision issue | Review severity | Current status | Publication gate |
|---|---|---:|---|---|
| MR-1 | Privacy, rights, and legacy raw-asset governance | P0 | **Deferred by decision** | Open and blocking |
| MR-2 | Statistical validity of BFS-bias, homophily, and power-law inference | P0/P1 | **Code remediated; real-data validation pending** | Depends on MR-4 |
| MR-3 | Release integrity and end-to-end reproducibility | P1 | **Engineering remediated; human release review pending** | Partly depends on MR-1/MR-4 |
| MR-4 | Exact-commit rerun on the recovered real database | P1 | **Blocked: `zhihu.db` unavailable locally** | Open and blocking |

## MR-1 — Privacy, rights, and legacy raw-asset governance

### Original findings

- The proposed public release is pseudonymized, not anonymous. The prior
  uniqueness audit found that 92.4% of users had a unique combination of five
  profile counts while the full follow graph and topic relationships were still
  retained.
- Repository materials reported that the original unredacted
  `dataset-v0/zhihu.zip` and an older Baidu share had circulated. Their current
  accessibility was not independently verified during the review.
- Therefore the paper’s earlier claim that holders of auxiliary information
  would learn nothing new was not supportable.

### Current decision

This item was deliberately deferred. The code now keeps private ID mappings
outside the public build and makes `publication_ready` fail closed, but those
engineering safeguards do not resolve the policy question.

### Closure evidence required

- Verify and restrict or remove any still-accessible raw release asset.
- Check the status of old third-party download links and document known prior
  circulation.
- Obtain an explicit privacy/ethics/rights decision among row-level public
  release, coarsened release, or controlled access.
- Complete human inspection of the final public files. Never publish
  `release_build_private/` or its equivalent.

## MR-2 — Statistical validity

### MR-2a: synthetic BFS-bias generator

The reviewed generator balanced directed stubs by adding millions of incoming
stubs to the smaller side. In the inspected configuration this added 4,730,566
incoming stubs, about 47.3 per node, invalidating the claimed planted in-degree
distribution and the archived “approximately 0.6” bias estimate.

The remediation:

- allocates incoming stubs using heavy-tailed target propensities while keeping
  total in- and out-stubs exactly balanced;
- repeats the experiment across independent synthetic graphs;
- aggregates seeds within each graph before computing graph-level confidence
  intervals;
- exposes seed, graph count, seeds per graph, layer depth, and distribution
  parameters in the CLI and manifest.

The old numeric claim remains withdrawn. A corrected simulation is a
sensitivity analysis of the historical sampling design, not a repair of the
historical crawler or dataset.

### MR-2b: homophily null model

The reviewed analysis compared observed edges with uniformly random user pairs.
That null mixed topic overlap with degree, activity, topic-set size, and crawl
layer, and treated a large collection of dyads as though it supplied independent
evidence.

The remediation uses repeated matched targets based on:

- in-degree and out-degree;
- answer activity;
- topic-set size;
- crawl layer.

It reports permutation-based uncertainty rather than treating dyads as
independent observations. The archived `1.83x` headline is withdrawn until the
real database is rerun.

### MR-2c: power-law goodness-of-fit and model selection

The reviewed workflow used only 100 bootstrap simulations, did not control all
random streams end to end, and could classify `--gof-sims 0` as statistical
support rather than “not evaluated.”

The remediation adds:

- deterministic random streams;
- the finite Monte Carlo correction `(b + 1) / (B + 1)`;
- exact binomial Monte Carlo intervals;
- explicit `not_evaluated` and invalid-fit states;
- finite-value checks;
- direct truncated-power-law versus lognormal comparison;
- Benjamini-Hochberg FDR control across the relevant test families;
- a canonical default of 2,500 GOF simulations.

No real-data power-law headline is accepted until MR-4 completes.

## MR-3 — Release integrity and reproducibility

### Original findings

- The public UID map did not close over every user appearing in
  `UserQuestion` and `UserTopic`; 53 known orphan UIDs could become null in the
  export.
- Release writes were not atomic and large SQLite tables were handled in ways
  that could exhaust memory or leave partial outputs.
- The environment was not exactly locked, and result files lacked sufficient
  source, configuration, dependency, seed, and artifact provenance.

### Remediation

- ID maps now close over every relation table and assert non-null integer IDs.
- The public schema is scanned for direct identifiers.
- Large SQLite-to-Parquet and release writes are chunked.
- Public outputs are replaced atomically; private mappings are written to a
  separate permission-restricted directory.
- `requirements-lock.txt` records the validated environment, and CI runs the
  unit/integrity suite plus a synthetic pipeline.
- Run manifests record the database hash, Git state, dependencies, seeds,
  configuration, and output hashes.
- The reproducibility gate is separate from publication approval;
  `publication_ready` remains false until privacy, rights, ethics, and human
  review are completed.

Synthetic validation and code tests establish these engineering contracts.
They do not prove that the real dataset is safe to publish.

## MR-4 — Exact-commit real-data rerun

The review requires a complete rerun from a clean, exact commit before updating
the paper’s headline numbers. The private `zhihu.db` was not found in the
repository, Documents, or Downloads, so this gate could not be completed.

After privately recovering the database, run:

```bash
python -m analysis.run_all \
  --db /private/path/to/zhihu.db \
  --out results/current \
  --gof-sims 2500 \
  --homophily-null-reps 200

python -m analysis.run_all \
  --bfs-bias \
  --out results/bfs-bias-current \
  --bfs-graphs 5 \
  --bfs-seeds-per-graph 2
```

Closure requires:

- a clean source commit recorded in `run_manifest.json`;
- a matching input database SHA-256;
- all expected artifact hashes and no partial output;
- all power-law fits evaluated at the intended bootstrap count;
- matched-null homophily and multi-graph BFS-bias intervals;
- manual review of regenerated tables and figures;
- paper and literature-review claims updated only from those regenerated
  artifacts.

Until then, committed numerical outputs under the old result directories are
archival. Synthetic runs prove pipeline behavior only.

## Additional reviewer concern — expert finding

The Hetero-GraphSAGE result remains a pilot: one fixed split/seed,
`agree_num` as an imperfect proxy for topic expertise, transductive graph
information, and non-comparable supervised versus unsupervised baselines.
It needs repeated seeds, confidence intervals, matched baselines, and per-topic
evaluation before it can support a “method generation” claim.

This concern was not part of the selected MR-2/MR-3/MR-4 remediation and remains
open research work.

## Current acceptance boundary

The remediation makes the canonical branch a stronger, testable engineering
baseline. It does not change the overall **Major Revision** decision:

- MR-2 and MR-3 are addressed at code and synthetic-validation level.
- MR-4 remains open until the real database is recovered and rerun.
- MR-1 remains an independent publication blocker even after all automated
  checks pass.
