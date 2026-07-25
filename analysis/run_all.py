# -*- coding: utf-8 -*-
"""Atomic orchestrator for the canonical Zhihu2015 analysis pipeline."""

import argparse
import gc
import json
import tempfile
import time
from pathlib import Path

import numpy as np

from . import bfs_bias as bb
from . import characterize, data_io, health_check
from . import powerlaw_fit as pf
from .atomic_io import atomic_directory
from .provenance import artifact_hashes, dependency_versions, git_state, write_manifest


PUBLICATION_GOF_SIMS = 2000
PUBLICATION_HOMOPHILY_REPS = 200
ANALYSIS_SEED = 20151201


def run_pipeline(
    db_path,
    out_dir,
    gof_sims,
    homophily_null_reps,
    seed=ANALYSIS_SEED,
    synthetic=False,
):
    """Run all canonical analyses into one atomic, manifested directory."""
    db_path = Path(db_path)
    out_dir = Path(out_dir)
    repo_root = Path(__file__).resolve().parent.parent
    source_state = git_state(repo_root)
    config = {
        "analysis_seed": seed,
        "gof_sims": gof_sims,
        "homophily_null_reps": homophily_null_reps,
        "positive_support_only": True,
    }

    with atomic_directory(out_dir) as staging:
        fig_dir = staging / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        parquet_dir = staging / "parquet"

        print(f"[1/5] export parquet <- {db_path.name}")
        data_io.export_parquet(db_path, parquet_dir)

        print("[2/5] health check")
        report = health_check.run_health_check(parquet_dir)
        (staging / "health_check.md").write_text(report)

        print("[3/5] build induced graph")
        user = data_io.load_parquet(parquet_dir, "User")
        following = data_io.load_parquet(parquet_dir, "Following")
        graph, info = data_io.build_induced_graph(user, following)
        print(
            f"      induced: {graph.vcount():,} nodes, {graph.ecount():,} edges "
            f"({info['frac_edges_induced']:.1%} of Following rows)"
        )
        degrees = data_io.induced_degree_frame(graph)

        print(f"[4/5] power-law fits (gof_sims={gof_sims})")
        rows = []
        series = {f"profile:{feature}": user[feature] for feature in data_io.USER_FEATURES}
        series["induced:in_degree"] = degrees["induced_in_degree"]
        series["induced:out_degree"] = degrees["induced_out_degree"]
        streams = np.random.SeedSequence(seed).spawn(len(series))
        for (name, values), stream in zip(series.items(), streams):
            started = time.time()
            row, fit = pf.analyze_series(
                name,
                values,
                n_sims=gof_sims,
                rng=np.random.default_rng(stream),
            )
            pf.plot_ccdf(name, fit, fig_dir / f"ccdf_{name.replace(':', '_')}.png")
            rows.append(row)
            print(
                f"      {name}: alpha={row['alpha']:.2f} xmin={row['xmin']:.0f} "
                f"-> {row['verdict']} ({time.time() - started:.0f}s)"
            )
        markdown, frame = pf.results_markdown(rows)
        (staging / "powerlaw_results.md").write_text(markdown)
        frame.to_csv(staging / "powerlaw_results.csv", index=False)
        config["all_powerlaw_evaluated"] = all(
            row["analysis_status"] == "evaluated" for row in rows
        )

        del user, following, graph, degrees, series, fit
        gc.collect()

        print(f"[5/5] characterization (matched-null reps={homophily_null_reps})")
        characterize.run_characterization(
            parquet_dir,
            staging,
            seed=seed + 100,
            homophily_null_reps=homophily_null_reps,
        )
        config["characterization_completed"] = True

        manifest = write_manifest(
            staging,
            db_path,
            config=config,
            source_state=source_state,
            synthetic=synthetic,
        )
        print(
            "manifest reproducibility_gate_passed="
            f"{json.dumps(manifest['reproducibility_gate_passed'])}; "
            f"publication_ready={json.dumps(manifest['publication_ready'])}"
        )
    print(f"done -> {out_dir}")


def run_bfs_bias(
    out_dir,
    n=100_000,
    alpha_in=2.3,
    alpha_out=2.6,
    base_out=48,
    n_graphs=5,
    seeds_per_graph=2,
    seed=7,
):
    out_dir = Path(out_dir)
    source_state = git_state(Path(__file__).resolve().parent.parent)
    print("BFS bias simulation (no real data needed)")
    with atomic_directory(out_dir) as staging:
        summary, frame, _, _ = bb.run_experiment(
            n=n,
            alpha_in=alpha_in,
            alpha_out=alpha_out,
            base_out=base_out,
            n_graphs=n_graphs,
            seeds_per_graph=seeds_per_graph,
            seed=seed,
        )
        (staging / "bfs_bias_simulation.md").write_text(
            bb.report_markdown(summary, frame)
        )
        frame.to_csv(staging / "bfs_bias_simulation.csv", index=False)
        manifest = {
            "method": "independent directed configuration-model graphs",
            "source": source_state,
            "runtime_dependencies": dependency_versions(),
            "config": {
                "n": n,
                "alpha_in": alpha_in,
                "alpha_out": alpha_out,
                "base_out": base_out,
                "seed": seed,
                "n_graphs": n_graphs,
                "seeds_per_graph": seeds_per_graph,
            },
            "summary": summary,
            "artifacts_sha256": artifact_hashes(staging),
        }
        (staging / "bfs_bias_manifest.json").write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            )
        )
    print(f"done -> {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="zhihu.db")
    parser.add_argument("--out")
    parser.add_argument(
        "--gof-sims",
        type=int,
        help=f"bootstrap simulations per series; publication runs require >= {PUBLICATION_GOF_SIMS}",
    )
    parser.add_argument(
        "--homophily-null-reps",
        type=int,
        help=f"matched-null repetitions; publication runs require >= {PUBLICATION_HOMOPHILY_REPS}",
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--bfs-bias", action="store_true")
    parser.add_argument("--bfs-nodes", type=int, default=100_000)
    parser.add_argument("--bfs-alpha-in", type=float, default=2.3)
    parser.add_argument("--bfs-alpha-out", type=float, default=2.6)
    parser.add_argument("--bfs-base-out", type=int, default=48)
    parser.add_argument("--bfs-graphs", type=int, default=5)
    parser.add_argument("--bfs-seeds-per-graph", type=int, default=2)
    parser.add_argument("--synth", action="store_true")
    args = parser.parse_args()

    if args.bfs_bias:
        target = args.out or "results/bfs-bias-current"
        run_bfs_bias(
            target,
            n=args.bfs_nodes,
            alpha_in=args.bfs_alpha_in,
            alpha_out=args.bfs_alpha_out,
            base_out=args.bfs_base_out,
            n_graphs=args.bfs_graphs,
            seeds_per_graph=args.bfs_seeds_per_graph,
            seed=args.seed if args.seed is not None else 7,
        )
        return

    target = args.out or "results/current"
    analysis_seed = args.seed if args.seed is not None else ANALYSIS_SEED
    gof_sims = args.gof_sims if args.gof_sims is not None else (5 if args.synth else 2500)
    null_reps = (
        args.homophily_null_reps
        if args.homophily_null_reps is not None
        else (10 if args.synth else 200)
    )
    if gof_sims < 0 or null_reps < 1:
        parser.error("gof-sims must be >= 0 and homophily-null-reps must be >= 1")
    if not args.synth and (
        gof_sims < PUBLICATION_GOF_SIMS or null_reps < PUBLICATION_HOMOPHILY_REPS
    ):
        print("WARNING: diagnostic thresholds selected; manifest will not be publication-ready")

    if args.synth:
        from . import synth_db

        with tempfile.TemporaryDirectory(prefix="zhihu-synth-") as temp_dir:
            db_path = synth_db.generate(Path(temp_dir) / "synthetic_zhihu.db")
            run_pipeline(
                db_path,
                target,
                gof_sims,
                null_reps,
                seed=analysis_seed,
                synthetic=True,
            )
    else:
        run_pipeline(
            args.db,
            target,
            gof_sims,
            null_reps,
            seed=analysis_seed,
            synthetic=False,
        )


if __name__ == "__main__":
    main()
