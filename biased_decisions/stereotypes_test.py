"""Specs for the stereotypes task: the build reproduces the imported files byte for byte, the
answer record has the right shape, and the replayed rows reproduce the staged numbers."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biased_decisions import stereotypes
from biased_decisions.build import build, build_stereotype_items
from biased_decisions.record import REQUIRED_FIELDS, read_record
from biased_decisions.scoring import score
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parents[1]
TASK = Task.load("stereotypes", root=ROOT)


def _lines(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def test_the_pool_build_reproduces_the_imported_items_file_byte_for_byte():
    result = build_stereotype_items(TASK)
    assert _lines(result.rows) == (ROOT / "tasks/stereotypes/items.jsonl").read_text(encoding="utf-8")
    assert len(result.rows) == 2000


@pytest.mark.parametrize("axis,n_versions", [("religion", 6), ("nationality", 8)])
def test_an_axis_versions_build_reproduces_the_imported_file_byte_for_byte(axis, n_versions):
    result = build(axis, TASK)
    assert _lines(result.rows) == (ROOT / f"tasks/stereotypes/versions/{axis}.jsonl").read_text(encoding="utf-8")
    assert len(result.rows) == 2000 * n_versions


def test_every_pool_bio_is_unique_and_prefixed_with_its_source_task():
    ids = [i.id for i in TASK.load_items()]
    assert len(set(ids)) == 2000
    assert all(i.startswith(stereotypes.SOURCE_TASKS) for i in ids)


def test_a_version_differs_from_its_bio_only_by_the_inserted_clause():
    item = TASK.load_items()[0]
    row = next(v for v in TASK.load_versions("religion") if v.id.endswith("religion-muslim"))
    assert "A devout Muslim, " in row.text and row.metadata["source_id"] == item.id


def test_each_axis_ends_in_a_floor_version_and_the_questions_carry_their_trope_answer():
    assert stereotypes.RELIGION[-1][0] == stereotypes.AXES["religion"].floor
    assert stereotypes.NATIONALITY[-1][0] == stereotypes.AXES["nationality"].floor
    q = {x.key: x.trope_consistent_answer for x in stereotypes.read_questions(TASK)}
    assert list(q) == ["greed", "violence", "arrogance", "worldliness", "diligence", "honesty"]
    assert q["worldliness"] is False and q["greed"] is True


@pytest.mark.parametrize("name,n", [("as-written", 2000), ("religion", 12000), ("nationality", 16000)])
def test_every_imported_answer_row_has_the_record_schema_and_six_answers_from_one_model(name, n):
    rows = read_record(ROOT / f"answers/laya/stereotypes/{name}.jsonl.gz")
    assert len(rows) == n
    assert all(all(f in r for f in REQUIRED_FIELDS) for r in rows)
    assert {r["model"] for r in rows} == {"laya-upstream:0.3.7"}
    assert all(set(r["answers"]) == {"greed", "violence", "arrogance", "worldliness", "diligence",
                                     "honesty"} for r in rows)
    assert all(0.0 <= a["noul"] <= 1.0 for r in rows for a in r["answers"].values())


def test_every_version_row_has_exactly_one_answer_and_the_as_written_pool_is_covered():
    for axis in ("religion", "nationality"):
        ids = {v.id for v in TASK.load_versions(axis)}
        assert ids == {r["id"] for r in read_record(ROOT / f"answers/laya/stereotypes/{axis}.jsonl.gz")}
    assert {i.id for i in TASK.load_items()} == {
        r["id"] for r in read_record(ROOT / "answers/laya/stereotypes/as-written.jsonl.gz")}


def _staged():
    rows = [json.loads(l) for l in (ROOT / "studies/batch2/stereotypes-laya.jsonl").read_text().splitlines()]
    return ({r["question"]: r for r in rows if r["record"] == "as_written_baseline"},
            [r for r in rows if r["record"] == "shift"],
            {(r["axis"], r["question"]): r for r in rows if r["record"] == "general_effect"})


@pytest.mark.parametrize("axis", ["religion", "nationality"])
def test_the_replayed_row_reproduces_every_number_in_the_staged_batch2_results(axis):
    baseline, shifts, general = _staged()
    row = score("laya", TASK, axis)
    assert row["model"] == "laya-upstream:0.3.7" and row["n"] == 2000
    for q, expected in baseline.items():
        got = row["as_written"][q]
        assert got["p_yes_mean"] == expected["p_yes_mean"]
        assert got["p_trope_consistent_mean"] == expected["p_trope_consistent_mean"]
    count = 0
    for s in shifts:
        if s["axis"] != axis:
            continue
        got = row["questions"][s["question"]]["groups"][s["group"]]
        assert row["questions"][s["question"]]["floor_mean"] == s["floor_mean"]
        for field in ("group_mean", "shift", "shift_ci_lo", "shift_ci_hi", "flip_rate", "trope_score",
                      "trope_score_ci_lo", "trope_score_ci_hi", "trope_detected"):
            assert got[field] == s[field], (axis, s["question"], s["group"], field)
        count += 1
    assert count == 6 * len(stereotypes.AXES[axis].groups)
    for (a, q), g in general.items():
        if a == axis:
            got = row["questions"][q]["general_effect"]
            assert (got["mean_shift"], got["ci_lo"], got["ci_hi"]) == (g["mean_shift"], g["ci_lo"], g["ci_hi"])
