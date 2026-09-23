"""The ``bd`` command line: ``list | build | answer | score | replay | report [--json]``.

See the design doc's "Commands" section for what each subcommand does; this module is the thin
argument-parsing and printing layer over ``biased_decisions.build`` (writing a cue's versions),
``biased_decisions.scoring`` (turning a record into a measurement row) and
``biased_decisions.report`` (regenerating ``RESULTS.md``). Nothing here calls an engine except
``bd answer``, which refuses to before its two preflight checks pass (see
``biased_decisions.answering``) -- milestone 1 never runs it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional

from biased_decisions.build import BuildError, CUES as BUILD_CUES, build as build_cue, write_versions
from biased_decisions.scoring import (
    ENGINES, SCORERS, ScoreError, SHORTLIST_PAIRS, TASK_CUES, has_record, score,
    score_port_vs_original, score_shortlist, write_rows,
)
from biased_decisions.tasks.base import DEFAULT_ROOT
from biased_decisions.tasks.bios import BIOS_TASKS, ORIGINAL_BIOS_TASKS, load_task

# Every cue that can be scored (a superset of BUILD_CUES: ``option-order`` has no versions file
# of its own to build -- it is scored straight from three other cues' records, see
# ``biased_decisions.scoring.has_record``).
CUES = tuple(SCORERS)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve() if args.root else DEFAULT_ROOT


# ---------------------------------------------------------------------------------------------
# bd list
# ---------------------------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> int:
    root = _root(args)
    print(f"Engines: {', '.join(ENGINES)}")
    print(f"Tasks:   {', '.join(BIOS_TASKS)}")
    print(f"Cues:    {', '.join(CUES)}")
    print()

    header = ["task", "cue"] + list(ENGINES)
    rows: List[List[str]] = [header]
    for task_slug in BIOS_TASKS:
        for cue in CUES:
            if cue not in TASK_CUES[task_slug]:
                continue
            row = [task_slug, cue]
            for engine in ENGINES:
                row.append("x" if has_record(engine, task_slug, cue, root=root) else ".")
            rows.append(row)
    widths = [max(len(r[c]) for r in rows) for c in range(len(header))]
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))
    return 0


# ---------------------------------------------------------------------------------------------
# bd build
# ---------------------------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> int:
    root = _root(args)
    task = load_task(args.task, root=root)
    try:
        result = build_cue(args.cue, task)
    except BuildError as error:
        print(f"bd build: {error}", file=sys.stderr)
        return 1

    path = write_versions(task, args.cue, result)
    print(f"wrote {len(result.rows)} rows to {path}")
    print(f"{result.excluded} test items had no insertion point for {args.cue!r} and were "
         f"excluded")
    if result.subsample is not None:
        sub_path = task.versions_dir() / f"{args.cue}_jev-subsample.txt"
        print(f"wrote {len(result.subsample)} ids to {sub_path}")
    return 0


# ---------------------------------------------------------------------------------------------
# bd answer -- preflight checks only; never places a request in milestone 1.
# ---------------------------------------------------------------------------------------------

def cmd_answer(args: argparse.Namespace) -> int:
    from biased_decisions.answering import AnswerRefused, preflight, price_estimate

    root = _root(args)
    task = load_task(args.task, root=root)
    try:
        path = preflight(args.engine, task, args.cue, root=root)
    except AnswerRefused as error:
        print(f"bd answer: refused -- {error}", file=sys.stderr)
        return 1

    if args.price_only:
        items = task.load_items()
        print(price_estimate(args.engine, task, args.cue, items, root=root))
        return 0

    print(
        f"bd answer: preflight passed for ({args.engine}, {args.task}, {args.cue}) -- record "
        f"at {path}. This command does not place a request on its own; wire "
        f"biased_decisions.answering.answer_all into your own run (with a key or a GPU "
        f"available) to actually fill this cell. Milestone 1 ships every cell's record "
        f"already committed.", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------------------------
# bd score
# ---------------------------------------------------------------------------------------------

def cmd_score(args: argparse.Namespace) -> int:
    root = _root(args)
    task = load_task(args.task, root=root)
    kwargs = {}
    if args.cue == "race-fullname" and args.sample:
        kwargs["sample"] = args.sample
    try:
        row = score(args.engine, task, args.cue, **kwargs)
    except ScoreError as error:
        print(f"bd score: {error}", file=sys.stderr)
        return 1

    print(json.dumps(row, indent=2))
    out = Path(args.out) if args.out else root / "studies" / f"{args.task}-{args.cue}.jsonl"
    key_fields = ("engine", "sample") if args.cue == "race-fullname" else ("engine",)
    write_rows(out, [row], key_fields)
    print(f"wrote 1 row to {out}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------------------------
# bd replay -- every cell that has a record, plus the shortlist block.
# ---------------------------------------------------------------------------------------------

def cmd_replay(args: argparse.Namespace) -> int:
    root = _root(args)
    n_cells = 0
    n_rows = 0

    for task_slug in BIOS_TASKS:
        task = load_task(task_slug, root=root)
        for cue in TASK_CUES[task_slug]:
            out = root / "studies" / f"{task_slug}-{cue}.jsonl"
            key_fields = ("engine", "sample") if cue == "race-fullname" else ("engine",)
            rows = []
            for engine in ENGINES:
                if not has_record(engine, task_slug, cue, root=root):
                    continue
                if cue == "race-fullname":
                    for sample in ("all", "500"):
                        try:
                            rows.append(score(engine, task, cue, sample=sample))
                        except ScoreError:
                            continue
                else:
                    try:
                        rows.append(score(engine, task, cue))
                    except ScoreError as error:
                        print(f"bd replay: skipping ({engine}, {task_slug}, {cue}): {error}",
                             file=sys.stderr)
                        continue
                n_cells += 1
            if rows:
                write_rows(out, rows, key_fields)
                n_rows += len(rows)
                print(f"{task_slug}-{cue}: {len(rows)} row(s) -> {out}")

    for pair_slug in SHORTLIST_PAIRS:
        task = load_task(pair_slug, root=root)
        out = root / "studies" / f"{pair_slug}-shortlist.jsonl"
        rows = []
        for engine in ENGINES:
            if not has_record(engine, pair_slug, "gender-pronouns", root=root):
                continue
            rows.extend(score_shortlist(engine, task))
        if rows:
            write_rows(out, rows, ("engine", "variant", "cut"))
            n_rows += len(rows)
            print(f"{pair_slug}-shortlist: {len(rows)} row(s) -> {out}")

    port_rows = []
    for task_slug in ORIGINAL_BIOS_TASKS:
        if not (has_record("laya-mlx", task_slug, "gender-pronouns", root=root)
                and has_record("laya", task_slug, "gender-pronouns", root=root)):
            continue
        task = load_task(task_slug, root=root)
        port_rows.append(score_port_vs_original(task))
        n_cells += 1
    if port_rows:
        out = root / "studies" / "batch1" / "port-vs-original.jsonl"
        write_rows(out, port_rows, ("task",))
        n_rows += len(port_rows)
        print(f"port-vs-original: {len(port_rows)} row(s) -> {out}")

    print(f"replayed {n_cells} cell(s), {n_rows} row(s) written")
    return 0


# ---------------------------------------------------------------------------------------------
# bd report
# ---------------------------------------------------------------------------------------------

def cmd_report(args: argparse.Namespace) -> int:
    from biased_decisions.report import write, write_json

    root = _root(args)
    out = Path(args.out) if args.out else None
    if args.json:
        if args.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            print(f"bd report: --date must be YYYY-MM-DD, got {args.date!r}", file=sys.stderr)
            return 1
        path = write_json(root, out, date=args.date)
    else:
        path = write(root, out)
    print(f"wrote {path}")
    return 0


# ---------------------------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bd", description="Biased-Decisions: a benchmark harness for bias in fast "
        "decision models. list | build | answer | score | replay | report.")
    parser.add_argument("--root", default=None,
                        help="repo root (default: this package's own repo)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="engines, tasks, cues, and which cells have a record")
    p_list.set_defaults(func=cmd_list)

    p_build = sub.add_parser("build", help="write a cue's versions file from items.jsonl")
    p_build.add_argument("task", choices=BIOS_TASKS)
    p_build.add_argument("--cue", required=True, choices=BUILD_CUES)
    p_build.set_defaults(func=cmd_build)

    p_answer = sub.add_parser(
        "answer", help="fill a record cell (needs a key or a GPU; refuses without one)")
    p_answer.add_argument("engine", choices=ENGINES)
    p_answer.add_argument("task", choices=BIOS_TASKS)
    p_answer.add_argument("--cue", required=True, choices=CUES)
    p_answer.add_argument("--price-only", action="store_true",
                          help="print a cost estimate and exit; place no request")
    p_answer.set_defaults(func=cmd_answer)

    p_score = sub.add_parser("score", help="score one (engine, task, cue) cell from its record")
    p_score.add_argument("engine", choices=ENGINES)
    p_score.add_argument("task", choices=BIOS_TASKS)
    p_score.add_argument("--cue", required=True, choices=CUES)
    p_score.add_argument("--out", default=None,
                         help="default: studies/<task>-<cue>.jsonl")
    p_score.add_argument("--sample", choices=("all", "500"), default=None,
                         help="race-fullname only: which sample to score (default: auto-detect "
                         "from the record)")
    p_score.set_defaults(func=cmd_score)

    p_replay = sub.add_parser(
        "replay", help="score every cell that has a record, including the shortlist block")
    p_replay.set_defaults(func=cmd_replay)

    p_report = sub.add_parser(
        "report", help="regenerate RESULTS.md (or, with --json, the leaderboard data) from the "
        "record")
    p_report.add_argument("--out", default=None,
                          help="default: RESULTS.md, or site/data/leaderboard.json with --json")
    p_report.add_argument("--json", action="store_true",
                          help="write the leaderboard's JSON data file instead of RESULTS.md")
    p_report.add_argument("--date", default=None,
                          help="--json only: the generated date (YYYY-MM-DD) to record in the "
                          "file's provenance; passed in so the build is deterministic")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
