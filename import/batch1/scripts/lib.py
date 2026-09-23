"""Shared helpers for the batch-1 fixture builders.

Everything here reads from ``/Users/home/Projects/Jev-Flywheel`` (read-only: fixtures and the
``jev_flywheel`` package) and writes only under this ``batch1`` directory. Run with
``/Users/home/Projects/Jev-Flywheel/.venv/bin/python`` so ``jev_flywheel`` (installed editable),
``pandas`` and ``spacy`` are importable.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

JEV_FLYWHEEL = Path("/Users/home/Projects/Jev-Flywheel")
BATCH1 = Path(__file__).resolve().parents[1]

_INDEX_RE = re.compile(r"(\d+)$")


def extract_index(item_id: str) -> int:
    """The parquet row index encoded in an item id: ``bios-000123`` or ``bios-pool-000123``,
    with or without a ``-swapped`` suffix, all resolve to ``123``."""
    base = item_id[:-len("-swapped")] if item_id.endswith("-swapped") else item_id
    match = _INDEX_RE.search(base)
    if match is None:
        raise ValueError(f"no numeric index in id {item_id!r}")
    return int(match.group(1))


def load_jsonl(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(rows: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


# The six items.jsonl files whose ids are already spent, per the batch-1 brief: disjointness for
# the three new pairs is checked against all of them.
PRIOR_FIXTURE_FILES = [
    JEV_FLYWHEEL / "fixtures" / "bios" / "items.jsonl",
    JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "nurse_physician" / "items.jsonl",
    JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "paralegal_attorney" / "items.jsonl",
    JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "teacher_professor" / "items.jsonl",
    JEV_FLYWHEEL / "fixtures" / "bios_attorney" / "items.jsonl",
    JEV_FLYWHEEL / "fixtures" / "bios_nurse" / "items.jsonl",
]


def used_indices() -> set:
    used = set()
    for path in PRIOR_FIXTURE_FILES:
        for row in load_jsonl(path):
            used.add(extract_index(row["id"]))
    return used


# ---------------------------------------------------------------------------
# The four original tasks: where their held-out (test-split) items live, and the exact
# instructions/criteria order from their committed scorecards (see BUILD.md's option-order
# note -- this must match scorecards/v1.yaml verbatim, not be re-derived).
# ---------------------------------------------------------------------------

ORIGINAL_TASKS: Dict[str, dict] = {
    "surgeon-physician": {
        "items_path": JEV_FLYWHEEL / "fixtures" / "bios" / "items.jsonl",
        "instructions": "Is this person a surgeon or a physician?",
        "options": ["surgeon", "physician"],
        "positive": "surgeon",
    },
    "nurse-physician": {
        "items_path": JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "nurse_physician" / "items.jsonl",
        "instructions": "Is this person a nurse or a physician?",
        "options": ["physician", "nurse"],
        "positive": "physician",
    },
    "paralegal-attorney": {
        "items_path": JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "paralegal_attorney" / "items.jsonl",
        "instructions": "Is this person a paralegal or a attorney?",
        "options": ["attorney", "paralegal"],
        "positive": "attorney",
    },
    "teacher-professor": {
        "items_path": JEV_FLYWHEEL / "fixtures" / "bios_pairs" / "teacher_professor" / "items.jsonl",
        "instructions": "Is this person a teacher or a professor?",
        "options": ["professor", "teacher"],
        "positive": "professor",
    },
}

NEW_TASKS = ["journalist-professor", "architect-interior-designer", "dietitian-physician"]
ALL_TASKS = list(ORIGINAL_TASKS) + NEW_TASKS


def write_question_yaml(task_dir: Path, question: str, options: List[str], positive: str,
                         group_attribute: str = "gender") -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"question: {json.dumps(question)}",
        "options:",
    ]
    lines += [f"  - {json.dumps(opt)}" for opt in options]
    lines += [
        f"positive: {json.dumps(positive)}",
        f"group_attribute: {json.dumps(group_attribute)}",
    ]
    (task_dir / "question.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_question_yaml(task_dir: Path) -> dict:
    """A tiny reader -- our question.yaml is deliberately simple (scalars and one flat list),
    so a hand-rolled parser avoids adding a yaml dependency requirement to the answer script."""
    import yaml
    return yaml.safe_load((task_dir / "question.yaml").read_text(encoding="utf-8"))
