"""The antisemitic-tropes-in-depth stereotype pool: 2,000 Bias in Bios bios drawn 500 per task
from the four original tasks' held-out splits, the same pool batch 2 used (see
``studies/batch2/README.md`` and ``docs/antisemitic-tropes-preregistration.md``, "Texts", Pool A).

This pool is a plain list of ``Item``s, not a ``biased_decisions.tasks.base.Task``: the
trope-susceptibility grid asks several independent yes/no questions per bio-version rather than
one binary occupation choice, so its ``question.yaml`` (``tasks/stereotypes-antisemitism/
question.yaml``) does not carry the ``options``/``positive``/``group_attribute`` keys
``Task.load`` requires, and is read directly by the scoring/build scripts for this study instead.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from biased_decisions.tasks.bios import load_task
from biased_decisions.tasks.items import Item

ORIGINAL_TASKS: Tuple[str, ...] = (
    "paralegal-attorney", "surgeon-physician", "teacher-professor", "nurse-physician",
)
PER_TASK = 500
POOL_SEED = 0


def draw_pool(tasks: Tuple[str, ...] = ORIGINAL_TASKS, *, per_task: int = PER_TASK,
             seed: int = POOL_SEED) -> List[Item]:
    """500 held-out (``split == "test"``) items per task, drawn
    ``random.Random(seed).sample(sorted_ids, per_task)`` then re-sorted -- the same
    draw-then-sort method ``biased_decisions.build.build_race_fullname`` uses for its Jev
    subsample, reused here for the same reason: a reproducible sample that needs no separately
    recorded random state, only the seed.

    Items are returned in task order, then by id within each task -- deterministic and stable
    across repeated calls with the same arguments.
    """
    rng = random.Random(seed)
    pool: List[Item] = []
    for task_slug in tasks:
        task = load_task(task_slug)
        test_items = {item.id: item for item in task.load_items()
                     if item.metadata.get("split") == "test"}
        sorted_ids = sorted(test_items)
        chosen_ids = rng.sample(sorted_ids, min(per_task, len(sorted_ids)))
        chosen_ids.sort()
        for item_id in chosen_ids:
            source = test_items[item_id]
            pool.append(Item(
                id=f"{task_slug}-{source.id}",
                text=source.text,
                metadata={
                    **source.metadata,
                    "source_task": task_slug,
                    "source_id": source.id,
                },
            ))
    return pool
