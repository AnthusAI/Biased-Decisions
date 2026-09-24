"""Feature: the veteran-status, sexuality and gender-identity versions are built, not pasted.

Each versions file under ``tasks/<task>/versions/`` was built outside this repository and
imported; ``bd build`` must reproduce every one of them byte for byte from the task's own
``items.jsonl``, so anyone can regenerate them. The imported answers must cover every row of
their versions file, in the record schema every other record uses.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biased_decisions.build import CUES, build, write_versions
from biased_decisions.record import REQUIRED_FIELDS, read_record, record_path
from biased_decisions.tasks.bios import BIOS_TASKS, load_task

ROOT = Path(__file__).resolve().parents[1]
NEW_CUES = ("veteran-status", "sexuality", "gender-identity")
ROWS_PER_CUE = {  # eligible bios x three versions, from the imported build logs
    "surgeon-physician": 4113, "nurse-physician": 4101, "paralegal-attorney": 4155,
    "teacher-professor": 4206, "journalist-professor": 4173,
    "architect-interior-designer": 3213, "dietitian-physician": 4014,
}


def test_the_three_cues_are_registered_build_cues():
    for cue in NEW_CUES:
        assert cue in CUES


@pytest.mark.parametrize("cue", NEW_CUES)
@pytest.mark.parametrize("task_slug", BIOS_TASKS)
def test_bd_build_reproduces_the_imported_versions_file_byte_for_byte(task_slug, cue, tmp_path):
    task = load_task(task_slug)
    result = build(cue, task)
    assert len(result.rows) == ROWS_PER_CUE[task_slug]
    rebuilt = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result.rows)
    committed = task.versions_path(cue).read_text(encoding="utf-8")
    assert rebuilt == committed


def test_write_versions_writes_the_same_bytes_as_the_committed_file(tmp_path):
    task = load_task("nurse-physician")
    from dataclasses import replace
    scratch = replace(task, root=tmp_path)
    (tmp_path / "tasks" / "nurse-physician").mkdir(parents=True)
    path = write_versions(scratch, "sexuality", build("sexuality", task))
    assert path.read_bytes() == task.versions_path("sexuality").read_bytes()


@pytest.mark.parametrize("cue", NEW_CUES)
@pytest.mark.parametrize("task_slug", BIOS_TASKS)
def test_the_imported_answers_cover_every_version_row_in_the_record_schema(task_slug, cue):
    task = load_task(task_slug)
    ids = [item.id for item in task.load_versions(cue)]
    rows = read_record(record_path("laya", task_slug, cue))
    assert [row["id"] for row in rows] == ids or set(row["id"] for row in rows) == set(ids)
    assert len(rows) == len(ids)
    for row in rows[:50]:
        assert all(field in row for field in REQUIRED_FIELDS)
        assert row["model"] == "laya-upstream:0.3.7"
        answer = row["answers"]["Occupation"]
        assert answer["choice"] in task.options
        assert set(answer["probabilities"]) == set(task.options)


def test_every_gender_identity_bio_carries_the_as_written_text_unchanged():
    task = load_task("surgeon-physician")
    originals = {item.id: item.text for item in task.load_items()}
    for item in task.load_versions("gender-identity"):
        if item.metadata["version"] == "asis":
            assert item.text == originals[item.metadata["source_id"]]


def test_a_sexuality_clause_never_changes_the_bios_pronoun_gender():
    task = load_task("nurse-physician")
    for item in task.load_versions("sexuality"):
        her = item.metadata["gender"] == "female"
        wanted = ("Married to her " if her else "Married to his ")
        if item.metadata["version"] != "floor-married":
            assert item.text.count(wanted) == 1
