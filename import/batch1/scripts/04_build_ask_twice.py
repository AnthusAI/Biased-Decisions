#!/usr/bin/env python
"""Build versions/ask-twice.txt for the four original tasks: a 500-id uniform subsample (seed
0) of each task's held-out (split=="test") bios, one id per line, sorted -- same method as
``fixtures/bios/race2_jev_subsample.txt`` in Jev-Flywheel (``random.Random(0).sample(sorted(ids),
500)``, then sort the draw for a stable file).

This same 500-id subsample also backs section D (option-order-reversed): both Jev batches ask
about exactly these ids, once with the committed option order and once reversed.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import BATCH1, ORIGINAL_TASKS, load_jsonl  # noqa: E402

SUBSAMPLE_SIZE = 500
SEED = 0


def main() -> None:
    for task, spec in ORIGINAL_TASKS.items():
        items = load_jsonl(spec["items_path"])
        test_ids = sorted(row["id"] for row in items if row["metadata"].get("split") == "test")
        rng = random.Random(SEED)
        subsample = rng.sample(test_ids, min(SUBSAMPLE_SIZE, len(test_ids)))
        subsample.sort()
        out = BATCH1 / "tasks" / task / "versions" / "ask-twice.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(subsample) + "\n", encoding="utf-8")
        print(f"{task}: {len(test_ids)} held-out bios, {len(subsample)} sampled -> {out}")


if __name__ == "__main__":
    main()
