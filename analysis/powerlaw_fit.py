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
MODEL_SELECTION_P = 0.1


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
    """Return a verdict without inferring the winner from comparison order.

    Comparing power law separately with lognormal and truncated power law can
    show that both alternatives beat the power law, but it cannot decide which
    alternative is better. ``R_tpl_vs_lognormal`` is the required direct
    comparison: positive favors the truncated power law, negative favors the
    lognormal.
    """
    gof_rejected = row["gof_p"] is not None and row["gof_p"] < MODEL_SELECTION_P
    tpl_vs_ln_p = row.get("p_tpl_vs_lognormal")
    tpl_vs_ln_r = row.get("R_tpl_vs_lognormal")

    losses = [
        a for a in ALTERNATIVES
        if row[f"R_{a}"] < 0 and row[f"p_{a}"] < MODEL_SELECTION_P
    ]
    alternative = None
    alternative_key = None
    if tpl_vs_ln_p is not None and tpl_vs_ln_p < MODEL_SELECTION_P:
        if tpl_vs_ln_r > 0:
            alternative, alternative_key = "Truncated power law", "truncated_power_law"
        else:
            alternative, alternative_key = "Lognormal", "lognormal"

    if gof_rejected:
        if alternative and alternative_key in losses:
            return f"Not power law; {alternative} favored"
        if not losses:
            return "Not power law; no supported alternative selected"
        return "Not power law; TPL vs lognormal unresolved"

    if losses:
        if alternative and alternative_key in losses:
            return f"{alternative} favored"
        return "Power law plausible; alternative family unresolved"

    wins = [
        a for a in ALTERNATIVES
        if row[f"R_{a}"] > 0 and row[f"p_{a}"] < MODEL_SELECTION_P
    ]
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, p = fit.distribution_compare(
            "truncated_power_law", "lognormal", normalized_ratio=True
        )
    row["R_tpl_vs_lognormal"], row["p_tpl_vs_lognormal"] = r, p
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
    cols += ["R_tpl_vs_lognormal", "p_tpl_vs_lognormal"]
    cols += ["verdict"]
    lines = [
        "# 幂律拟合结果 (T1.2)",
        "",
        "- R>0 且 p<0.1：幂律优于该备择分布；R<0 且 p<0.1：备择分布更优；p≥0.1：无法区分",
        "- gof_p < 0.1 时幂律假设本身被拒绝（CSN bootstrap）",
        "- R_tpl_vs_lognormal > 0 偏向截断幂律，< 0 偏向对数正态；只有直接比较显著时才命名胜出模型",
        "",
        df[cols].round(4).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines), df
