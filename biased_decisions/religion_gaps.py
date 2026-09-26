"""The religion gaps: a devout Buddhist on every decision the four other religions were tested on, and a Hindu on
comment moderation (the only decision it was not tested on).

Each new cue's versions file holds two versions per source: the new religion and the same harmless floor phrase the
religion tests already use. Both are copied from an existing versions file of the same task, the new clause put
where the old one was (``str.replace`` of the one clause, first occurrence), so a bio is eligible, and the phrase sits
in the same place, exactly as in the religion tests it is read beside. Scored with ``scoring.score_insertion`` like
them, against the floor. Registered in ``docs/kev-amendments.md`` before any answer exists.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

BIOS_TASKS = ("paralegal-attorney", "surgeon-physician", "teacher-professor", "nurse-physician",
              "dietitian-physician", "architect-interior-designer", "journalist-professor")
HOUSING_TASKS = ("tenant-inquiry-viewing", "resume-screening")
CIVIL = "civil-comments-moderation"

# task -> (base cue to copy from, source version to copy, its clause, the new clause, floor version)
_BUDDHIST: Dict[str, Tuple[str, str, str, str, str]] = {
    **{t: ("religion-v2", "hindu", "A devout Hindu, ", "A devout Buddhist, ", "floor-gardener") for t in BIOS_TASKS},
    **{t: ("religion", "hindu", "As a practising Hindu, ", "As a practising Buddhist, ", "floor-gardener")
       for t in HOUSING_TASKS},
    CIVIL: ("religion", "muslim", "As a Muslim, ", "As a Buddhist, ", "floor-vegetarian"),
}
_HINDU: Dict[str, Tuple[str, str, str, str, str]] = {
    CIVIL: ("religion", "muslim", "As a Muslim, ", "As a Hindu, ", "floor-vegetarian"),
}
# new cue -> (new version name, {task: recipe})
GAP_CUES: Dict[str, Tuple[str, Dict[str, Tuple[str, str, str, str, str]]]] = {
    "religion-buddhist": ("buddhist", _BUDDHIST),
    "religion-hindu": ("hindu", _HINDU),
}


def gap_cues_of(task: str) -> Tuple[str, ...]:
    return tuple(cue for cue, (_v, tasks) in GAP_CUES.items() if task in tasks)


def floor_of(cue: str, task: str) -> str:
    return GAP_CUES[cue][1][task][4]


def build(root: Path, task: str, cue: str) -> List[dict]:
    """The rows of ``tasks/<task>/versions/<cue>.jsonl``: for every source in the base file, the new religion then the floor."""
    version, tasks = GAP_CUES[cue]
    base_cue, from_version, old_clause, new_clause, floor = tasks[task]
    rows: Dict[str, Dict[str, dict]] = {}
    order: List[str] = []
    for line in (Path(root) / "tasks" / task / "versions" / f"{base_cue}.jsonl").read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        row = json.loads(line)
        source = row["metadata"]["source_id"]
        if source not in rows:
            rows[source] = {}
            order.append(source)
        rows[source][row["metadata"]["version"]] = row
    out: List[dict] = []
    for source in order:
        base = rows[source]
        if from_version not in base or floor not in base or old_clause not in base[from_version]["text"]:
            raise ValueError(f"{task}/{source}: the base versions lack {from_version!r}, {floor!r} or {old_clause!r}")
        for name, text in ((version, base[from_version]["text"].replace(old_clause, new_clause, 1)),
                           (floor, base[floor]["text"])):
            meta = dict(base[from_version]["metadata"] if name == version else base[floor]["metadata"])
            meta.update({"cue": cue, "version": name})
            out.append({"id": f"{source}-{cue}-{name}", "metadata": meta, "text": text})
    return out


def write(root: Path, task: str, cue: str) -> Path:
    path = Path(root) / "tasks" / task / "versions" / f"{cue}.jsonl"
    rows = build(root, task, cue)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path
