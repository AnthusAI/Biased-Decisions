"""The registered first-pass subsample (docs/subsample-preregistration.md).

Items are ranked by a hash of their family, never by anything a model said, so a cell's first N
families are the same for every model, every cue of the task, and every later, larger cap. A family is an
original text together with its twin, edited versions and controls; it is kept or dropped as a whole.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Sequence

from biased_decisions.tasks.items import Item

SEED = "biased-decisions-subsample-1"


def family_id(item: Item, task: str) -> str:
    """The id of the original text this item derives from, without any task prefix."""
    meta = item.metadata or {}
    family = str(meta.get("source_id") or meta.get("counterfactual_of") or item.id)
    for prefix in {task, meta.get("source_task")}:
        if prefix and family.startswith(f"{prefix}-"):
            return family[len(prefix) + 1:]
    return family


def _rank(task: str, family: str) -> tuple:
    digest = hashlib.sha256(f"{SEED}|{task}|{family}".encode()).hexdigest()
    return digest, family


def subsample(items: Sequence[Item], task: str, cap: Optional[int]) -> list:
    """The items of the first ``cap`` families of a cell, in the cell's own order."""
    if cap is None:
        return list(items)
    if cap < 1:
        raise ValueError("the item cap must be positive")
    families = {family_id(i, task) for i in items}
    if len(families) <= cap:
        return list(items)
    chosen = set(sorted(families, key=lambda f: _rank(task, f))[:cap])
    return [i for i in items if family_id(i, task) in chosen]


def cell_sample(items: Sequence[Item], task: str, cue: str, cap: Optional[int], versions_dir: Path) -> list:
    """The items a capped collection answers for one cell.

    A cell that already has a committed sample (``<cue>_jev-subsample.txt``, the 500 bios Jev answered for
    race-fullname) keeps exactly those families, so every model answers the same bios. Every other cell
    takes the first ``cap`` families of the registered ranking. With no cap the cell is whole."""
    if cap is None:
        return list(items)
    committed = Path(versions_dir) / f"{cue}_jev-subsample.txt"
    if committed.exists():
        fixed = {line.strip() for line in committed.read_text(encoding="utf-8").splitlines() if line.strip()}
        return [i for i in items if family_id(i, task) in fixed]
    return subsample(items, task, cap)
