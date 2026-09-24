"""Specs for the general trope scorer, on tiny synthetic axes (no record, no model)."""
from __future__ import annotations

import random

from biased_decisions.metrics import tropes
from biased_decisions.metrics.tropes import Axis, Question

AXIS = Axis("toy", ("a", "b", "c"), "floor")
YES = Question("q_yes", "Is it so?", True)
NO = Question("q_no", "Is it not so?", False)


def _data(n=40, a_bump=0.2):
    rng = random.Random(3)
    base = [rng.random() * 0.6 for _ in range(n)]
    v = {"floor": base, "a": [min(1.0, p + a_bump) for p in base], "b": list(base), "c": list(base)}
    return {"q_yes": v, "q_no": {k: [1.0 - p for p in vals] for k, vals in v.items()}}


def test_a_probability_is_flipped_to_trope_consistent_when_the_trope_predicts_no():
    assert tropes.p_trope_consistent(0.3, True) == 0.3
    assert tropes.p_trope_consistent(0.3, False) == 0.7


def test_a_question_whose_trope_answer_is_no_gives_the_same_shift_as_its_mirror_image():
    r = tropes.score_axis(AXIS, [YES, NO], _data(), n_resamples=50)
    assert r["q_yes"]["groups"]["a"]["shift"] == r["q_no"]["groups"]["a"]["shift"] > 0.1


def test_the_trope_score_is_the_groups_shift_minus_the_mean_shift_of_the_other_groups():
    r = tropes.score_axis(AXIS, [YES], _data(), n_resamples=50)["q_yes"]["groups"]
    assert abs(r["a"]["trope_score"] - (r["a"]["shift"] - (r["b"]["shift"] + r["c"]["shift"]) / 2)) < 2e-4
    assert r["a"]["trope_detected"] is True and r["b"]["trope_detected"] is False


def test_the_general_effect_is_the_mean_shift_of_all_groups():
    r = tropes.score_axis(AXIS, [YES], _data(), n_resamples=50)["q_yes"]
    g = r["groups"]
    assert abs(r["general_effect"]["mean_shift"] - (g["a"]["shift"] + g["b"]["shift"] + g["c"]["shift"]) / 3) < 2e-4


def test_the_flip_rate_counts_bios_whose_verdict_at_one_half_differs_from_the_floors():
    d = {"q_yes": {"floor": [0.4, 0.4, 0.6, 0.6], "a": [0.6, 0.4, 0.6, 0.4],
                   "b": [0.4] * 4, "c": [0.4] * 4}}
    r = tropes.score_axis(AXIS, [YES], d, n_resamples=10)
    assert r["q_yes"]["groups"]["a"]["flip_rate"] == 0.5


def test_the_same_seed_gives_the_same_rows_and_the_intervals_bracket_the_point_estimate():
    one = tropes.score_axis(AXIS, [YES, NO], _data(), n_resamples=100)
    two = tropes.score_axis(AXIS, [YES, NO], _data(), n_resamples=100)
    assert one == two
    g = one["q_yes"]["groups"]["a"]
    assert g["shift_ci_lo"] <= g["shift"] <= g["shift_ci_hi"]


def test_scoring_a_later_question_alone_with_skipped_draws_matches_scoring_it_in_the_stream():
    n, r = 30, 20
    d = _data(n)
    both = tropes.score_axis(AXIS, [YES, NO], d, n_resamples=r)
    alone = tropes.score_axis(AXIS, [NO], d, n_resamples=r,
                              skip_draws=tropes.burn_draws(1, n, n_resamples=r))
    assert alone["q_no"] == both["q_no"]
    assert tropes.burn_draws(2, n, n_resamples=r) == 2 * r * n


def test_the_as_written_baseline_reports_p_yes_and_the_trope_consistent_mean():
    b = tropes.as_written_baseline([YES, NO], {"q_yes": [0.2, 0.4], "q_no": [0.2, 0.4]})
    assert b["q_yes"]["p_yes_mean"] == 0.3 and b["q_yes"]["p_trope_consistent_mean"] == 0.3
    assert b["q_no"]["p_trope_consistent_mean"] == 0.7


def test_percentile_interpolates_linearly_between_sorted_values():
    assert tropes.percentile([0.0, 1.0, 2.0, 3.0], 0.5) == 1.5
