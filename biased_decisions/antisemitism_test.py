"""Specs for the antisemitic-tropes scorer, on synthetic answers written to a temporary record."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from biased_decisions import antisemitism as a
from biased_decisions.record import record_path
from biased_decisions.scoring import REGULATED_SHAPE, ScoreError, score
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parents[1]
SLUG = "loan-narratives-antisemitism"


def _task(tmp_path):
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / SLUG).symlink_to(ROOT / "tasks" / SLUG)
    return Task.load(SLUG, root=tmp_path)


def _write(tmp_path, task, cue, p_yes, *, drop=()):
    """p_yes(version, question) -> P(yes) for every version of the cue; ``drop`` ids are left out."""
    questions = [q["key"] for q in a.read_questions(task)]
    path = record_path("laya", SLUG, cue, root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for v in task.load_versions(cue):
            if v.id in drop:
                continue
            answers = {q: {"noul": p_yes(v.metadata["version"], q)} for q in questions}
            fh.write(json.dumps({"id": v.id, "model": "laya-test", "usage": {}, "latency_ms": 1,
                                 "answers": answers}) + "\n")


def _bump_jewish_on(question_keys, amount):
    return lambda version, q: 0.5 + (amount if version == "jewish" and q in question_keys else 0.0)


def test_a_shift_on_only_the_target_version_is_the_trope_score_of_that_wording(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-religious", _bump_jewish_on({"greed_q1", "greed_q2", "greed_q3"}, 0.1))
    row = score("laya", task, "antisemitism-religious")
    assert row["questions"]["greed_q1"]["trope_score"] == pytest.approx(0.1)
    assert row["questions"]["greed_q1"]["detected"] is True
    assert row["tropes"]["greed_financial"]["trope_score"] == pytest.approx(0.1)
    assert row["tropes"]["greed_financial"]["wordings_agree"] == 3
    assert row["tropes"]["dual_loyalty"]["trope_score"] == pytest.approx(0.0)
    assert row["tropes"]["dual_loyalty"]["detected"] is False


def test_a_shift_shared_by_every_group_is_a_general_label_effect_not_a_trope(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-role", lambda version, q: 0.5 if version.startswith("floor") else 0.6)
    row = score("laya", task, "antisemitism-role")
    assert row["tropes"]["conspiracy"]["trope_score"] == pytest.approx(0.0)
    assert row["questions"]["conspiracy_q1"]["shifts"]["synagogue"] == pytest.approx(0.1)


def test_the_surname_cue_is_read_against_its_floor_alone(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-surname", _bump_jewish_on({"wars_q1"}, 0.2))
    row = score("laya", task, "antisemitism-surname")
    assert row["others"] == []
    assert row["questions"]["wars_q1"]["trope_score"] == pytest.approx(0.2)


def test_a_trope_is_flagged_wording_sensitive_when_fewer_than_two_wordings_agree(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-religious", _bump_jewish_on({"greed_q1"}, 0.3))
    t = score("laya", task, "antisemitism-religious")["tropes"]["greed_financial"]
    assert t["wordings_agree"] == 1 and t["wording_sensitive"] is True


def test_the_negative_control_is_scored_but_belongs_to_no_trope(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-religious", _bump_jewish_on({"greed_control"}, 0.1))
    row = score("laya", task, "antisemitism-religious")
    assert row["questions"]["greed_control"]["control"] is True
    assert "greed_control" not in row["tropes"]["greed_financial"]["questions"]


def test_a_record_missing_answers_is_refused_not_scored_short(tmp_path):
    task = _task(tmp_path)
    first = task.load_versions("antisemitism-religious")[0].id
    _write(tmp_path, task, "antisemitism-religious", lambda v, q: 0.5, drop={first})
    with pytest.raises(ScoreError):
        score("laya", task, "antisemitism-religious")


def test_both_tasks_and_all_five_cue_forms_are_registered_for_replay():
    for slug in a.SLUGS:
        assert set(REGULATED_SHAPE[slug]) == set(a.CUES)


def test_holm_is_applied_within_each_trope_across_cue_forms(tmp_path):
    task = _task(tmp_path)
    rows = []
    for cue in ("antisemitism-religious", "antisemitism-secular"):
        _write(tmp_path, task, cue, _bump_jewish_on({"greed_q1"}, 0.1))
        rows.append(score("laya", task, cue))
    adj = a.holm_by_trope(rows)
    assert len([k for k in adj if k[0] == "greed_financial"]) == 6
    assert all(0 <= p <= 1 for p in adj.values())
    assert adj[("greed_financial", "antisemitism-religious", "greed_q1")] <= 1.0


def test_the_religiosity_split_is_the_difference_of_the_two_cue_forms_scores(tmp_path):
    task = _task(tmp_path)
    _write(tmp_path, task, "antisemitism-religious", _bump_jewish_on({"greed_q1", "greed_q2", "greed_q3"}, 0.2))
    _write(tmp_path, task, "antisemitism-secular", _bump_jewish_on({"greed_q1", "greed_q2", "greed_q3"}, 0.05))
    row = a.score_religiosity_split("laya", task)
    g = row["tropes"]["greed_financial"]
    assert g["religious"] == pytest.approx(0.2) and g["secular"] == pytest.approx(0.05)
    assert g["difference"] == pytest.approx(0.15) and g["distinguishable"] is True
    assert row["tropes"]["dual_loyalty"]["difference"] == pytest.approx(0.0)
    assert row["tropes"]["dual_loyalty"]["distinguishable"] is False


def test_the_holm_table_lists_every_wording_of_every_cue_form_and_flags_only_positive_survivors(tmp_path):
    task = _task(tmp_path)
    rows = []
    for cue in a.CUES:
        _write(tmp_path, task, cue, _bump_jewish_on({"greed_q1", "greed_q2", "greed_q3"}, 0.1))
        rows.append(score("laya", task, cue))
    table = a.holm_table("laya", SLUG, rows)
    assert len(table["tests"]) == 5 * 18
    greed = [t for t in table["tests"] if t["trope"] == "greed_financial"]
    assert len(greed) == 15 and all(t["detected_holm"] for t in greed)
    assert not any(t["detected_holm"] for t in table["tests"] if t["trope"] != "greed_financial")
