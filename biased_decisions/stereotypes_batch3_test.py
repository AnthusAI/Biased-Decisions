"""Specs for the stereotypes-batch3 task: the pool is batch 2's, each axis rebuilds byte for byte,
the questions are scoped to their axes with matched negative controls, and every axis loads and
scores on synthetic answers through the one generic trope scorer."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from biased_decisions import stereotypes, stereotypes_batch3 as sb
from biased_decisions.build import build, build_stereotype_batch3_items
from biased_decisions.record import record_path, write_record
from biased_decisions.scoring import REGULATED_SHAPE, ScoreError, score
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parents[1]
TASK = Task.load(sb.SLUG, root=ROOT)
ITEMS = [{"id": i.id, "text": i.text, "metadata": i.metadata} for i in TASK.load_items()]


def _lines(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def test_the_pool_is_batch_twos_2000_bios_byte_for_byte():
    assert _lines(build_stereotype_batch3_items(TASK).rows) == (ROOT / "tasks/stereotypes-batch3/items.jsonl").read_text()
    assert (ROOT / "tasks/stereotypes/items.jsonl").read_bytes() == (ROOT / "tasks/stereotypes-batch3/items.jsonl").read_bytes()


@pytest.mark.parametrize("axis", list(sb.CLAUSES))
def test_an_axis_versions_build_reproduces_the_committed_file_byte_for_byte(axis):
    result = build(axis, TASK)
    assert _lines(result.rows) == (ROOT / f"tasks/stereotypes-batch3/versions/{axis}.jsonl").read_text(encoding="utf-8")
    assert len(result.rows) == 2000 * len(sb.CLAUSES[axis])


def test_the_nationality_axis_keeps_batch_twos_seven_and_the_floor_and_adds_six():
    batch2 = [v for v, _ in stereotypes.NATIONALITY]
    now = [v for v, _ in sb.CLAUSES["nationality-x"]]
    assert now[:7] + [now[-1]] == batch2[:7] + [batch2[-1]]
    assert now[7:-1] == ["israeli", "palestinian", "russian", "ukrainian", "korean", "japanese"]
    assert dict(stereotypes.NATIONALITY)["floor-cyclist"] == dict(sb.CLAUSES["nationality-x"])["floor-cyclist"]


@pytest.mark.parametrize("axis", list(sb.CLAUSES))
def test_each_axis_ends_in_its_floor_and_its_groups_exclude_the_floor(axis):
    spec = sb.AXES[axis]
    assert sb.CLAUSES[axis][-1][0] == spec.floor
    assert spec.floor not in spec.groups
    assert list(spec.groups) == [v for v, _ in sb.CLAUSES[axis][:-1]]
    assert len(spec.groups) >= 4


def test_a_clause_that_names_a_gender_is_written_for_the_bios_own_gender():
    for axis in ("orientation", "family", "race"):
        for _, clause in sb.CLAUSES[axis]:
            if isinstance(clause, dict):
                assert set(clause) == {"female", "male"}
    rows = build("family", TASK).rows
    female = next(r for r in rows if r["id"].endswith("family-single-parent") and r["metadata"]["gender"] == "female")
    male = next(r for r in rows if r["id"].endswith("family-single-parent") and r["metadata"]["gender"] == "male")
    assert "A single mother, she" in female["text"] and "A single father, he" in male["text"]
    assert not any(r["id"].endswith("family-pregnant") and r["metadata"]["gender"] == "male"
                   and "Currently pregnant" in r["text"] for r in rows)


def test_a_version_differs_from_its_bio_only_by_the_inserted_clause():
    item = ITEMS[0]
    row = next(v for v in build("china", TASK).rows if v["id"] == f"{item['id']}-china-henan")
    assert "A native of Henan province, " in row["text"] and "A native of Henan province" not in item["text"]
    assert row["metadata"]["source_id"] == item["id"]


def _yaml():
    return yaml.safe_load((ROOT / "tasks/stereotypes-batch3/question.yaml").read_text())["questions"]


def test_every_axis_is_scored_on_its_own_stereotype_questions_and_both_controls():
    doc = _yaml()
    for axis in sb.AXES:
        keys = [q.key for q in sb.read_questions(TASK, axis)]
        assert set(sb.CONTROLS) <= set(keys)
        assert len(keys) - 2 >= 4, axis
        assert all(axis in doc[k]["axes"] for k in keys)


def test_the_controls_are_negative_non_stereotype_traits_with_the_same_yes_shape():
    doc = _yaml()
    for key in sb.CONTROLS:
        assert doc[key]["trope_consistent_answer"] is True
    for key, spec in doc.items():
        assert spec["question"].endswith("?") and "person" in spec["question"]
    stereotype_text = " ".join(spec["question"] for k, spec in doc.items() if k not in sb.CONTROLS)
    assert "birthday" not in stereotype_text and "email" not in stereotype_text


def test_every_prediction_names_a_question_scored_on_its_axis_and_a_group_of_that_axis():
    for axis, spec in sb.AXES.items():
        scored = {q.key for q in sb.read_questions(TASK, axis)}
        for question, groups in spec.predictions.items():
            assert question in scored and question not in sb.CONTROLS
            assert set(groups) <= set(spec.groups)


def test_the_task_definition_loads_for_the_collector_as_a_multi_question_task():
    from biased_decisions import collector
    plan = collector.collect(ROOT, "spec-probe", sb.SLUG, "china", dry_run=True)   # an engine with no record
    assert plan["total"] == 10000


def test_the_axes_are_registered_for_scoring_and_replay():
    assert set(REGULATED_SHAPE[sb.SLUG]) == set(sb.AXES)
    for axis, spec in sb.AXES.items():
        assert REGULATED_SHAPE[sb.SLUG][axis] == (spec.floor, spec.groups)


def test_holm_adjusts_the_smallest_p_by_the_number_of_tests_and_stays_monotone():
    adjusted = sb.holm_adjust({"a": 0.01, "b": 0.02, "c": 0.04})
    assert adjusted == {"a": 0.03, "b": 0.04, "c": 0.04}
    assert sb.holm_adjust({"a": 0.5, "b": 0.9}) == {"a": 1.0, "b": 1.0}


def _synthetic_root(tmp_path: Path, axis: str, n: int = 40) -> Task:
    """A copy of the real question file with 40 synthetic bios answered so that the first group
    of the axis moves toward the stereotype on the first stereotype question only."""
    task_dir = tmp_path / "tasks" / sb.SLUG
    (task_dir / "versions").mkdir(parents=True)
    shutil.copy(ROOT / "tasks/stereotypes-batch3/question.yaml", task_dir / "question.yaml")
    items = [{"id": f"b{i}", "text": "Dr. Ada is a clinician. She treats patients.",
              "metadata": {"gender": "female" if i % 2 else "male", "occupation": "x", "source_task": "t"}}
             for i in range(n)]
    (task_dir / "items.jsonl").write_text(_lines(items))
    rows = sb.build_versions(items, axis)
    (task_dir / "versions" / f"{axis}.jsonl").write_text(_lines(rows))
    questions = sb.read_questions(Task.load(sb.SLUG, root=tmp_path), axis)
    target = sb.AXES[axis].groups[0]
    answers = []
    for r in rows:
        answer = {}
        for j, q in enumerate(questions):
            p = 0.30 + 0.01 * (int(r["metadata"]["source_id"][1:]) % 5)
            if q is questions[0] and r["metadata"]["version"] == target:
                p += 0.30 if q.trope_consistent_answer else -0.30
            answer[q.key] = {"type": "noul", "noul": p}
        # a full call answers every question in the file, so add the others too
        for key in _yaml():
            answer.setdefault(key, {"type": "noul", "noul": 0.5})
        answers.append({"id": r["id"], "model": "synthetic", "usage": None, "latency_ms": 1.0,
                        "answers": answer})
    write_record(record_path("laya", sb.SLUG, axis, root=tmp_path), answers)
    return Task.load(sb.SLUG, root=tmp_path)


@pytest.mark.parametrize("axis", list(sb.AXES))
def test_an_axis_loads_and_scores_on_synthetic_answers_and_finds_the_planted_shift(axis, tmp_path):
    task = _synthetic_root(tmp_path, axis)
    row = score("laya", task, axis)
    spec = sb.AXES[axis]
    first = sb.read_questions(task, axis)[0]
    assert row["n"] == 40 and row["floor"] == spec.floor and row["groups"] == list(spec.groups)
    assert set(row["questions"]) == {q.key for q in sb.read_questions(task, axis)}
    cell = row["questions"][first.key]["groups"][spec.groups[0]]
    assert cell["shift"] == pytest.approx(0.30, abs=1e-3)
    assert cell["trope_detected"] is True and cell["trope_detected_holm"] is True
    other = row["questions"][first.key]["groups"][spec.groups[1]]
    assert other["trope_detected"] is False and other["trope_score"] < 0
    assert set(sb.CONTROLS) <= set(row["questions"])
    assert "trope_p_holm" not in row["questions"][sb.CONTROLS[0]]["groups"][spec.groups[0]]


def test_scoring_a_missing_record_is_a_score_error_not_a_crash(tmp_path):
    task = _synthetic_root(tmp_path, "china")
    record_path("laya", sb.SLUG, "china", root=tmp_path).unlink()
    with pytest.raises((ScoreError, FileNotFoundError)):
        score("laya", task, "china")
    with pytest.raises(ScoreError):
        score("laya", task, "no-such-axis")
