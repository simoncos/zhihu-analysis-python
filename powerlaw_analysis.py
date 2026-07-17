# -*- coding: utf-8 -*-
"""
Rigorous power-law testing of the 2015 Zhihu dataset (literature review
recommendation 6.6, see analysis-report/literature-review-2026.md).

The original 2015 report concluded the five user features follow power laws
based on visual inspection of log-log plots. Current network-science standards
(Clauset, Shalizi & Newman 2009) require maximum-likelihood fitting with
KS-minimized xmin and likelihood-ratio tests against alternative heavy-tailed
distributions. Notably, 社会化问答社区用户行为统计特性及其动力学分析 (数据分析与知识发现
2018, 2(4):48-58, DOI 10.11925/infotech.2096-3467.2017.0904) reports that
Zhihu's degree and activity distributions follow *exponentially truncated*
power laws rather than pure ones — this script tests that claim on the 2015
snapshot.

Usage:
    pip install powerlaw pandas matplotlib
    python powerlaw_analysis.py [path/to/zhihu.db] [--out results_dir]

Outputs (in results_dir, default powerlaw_results/):
    - powerlaw_results.csv / .md : fit parameters and likelihood-ratio tests
    - ccdf_<feature>.png         : CCDF plots with fitted candidates

Interpretation of the likelihood-ratio columns (R, p):
    R > 0 favors the pure power law, R < 0 favors the alternative;
    the sign is only meaningful when p < 0.05 (Clauset et al. 2009).
"""

import argparse
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import powerlaw

FEATURES = ['followee_num', 'follower_num', 'answer_num', 'agree_num', 'thanks_num']
ALTERNATIVES = ['truncated_power_law', 'lognormal', 'exponential', 'stretched_exponential']


def load_features(db_path):
    conn = sqlite3.connect(db_path)
    user_data = pd.read_sql('select %s from User' % ', '.join(FEATURES), conn)
    conn.close()
    return user_data


def fit_feature(values, feature_name):
    """Fit one feature; returns a result row and the Fit object for plotting."""
    data = np.asarray(values, dtype=float)
    data = data[data > 0]  # power-law support requires x > 0; zeros are reported separately
    zeros = len(values) - len(data)

    fit = powerlaw.Fit(data, discrete=True, verbose=False)

    row = {
        'feature': feature_name,
        'n': len(values),
        'n_zero_dropped': zeros,
        'alpha': fit.power_law.alpha,
        'xmin': fit.power_law.xmin,
        'n_tail': int((data >= fit.power_law.xmin).sum()),
        'ks_distance': fit.power_law.D,
    }
    for alt in ALTERNATIVES:
        R, p = fit.distribution_compare('power_law', alt, normalized_ratio=True)
        row['R_vs_%s' % alt] = R
        row['p_vs_%s' % alt] = p

    # Truncated power law's own parameters, since it is the hypothesis from the
    # 2018 数据分析与知识发现 study we are testing against.
    row['tpl_alpha'] = fit.truncated_power_law.alpha
    row['tpl_lambda'] = fit.truncated_power_law.parameter2
    return row, fit


def verdict(row):
    """Plain-language verdict per Clauset et al. decision rules."""
    tpl_p, tpl_r = row['p_vs_truncated_power_law'], row['R_vs_truncated_power_law']
    ln_p, ln_r = row['p_vs_lognormal'], row['R_vs_lognormal']
    if tpl_p < 0.05 and tpl_r < 0:
        return 'truncated power law favored over pure power law'
    if ln_p < 0.05 and ln_r < 0:
        return 'lognormal favored over pure power law'
    if (tpl_p >= 0.05) and (ln_p >= 0.05):
        return 'power law plausible; alternatives not distinguishable'
    return 'pure power law not rejected against favored alternatives'


def plot_ccdf(fit, feature, out_dir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4.5))
    fit.plot_ccdf(ax=ax, marker='.', linestyle='none', color='#4269d0', label='data (CCDF)')
    fit.power_law.plot_ccdf(ax=ax, color='#efb118', linestyle='--',
                            label=r'power law ($\alpha$=%.2f)' % fit.power_law.alpha)
    fit.truncated_power_law.plot_ccdf(ax=ax, color='#ff725c', linestyle='-',
                                      label='truncated power law')
    fit.lognormal.plot_ccdf(ax=ax, color='#6cc5b0', linestyle=':', label='lognormal')
    ax.set_xlabel(feature)
    ax.set_ylabel(r'$P(X \geq x)$')
    ax.set_title('CCDF and fitted tails: %s (x >= xmin=%g)' % (feature, fit.power_law.xmin))
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, 'ccdf_%s.png' % feature)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def to_markdown(results):
    lines = [
        '| feature | n_tail | alpha | xmin | R vs TPL | p | R vs lognormal | p | verdict |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for r in results:
        lines.append('| %s | %d | %.3f | %g | %.2f | %.3g | %.2f | %.3g | %s |' % (
            r['feature'], r['n_tail'], r['alpha'], r['xmin'],
            r['R_vs_truncated_power_law'], r['p_vs_truncated_power_law'],
            r['R_vs_lognormal'], r['p_vs_lognormal'], r['verdict']))
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('db', nargs='?', default='zhihu.db', help='path to zhihu.db')
    parser.add_argument('--out', default='powerlaw_results', help='output directory')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        sys.exit('database not found: %s (download the 2015 dataset and point this script at it)' % args.db)
    os.makedirs(args.out, exist_ok=True)

    user_data = load_features(args.db)
    print('loaded %d users from %s' % (len(user_data), args.db))

    results = []
    for feature in FEATURES:
        print('fitting %s ...' % feature)
        row, fit = fit_feature(user_data[feature], feature)
        row['verdict'] = verdict(row)
        results.append(row)
        plot_ccdf(fit, feature, args.out)
        print('  alpha=%.3f xmin=%g n_tail=%d -> %s' % (
            row['alpha'], row['xmin'], row['n_tail'], row['verdict']))

    df = pd.DataFrame(results)
    csv_path = os.path.join(args.out, 'powerlaw_results.csv')
    df.to_csv(csv_path, index=False)
    md_path = os.path.join(args.out, 'powerlaw_results.md')
    with open(md_path, 'w') as f:
        f.write('# Power-law statistical tests (CSN method) on 2015 Zhihu features\n\n')
        f.write(to_markdown(results) + '\n\n')
        f.write('R > 0 favors pure power law, R < 0 favors the alternative; '
                'sign meaningful only when p < 0.05 (Clauset-Shalizi-Newman 2009).\n')
    print('\nwrote %s, %s and CCDF plots to %s/' % (csv_path, md_path, args.out))
    print('\n' + to_markdown(results))


if __name__ == '__main__':
    main()
