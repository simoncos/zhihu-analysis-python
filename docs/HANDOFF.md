# Canonical project handoff

> Updated 2026-07-19 on `codex/canonical-integration`. This branch preserves
> both Claude branch histories and reconciles their duplicated engineering and
> research surfaces.

## Current state

| Area | Status |
|---|---|
| 2015 source project and reports | Preserved as historical Python 2 material |
| Python 3 data/analysis pipeline | Implemented in `analysis/` |
| Real-data health, graph, topic and BFS-bias artifacts | Committed in `results/`; not independently rerun during integration |
| Power-law model selection | Canonical code includes GOF plus direct TPL-vs-lognormal comparison; committed table needs regeneration |
| 2015-2026 literature review | Preserved in `analysis-report/literature-review-2026.md` |
| Expert-finding comparison | Pilot result preserved; single split/seed, not yet publication-grade |
| Concentration/Lorenz analysis | Ported into scalable `analysis.characterize`; needs a real-data rerun |
| Anonymous dataset release | Tooling and documentation prepared; publication not completed |
| Community-interest alignment | Only the homophily demonstration is complete; full community study remains future work |

## Canonical decisions

1. `analysis/` is the only maintained general analysis pipeline.
2. The standalone literature-branch `powerlaw_analysis.py` was retired. Its
   five-series artifacts remain under `analysis-report/powerlaw-results/` as
   a clearly labelled archive.
3. Structural characterization uses igraph. The Gini, 90-9-1, k-core and
   Lorenz metrics from the incomplete NetworkX script were ported into
   `analysis.characterize`.
4. A model may be named lognormal or truncated power law only after their
   direct likelihood comparison is significant. Both beating pure power law
   does not select between them.
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
anonymization work is ineffective. Do not upload `release_build/private/`.

## Reproduction

```bash
python -m pip install -r requirements.txt

# Fast synthetic validation
python -m analysis.run_all --synth --out /tmp/zhihu-smoke --gof-sims 5

# Canonical real-data analyses
python -m analysis.run_all --db zhihu.db --out results --gof-sims 100
python -m analysis.characterize --parquet results/parquet --out results
python -m analysis.run_all --bfs-bias --out results

# Optional expert-finding pilot
python -m pip install -r requirements-expert.txt
python expert_finding_analysis.py zhihu.db --out expert_results
```

## Evidence currently committed

- Six of seven examined series have bootstrap GOF below 0.1, so pure power
  law is rejected for those series. Followee counts remain compatible with a
  pure power law under GOF while a truncated alternative is marginal in the
  existing comparison.
- Existing tables show that both lognormal and truncated power law can beat
  pure power law for several series. The direct alternative comparison added
  during integration must be rerun before choosing between them.
- The induced graph artifact reports 26,161 nodes, 3.13M internal edges, a
  giant SCC containing 98.0% of users, 14.4% reciprocity and sampled mean
  shortest path 2.62.
- The topic homophily pilot reports followed pairs with 1.83 times the mean
  topic Jaccard similarity of random pairs.
- The expert pilot reports Hetero-GraphSAGE ahead on its one held-out split
  (Spearman 0.871), but it lacks repeated seeds and confidence intervals.

These are committed branch artifacts, not a fresh independent rerun by the
integration session.

## Next work, in order

1. Remove or restrict the raw GitHub release asset and confirm old Baidu links
   are inactive.
2. Recover `zhihu.db` privately and rerun the canonical pipeline, including
   direct TPL-vs-lognormal selection and the integrated concentration metrics.
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
