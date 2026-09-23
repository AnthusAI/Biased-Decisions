#!/usr/bin/env python
"""Write question.yaml for the four original tasks, verbatim from their committed scorecards
(fixtures/bios/scorecards/v1.yaml and fixtures/bios_pairs/<pair>/scorecards/v1.yaml in
Jev-Flywheel), per the coordinator's option-order rule: instructions text and criteria key
order must match the record exactly, since Laya's (and possibly Jev's) answer depends on it.

No items.jsonl is written for these four tasks -- their held-out bios already exist, read-only,
in the Jev-Flywheel fixtures named in lib.ORIGINAL_TASKS; batch1 only adds what's new (the
question.yaml pin and the cue version files).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import BATCH1, ORIGINAL_TASKS, write_question_yaml  # noqa: E402


def main() -> None:
    for task, spec in ORIGINAL_TASKS.items():
        out_dir = BATCH1 / "tasks" / task
        write_question_yaml(out_dir, spec["instructions"], spec["options"], spec["positive"])
        print(f"{task}: {spec['instructions']!r} options={spec['options']} "
              f"positive={spec['positive']!r} -> {out_dir/'question.yaml'}")


if __name__ == "__main__":
    main()
