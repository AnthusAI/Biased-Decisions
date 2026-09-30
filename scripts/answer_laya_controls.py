"""Answer the trivial-edit floor and the controlled direct statements with upstream Laya.

    python -m scripts.answer_laya_controls

For the trivial edit, each touched bio is asked twice in this run -- as written and edited -- so
both texts go through the same prompt format (docs/trivial-edit-floor-preregistration.md,
Deviations). Records are written under answers/laya/. One GPU job; a finished record is skipped.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

from biased_decisions import direct_statements as ds
from biased_decisions.engines.builds import load_engine, model_tag
from biased_decisions.engines.laya import build_question
from biased_decisions.record import record_path, write_record
from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.tasks.bios import BIOS_TASKS


async def _answer(engine, model, items, questions):
    rows = []
    for item in items:
        started = time.perf_counter()
        answers = await engine.answer(item.text, questions)
        rows.append({"id": item.id, "model": model, "usage": None,
                     "latency_ms": round((time.perf_counter() - started) * 1000.0, 2), "answers": answers})
    return rows


async def main(root: Path = DEFAULT_ROOT) -> None:
    engine, model = load_engine("laya"), model_tag("laya")
    for slug in BIOS_TASKS:
        path = record_path("laya", slug, "trivial-edit", root=root)
        if path.exists():
            continue
        task = Task.load(slug, root=root)
        by_id = {i.id: i for i in task.load_items()}
        edited = [v for v in task.load_versions("trivial-edit") if v.metadata.get("swapped", 0) > 0]
        originals = [by_id[v.metadata["counterfactual_of"]] for v in edited]
        q = {"Occupation": build_question(task.question, task.options)}
        write_record(path, await _answer(engine, model, originals + edited, q))
        print(f"{slug}: {len(edited)} touched bios, {2 * len(edited)} answers -> {path}", flush=True)
    for slug in (ds.CLAIMS_SLUG, ds.GAZA_SLUG):
        path = record_path("laya", slug, "as-written", root=root)
        if path.exists():
            continue
        task = Task.load(slug, root=root)
        items = task.load_items()
        q = {"Decision": build_question(task.question, task.options)}
        write_record(path, await _answer(engine, model, items, q))
        print(f"{slug}: {len(items)} answers -> {path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
