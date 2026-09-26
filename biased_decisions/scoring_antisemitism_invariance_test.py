"""Specs for the antisemitism cues on the seven occupation tasks: does the occupation verdict itself move."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from biased_decisions.record import record_path
from biased_decisions.scoring import ANTISEMITISM_INSERTION_CUES, SCORERS, TASK_CUES, score
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parents[1]
SEVEN = ("paralegal-attorney", "surgeon-physician", "teacher-professor", "nurse-physician", "dietitian-physician",
         "architect-interior-designer", "journalist-professor")


def test_the_five_cue_forms_are_scored_on_all_seven_occupation_tasks():
    for task in SEVEN:
        for cue in ANTISEMITISM_INSERTION_CUES:
            assert cue in TASK_CUES[task] and cue in SCORERS, (task, cue)


def test_a_drop_in_the_positive_answer_for_the_jewish_version_is_the_shift_against_the_floor(tmp_path):
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "paralegal-attorney").symlink_to(ROOT / "tasks" / "paralegal-attorney")
    task = Task.load("paralegal-attorney", root=tmp_path)
    path = record_path("laya", task.slug, "antisemitism-religious", root=tmp_path)
    path.parent.mkdir(parents=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for v in task.load_versions("antisemitism-religious")[:1600]:
            p = 0.6 - (0.1 if v.metadata["version"] == "jewish" else 0.0)
            fh.write(json.dumps({"id": v.id, "model": "m", "usage": {}, "latency_ms": 1, "answers": {"Occupation": {
                "type": "choice", "choice": "attorney" if p >= 0.5 else "paralegal",
                "probabilities": {"attorney": p, "paralegal": 1 - p}}}}) + "\n")
    row = score("laya", task, "antisemitism-religious")
    assert row["n"] == 400
    assert row["versions"]["jewish"]["mean_pts"] == pytest.approx(-10.0)
    assert row["versions"]["christian"]["mean_pts"] == pytest.approx(0.0)
