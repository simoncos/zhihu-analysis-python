# -*- coding: utf-8 -*-
"""Orchestrator for Phase 0 + Project 1.

Usage:
    python -m analysis.run_all --db zhihu.db --out results [--gof-sims 100]
    python -m analysis.run_all --bfs-bias --out results   # needs no data
    python -m analysis.run_all --synth --out /tmp/smoke   # smoke test on synthetic db
"""

import argparse
import time
from pathlib import Path

from . import bfs_bias as bb
from . import data_io, health_check
from . import powerlaw_fit as pf


def run_pipeline(db_path, out_dir, gof_sims):
    out_dir = Path(out_dir)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir = out_dir / "parquet"

    print(f"[1/4] export parquet <- {db_path}")
    data_io.export_parquet(db_path, parquet_dir)

    print("[2/4] health check")
    report = health_check.run_health_check(parquet_dir)
    (out_dir / "health_check.md").write_text(report)

    print("[3/4] build induced graph")
    user = data_io.load_parquet(parquet_dir, "User")
    following = data_io.load_parquet(parquet_dir, "Following")
    g, info = data_io.build_induced_graph(user, following)
    print(f"      induced: {g.vcount():,} nodes, {g.ecount():,} edges "
          f"({info['frac_edges_induced']:.1%} of Following rows)")
    degrees = data_io.induced_degree_frame(g)

    print(f"[4/4] power-law fits (gof_sims={gof_sims})")
    rows = []
    series = {f"profile:{f}": user[f] for f in data_io.USER_FEATURES}
    series["induced:in_degree"] = degrees["induced_in_degree"]
    series["induced:out_degree"] = degrees["induced_out_degree"]
    for name, values in series.items():
        t0 = time.time()
        row, fit = pf.analyze_series(name, values, n_sims=gof_sims)
        pf.plot_ccdf(name, fit, fig_dir / f"ccdf_{name.replace(':', '_')}.png")
        rows.append(row)
        print(f"      {name}: α={row['alpha']:.2f} xmin={row['xmin']:.0f} "
              f"-> {row['verdict']} ({time.time() - t0:.0f}s)")
    md, df = pf.results_markdown(rows)
    (out_dir / "powerlaw_results.md").write_text(md)
    df.to_csv(out_dir / "powerlaw_results.csv", index=False)
    print(f"done -> {out_dir}")


def run_bfs_bias(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print("BFS bias simulation (no real data needed)")
    summary, df, _, _ = bb.run_experiment()
    (out_dir / "bfs_bias_simulation.md").write_text(bb.report_markdown(summary, df))
    df.to_csv(out_dir / "bfs_bias_simulation.csv", index=False)
    print(f"true α={summary['alpha_true_fitted']:.2f}  "
          f"profile α={summary['alpha_profile_mean']:.2f}  "
          f"induced α={summary['alpha_induced_mean']:.2f}  "
          f"degree oversampling ×{summary['oversampling_of_degree']:.1f}")
    print(f"done -> {out_dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="zhihu.db")
    ap.add_argument("--out", default="results")
    ap.add_argument("--gof-sims", type=int, default=100,
                    help="bootstrap GOF simulations per series; 0 to skip (fast)")
    ap.add_argument("--bfs-bias", action="store_true", help="run only the sampling-bias simulation")
    ap.add_argument("--synth", action="store_true", help="generate synthetic db and smoke-test")
    args = ap.parse_args()

    if args.bfs_bias:
        run_bfs_bias(args.out)
        return
    db = args.db
    if args.synth:
        from . import synth_db
        db = Path(args.out) / "synthetic_zhihu.db"
        Path(args.out).mkdir(parents=True, exist_ok=True)
        synth_db.generate(db)
        print(f"synthetic db -> {db}")
    run_pipeline(db, args.out, args.gof_sims)


if __name__ == "__main__":
    main()
