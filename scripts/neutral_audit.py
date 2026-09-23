"""Audit script to compare neutral pronoun versions with original text."""
import json
import random
from pathlib import Path
from typing import Dict

from biased_decisions.tasks.base import Task, DEFAULT_ROOT


def audit_task(task_slug: str, root: Path = DEFAULT_ROOT):
    """Load neutral.jsonl for a task, filter to 'they' version, and print audit output.

    Args:
        task_slug: The task slug (e.g., "surgeon-physician").
        root: The project root directory.
    """
    root = Path(root)

    # Load the task.
    task = Task.load(task_slug, root=root)

    # Load the neutral versions.
    versions = task.load_versions("neutral")

    # Keep only rows where metadata.version is "they".
    they_rows = [row for row in versions if row.metadata.get("version") == "they"]

    # Sort by id for determinism, then sample 50 rows.
    they_rows_sorted = sorted(they_rows, key=lambda r: r.id)
    sampled_rows = random.Random(0).sample(they_rows_sorted, min(50, len(they_rows_sorted)))

    # Load all items to create a lookup by id.
    items = task.load_items()
    items_by_id: Dict[str, str] = {item.id: item.text for item in items}

    # Print audit output.
    for row in sampled_rows:
        source_id = row.metadata.get("source_id")
        original_text = items_by_id.get(source_id, "NOT FOUND")
        print(f"ORIGINAL: {original_text}")
        print(f"THEY: {row.text}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit neutral pronoun versions")
    parser.add_argument("task", help="Task slug (e.g., surgeon-physician)")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Project root")
    args = parser.parse_args()

    audit_task(args.task, args.root)
