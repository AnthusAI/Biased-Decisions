"""A resumable answer runner for any task and cue on upstream Laya."""
import asyncio
import argparse
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from biased_decisions.tasks.base import Task, DEFAULT_ROOT
from biased_decisions.engines.laya import LayaEngine, build_question
from biased_decisions.record import write_record


async def run(
    root: Path,
    task_slug: str,
    cue: str,
    *,
    engine: Optional[Any] = None,
    out_dir: Optional[Path] = None,
    model_name: str = "laya-upstream:0.3.7",
    skip_as_written: bool = False,
) -> None:
    """Run the answer script on a task and cue.

    Args:
        root: The project root directory.
        task_slug: The task slug (e.g., "qpain-treatment").
        cue: The cue name (e.g., "race").
        engine: The engine to use (defaults to LayaEngine).
        out_dir: The output directory (defaults to root).
        model_name: The model name string for the record.
        skip_as_written: If True, skip answering the as-written set.
    """
    root = Path(root)
    out_dir = Path(out_dir) if out_dir else root

    # Load the task.
    task = Task.load(task_slug, root=root)

    # Build the question.
    question_dict = build_question(task.question, task.options)
    questions = {"Decision": question_dict}

    # Use default engine if not provided.
    if engine is None:
        engine = LayaEngine()

    # Answer the as-written set unless skipped.
    if not skip_as_written:
        await _answer_set(
            root, out_dir, task_slug, "as-written",
            task.load_items(), questions, engine, model_name,
            split_filter="test"
        )

    # Answer the cue set.
    await _answer_set(
        root, out_dir, task_slug, cue,
        task.load_versions(cue), questions, engine, model_name
    )


async def _answer_set(
    root: Path,
    out_dir: Path,
    task_slug: str,
    name: str,
    items: List[Any],
    questions: Dict[str, Dict[str, Any]],
    engine: Any,
    model_name: str,
    split_filter: Optional[str] = None,
) -> None:
    """Answer a set of items and write to a record file.

    Args:
        root: The project root.
        out_dir: The output directory.
        task_slug: The task slug.
        name: The set name (e.g., "as-written" or cue name).
        items: The items to answer.
        questions: The questions to answer.
        engine: The engine to use.
        model_name: The model name string.
        split_filter: Optional split filter (e.g., "test" for items metadata.split).
    """
    # Filter items if split_filter is provided.
    if split_filter:
        items = [item for item in items if item.metadata.get("split") == split_filter]

    # Determine output paths.
    answers_dir = out_dir / "answers" / "laya" / task_slug
    answers_dir.mkdir(parents=True, exist_ok=True)

    final_path = answers_dir / f"{name}.jsonl.gz"
    partial_path = answers_dir / f"{name}.jsonl.partial.jsonl"

    # Load any existing partial rows and their IDs.
    existing_rows: List[Dict[str, Any]] = []
    existing_ids = set()
    if partial_path.exists():
        with open(partial_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    existing_ids.add(row["id"])
                    existing_rows.append(row)

    # Answer the items.
    rows: List[Dict[str, Any]] = []
    total = len(items)
    last_print_time = time.time()
    start_time = time.time()

    with open(partial_path, "a", encoding="utf-8") as partial_f:
        for idx, item in enumerate(items):
            if item.id in existing_ids:
                # Already answered, skip.
                continue

            # Get the item's text.
            text = item.text

            # Answer the question.
            started = time.perf_counter()
            answers = await engine.answer(text, questions)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)

            # Build the row.
            row = {
                "id": item.id,
                "model": model_name,
                "usage": None,
                "latency_ms": latency_ms,
                "answers": answers,
            }
            rows.append(row)

            # Write to partial file and flush.
            partial_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            partial_f.flush()

            # Print progress every 200 items.
            now = time.time()
            if (idx + 1) % 200 == 0 or now - last_print_time > 5:
                elapsed = now - start_time
                items_per_sec = (idx + 1 - len(existing_ids)) / elapsed if elapsed > 0 else 0
                print(f"  {idx + 1 - len(existing_ids)}/{total - len(existing_ids)} items, {items_per_sec:.1f} items/sec")
                last_print_time = now

    # Write the final file with both existing and new rows.
    all_rows = existing_rows + rows
    write_record(final_path, all_rows)

    # Delete the partial file.
    if partial_path.exists():
        partial_path.unlink()

    print(f"Finished {name}: {len(rows)} new rows written")


async def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Answer a task and cue with upstream Laya")
    parser.add_argument("task", help="Task slug (e.g., qpain-treatment)")
    parser.add_argument("cue", help="Cue name (e.g., race)")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Project root")
    parser.add_argument("--skip-as-written", action="store_true", help="Skip answering the as-written set")
    args = parser.parse_args()

    await run(args.root, args.task, args.cue, skip_as_written=args.skip_as_written)


if __name__ == "__main__":
    asyncio.run(main())
