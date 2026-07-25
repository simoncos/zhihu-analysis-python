# -*- coding: utf-8 -*-
"""Project 1 (T1.2): rigorous power-law fitting via Clauset-Shalizi-Newman.

For each series we report the MLE fit, a semi-parametric bootstrap
goodness-of-fit p-value, and Vuong likelihood-ratio comparisons against
lognormal / exponential / truncated power law / stretched exponential, then
classify the result following Broido & Clauset (2019). The output also retains
the sample-accounting and truncated-power-law parameters from the retired
profile-only analysis.
"""

import warnings

import numpy as np
import pandas as pd
import powerlaw

ALTERNATIVES = [
    "lognormal",
    "exponential",
    "truncated_power_law",
    "stretched_exponential",
]
MODEL_SELECTION_P = 0.1
DEFAULT_GOF_SIMS = 2500


def _fit(data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return powerlaw.Fit(data, discrete=True, verbose=False)


def _controlled_generate_random(distribution, size, rng):
    """Control libraries that draw from NumPy's legacy global RNG.

    ``powerlaw`` does not accept a Generator in its random-sampling API. Save
    and restore the legacy state so a caller-owned Generator still determines
    every bootstrap draw without leaking mutations into unrelated code.
    """
    if size <= 0:
        return np.array([], dtype=float)
    state = np.random.get_state()
    try:
        np.random.seed(int(rng.integers(0, np.iinfo(np.uint32).max, dtype=np.uint32)))
        return np.asarray(distribution.generate_random(size))
    finally:
        np.random.set_state(state)


def gof_bootstrap(data, fit, n_sims=DEFAULT_GOF_SIMS, rng=None):
    """CSN semi-parametric bootstrap: simulate from the fitted model above
    xmin and resample the empirical data below it, refit, compare KS.

    The corrected Monte Carlo p-value cannot be exactly zero. The interval is
    an exact binomial interval for the simulation exceedance probability.
    """
    if n_sims < 1:
        raise ValueError("n_sims must be at least 1 for an evaluated GOF test")
    rng = rng or np.random.default_rng(42)
    data = np.asarray(data)
    below = data[data < fit.xmin]
    n_tail = int(fit.n_tail)
    n = len(data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d_emp = fit.power_law.D  # KS distance computed during fitting
    exceed = 0
    for _ in range(n_sims):
        n_tail_sim = rng.binomial(n, n_tail / n)
        sim_tail = _controlled_generate_random(fit.power_law, n_tail_sim, rng)
        if len(below):
            sim_below = rng.choice(below, size=n - n_tail_sim, replace=True)
            sim = np.concatenate([sim_below, sim_tail])
        else:
            sim = sim_tail
        sim_fit = _fit(sim)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d_sim = sim_fit.power_law.D
        if d_sim >= d_emp:
            exceed += 1
    from scipy.stats import beta

    pvalue = (exceed + 1) / (n_sims + 1)
    ci_low = 0.0 if exceed == 0 else float(beta.ppf(0.025, exceed, n_sims - exceed + 1))
    ci_high = 1.0 if exceed == n_sims else float(
        beta.ppf(0.975, exceed + 1, n_sims - exceed)
    )
    return {
        "pvalue": float(pvalue),
        "exceedances": int(exceed),
        "n_sims": int(n_sims),
        "mc_ci_low": ci_low,
        "mc_ci_high": ci_high,
    }


def gof_pvalue(data, fit, n_sims=DEFAULT_GOF_SIMS, rng=None):
    """Compatibility wrapper returning only the corrected p-value."""
    return gof_bootstrap(data, fit, n_sims=n_sims, rng=rng)["pvalue"]


def classify(row):
    """Return a verdict without inferring the winner from comparison order.

    Comparing power law separately with lognormal and truncated power law can
    show that both alternatives beat the power law, but it cannot decide which
    alternative is better. ``R_tpl_vs_lognormal`` is the required direct
    comparison: positive favors the truncated power law, negative favors the
    lognormal.
    """
    status = row.get("analysis_status")
    if status is None:
        status = "evaluated" if row.get("gof_p") is not None else "not_evaluated"
    if status == "not_evaluated":
        return "Not evaluated; GOF skipped"
    if status != "evaluated":
        return "Invalid fit; inspect diagnostics"

    required = ["gof_p", "R_tpl_vs_lognormal", "p_tpl_vs_lognormal"]
    required += [f"{prefix}_{alt}" for alt in ALTERNATIVES for prefix in ("R", "p")]
    if any(row.get(key) is None or not np.isfinite(row[key]) for key in required):
        return "Invalid fit; non-finite test statistic"

    ci_low = row.get("gof_mc_ci_low")
    ci_high = row.get("gof_mc_ci_high")
    if (
        ci_low is not None
        and ci_high is not None
        and np.isfinite(ci_low)
        and np.isfinite(ci_high)
        and ci_low < MODEL_SELECTION_P < ci_high
    ):
        return "GOF threshold unresolved at current Monte Carlo resolution"

    gof_rejected = row["gof_p"] < MODEL_SELECTION_P
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
            alternative = "Truncated power law favored over lognormal"
            alternative_key = "truncated_power_law"
        else:
            alternative = "Lognormal favored over truncated power law"
            alternative_key = "lognormal"

    if gof_rejected:
        if alternative and alternative_key in losses:
            return f"Not power law; {alternative}"
        if not losses:
            return "Not power law; no supported alternative selected"
        return "Not power law; alternative family unresolved"

    if losses:
        if alternative and alternative_key in losses:
            return alternative
        return "Power law plausible; alternative family unresolved"

    wins = [
        a for a in ALTERNATIVES
        if row[f"R_{a}"] > 0 and row[f"p_{a}"] < MODEL_SELECTION_P
    ]
    if len(wins) == len(ALTERNATIVES):
        return "Power law (beats all alternatives)"
    return "Power law plausible (alternatives indistinguishable)"


def analyze_series(name, values, n_sims=DEFAULT_GOF_SIMS, rng=None):
    raw = np.asarray(values, dtype=float)
    finite = np.isfinite(raw)
    data = raw[finite & (raw > 0)]
    if len(data) == 0:
        raise ValueError(f"{name} has no finite positive observations")
    fit = _fit(data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        alpha = fit.power_law.alpha
        xmin = fit.power_law.xmin
        sigma = fit.power_law.sigma
        ks_distance = fit.power_law.D
        tpl_alpha = fit.truncated_power_law.alpha
        tpl_lambda = fit.truncated_power_law.parameter2
    if n_sims:
        gof = gof_bootstrap(data, fit, n_sims=n_sims, rng=rng)
        gof_status = "evaluated"
    else:
        gof = {
            "pvalue": None,
            "exceedances": None,
            "n_sims": 0,
            "mc_ci_low": None,
            "mc_ci_high": None,
        }
        gof_status = "not_evaluated"

    row = {
        "series": name,
        # Keep ``n`` as the positive-support count for compatibility with the
        # existing canonical CSV while making the full accounting explicit.
        "n": len(data),
        "n_total": len(raw),
        "n_positive": len(data),
        "n_zero_dropped": int(np.sum(finite & (raw == 0))),
        "n_negative_dropped": int(np.sum(finite & (raw < 0))),
        "n_nonfinite_dropped": int(np.sum(~finite)),
        "alpha": alpha,
        "xmin": xmin,
        "sigma": sigma,
        "ks_distance": ks_distance,
        "n_tail": int(fit.n_tail),
        "gof_p": gof["pvalue"],
        "gof_exceedances": gof["exceedances"],
        "gof_n_sims": gof["n_sims"],
        "gof_mc_ci_low": gof["mc_ci_low"],
        "gof_mc_ci_high": gof["mc_ci_high"],
        "tpl_alpha": tpl_alpha,
        "tpl_lambda": tpl_lambda,
        "analysis_status": gof_status,
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
    core = [alpha, xmin, sigma, ks_distance, tpl_alpha, tpl_lambda]
    comparisons = [
        row[key]
        for alt in ALTERNATIVES
        for key in (f"R_{alt}", f"p_{alt}")
    ] + [row["R_tpl_vs_lognormal"], row["p_tpl_vs_lognormal"]]
    if not all(np.isfinite(value) for value in core + comparisons):
        row["analysis_status"] = "invalid_fit"
    row["verdict"] = classify(row)
    return row, fit


def _bh_adjust(values):
    """Benjamini-Hochberg adjustment, returned in original order."""
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.minimum(adjusted, 1.0)
    return result


def apply_fdr_adjustments(rows):
    """Control FDR across series for GOF and across all model comparisons."""
    rows = list(rows)

    def assign(keys):
        locations = []
        values = []
        for row_index, row in enumerate(rows):
            for key in keys:
                value = row.get(key)
                if value is not None and np.isfinite(value):
                    locations.append((row_index, key))
                    values.append(value)
        if values:
            for (row_index, key), adjusted in zip(locations, _bh_adjust(values)):
                rows[row_index][f"q_{key}"] = float(adjusted)

    assign(["gof_p"])
    comparison_keys = [f"p_{alt}" for alt in ALTERNATIVES] + ["p_tpl_vs_lognormal"]
    assign(comparison_keys)

    for row in rows:
        row["verdict_unadjusted"] = row.get("verdict", classify(row))
        adjusted_row = dict(row)
        if "q_gof_p" in row:
            adjusted_row["gof_p"] = row["q_gof_p"]
        for key in comparison_keys:
            if f"q_{key}" in row:
                adjusted_row[key] = row[f"q_{key}"]
        row["verdict"] = classify(adjusted_row)
    return rows


def plot_ccdf(name, fit, out_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    fit.plot_ccdf(ax=ax, marker=".", linestyle="none", color="#555", label="data")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit.power_law.plot_ccdf(
            ax=ax, linestyle="--", label=f"power law (α={fit.power_law.alpha:.2f})"
        )
        fit.truncated_power_law.plot_ccdf(
            ax=ax, linestyle="-", label="truncated power law"
        )
        fit.lognormal.plot_ccdf(ax=ax, linestyle=":", label="lognormal")
    ax.set_title(f"CCDF: {name}")
    ax.set_xlabel(name)
    ax.set_ylabel("P(X ≥ x)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def results_markdown(rows):
    rows = apply_fdr_adjustments(rows)
    df = pd.DataFrame(rows)
    cols = [
        "series",
        "n_total",
        "n_positive",
        "n_zero_dropped",
        "n_negative_dropped",
        "n_nonfinite_dropped",
        "n_tail",
        "alpha",
        "xmin",
        "sigma",
        "ks_distance",
        "analysis_status",
        "gof_p",
        "q_gof_p",
        "gof_exceedances",
        "gof_n_sims",
        "gof_mc_ci_low",
        "gof_mc_ci_high",
        "tpl_alpha",
        "tpl_lambda",
    ]
    cols += [c for a in ALTERNATIVES for c in (f"R_{a}", f"p_{a}")]
    cols += [f"q_p_{a}" for a in ALTERNATIVES]
    cols += ["R_tpl_vs_lognormal", "p_tpl_vs_lognormal", "q_p_tpl_vs_lognormal"]
    cols += ["verdict_unadjusted", "verdict"]
    for column in cols:
        if column not in df.columns:
            df[column] = None
    lines = [
        "# 幂律拟合结果 (T1.2)",
        "",
        "- R>0 且 p<0.1：幂律优于该备择分布；R<0 且 p<0.1：备择分布更优；p≥0.1：无法区分",
        "- gof_p < 0.1 时幂律假设本身被拒绝（CSN bootstrap）",
        "- GOF 使用 (b+1)/(B+1) Monte Carlo 修正并报告 95% 模拟区间；跳过 GOF 时 verdict 明确为 Not evaluated",
        "- 所有拟合均以 X>0 的条件分布为 estimand；零值数量单独报告，不能将结果解释为完整计数分布",
        "- R_tpl_vs_lognormal > 0 偏向截断幂律，< 0 偏向对数正态；只有直接比较显著时才命名两者之间的胜出模型",
        "- stretched exponential 作为独立诊断对照；当前结论不声称 TPL/lognormal 胜者优于它",
        "- 主 verdict 使用 Benjamini-Hochberg：GOF 在各序列间成一族，全部模型比较成另一族；verdict_unadjusted 仅供敏感性核对",
        "",
        df[cols].round(4).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines), df
