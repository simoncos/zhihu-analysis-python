# -*- coding: utf-8 -*-
"""Machine-readable provenance for canonical analysis runs."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEPENDENCIES = [
    "numpy",
    "pandas",
    "pyarrow",
    "igraph",
    "python-igraph",
    "powerlaw",
    "matplotlib",
    "scipy",
    "tabulate",
    "leidenalg",
]


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_state(repo_root):
    repo_root = Path(repo_root)

    def run(*args):
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    try:
        return {
            "commit": run("rev-parse", "HEAD"),
            "branch": run("branch", "--show-current"),
            "dirty": bool(run("status", "--porcelain")),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "branch": None, "dirty": None}


def dependency_versions():
    versions = {}
    for name in DEPENDENCIES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def artifact_hashes(root):
    root = Path(root)
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "run_manifest.json"
    }


def build_manifest(output_root, db_path, config, source_state, synthetic=False):
    db_path = Path(db_path)
    reproducibility_gate_passed = (
        not synthetic
        and source_state.get("dirty") is False
        and config["gof_sims"] >= 2000
        and config["homophily_null_reps"] >= 200
        and config.get("all_powerlaw_evaluated") is True
        and config.get("characterization_completed") is True
    )
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reproducibility_gate_passed": reproducibility_gate_passed,
        # This pipeline cannot decide privacy, ethics, rights, or human-review
        # gates. Keep the broader publication flag fail-closed.
        "publication_ready": False,
        "publication_ready_note": (
            "Reproducibility gate passed, but privacy, ethics, rights, and human review remain required."
            if reproducibility_gate_passed
            else "Diagnostic or non-clean run; do not use as publication evidence."
        ),
        "source": source_state,
        "input": {
            "database_filename": db_path.name,
            "database_sha256": sha256_file(db_path),
            "synthetic": synthetic,
        },
        "config": config,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "dependencies": dependency_versions(),
        },
        "artifacts_sha256": artifact_hashes(output_root),
    }


def write_manifest(output_root, db_path, config, source_state, synthetic=False):
    manifest = build_manifest(output_root, db_path, config, source_state, synthetic)
    path = Path(output_root) / "run_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest
