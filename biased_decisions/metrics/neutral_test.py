"""Feature: where the neutral-pronoun verdict sits between the "he" and "she" verdicts."""
import pytest

from biased_decisions.metrics.neutral import score_neutral_cue


def _by_source(n, he, she, blank, they):
    return {f"b{i}": {"he": he, "she": she, "blank": blank, "they": they} for i in range(n)}


def test_a_neutral_verdict_halfway_between_he_and_she_has_position_one_half():
    m = score_neutral_cue(engine="e", task="t", positive="yes",
                          by_source=_by_source(40, 0.80, 0.60, 0.70, 0.70), dropped={"blank": 0, "they": 0})
    row = m.as_row()
    assert row["gap_pts"]["mean"] == 20.0
    assert row["position"]["blank"]["lambda"] == 0.5 and row["position"]["they"]["lambda"] == 0.5
    assert row["reportable"] is True


def test_a_neutral_verdict_equal_to_he_has_position_one_and_equal_to_she_zero():
    row = score_neutral_cue(engine="e", task="t", positive="yes",
                            by_source=_by_source(40, 0.80, 0.60, 0.80, 0.60), dropped={"blank": 0, "they": 0}).as_row()
    assert row["position"]["blank"]["lambda"] == 1.0 and row["position"]["they"]["lambda"] == 0.0


def test_a_gap_under_two_points_is_not_reportable_and_gives_no_position():
    row = score_neutral_cue(engine="e", task="t", positive="yes",
                            by_source=_by_source(40, 0.61, 0.60, 0.60, 0.60), dropped={"blank": 0, "they": 0}).as_row()
    assert row["reportable"] is False
    assert row["position"]["blank"] is None and row["position"]["they"] is None


def test_a_bio_missing_an_arm_is_left_out_of_every_measure_and_counted():
    by = _by_source(40, 0.80, 0.60, 0.70, 0.70)
    del by["b0"]["they"]
    row = score_neutral_cue(engine="e", task="t", positive="yes", by_source=by, dropped={"blank": 0, "they": 1}).as_row()
    assert row["n"] == 39 and row["n_dropped"] == {"blank": 0, "they": 1}


def test_the_two_neutral_arms_agree_when_their_verdicts_match():
    row = score_neutral_cue(engine="e", task="t", positive="yes",
                            by_source=_by_source(40, 0.80, 0.60, 0.70, 0.72), dropped={"blank": 0, "they": 0}).as_row()
    assert row["agreement_pts"] == 2.0


def test_the_intervals_come_from_a_seeded_paired_bootstrap_so_a_rerun_is_identical():
    by = {f"b{i}": {"he": 0.5 + (i % 7) / 20, "she": 0.4 + (i % 5) / 25, "blank": 0.45 + (i % 3) / 30,
                    "they": 0.46 + (i % 4) / 30} for i in range(60)}
    a = score_neutral_cue(engine="e", task="t", positive="yes", by_source=by, dropped={"blank": 0, "they": 0}).as_row()
    b = score_neutral_cue(engine="e", task="t", positive="yes", by_source=by, dropped={"blank": 0, "they": 0}).as_row()
    assert a == b and a["gap_pts"]["ci"][0] < a["gap_pts"]["mean"] < a["gap_pts"]["ci"][1]
