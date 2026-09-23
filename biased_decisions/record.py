"""The answer record: committed caches so ``bd replay`` reproduces every row without a key.

A record lives at ``answers/<engine>/<task>/<cue>.jsonl.gz`` (see the design doc's package
layout) and holds one gzipped JSONL row per item, in the exact shape every answer builder in
Jev-Flywheel already wrote: ``{id, model, usage, latency_ms, answers}``, where ``answers`` is a
mapping of question name (``"Occupation"`` for every milestone-1 task) to that question's answer
body (``type``, ``choice``, ``probabilities``, and whatever else the engine reports).

The record is the unit of reproducibility: nothing above this module needs a network key or a
GPU to turn a record into a score.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

from biased_decisions.tasks.base import DEFAULT_ROOT

REQUIRED_FIELDS: Tuple[str, ...] = ("id", "model", "usage", "latency_ms", "answers")


def record_path(engine: str, task: str, cue: str, *, root: Path = DEFAULT_ROOT) -> Path:
    """Where a record cell lives: ``answers/<engine>/<task>/<cue>.jsonl.gz``."""
    return root / "answers" / engine / task / f"{cue}.jsonl.gz"


def read_record(path: Path) -> List[Dict]:
    """Every row in a record file, in file order. ``[]`` if the file does not exist -- a cell
    with no record yet is not an error, just empty."""
    if not path.exists():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    rows: List[Dict] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_record_by_id(path: Path) -> Dict[str, Dict]:
    """A record's rows keyed by item id, the shape scoring reads them in (see
    ``biased_decisions.tasks.bios``)."""
    return {row["id"]: row for row in read_record(path)}


def write_record(path: Path, rows: Iterable[Mapping], *, append: bool = False) -> None:
    """Write (or append to) a record file, validating each row carries every required field.

    Never called during milestone-1 replay -- every cell's record is already committed -- but
    this is what an engine's answer builder (``bd answer``, filled in by task 2) writes through.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "at" if append else "wt"
    with gzip.open(path, mode, encoding="utf-8") as handle:
        for row in rows:
            missing = [field for field in REQUIRED_FIELDS if field not in row]
            if missing:
                raise ValueError(f"record row {row.get('id')!r} is missing {missing}")
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


# Where each OLD Jev-Flywheel fixture answer file lands in this repo's (engine, task, cue)
# scheme. Keys are paths relative to the Jev-Flywheel repo root; see ``data/MANIFEST.md`` for
# the full copy log this mapping was built from.
OLD_TO_NEW: Dict[str, Tuple[str, str, str]] = {
    "fixtures/bios/answers.jsonl.gz": ("jev", "surgeon-physician", "gender-pronouns"),
    "fixtures/bios/answers-laya.jsonl.gz": ("laya-mlx", "surgeon-physician", "gender-pronouns"),
    "fixtures/bios/answers-race.jsonl.gz": ("jev", "surgeon-physician", "race-name"),
    "fixtures/bios/answers-race-laya.jsonl.gz": ("laya-mlx", "surgeon-physician", "race-name"),
    "fixtures/bios/answers-race2.jsonl.gz": ("jev", "surgeon-physician", "race-fullname"),
    "fixtures/bios/answers-race2-laya.jsonl.gz": (
        "laya-mlx", "surgeon-physician", "race-fullname"),
    "fixtures/bios/answers-age.jsonl.gz": ("jev", "surgeon-physician", "age-inserted"),
    "fixtures/bios/answers-age-laya.jsonl.gz": ("laya-mlx", "surgeon-physician", "age-inserted"),
    "fixtures/bios_pairs/nurse_physician/answers.jsonl.gz": (
        "jev", "nurse-physician", "gender-pronouns"),
    "fixtures/bios_pairs/nurse_physician/answers-laya.jsonl.gz": (
        "laya-mlx", "nurse-physician", "gender-pronouns"),
    "fixtures/bios_pairs/paralegal_attorney/answers.jsonl.gz": (
        "jev", "paralegal-attorney", "gender-pronouns"),
    "fixtures/bios_pairs/paralegal_attorney/answers-laya.jsonl.gz": (
        "laya-mlx", "paralegal-attorney", "gender-pronouns"),
    "fixtures/bios_pairs/teacher_professor/answers.jsonl.gz": (
        "jev", "teacher-professor", "gender-pronouns"),
    "fixtures/bios_pairs/teacher_professor/answers-laya.jsonl.gz": (
        "laya-mlx", "teacher-professor", "gender-pronouns"),
    # The upstream (non-port) Laya record, imported from import/laya-record/laya/.
    "laya-record/laya/surgeon-physician--gender-pronouns.jsonl.gz": (
        "laya", "surgeon-physician", "gender-pronouns"),
    "laya-record/laya/nurse-physician--gender-pronouns.jsonl.gz": (
        "laya", "nurse-physician", "gender-pronouns"),
    "laya-record/laya/paralegal-attorney--gender-pronouns.jsonl.gz": (
        "laya", "paralegal-attorney", "gender-pronouns"),
    "laya-record/laya/teacher-professor--gender-pronouns.jsonl.gz": (
        "laya", "teacher-professor", "gender-pronouns"),
}


def new_path_for_old(old_relpath: str, *, root: Path = DEFAULT_ROOT) -> Path:
    """Where an OLD Jev-Flywheel (or ``import/laya-record``) fixture file's answers land in this
    repo's ``answers/<engine>/<task>/<cue>.jsonl.gz`` scheme."""
    try:
        engine, task, cue = OLD_TO_NEW[old_relpath]
    except KeyError as error:
        raise KeyError(f"{old_relpath!r} has no mapping onto (engine, task, cue)") from error
    return record_path(engine, task, cue, root=root)
