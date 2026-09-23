#!/usr/bin/env python
"""Step 2: answer batch-1 rows with Jev, priced first, cap 24,000 requests total.

Network only (needs TYPESAFE_API_KEY, loaded from Jev-Flywheel's .env via python-dotenv; never
printed). Runs the files in this fixed order, pricing and logging each one to batch1/spend.md
before sending, and refusing to start a file that would push the running total over 24,000:

  (a) gender-pronouns on the three new tasks -- every row (test + counterfactual) of each
      task's own items.jsonl.
  (b) disability on paralegal-attorney and surgeon-physician -- all eligible rows of both
      versions (versions/disability.jsonl already excludes ineligible bios).
  (c) ask-twice -- the 500-bio subsample (versions/ask-twice.txt) of each of the four original
      tasks, asked once more, unchanged, with the task's own committed option order.
  (d) option-order-reversed -- the same 500-bio subsample, same instructions text, but with the
      criteria order reversed relative to the committed scorecard (pre-registration section D).

religion is never sent to Jev (out of scope for this batch by the pre-registration).

Every question dict is built from question.yaml's ``options`` list (or its reverse for (d)):
``{"Occupation": {"type": "choice", "instructions": <question>, "criteria": {opt: null, ...}}}``
-- the order of ``options`` is preserved into ``criteria`` because dict comprehensions preserve
insertion order in Python, and this is exactly why (d) exists to check.

Resumable: each output keeps a ``.partial.jsonl`` file under the same answers/jev/<task>/
directory; ids already in it are skipped on a rerun, and gzip finalization only happens once
every planned id for that file is done.
"""
from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import BATCH1, ORIGINAL_TASKS, NEW_TASKS, load_jsonl  # noqa: E402

from jev_flywheel.jev import JevSession  # noqa: E402

REQUEST_CAP = 24000
SPEND_LOG = BATCH1 / "spend.md"
CONCURRENCY = 16

# (b): disability on these two tasks, in this order, per the brief.
DISABILITY_TASKS = ["paralegal-attorney", "surgeon-physician"]
# (c)/(d): all four original tasks, in a fixed order.
ORIGINAL_TASK_ORDER = ["surgeon-physician", "nurse-physician", "paralegal-attorney",
                       "teacher-professor"]


def read_question_yaml(task: str) -> dict:
    return yaml.safe_load((BATCH1 / "tasks" / task / "question.yaml").read_text(encoding="utf-8"))


def build_questions(instructions: str, options: List[str]) -> Dict[str, dict]:
    return {"Occupation": {"type": "choice", "instructions": instructions,
                           "criteria": {opt: None for opt in options}}}


def rows_gender_pronouns(task: str) -> List[dict]:
    return load_jsonl(BATCH1 / "tasks" / task / "items.jsonl")


def rows_disability(task: str) -> List[dict]:
    return load_jsonl(BATCH1 / "tasks" / task / "versions" / "disability.jsonl")


def subsample_ids(task: str) -> List[str]:
    path = BATCH1 / "tasks" / task / "versions" / "ask-twice.txt"
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def text_lookup(task: str, ids: List[str]) -> Dict[str, str]:
    ids = set(ids)
    items = load_jsonl(ORIGINAL_TASKS[task]["items_path"])
    return {row["id"]: row["text"] for row in items if row["id"] in ids}


class Plan:
    """One file to build: a list of (id, text) rows and the fixed question set to ask."""

    def __init__(self, task: str, cue: str, rows: List[Tuple[str, str]], questions: dict,
                order_note: str):
        self.task = task
        self.cue = cue
        self.rows = rows
        self.questions = questions
        self.order_note = order_note
        self.out = BATCH1 / "answers" / "jev" / task / f"{cue}.jsonl.gz"
        self.partial = BATCH1 / "answers" / "jev" / task / f"{cue}.partial.jsonl"


def build_plans() -> List[Plan]:
    plans: List[Plan] = []

    # (a) gender-pronouns on the three new tasks.
    for task in NEW_TASKS:
        q = read_question_yaml(task)
        questions = build_questions(q["question"], q["options"])
        rows = [(r["id"], r["text"]) for r in rows_gender_pronouns(task)]
        plans.append(Plan(task, "gender-pronouns", rows, questions,
                          f"committed order {q['options']}"))

    # (b) disability on paralegal-attorney and surgeon-physician, all eligible rows.
    for task in DISABILITY_TASKS:
        spec = ORIGINAL_TASKS[task]
        questions = build_questions(spec["instructions"], spec["options"])
        rows = [(r["id"], r["text"]) for r in rows_disability(task)]
        plans.append(Plan(task, "disability", rows, questions,
                          f"committed order {spec['options']}"))

    # (c) ask-twice: the 500-bio subsample of each of the four original tasks, unchanged.
    for task in ORIGINAL_TASK_ORDER:
        spec = ORIGINAL_TASKS[task]
        questions = build_questions(spec["instructions"], spec["options"])
        ids = subsample_ids(task)
        texts = text_lookup(task, ids)
        rows = [(i, texts[i]) for i in ids]
        plans.append(Plan(task, "ask-twice", rows, questions,
                          f"committed order {spec['options']}"))

    # (d) option-order-reversed: same subsample, same instructions, reversed criteria order.
    for task in ORIGINAL_TASK_ORDER:
        spec = ORIGINAL_TASKS[task]
        reversed_options = list(reversed(spec["options"]))
        questions = build_questions(spec["instructions"], reversed_options)
        ids = subsample_ids(task)
        texts = text_lookup(task, ids)
        rows = [(i, texts[i]) for i in ids]
        plans.append(Plan(task, "option-order-reversed", rows, questions,
                          f"reversed order {reversed_options} (committed was {spec['options']})"))

    return plans


def log_spend(line: str) -> None:
    print(line)
    with SPEND_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


async def run_plan(plan: Plan, price_only: bool, running_total: int) -> Tuple[int, int, int, int]:
    """Returns (requests_counted_toward_cap, requests_sent, input_tokens, output_tokens)."""
    done_ids = set()
    if plan.partial.exists():
        done_ids = {json.loads(line)["id"] for line in plan.partial.read_text().splitlines()
                    if line.strip()}
    todo = [(i, t) for i, t in plan.rows if i not in done_ids]

    planned = len(plan.rows)
    log_spend(f"\n### {plan.task} / {plan.cue}\n"
              f"- rows: {planned} ({plan.order_note})\n"
              f"- already done (resumed): {len(done_ids)}\n"
              f"- to send this run: {len(todo)}\n"
              f"- running total before this file: {running_total}\n"
              f"- running total after this file (if sent in full): "
              f"{running_total + len(todo)}")

    if running_total + len(todo) > REQUEST_CAP:
        log_spend(f"- STOPPING: sending {len(todo)} would put the running total at "
                  f"{running_total + len(todo)}, over the {REQUEST_CAP} cap. Not sent.")
        return 0, 0, 0, 0

    if price_only:
        log_spend("- price-only run: not sent.")
        return len(todo), 0, 0, 0

    if not todo:
        log_spend("- nothing to send (already complete); finalizing.")
        _finish(plan)
        return 0, 0, 0, 0

    session = JevSession()
    semaphore = asyncio.Semaphore(CONCURRENCY)
    plan.partial.parent.mkdir(parents=True, exist_ok=True)
    write_lock = asyncio.Lock()
    handle = plan.partial.open("a", encoding="utf-8")
    started = time.perf_counter()
    n_done = 0
    failures: List[str] = []

    async def one(item_id: str, text: str):
        nonlocal n_done
        async with semaphore:
            t0 = time.perf_counter()
            try:
                result = await session.ask(text, plan.questions)
            except Exception as error:  # noqa: BLE001
                failures.append(f"{item_id}: {type(error).__name__}: {error}")
                print(f"  FAILED {item_id}: {type(error).__name__}: {error}")
                return
            row = {"id": item_id, "model": result.model, "usage": result.usage,
                   "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                   "answers": result.answers}
            async with write_lock:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                n_done += 1
                if n_done % 500 == 0:
                    rate = n_done / (time.perf_counter() - started)
                    print(f"  {plan.task}/{plan.cue}: {n_done}/{len(todo)}  {rate:.1f} items/s",
                         flush=True)

    await asyncio.gather(*(one(i, t) for i, t in todo))
    handle.close()
    log_spend(f"- sent {session.requests_sent} requests, {session.input_tokens:,} input tokens, "
              f"{session.output_tokens:,} output tokens")
    if failures:
        log_spend(f"- {len(failures)} FAILURES: " + "; ".join(failures[:10]) +
                  (" ..." if len(failures) > 10 else ""))
    _finish(plan)
    return len(todo), session.requests_sent, session.input_tokens, session.output_tokens


def _finish(plan: Plan) -> None:
    if not plan.partial.exists():
        return
    done_ids = {json.loads(line)["id"] for line in plan.partial.read_text().splitlines()
               if line.strip()}
    if not all(i in done_ids for i, _ in plan.rows):
        return  # not complete yet
    plan.out.parent.mkdir(parents=True, exist_ok=True)
    with plan.partial.open(encoding="utf-8") as src, gzip.open(plan.out, "wt",
                                                                encoding="utf-8") as dst:
        for line in src:
            dst.write(line)
    print(f"  wrote {plan.out} ({plan.out.stat().st_size / 1e6:.2f} MB)")


async def main_async(price_only: bool, only: Optional[str]) -> None:
    plans = build_plans()
    if only:
        plans = [p for p in plans if f"{p.task}/{p.cue}" == only]
        if not plans:
            raise SystemExit(f"no plan matches --only {only!r}")

    SPEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not SPEND_LOG.exists():
        SPEND_LOG.write_text("# Batch 1: Jev spend log\n", encoding="utf-8")

    running_total = 1  # the pre-flight smoke test (see spend.md), sent by hand before this script
    total_sent = 0
    total_input = 0
    total_output = 0
    for plan in plans:
        counted, sent, inp, out = await run_plan(plan, price_only, running_total)
        running_total += counted
        total_sent += sent
        total_input += inp
        total_output += out

    label = "would send" if price_only else "sent"
    log_spend(f"\n## Run summary\n- total requests {label} this run: {running_total}\n"
              f"- total requests actually sent (API calls) this run: {total_sent}\n"
              f"- total input tokens this run: {total_input:,}\n"
              f"- total output tokens this run: {total_output:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--price-only", action="store_true",
                        help="report counts and log to spend.md; send nothing")
    parser.add_argument("--only", type=str, default=None,
                        help="run only the plan matching 'task/cue', e.g. "
                             "'surgeon-physician/ask-twice'")
    args = parser.parse_args()
    load_dotenv(Path("/Users/home/Projects/Jev-Flywheel") / ".env")
    asyncio.run(main_async(args.price_only, args.only))


if __name__ == "__main__":
    main()
