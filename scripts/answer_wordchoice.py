"""A resumable answer runner for ``gendered-word-choice`` (Laya, local, no network, no spend).

Every text of this task carries its own question and option order (``metadata.question`` and
``metadata.options`` in ``versions/<pair>.jsonl``), so the fixed-question runner cannot be used.
One choice question per text, keyed ``Decision``; the record shape and the ``.partial.jsonl``
resume file are those of ``scripts/answer_task.py``.

    scripts/answer_wordchoice.py <pair> --build laya-mlx
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Optional

from biased_decisions.engines.builds import BUILDS, DEFAULT_BUILD, check_build, load_engine, model_tag
from biased_decisions.engines.laya import build_question
from biased_decisions.record import write_record
from biased_decisions.tasks.base import DEFAULT_ROOT, Task

SLUG = "gendered-word-choice"


async def run(root: Path, cue: str, *, engine: Optional[Any] = None, build: str = DEFAULT_BUILD) -> None:
    root = Path(root)
    check_build(build)
    task = Task.load(SLUG, root=root)
    items = task.load_versions(cue)
    if not items:
        raise SystemExit(f"no versions for {SLUG}/{cue}")
    if engine is None:
        engine = load_engine(build)
    out_dir = root / "answers" / build / SLUG
    out_dir.mkdir(parents=True, exist_ok=True)
    final, partial = out_dir / f"{cue}.jsonl.gz", out_dir / f"{cue}.jsonl.partial.jsonl"
    rows = []
    if partial.exists():
        rows = [json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = {row["id"] for row in rows}
    model = model_tag(build)
    started_all, printed = time.time(), time.time()
    with partial.open("a", encoding="utf-8") as handle:
        for index, item in enumerate(items):
            if item.id in done:
                continue
            question = build_question(item.metadata["question"], item.metadata["options"])
            started = time.perf_counter()
            answers = await engine.answer(item.text, {"Decision": question})
            row = {"id": item.id, "model": model, "usage": None,
                   "latency_ms": round((time.perf_counter() - started) * 1000.0, 2), "answers": answers}
            rows.append(row)
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            if time.time() - printed > 5:
                printed = time.time()
                print(f"  {index + 1}/{len(items)} texts, {(len(rows)) / max(printed - started_all, 1e-9):.1f} per second")
    by_id = {row["id"]: row for row in rows}
    write_record(final, [by_id[item.id] for item in items])
    partial.unlink()
    print(f"Finished {cue}: {len(items)} rows")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cue", help="a word pair, e.g. assertive-bossy")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--build", choices=BUILDS, default=DEFAULT_BUILD)
    args = parser.parse_args()
    await run(args.root, args.cue, build=args.build)


if __name__ == "__main__":
    asyncio.run(main())
