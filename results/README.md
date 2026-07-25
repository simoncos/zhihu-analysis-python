# Result provenance

The legacy files at the top of this directory are historical outputs from the
recovered 2015 database. They are not outputs of the corrected canonical HEAD.

In particular, the committed power-law table predates the deterministic,
Monte Carlo-corrected GOF and direct truncated-power-law-versus-lognormal
comparison. The committed homophily result uses an unmatched uniform-user
null, and the committed BFS simulation was produced by the invalid stub
balancing implementation. Do not cite their headline numbers.

Fresh runs are written atomically to `results/current/` and include all graph,
distribution, homophily and provenance outputs:

```bash
python -m analysis.run_all --db zhihu.db --out results/current \
  --gof-sims 2500 --homophily-null-reps 200
```

`results/current/run_manifest.json` records the exact source commit, dirty
state, database SHA-256, seeds, dependency versions, thresholds and artifact
hashes. The raw database is intentionally not tracked.
