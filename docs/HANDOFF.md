# Canonical project handoff

> Updated 2026-07-19 on `codex/canonical-integration`. This branch preserves
> both Claude branch histories and reconciles their duplicated engineering and
> research surfaces.

The publication-review findings and their closure criteria are tracked in
[`docs/MAJOR_REVISION.md`](MAJOR_REVISION.md).

## Current state

| Area | Status |
|---|---|
| 2015 source project and reports | Preserved as historical Python 2 material |
| Python 3 data/analysis pipeline | Implemented in `analysis/` |
| Real-data health, graph and topic artifacts | Legacy outputs committed in `results/`; corrected canonical rerun pending |
| Power-law model selection | Canonical code includes GOF plus direct TPL-vs-lognormal comparison; committed table needs regeneration |
| 2015-2026 literature review | Preserved in `analysis-report/literature-review-2026.md` |
| Expert-finding comparison | Pilot result preserved; single split/seed, not yet publication-grade |
| Structural/concentration analysis | SCC/WCC, assortativity, k-core, topic-size, concentration and Lorenz metrics are integrated; homophily now uses a matched repeated null; real-data rerun pending |
| Anonymous dataset release | Tooling and documentation prepared; publication not completed |
| Community-interest alignment | Only the homophily demonstration is complete; full community study remains future work |

## Canonical decisions

1. `analysis/` is the only maintained general analysis pipeline.
2. The standalone literature-branch `powerlaw_analysis.py` was retired. Its
   sample accounting, stretched-exponential comparison, truncated-power-law
   parameters and fitted curve are integrated into `analysis.powerlaw_fit`;
   its five-series artifacts remain under `analysis-report/powerlaw-results/`
   as a clearly labelled archive.
3. Structural characterization uses igraph. The Gini, 90-9-1, k-core,
   Lorenz, topic-size, undirected assortativity and giant-WCC path metrics
   from the incomplete NetworkX script are ported alongside the existing
   directed giant-SCC metrics in `analysis.characterize`.
4. A model may be named lognormal or truncated power law only after their
   direct likelihood comparison is significant. Both beating pure power law
   does not select between them. The stretched-exponential comparison is
   retained as a diagnostic; the direct TPL-vs-lognormal result does not claim
   that its winner also beats the stretched exponential.
5. Expert finding remains a standalone optional experiment because its
   PyTorch/PyG dependency footprint is much heavier than the core pipeline.

## Data and privacy boundary

The recovered database should have these row counts:

| Table | Rows |
|---|---:|
| User | 26,161 |
| Following | 4,612,110 |
| Question | 2,245,143 |
| UserQuestion | 1,655,414 |
| UserTopic | 5,414,129 |

The old `dataset-v0/zhihu.zip` asset reportedly contains the original,
unredacted database. It must not be promoted as a reproduction URL. Restrict
or remove that asset before publishing the anonymous dataset; otherwise the
anonymization work is ineffective. Do not upload the separate private mapping
directory (default `release_build_private/`).

## Reproduction

```bash
python -m pip install -r requirements-lock.txt

# Fast synthetic validation
python -m analysis.run_all --synth --out /tmp/zhihu-smoke

# Canonical real-data analyses
python -m analysis.run_all --db zhihu.db --out results/current \
  --gof-sims 2500 --homophily-null-reps 200
python -m analysis.run_all --bfs-bias --out results/bfs-bias-current \
  --bfs-graphs 5 --bfs-seeds-per-graph 2

# Optional expert-finding pilot
python -m pip install -r requirements-expert.txt
python expert_finding_analysis.py zhihu.db --out expert_results
```

## Evidence currently committed

- The legacy 100-replicate table suggested several departures from pure power
  law, but it is not publication evidence. Corrected GOF uses deterministic
  random streams, `(b+1)/(B+1)`, Monte Carlo intervals and explicit
  not-evaluated/invalid states; it must be rerun on the real database.
- The induced graph artifact reports 26,161 nodes, 3.13M internal edges, a
  giant SCC containing 98.0% of users, 14.4% reciprocity and sampled mean
  shortest path 2.62.
- The old 1.83 homophily ratio used a confounded uniform-user null. Canonical
  code now matches target degree, activity, topic-set size and crawl layer and
  repeats the null; no replacement number is claimed before real-data rerun.
- The old ≈0.6 BFS effect is withdrawn. Canonical code allocates incoming stubs
  from heavy-tailed target propensities and aggregates repeated seeds within
  independent graph replicates before reporting graph-level intervals.
- The expert pilot reports Hetero-GraphSAGE ahead on its one held-out split
  (Spearman 0.871), but it lacks repeated seeds and confidence intervals.

The remaining committed numerical artifacts are historical evidence, not a
fresh corrected run. New canonical results belong in `results/current/` with
`run_manifest.json`.

## Next work, in order

1. Remove or restrict the raw GitHub release asset and confirm old Baidu links
   are inactive.
2. Recover `zhihu.db` privately and rerun the atomic canonical pipeline,
   including direct TPL-vs-lognormal selection, matched-null homophily and the
   integrated concentration metrics.
3. Update the paper and literature review with regenerated tables.
4. Strengthen expert finding with repeated seeds, confidence intervals,
   matched supervised baselines and per-topic evaluation.
5. Complete the publishing checklist, then publish anonymous Parquet files to
   Zenodo/Hugging Face and fill the DOI/CITATION metadata.
6. Continue the full social-community versus interest-community alignment
   study described in `RESEARCH_PLAN.md`.

## Source branch provenance

- `claude/legacy-project-analysis-ior8d5` supplied the Python 3 pipeline,
  real-data characterization, release tooling and dataset-paper draft.
- `claude/literature-review-update-9vlyea` supplied the expanded literature
  review, expert-finding pilot, profile-only power-law archive and
  concentration-analysis ideas.

Both histories are ancestors of this canonical integration branch.
