#!/usr/bin/env python
"""A resumable answer runner for the antisemitic-tropes studies with upstream Laya.

Answers multi-question trope tasks (24 yes/no noul questions per text in ONE model call
per text). Designed to follow the pattern from Biased-Decisions-tooling/var/batch2/scripts/04_laya_answers.py
but adapted for the multi-question trope structure used in the antisemitic-tropes study.

Runs locally, no network, no spend. Each output keeps a `.partial.jsonl` file; ids already
in it are skipped on a rerun, and gzip finalization only happens once every planned id is done.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml


def read_questions(task_dir: Path) -> Dict[str, dict]:
    """Load questions from question.yaml and format for system_one call.

    Returns a dict mapping question keys to {"type": "noul", "instructions": text}.
    """
    doc = yaml.safe_load((task_dir / "question.yaml").read_text(encoding="utf-8"))
    return {key: {"type": "noul", "instructions": spec["question"]}
            for key, spec in doc["questions"].items()}


def load_jsonl(path: Path) -> List[dict]:
    """Load all rows from a JSONL file."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def rows_as_written(task_dir: Path) -> List[Tuple[str, str]]:
    """Load all rows from items.jsonl, returning (id, text) pairs."""
    items = load_jsonl(task_dir / "items.jsonl")
    return [(r["id"], r["text"]) for r in items]


def rows_versions(task_dir: Path, plan_name: str) -> List[Tuple[str, str]]:
    """Load all rows from a versions file, returning (id, text) pairs.

    plan_name is the basename of a file in versions/ (e.g., "antisemitism-religious"
    or "antisemitism-surname").
    """
    rows = load_jsonl(task_dir / "versions" / f"{plan_name}.jsonl")
    return [(r["id"], r["text"]) for r in rows]


class Plan:
    """A single answer plan (as-written or a versions plan)."""

    def __init__(self, name: str, rows: List[Tuple[str, str]], out_dir: Path, task: str):
        self.name = name
        self.rows = rows
        self.out_dir = out_dir / "answers" / "laya" / task
        self.out = self.out_dir / f"{name}.jsonl.gz"
        self.partial = self.out_dir / f"{name}.jsonl.partial.jsonl"


def answer_tropes(
    root: Path,
    task: str,
    plan: str,
    model: Optional[Any] = None,
    out_dir: Optional[Path] = None,
) -> None:
    """Run the answer script on a single plan for a trope task.

    Args:
        root: The project root directory.
        task: The task slug (e.g., "stereotypes-antisemitism").
        plan: The plan name ("as-written" or a versions file basename).
        model: The Laya model object (defaults to laya.load()).
        out_dir: The output directory (defaults to root).
    """
    root = Path(root)
    out_dir = Path(out_dir) if out_dir else root
    task_dir = root / "tasks" / task

    # Load questions and build the plan.
    questions = read_questions(task_dir)

    if plan == "as-written":
        rows = rows_as_written(task_dir)
    else:
        rows = rows_versions(task_dir, plan)

    plan_obj = Plan(plan, rows, out_dir, task)

    # Use default model if not provided (lazy import).
    if model is None:
        import laya
        model = laya.load()
        model_tag = f"laya-upstream:{laya.__version__}"
    else:
        # For testing with a fake model, use a fixed tag.
        model_tag = "laya-upstream:0.3.7"

    # Run the plan.
    _run_plan(plan_obj, model, model_tag, questions)


def _run_plan(plan: Plan, model: Any, model_tag: str, questions: Dict[str, dict]) -> None:
    """Answer all rows in a plan, writing to a partial file and finalizing when done.

    Args:
        plan: The Plan object.
        model: The Laya model object.
        model_tag: The model identifier string (e.g., "laya-upstream:0.3.7").
        questions: The questions dict.
    """
    # Load any existing partial rows and their IDs.
    done_ids = set()
    if plan.partial.exists():
        done_ids = {json.loads(line)["id"] for line in plan.partial.read_text().splitlines()
                    if line.strip()}

    todo = [(i, t) for i, t in plan.rows if i not in done_ids]

    print(f"\n=== {plan.name}: {len(plan.rows)} planned, {len(done_ids)} already done, "
          f"{len(todo)} to answer ===")

    if not todo:
        print("  nothing to send; finalizing.")
        _finish(plan)
        return

    plan.out_dir.mkdir(parents=True, exist_ok=True)
    handle = plan.partial.open("a", encoding="utf-8")
    started = time.perf_counter()
    n_done = 0

    for item_id, text in todo:
        t0 = time.perf_counter()
        result = model.system_one(state=text, questions=questions)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        row = {
            "id": item_id,
            "model": model_tag,
            "usage": result["usage"],
            "latency_ms": latency_ms,
            "answers": result["answers"],
        }
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        n_done += 1
        if n_done % 1000 == 0:
            rate = n_done / (time.perf_counter() - started)
            elapsed = time.perf_counter() - started
            remaining = (len(todo) - n_done) / rate if rate > 0 else float("inf")
            print(f"  {plan.name}: {n_done}/{len(todo)}  {rate:.1f} items/s  "
                  f"elapsed {elapsed:.0f}s  eta {remaining:.0f}s", flush=True)

    handle.close()
    total_s = time.perf_counter() - started
    print(f"  {plan.name}: done, {len(todo)} rows in {total_s:.1f}s "
          f"({len(todo) / total_s:.1f} items/s)")
    _finish(plan)


def _finish(plan: Plan) -> None:
    """Finalize the plan by writing the .gz file if all rows are done.

    Deletes the partial file only once the .gz file is written.
    """
    if not plan.partial.exists():
        return

    done_ids = {json.loads(line)["id"] for line in plan.partial.read_text().splitlines()
                if line.strip()}

    # Only finalize if all planned ids are done.
    if not all(i in done_ids for i, _ in plan.rows):
        return

    plan.out_dir.mkdir(parents=True, exist_ok=True)
    with plan.partial.open(encoding="utf-8") as src, \
            gzip.open(plan.out, "wt", encoding="utf-8") as dst:
        for line in src:
            dst.write(line)
    print(f"  wrote {plan.out} ({plan.out.stat().st_size / 1e6:.2f} MB)")
    plan.partial.unlink()


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "task",
        help="Task slug (e.g., stereotypes-antisemitism, loan-narratives-antisemitism)"
    )
    parser.add_argument(
        "plans",
        nargs="+",
        help="One or more plans: 'as-written' or a versions file basename (e.g., antisemitism-religious)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root (default: current directory)"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: root)"
    )
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out_dir) if args.out_dir else root

    # Import Laya lazily (only when not using a fake model for testing).
    import laya
    model = laya.load()
    model_tag = f"laya-upstream:{laya.__version__}"

    print(f"laya {laya.__version__}")
    print(f"task: {args.task}")
    print(f"plans: {args.plans}")

    overall_start = time.perf_counter()
    for plan_name in args.plans:
        task_dir = root / "tasks" / args.task
        questions = read_questions(task_dir)

        if plan_name == "as-written":
            rows = rows_as_written(task_dir)
        else:
            rows = rows_versions(task_dir, plan_name)

        plan_obj = Plan(plan_name, rows, out_dir, args.task)
        _run_plan(plan_obj, model, model_tag, questions)

    print(f"\nTOTAL wall time: {time.perf_counter() - overall_start:.1f}s")


if __name__ == "__main__":
    main()
