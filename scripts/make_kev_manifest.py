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
from biased_decisions.record import record_path
from biased_decisions.tasks.base import DEFAULT_ROOT
from scripts.run_kev_study import _sha256, collection_cue, load_coverage


def _cell(root: Path, task: str, cue: str, item_cap: int | None = None) -> dict:
    plan = collect(root, "kev", task, collection_cue(cue), dry_run=True, item_cap=item_cap)
    files = {}
    for relative in (f"tasks/{task}/question.yaml", f"tasks/{task}/items.jsonl",
                     f"tasks/{task}/versions/{cue}.jsonl"):
        path = root / relative
        if path.is_file():
            files[relative] = _sha256(path)
    if not files:
        raise ValueError(f"no input files for {task}/{cue}")
    cell = {"task": task, "cue": cue, "requests": plan["total"], "status": "ready", "files": files}
    if item_cap is not None:
        cell["item_cap"] = item_cap
    return cell


def build_manifest(root: Path, cells: Iterable[Tuple[str, str]], frozen: Path | None = None,
                   item_cap: int | None = None) -> dict:
    root = Path(root)
    frozen_manifest = load_coverage(frozen or root / "docs" / "kev-coverage.json")
    return {"schema": "kev-coverage@1", "checkpoint": frozen_manifest["checkpoint"],
            "cells": [_cell(root, task, cue, item_cap) for task, cue in cells]}


def write_run_manifests(root: Path, engine: str, frozen: Path, out_dir: Path,
                        item_cap: int | None = None) -> list:
    """One manifest per task, holding the frozen cells that ``engine`` has not yet answered.

    Each file is one dispatchable run (docs/subsample-preregistration.md): a machine collects it
    with ``run_kev_study collect --manifest <file>`` and commits the finished answer files."""
    root, out_dir = Path(root), Path(out_dir)
    by_task: dict = {}
    for cell in load_coverage(frozen)["cells"]:
        answered = record_path(engine, cell["task"], collection_cue(cell["cue"]), root=root)
        if not answered.exists():
            by_task.setdefault(cell["task"], []).append((cell["task"], cell["cue"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for task, cells in sorted(by_task.items()):
        path = out_dir / f"{task}.json"
        path.write_text(json.dumps(build_manifest(root, cells, frozen, item_cap), indent=2) + "\n",
                        encoding="utf-8")
        written.append(path)
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cells", nargs="*", help="<task>:<cue>")
    parser.add_argument("--out", type=Path, help="the manifest file to write")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--item-cap", type=int, default=None,
                        help="answer only the first N item families (docs/subsample-preregistration.md)")
    parser.add_argument("--runs-dir", type=Path,
                        help="write one manifest per task for the frozen cells ENGINE has not answered")
    parser.add_argument("--engine", default="kev", help="with --runs-dir: the model whose gaps to plan")
    parser.add_argument("--frozen", type=Path, default=None,
                        help="with --runs-dir: the frozen coverage (default docs/kev-coverage.json)")
    args = parser.parse_args(argv)
    if args.runs_dir:
        frozen = args.frozen or args.root / "docs" / "kev-coverage.json"
        for path in write_run_manifests(args.root, args.engine, frozen, args.runs_dir, args.item_cap):
            print(path)
        return 0
    if not args.out or not args.cells:
        parser.error("give --out and at least one <task>:<cue>, or --runs-dir")
    pairs = [tuple(c.split(":", 1)) for c in args.cells]
    manifest = build_manifest(args.root, pairs, item_cap=args.item_cap)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    total = sum(c["requests"] for c in manifest["cells"])
    print(f"{len(manifest['cells'])} cells, {total} requests -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
