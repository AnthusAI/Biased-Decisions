"""Build a Kev coverage manifest for task/cue cells registered after the frozen manifest.

    python -m scripts.make_kev_manifest --out docs/kev-coverage-<study>.json <task>:<cue> [<task>:<cue> ...]

The manifest has the same schema as ``docs/kev-coverage.json`` (``kev-coverage@1``), names the same
pinned checkpoint, pins the sha256 of every input file, and counts the requests a collection would
make (one per text, however many questions it carries). It is committed, with a note in
``docs/kev-amendments.md``, BEFORE any Kev answer for those cells exists. Collect it with
``python -m scripts.run_kev_study collect --manifest <the file> ...`` (its own validation re-checks the
hashes and counts first).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Tuple

from biased_decisions.collector import collect
from biased_decisions.tasks.base import DEFAULT_ROOT
from scripts.run_kev_study import _sha256, collection_cue, load_coverage


def _cell(root: Path, task: str, cue: str) -> dict:
    plan = collect(root, "kev", task, collection_cue(cue), dry_run=True)
    files = {}
    for relative in (f"tasks/{task}/question.yaml", f"tasks/{task}/items.jsonl",
                     f"tasks/{task}/versions/{cue}.jsonl"):
        path = root / relative
        if path.is_file():
            files[relative] = _sha256(path)
    if not files:
        raise ValueError(f"no input files for {task}/{cue}")
    return {"task": task, "cue": cue, "requests": plan["total"], "status": "ready", "files": files}


def build_manifest(root: Path, cells: Iterable[Tuple[str, str]], frozen: Path | None = None) -> dict:
    root = Path(root)
    frozen_manifest = load_coverage(frozen or root / "docs" / "kev-coverage.json")
    return {"schema": "kev-coverage@1", "checkpoint": frozen_manifest["checkpoint"],
            "cells": [_cell(root, task, cue) for task, cue in cells]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cells", nargs="+", help="<task>:<cue>")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    pairs = [tuple(c.split(":", 1)) for c in args.cells]
    manifest = build_manifest(args.root, pairs)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    total = sum(c["requests"] for c in manifest["cells"])
    print(f"{len(manifest['cells'])} cells, {total} requests -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
