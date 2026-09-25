"""Collect a run manifest with Jev, many requests at once.

    python -m scripts.run_jev_study --manifest docs/jev-runs/<study>/<task>.json [--dry-run]

Jev is a hosted, paid service that costs one request per item. The manifest is the same shape as a Kev run
manifest (docs/subsample-preregistration.md): each cell pins its input files, states its request count, and
carries the registered ``item_cap``. Every pinned hash and count is checked before the first request is
sent. ``TYPESAFE_API_KEY`` comes from the environment or a gitignored ``.env`` (``--env-file``); it is never
printed or logged. Requests run ``--concurrency`` at a time; a failed request is saved around and a rerun
resumes with only what is missing.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable

from biased_decisions.collector import collect
from biased_decisions.tasks.base import DEFAULT_ROOT
from scripts.run_kev_study import collection_cue, validate_manifest

DEFAULT_CONCURRENCY = 16


def run_manifest(root: Path, manifest_path: Path, *, engine_factory: Callable[[], Any], model: str,
                 concurrency: int = DEFAULT_CONCURRENCY) -> dict:
    """Validate every pinned input, then collect each cell of the manifest into ``answers/jev``.

    Each cell gets a fresh engine: the hosted client belongs to the event loop that first used it, and
    every cell runs in its own loop."""
    planned = validate_manifest(Path(root), Path(manifest_path))
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    results = [collect(Path(root), "jev", cell["task"], collection_cue(cell["cue"]), engine=engine_factory(),
                       model=model, provenance={"model": model}, item_cap=cell.get("item_cap"),
                       concurrency=concurrency)
               for cell in manifest["cells"]]
    return {"cells": len(results), "requests": planned, "complete": all(r["complete"] for r in results)}


def _discover_model(engine) -> str:
    """Ask Jev one tiny question to learn which model version it reports (the record names it)."""
    import asyncio
    from biased_decisions.collector import build_question
    question = {"Probe": build_question("Is this a greeting?", ("yes", "no"))}
    _answers, meta = asyncio.run(engine.answer_with_meta("Hello.", question))
    if not meta.get("model"):
        raise ValueError("Jev did not report a model version; refusing to collect an unnamed record")
    return meta["model"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--env-file", type=Path, default=None, help="a gitignored .env holding TYPESAFE_API_KEY")
    parser.add_argument("--dry-run", action="store_true", help="validate the manifest; send nothing")
    args = parser.parse_args(argv)
    try:
        if args.dry_run:
            planned = validate_manifest(args.root, args.manifest)
            print(json.dumps({"mode": "dry-run", "requests": planned}, sort_keys=True))
            return 0
        if args.env_file:
            from dotenv import load_dotenv
            load_dotenv(args.env_file, override=False)
        if not os.environ.get("TYPESAFE_API_KEY"):
            parser.error("TYPESAFE_API_KEY is not set (environment or --env-file)")
        from biased_decisions.engines.jev import JevEngine
        model = _discover_model(JevEngine())        # a throwaway client: it belongs to the probe's own loop
        result = run_manifest(args.root, args.manifest, engine_factory=JevEngine, model=model,
                              concurrency=args.concurrency)
        print(json.dumps({"mode": "collect", "model": model, **result}, sort_keys=True))
        return 0 if result["complete"] else 1
    except (ValueError, OSError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
