"""Build the antisemitic-tropes-in-depth cue versions for a *pool* of items (the stereotype pool
or the synthetic loan-narrative pool), rather than for a single occupation ``Task`` -- see
``biased_decisions.build.build_antisemitism_insertion``/``build_antisemitism_surname`` for the
occupation-task equivalents this module mirrors.

Kept separate from ``biased_decisions.build`` because those builders read a ``Task``'s
``items.jsonl`` through ``Task.load_items()``; the pools here are plain ``Item`` lists (see
``biased_decisions.tasks.stereotype_pool.draw_pool``), not backed by a ``question.yaml`` with the
binary-choice schema ``Task.load`` requires.
"""
from __future__ import annotations

from typing import List, Tuple

from biased_decisions.cues.antisemitism import (
    CUES as INSERTION_CUES, eligible, insert_clause, surname_versions, versions_for,
)
from biased_decisions.tasks.items import Item

SURNAME_CUE = "antisemitism-surname"
ALL_CUES: Tuple[str, ...] = INSERTION_CUES + (SURNAME_CUE,)


def build_insertion_versions(pool: List[Item], cue: str) -> Tuple[List[dict], int]:
    """Rows for one of the four clause-insertion cues, over an arbitrary item pool. Same
    eligibility rule and row shape as ``biased_decisions.build.build_antisemitism_insertion``,
    generalized to a plain list of items instead of a ``Task``.
    """
    rows: List[dict] = []
    excluded = 0
    for item in pool:
        if not eligible(item.text):
            excluded += 1
            continue
        for version, clause in versions_for(cue):
            rows.append({
                "id": f"{item.id}-{cue}-{version}",
                "text": insert_clause(item.text, clause),
                "metadata": {"cue": cue, "version": version, "source_id": item.id, **item.metadata},
            })
    return rows, excluded


def build_surname_versions(pool: List[Item]) -> Tuple[List[dict], int]:
    """Rows for the surname cue, over an arbitrary item pool. ``index`` (for the deterministic
    surname/first-name draw) is the item's position in ``pool``, matching
    ``biased_decisions.build.build_antisemitism_surname``'s use of its sorted-items index.
    """
    rows: List[dict] = []
    excluded = 0
    for index, item in enumerate(pool):
        gender = item.metadata.get("gender")
        versions = surname_versions(item.text, gender, index)
        if versions is None:
            excluded += 1
            continue
        for version, text, surname in (
            ("jewish", versions.jewish_text, versions.jewish_surname),
            ("floor", versions.floor_text, versions.floor_surname),
        ):
            rows.append({
                "id": f"{item.id}-{SURNAME_CUE}-{version}",
                "text": text,
                "metadata": {
                    "cue": SURNAME_CUE, "version": version, "source_id": item.id,
                    "first": versions.first, "surname": surname, **item.metadata,
                },
            })
    return rows, excluded


def build_versions(pool: List[Item], cue: str) -> Tuple[List[dict], int]:
    """Dispatch to the right builder for ``cue`` -- the surname cue, or one of the four
    clause-insertion cues."""
    if cue == SURNAME_CUE:
        return build_surname_versions(pool)
    if cue in INSERTION_CUES:
        return build_insertion_versions(pool, cue)
    raise KeyError(f"unknown antisemitism cue {cue!r}; one of {ALL_CUES}")
