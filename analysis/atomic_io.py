# -*- coding: utf-8 -*-
"""Small atomic-output helpers shared by analysis and release pipelines."""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def atomic_directory(target):
    """Build a complete directory beside *target*, then swap it into place.

    A failed build never mutates the previous target. The final rename is on
    the same filesystem, so consumers see either the old run or the new run,
    never a directory containing a mixture of both.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=str(target.parent))
    )
    backup = None
    try:
        yield staging
        if target.exists():
            backup = Path(
                tempfile.mkdtemp(prefix=f".{target.name}.backup-", dir=str(target.parent))
            )
            backup.rmdir()
            os.replace(target, backup)
        try:
            os.replace(staging, target)
        except Exception:
            if backup is not None and backup.exists() and not target.exists():
                os.replace(backup, target)
            raise
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
