"""Validate and run the frozen Kev collection, retained timing pilot, or offline dry run."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Mapping

import yaml

from biased_decisions.collector import collect, load_definition
from biased_decisions.engines.laya import build_question
from biased_decisions.tasks.base import DEFAULT_ROOT


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_coverage(manifest_path: Path) -> dict:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read Kev coverage manifest: {error}") from None
    if manifest.get("schema") != "kev-coverage@1" or not isinstance(manifest.get("cells"), list):
        raise ValueError("unsupported Kev coverage manifest")
    return manifest


def validate_manifest(root: Path, manifest_path: Path, *,
                      dry_run_cell: Callable | None = None,
                      cell_results: list | None = None) -> int:
    """Validate all frozen file hashes and planned cell counts before any answers are requested."""
    root, manifest_path = Path(root), Path(manifest_path)
    manifest = load_coverage(manifest_path)
    seen = set()
    for cell in manifest["cells"]:
        key = (cell.get("task"), cell.get("cue"))
        if not all(key) or key in seen:
            raise ValueError(f"coverage manifest has a missing or duplicate cell: {key!r}")
        seen.add(key)
        if cell.get("status") != "ready":
            raise ValueError(f"coverage cell {key} is not ready")
        files = cell.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError(f"coverage cell {key} has no pinned input hashes")
        for relative, expected in files.items():
            path = root / relative
            if not path.is_file():
                raise ValueError(f"pinned input is missing: {relative}")
            actual = _sha256(path)
            if actual != expected:
                raise ValueError(f"pinned input hash changed: {relative}")

    if dry_run_cell is None:
        dry_run_cell = lambda root, task, cue: collect(
            root, "kev", task, collection_cue(cue), dry_run=True)
    total = 0
    for cell in manifest["cells"]:
        result = dry_run_cell(root, cell["task"], cell["cue"])
        if result.get("total") != cell.get("requests"):
            raise ValueError(
                f"request count mismatch for {cell['task']}/{cell['cue']}: "
                f"manifest={cell.get('requests')}, planned={result.get('total')}"
            )
        total += cell["requests"]
        if cell_results is not None:
            cell_results.append({"task": cell["task"], "cue": cell["cue"],
                                 "total": result["total"],
                                 "pending": result.get("pending", result["total"])})
    return total


def collection_cue(manifest_cue: str) -> str:
    """Translate the preregistered contrast label to its stored reversed-arm cell."""
    return "option-order-reversed" if manifest_cue == "option-order" else manifest_cue


def validate_pinned_checkpoint(manifest: Mapping, provenance: Mapping) -> None:
    selected = provenance.get("checkpoint")
    expected = manifest.get("checkpoint")
    if not expected or selected != expected:
        raise ValueError("selected model checkpoint does not match the coverage manifest checkpoint")


def _atomic_json(path: Path, value: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def run_pilot(root: Path, engine, provenance: Mapping, *, pilot_size: int = 20) -> dict:
    """Run/resume the separate first-20-original surgeon/physician timing pilot."""
    root = Path(root)
    slug, cue = "surgeon-physician", "gender-pronouns"
    definition = load_definition(root, slug)
    originals = [item for item in definition.load_items()
                 if item.metadata.get("split") == "test"]
    items = originals[:pilot_size]
    if len(items) != pilot_size:
        raise ValueError(f"pilot requires {pilot_size} original test bios; found {len(items)}")
    question = build_question(definition.question, definition.options)
    questions = {"Occupation": question}
    raw_task_definition = yaml.safe_load(
        (root / "tasks" / slug / "question.yaml").read_text(encoding="utf-8"))
    fingerprint_doc = {
        "task": slug, "cue": cue, "items": [asdict(item) for item in items],
        "task_definition": raw_task_definition, "question": questions,
        "options": list(definition.options), "model": getattr(engine, "model_name", None),
        "provenance": dict(provenance),
    }
    fingerprint = hashlib.sha256(json.dumps(
        fingerprint_doc, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    out_dir = root / "studies" / "kev"
    rows_path = out_dir / "pilot.jsonl"
    metadata_path = out_dir / "pilot.metadata.json"
    timing_path = out_dir / "pilot.timing.json"
    expected_metadata = {"schema": "kev-pilot@1", "input_fingerprint": fingerprint,
                         "model": getattr(engine, "model_name", None),
                         "provenance": dict(provenance), "item_ids": [item.id for item in items],
                         "question_name": "Occupation"}
    out_dir.mkdir(parents=True, exist_ok=True)
    if metadata_path.exists():
        saved = json.loads(metadata_path.read_text(encoding="utf-8"))
        for key in ("schema", "input_fingerprint", "model", "provenance", "item_ids", "question_name"):
            if saved.get(key) != expected_metadata.get(key):
                raise ValueError(f"pilot metadata {key} does not match requested inputs/provenance")
    else:
        if rows_path.exists() and rows_path.stat().st_size:
            raise ValueError("pilot rows exist without metadata; refusing unsafe resume")
        _atomic_json(metadata_path, expected_metadata)

    rows = {}
    if rows_path.exists():
        try:
            with rows_path.open(encoding="utf-8") as source:
                for line in source:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("id") in rows or row.get("id") not in expected_metadata["item_ids"]:
                        raise ValueError("pilot contains duplicate or unexpected item ids")
                    if row.get("model") not in {expected_metadata["model"], provenance.get("model"),
                                                  provenance.get("checkpoint")}:
                        raise ValueError("pilot row model does not match provenance")
                    rows[row["id"]] = row
        except (OSError, json.JSONDecodeError):
            raise ValueError("pilot rows are corrupt; refusing unsafe resume") from None
    ordered_ids = expected_metadata["item_ids"]
    if list(rows) != ordered_ids[:len(rows)]:
        raise ValueError("pilot partial rows must be an ordered prefix of the retained inputs")
    was_complete = len(rows) == len(ordered_ids) and set(rows) == set(ordered_ids)
    if was_complete and timing_path.exists():
        return {"path": rows_path, "total": pilot_size, "pending": 0, "complete": True,
                "new_items": 0}
    new_items = sum(item.id not in rows for item in items)
    elapsed_started = time.perf_counter()
    latency_samples = [row.get("latency_ms") for row in rows.values()
                       if isinstance(row.get("latency_ms"), (int, float))]
    with rows_path.open("a", encoding="utf-8") as output:
        for item in items:
            if item.id in rows:
                continue
            started = time.perf_counter()
            answers = asyncio.run(engine.answer(item.text, questions))
            wall_elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            row = {"id": item.id,
                   "model": getattr(engine, "model", None) or expected_metadata["model"],
                   "usage": getattr(engine, "usage", None),
                   "latency_ms": getattr(engine, "latency_ms", None) or
                       round(wall_elapsed_ms, 2),
                   "wall_elapsed_ms": wall_elapsed_ms,
                   "answers": answers}
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            os.fsync(output.fileno())
            rows[item.id] = row
            latency_samples.append(row["latency_ms"])
    elapsed = time.perf_counter() - elapsed_started
    if list(rows) and set(rows) != set(ordered_ids):
        raise ValueError("pilot did not collect exactly the retained item set")
    ordered_rows = [rows[item_id] for item_id in ordered_ids]
    observed_call_seconds = sum(row.get("wall_elapsed_ms", 0) for row in ordered_rows) / 1000
    _atomic_json(timing_path, {"items": len(ordered_rows),
                               "total_observed_call_seconds": round(observed_call_seconds, 6),
                               "last_invocation_elapsed_seconds": round(elapsed, 3),
                               "latency_ms": [row.get("latency_ms") for row in ordered_rows],
                               "wall_elapsed_ms": [row.get("wall_elapsed_ms") for row in ordered_rows],
                               "mean_latency_ms": round(sum(latency_samples) / len(latency_samples), 2)
                               if latency_samples else None})
    return {"path": rows_path, "total": pilot_size, "pending": 0, "complete": True,
            "new_items": new_items}


def _engine_from_args(args):
    from biased_decisions.engines.kev import KevEngine
    engine = KevEngine(model=args.model)
    provenance = engine.provenance(server_revision=args.server_revision,
                                   base_revision=args.base_revision, backend=args.backend,
                                   dtype=args.dtype, calibration=args.calibration)
    engine.provenance_data = provenance
    return engine, provenance


def main(argv=None, *, engine_factory: Callable | None = None,
         dry_run_cell: Callable | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("dry-run", "pilot", "collect"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--server-revision", default=None)
    parser.add_argument("--base-revision", default=None)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--dtype", default=None)
    parser.add_argument("--calibration", default=None)
    parser.add_argument("--max-new-items", type=int, default=None,
                        help="optional per-cell cap for operational debugging; never changes full manifest")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or (args.root / "docs" / "kev-coverage.json")
    try:
        planned_cells = []
        planned = validate_manifest(args.root, manifest_path, dry_run_cell=dry_run_cell,
                                    cell_results=planned_cells)
        manifest = load_coverage(manifest_path)
        if args.mode == "dry-run":
            print(json.dumps({"mode": args.mode, "cells": len(manifest["cells"]),
                              "requests": planned, "planned_cells": planned_cells}, sort_keys=True))
            return 0
        required = (args.server_revision, args.base_revision, args.backend, args.dtype, args.calibration)
        if not all(required):
            parser.error("pilot and collect require --server-revision, --base-revision, --backend, --dtype, and --calibration")
        factory = engine_factory or _engine_from_args
        engine, provenance = factory(args)
        validate_pinned_checkpoint(manifest, provenance)
        if args.mode == "pilot":
            result = run_pilot(args.root, engine, provenance)
            print(json.dumps({"mode": args.mode, "path": str(result["path"]),
                              "complete": result["complete"]}, sort_keys=True))
            return 0
        results = []
        for cell in manifest["cells"]:
            results.append(collect(args.root, "kev", cell["task"], collection_cue(cell["cue"]), engine=engine,
                                   model=args.model, provenance=provenance,
                                   max_new_items=args.max_new_items))
        print(json.dumps({"mode": args.mode, "cells": len(results), "requests": planned,
                          "complete": all(result["complete"] for result in results)}, sort_keys=True))
        return 0
    except (ValueError, OSError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
