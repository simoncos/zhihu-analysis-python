# -*- coding: utf-8 -*-
"""Project 1 (T1.2): rigorous power-law fitting via Clauset-Shalizi-Newman.

For each series we report the MLE fit, a semi-parametric bootstrap
goodness-of-fit p-value, and Vuong likelihood-ratio comparisons against
lognormal / exponential / truncated power law, then classify the result
following Broido & Clauset (2019).
"""

import warnings

import numpy as np
import pandas as pd
import powerlaw

ALTERNATIVES = ["lognormal", "exponential", "truncated_power_law"]


def _fit(data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return powerlaw.Fit(data, discrete=True, verbose=False)


def gof_pvalue(data, fit, n_sims=100, rng=None):
    """CSN semi-parametric bootstrap: simulate from the fitted model above
    xmin and resample the empirical data below it, refit, compare KS."""
    rng = rng or np.random.default_rng(42)
    data = np.asarray(data)
    below = data[data < fit.xmin]
    n_tail = int(fit.n_tail)
    n = len(data)
    d_emp = fit.power_law.D  # KS distance computed during fitting
    exceed = 0
    for _ in range(n_sims):
        n_tail_sim = rng.binomial(n, n_tail / n)
        sim_tail = fit.power_law.generate_random(n_tail_sim)
        if len(below):
            sim_below = rng.choice(below, size=n - n_tail_sim, replace=True)
            sim = np.concatenate([sim_below, sim_tail])
        else:
            sim = sim_tail
        sim_fit = _fit(sim)
        if sim_fit.power_law.D >= d_emp:
            exceed += 1
    return exceed / n_sims


def classify(row):
    """Simplified Broido-Clauset style verdict for one fitted series."""
    if row["gof_p"] is not None and row["gof_p"] < 0.1:
        return "Not power law (GOF rejected)"
    losses = [a for a in ALTERNATIVES if row[f"R_{a}"] < 0 and row[f"p_{a}"] < 0.1]
    if "lognormal" in losses:
        return "Lognormal favored"
    if losses:
        return f"Alternative favored ({','.join(losses)})"
    wins = [a for a in ALTERNATIVES if row[f"R_{a}"] > 0 and row[f"p_{a}"] < 0.1]
    if len(wins) == len(ALTERNATIVES):
        return "Power law (beats all alternatives)"
    return "Power law plausible (alternatives indistinguishable)"


def analyze_series(name, values, n_sims=100):
    data = np.asarray(values)
    data = data[data > 0]
    fit = _fit(data)
    row = {
        "series": name,
        "n": len(data),
        "alpha": fit.power_law.alpha,
        "xmin": fit.power_law.xmin,
        "sigma": fit.power_law.sigma,
        "n_tail": int(fit.n_tail),
        "gof_p": gof_pvalue(data, fit, n_sims=n_sims) if n_sims else None,
    }
    for alt in ALTERNATIVES:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r, p = fit.distribution_compare("power_law", alt, normalized_ratio=True)
        row[f"R_{alt}"], row[f"p_{alt}"] = r, p
    row["verdict"] = classify(row)
    return row, fit


def plot_ccdf(name, fit, out_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    fit.plot_ccdf(ax=ax, marker=".", linestyle="none", color="#555", label="data")
    fit.power_law.plot_ccdf(ax=ax, linestyle="--", label=f"power law (α={fit.power_law.alpha:.2f})")
    fit.lognormal.plot_ccdf(ax=ax, linestyle=":", label="lognormal")
    ax.set_title(f"CCDF: {name}")
    ax.set_xlabel(name)
    ax.set_ylabel("P(X ≥ x)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def results_markdown(rows):
    df = pd.DataFrame(rows)
    cols = ["series", "n", "n_tail", "alpha", "xmin", "sigma", "gof_p"]
    cols += [c for a in ALTERNATIVES for c in (f"R_{a}", f"p_{a}")]
    cols += ["verdict"]
    lines = [
        "# 幂律拟合结果 (T1.2)",
        "",
        "- R>0 且 p<0.1：幂律优于该备择分布；R<0 且 p<0.1：备择分布更优；p≥0.1：无法区分",
        "- gof_p < 0.1 时幂律假设本身被拒绝（CSN bootstrap）",
        "",
        df[cols].round(4).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines), df
