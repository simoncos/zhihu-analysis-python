# Result provenance

The files in this directory are the canonical outputs of the Python 3
`analysis/` pipeline on the recovered 2015 database.

The committed power-law table predates the direct truncated-power-law versus
lognormal comparison now implemented in `analysis/powerlaw_fit.py`. Its MLE,
GOF, and power-law-versus-alternative values remain useful, but its named
alternative verdicts must be regenerated before publication:

```bash
python -m analysis.run_all --db zhihu.db --out results --gof-sims 100
```

Do not treat committed result artifacts as an independently reproduced test
run. The raw database is intentionally not tracked.
