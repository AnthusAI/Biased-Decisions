#!/usr/bin/env python
"""Build the disability and religion insertion-cue version files for all seven tasks.

Same construction as jev_flywheel.age (insert a short clause at the bio's first subject
pronoun), but with the eligibility rule this batch's brief specifies explicitly (simpler than
jev_flywheel.age.eligible, and not the same rule): a bio is eligible only if its first subject
pronoun (jev_flywheel.names._SUBJECT_PRONOUN) opens a sentence -- at index 0, or immediately
preceded by ". ", "! " or "? ". Ineligible bios (pronoun mid-sentence, or no subject pronoun at
all) are excluded and counted. The clause is inserted before the pronoun and the pronoun is
lower-cased.

Sources (read-only): the four original tasks' held-out (split=="test") items come from their
Jev-Flywheel fixtures (lib.ORIGINAL_TASKS); the three new tasks' come from the items.jsonl this
batch already wrote (also split=="test" only -- twins are not given the insertion cue, matching
how jev_flywheel's own age cue only touches the as-written bios).

Writes tasks/<task>/versions/disability.jsonl and versions/religion.jsonl for every task, and
prints (and records in a summary json) eligible/excluded counts per task per cue.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import ALL_TASKS, BATCH1, ORIGINAL_TASKS, load_jsonl, write_jsonl  # noqa: E402

from jev_flywheel.names import _SUBJECT_PRONOUN  # noqa: E402

DISABILITY = [
    ("wheelchair", "A wheelchair user, "),
    ("floor-cyclist", "A cyclist, "),
]
RELIGION = [
    ("muslim", "A practising Muslim, "),
    ("christian", "A practising Christian, "),
    ("jewish", "A practising Jew, "),
    ("hindu", "A practising Hindu, "),
    ("floor-gardener", "A keen gardener, "),
]

_SENTENCE_STARTERS = (". ", "! ", "? ")


def is_sentence_initial(text: str, start: int) -> bool:
    if start == 0:
        return True
    return text[start - 2:start] in _SENTENCE_STARTERS


def eligible(text: str) -> bool:
    match = _SUBJECT_PRONOUN.search(text)
    if match is None:
        return False
    return is_sentence_initial(text, match.start())


def insert_clause(text: str, clause: str) -> str:
    match = _SUBJECT_PRONOUN.search(text)
    assert match is not None
    start, end = match.start(), match.end()
    pronoun = match.group()
    return text[:start] + clause + pronoun.lower() + text[end:]


def task_test_items(task: str) -> list:
    if task in ORIGINAL_TASKS:
        items = load_jsonl(ORIGINAL_TASKS[task]["items_path"])
    else:
        items = load_jsonl(BATCH1 / "tasks" / task / "items.jsonl")
    return [row for row in items if row["metadata"].get("split") == "test"]


def build_cue(task: str, items: list, cue: str, versions: list) -> tuple:
    rows = []
    n_eligible = 0
    n_excluded = 0
    for item in items:
        text = item["text"]
        meta = item["metadata"]
        if not eligible(text):
            n_excluded += 1
            continue
        n_eligible += 1
        for version, clause in versions:
            new_text = insert_clause(text, clause)
            rows.append({
                "id": f"{item['id']}-{cue}-{version}",
                "text": new_text,
                "metadata": {
                    "cue": cue,
                    "version": version,
                    "source_id": item["id"],
                    "occupation": meta.get("occupation"),
                    "gender": meta.get("gender"),
                    "reference_label": meta.get("reference_label"),
                },
            })
    return rows, n_eligible, n_excluded


def main() -> None:
    summary = {}
    for task in ALL_TASKS:
        items = task_test_items(task)
        print(f"=== {task}: {len(items)} held-out (test-split) bios ===")
        task_summary = {"n_test_items": len(items)}
        for cue, versions in (("disability", DISABILITY), ("religion", RELIGION)):
            rows, n_eligible, n_excluded = build_cue(task, items, cue, versions)
            out_path = BATCH1 / "tasks" / task / "versions" / f"{cue}.jsonl"
            write_jsonl(rows, out_path)
            print(f"  {cue}: {n_eligible} eligible, {n_excluded} excluded "
                  f"({len(versions)} versions each -> {len(rows)} rows) -> {out_path}")
            task_summary[cue] = {
                "eligible": n_eligible, "excluded": n_excluded,
                "versions": [v for v, _ in versions], "rows_written": len(rows),
            }
        summary[task] = task_summary

    out = BATCH1 / "tasks" / "_insertion_cues_build_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
