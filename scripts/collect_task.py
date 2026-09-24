"""Collect one registered task/cue cell from an explicitly configured engine."""
import argparse
import json
from pathlib import Path

from biased_decisions.collector import collect
from biased_decisions.engines.kev import KevEngine
from biased_decisions.tasks.base import DEFAULT_ROOT


def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect/resume one Kev task/cue cell")
    parser.add_argument("engine", choices=("kev",))
    parser.add_argument("task")
    parser.add_argument("cue")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model", default=None)
    parser.add_argument("--server-revision", default=None,
                        help="immutable Kev server git revision; required for real collection")
    parser.add_argument("--base-revision", default=None,
                        help="immutable Qwen base model revision selected for the run")
    parser.add_argument("--backend", default=None)
    parser.add_argument("--dtype", default=None)
    parser.add_argument("--calibration", default=None,
                        help="calibration identity, such as checkpoint temperature")
    parser.add_argument("--dry-run", action="store_true",
                        help="print pending counts without contacting the server")
    parser.add_argument("--max-new-items", type=int, default=None,
                        help="stop after this many new answers, leaving the full cell resumable")
    args = parser.parse_args(argv)
    if args.dry_run:
        result = collect(args.root, args.engine, args.task, args.cue, dry_run=True,
                         model=args.model, max_new_items=args.max_new_items)
    else:
        required = (args.server_revision, args.base_revision, args.backend, args.dtype, args.calibration)
        if not all(required):
            parser.error("real collection requires --server-revision, --base-revision, --backend, --dtype, and --calibration")
        engine = KevEngine(model=args.model)
        engine.provenance_data = engine.provenance(
            server_revision=args.server_revision, base_revision=args.base_revision,
            backend=args.backend,
            dtype=args.dtype, calibration=args.calibration)
        result = collect(args.root, args.engine, args.task, args.cue, engine=engine,
                         model=args.model, provenance=engine.provenance_data,
                         max_new_items=args.max_new_items)
    print(json.dumps({**result, "path": str(result["path"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
