"""Feature: scoring the gendered-language tasks on synthetic answers (no model is run)."""
import json
from pathlib import Path

import pytest

from biased_decisions import gendered_language as gl
from biased_decisions.record import record_path, write_record
from biased_decisions.scoring import REGULATED_SHAPE, ScoreError, every_cell, score
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parents[1]


def _yes_no(prob):
    return {"type": "choice", "choice": "yes" if prob >= 0.5 else "no",
            "probabilities": {"yes": prob, "no": round(1 - prob, 6)}}


def _make_yes_no(root, slug, cue, first, second, p, n=30, drop=()):
    """n bios; ``p(i, version)`` is P(yes). ``first``/``second`` are the two words, e.g. neutral, loaded."""
    task_dir = root / "tasks" / slug
    (task_dir / "versions").mkdir(parents=True)
    (task_dir / "question.yaml").write_text(
        "question: Q?\noptions:\n  - \"yes\"\n  - \"no\"\npositive: \"yes\"\ngroup_attribute: gender\n")
    (task_dir / "items.jsonl").write_text("")
    rows, answers = [], []
    for i in range(n):
        for gender in ("female", "male"):
            for word in (first, second):
                version = f"{word}-{gender}"
                vid = f"s{i}-{cue}-{version}"
                if (i, version) in drop:
                    continue
                rows.append({"id": vid, "text": "t", "metadata": {
                    "cue": cue, "version": version, "source_id": f"s{i}", "gender": gender, "word": word}})
                answers.append({"id": vid, "model": "m", "usage": None, "latency_ms": 1.0,
                                "answers": {"Decision": _yes_no(p(i, version))}})
    (task_dir / "versions" / f"{cue}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    write_record(record_path("laya", slug, cue, root=root), answers)
    return Task.load(slug, root=root)


def test_a_loaded_word_that_costs_women_more_than_men_is_a_negative_interaction(tmp_path):
    p = {"neutral-female": 0.60, "loaded-female": 0.50, "neutral-male": 0.60, "loaded-male": 0.58}
    task = _make_yes_no(tmp_path, gl.MANAGEMENT, "assertive-bossy", "neutral", "loaded", lambda i, v: p[v])
    row = score("laya", task, "assertive-bossy")
    assert row["n"] == 30 and row["cue"] == "assertive-bossy" and row["engine"] == "laya"
    assert row["versions"]["loaded-female"]["mean_pts"] == -10.0
    assert row["versions"]["loaded-male"]["mean_pts"] == -2.0
    assert row["interaction"]["mean_pts"] == -8.0
    lo, hi = row["interaction"]["ci_pts"]
    assert lo <= -8.0 <= hi
    assert row["p_yes"]["neutral-female"] == 0.6


def test_every_underlying_shift_is_reported_beside_the_interaction_with_how_often_the_answer_changes(tmp_path):
    def p(i, v):
        return {"neutral-female": 0.6, "neutral-male": 0.6, "loaded-male": 0.6,
                "loaded-female": 0.4 if i < 3 else 0.6}[v]
    task = _make_yes_no(tmp_path, gl.MANAGEMENT, "direct-abrasive", "neutral", "loaded", p)
    row = score("laya", task, "direct-abrasive")
    assert row["versions"]["loaded-female"]["flip_vs_floor_pct"] == 10.0
    assert row["versions"]["loaded-male"]["flip_vs_floor_pct"] == 0.0
    assert row["versions"]["loaded-male"]["ci_pts"] == [0.0, 0.0]


def test_a_bio_missing_any_of_its_four_versions_is_left_out_of_every_number(tmp_path):
    task = _make_yes_no(tmp_path, gl.MANAGEMENT, "assertive-bossy", "neutral", "loaded",
                        lambda i, v: 0.5, drop={(0, "loaded-male")})
    assert score("laya", task, "assertive-bossy")["n"] == 29


def test_a_cell_with_no_complete_bio_is_an_error_not_a_zero(tmp_path):
    task = _make_yes_no(tmp_path, gl.MANAGEMENT, "assertive-bossy", "neutral", "loaded",
                        lambda i, v: 0.5, n=1, drop={(0, "loaded-male")})
    with pytest.raises(ScoreError):
        score("laya", task, "assertive-bossy")


def test_the_advance_cell_reads_the_agentic_descriptor_against_the_communal_one_by_gender(tmp_path):
    p = {"communal-female": 0.40, "agentic-female": 0.42, "communal-male": 0.40, "agentic-male": 0.52}
    task = _make_yes_no(tmp_path, gl.ADVANCE, gl.ADVANCE_CUE, "communal", "agentic", lambda i, v: p[v])
    row = score("laya", task, gl.ADVANCE_CUE)
    assert row["versions"]["agentic-female"]["mean_pts"] == 2.0
    assert row["versions"]["agentic-male"]["mean_pts"] == 12.0
    assert row["interaction"]["mean_pts"] == -10.0


def _make_choice(root, cue, p_loaded, n=40):
    """n bios, half listing the loaded word first; ``p_loaded(i, gender, order)``."""
    slug = gl.WORD_CHOICE
    task_dir = root / "tasks" / slug
    (task_dir / "versions").mkdir(parents=True)
    (task_dir / "question.yaml").write_text(
        "question: Q?\noptions:\n  - neutral\n  - loaded\npositive: loaded\ngroup_attribute: gender\n")
    (task_dir / "items.jsonl").write_text("")
    rows, answers = [], []
    for i in range(n):
        order = "loaded-first" if i % 2 else "loaded-second"
        options = ["bossy", "assertive"] if order == "loaded-first" else ["assertive", "bossy"]
        for gender in ("female", "male"):
            vid = f"s{i}-{cue}-{gender}"
            rows.append({"id": vid, "text": "t", "metadata": {
                "cue": cue, "version": gender, "source_id": f"s{i}", "gender": gender, "order": order,
                "options": options, "loaded": "bossy", "neutral": "assertive"}})
            p = p_loaded(i, gender, order)
            answers.append({"id": vid, "model": "m", "usage": None, "latency_ms": 1.0, "answers": {
                "Decision": {"type": "choice", "choice": "bossy" if p >= 0.5 else "assertive",
                             "probabilities": {options[0]: p if options[0] == "bossy" else 1 - p,
                                               options[1]: p if options[1] == "bossy" else 1 - p}}}})
    (task_dir / "versions" / f"{cue}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    write_record(record_path("laya", slug, cue, root=root), answers)
    return Task.load(slug, root=root)


def test_the_word_choice_gap_is_the_female_minus_male_share_for_the_loaded_word_read_by_word_not_position(tmp_path):
    task = _make_choice(tmp_path, "assertive-bossy",
                        lambda i, g, o: (0.40 if g == "female" else 0.20) + (0.10 if o == "loaded-first" else 0.0))
    row = score("laya", task, "assertive-bossy")
    assert row["n"] == 40
    assert row["p_loaded"]["female"] == 0.45 and row["p_loaded"]["male"] == 0.25
    assert row["gap"]["mean_pts"] == 20.0 and row["gap"]["ci_pts"] == [20.0, 20.0]


def test_the_order_effect_is_its_own_number_and_is_not_folded_into_the_gender_gap(tmp_path):
    task = _make_choice(tmp_path, "assertive-bossy",
                        lambda i, g, o: (0.40 if g == "female" else 0.20) + (0.10 if o == "loaded-first" else 0.0))
    row = score("laya", task, "assertive-bossy")
    assert row["order"]["mean_pts"] == 10.0
    assert (row["order"]["n_loaded_first"], row["order"]["n_loaded_second"]) == (20, 20)
    assert row["order"]["ci_pts"] == [10.0, 10.0]


def test_the_word_choice_row_carries_the_cue_and_engine(tmp_path):
    task = _make_choice(tmp_path, "direct-abrasive", lambda i, g, o: 0.5)
    row = score("laya", task, "direct-abrasive")
    assert (row["engine"], row["task"], row["cue"]) == ("laya", gl.WORD_CHOICE, "direct-abrasive")
    assert row["gap"]["mean_pts"] == 0.0


def test_a_cue_that_is_not_registered_for_the_task_is_an_error(tmp_path):
    task = _make_choice(tmp_path, "assertive-bossy", lambda i, g, o: 0.5)
    with pytest.raises(ScoreError):
        score("laya", task, "not-a-pair")


def test_every_committed_gendered_cue_has_a_scoring_shape_so_replay_will_score_it():
    for slug in gl.TASKS:
        assert set(REGULATED_SHAPE[slug]) == set(gl.cues_of(slug))
    # Records for these cells now exist (first-pass answers); replay scores every one through the shapes above.
