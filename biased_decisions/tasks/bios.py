"""The Bias in Bios tasks: four occupation-pair choice questions over the same redacted-bios
corpus family (De-Arteaga et al. 2019's "Bias in Bios", first names redacted -- see
``biased_decisions.cues.redaction``).

``surgeon-physician`` is the primary task: every cue (``gender-pronouns``, ``race-name``,
``race-fullname``, ``age-inserted``) has a committed record for it. The other three
(``nurse-physician``, ``teacher-professor``, ``paralegal-attorney``) exist to check whether the
gender result generalizes to other occupation pairs and carry only the ``gender-pronouns`` cue.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.tasks.items import Item

# Every milestone-1 Bias in Bios task, in the order the design doc lists them. The pair label
# names the *primary* (positive) class first, matching each task's own directory name.
BIOS_TASKS: Tuple[str, ...] = (
    "surgeon-physician", "nurse-physician", "teacher-professor", "paralegal-attorney")

# The one question every bios task asks; matches the "Occupation" key every committed answer
# row keys its answer by.
QUESTION_NAME = "Occupation"


def load_task(slug: str, *, root: Optional[Path] = None) -> Task:
    """A bios task by slug, e.g. ``load_task("surgeon-physician")``."""
    if slug not in BIOS_TASKS:
        raise ValueError(f"{slug!r} is not one of the bios tasks {BIOS_TASKS!r}")
    return Task.load(slug, root=root or DEFAULT_ROOT)


def load_all() -> Dict[str, Task]:
    return {slug: load_task(slug) for slug in BIOS_TASKS}


def split_test_and_twins(items: List[Item]) -> Tuple[List[Item], Dict[str, Item]]:
    """Split a task's ``items.jsonl`` into the held-out test bios and a mapping from each one's
    id to its ``gender-pronouns`` counterfactual twin.

    Every milestone-1 bios task commits its twins inside ``items.jsonl`` itself: the twin's id is
    the original's with ``-swapped`` appended, its ``metadata.split`` is ``"counterfactual"``,
    and ``metadata.counterfactual_of`` names the original id it belongs to. A bio the swap could
    not touch (no subject pronoun) has no twin and is simply absent from the mapping.
    """
    by_source: Dict[str, Item] = {}
    test_items: List[Item] = []
    for item in items:
        split = item.metadata.get("split")
        if split == "test":
            test_items.append(item)
        elif split == "counterfactual":
            source_id = item.metadata.get("counterfactual_of")
            if source_id:
                by_source[source_id] = item
    return test_items, by_source
