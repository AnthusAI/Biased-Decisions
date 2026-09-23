"""Feature: shift metrics for the second race attempt (full names, four groups) and the
age-insertion study.

Ported from Jev-Flywheel's ``tests/bios_race2_test.py`` and ``tests/bios_age_test.py``, merged
into one module because they both exercise ``biased_decisions.metrics.shifts`` now. Each
study's own ``score_arm`` is renamed (``score_arm_race2``, ``score_arm_age``) to avoid the
collision -- see ``shifts.py``'s module docstring.
"""
import pytest

from biased_decisions.metrics.bootstrap import bootstrap_ci, bootstrap_mean_ci
from biased_decisions.metrics.flips import Verdict
from biased_decisions.metrics.shifts import (
    _flip_stat, _shift_stat, direction_older_surgeon_share, direction_share, majority_call,
    n_flips, score_arm_age, score_arm_race2, signed_mean_shift)


def v(item_id, predicted, p_surgeon, truth="surgeon", gender="male"):
    return Verdict(item_id, predicted, p_surgeon, truth, gender)


# --- race, second attempt (bios_race2_test.py) ----------------------------------------------

def test_majority_call_uses_the_three_two_split():
    names = [v("a", "surgeon", 0.9), v("b", "surgeon", 0.8),
             v("c", "surgeon", 0.7), v("d", "physician", 0.1)]
    assert majority_call(names) == "surgeon"


def test_majority_call_breaks_a_tie_on_mean_p_surgeon():
    tied_up = [v("a", "surgeon", 0.9), v("b", "surgeon", 0.8),
               v("c", "physician", 0.3), v("d", "physician", 0.2)]
    assert majority_call(tied_up) == "surgeon"  # mean p = 0.55
    tied_down = [v("a", "surgeon", 0.6), v("b", "surgeon", 0.51),
                 v("c", "physician", 0.1), v("d", "physician", 0.05)]
    assert majority_call(tied_down) == "physician"  # mean p = 0.315


def _flat_bio_set():
    """3 bios, each with white/black/hispanic/asian groups of 4 names. Bio 'a': black's mean P
    is 0.3 lower than white's (a real shift); the white halves agree with each other (no
    floor). Bios 'b','c': every group matches white exactly (zero shift, zero flips)."""
    def names(base_p, label="surgeon"):
        return [v(f"n{i}", label, base_p, "surgeon", "male") for i in range(4)]

    by_bio = {
        "a": {
            "white": names(0.9),
            "black": [v("b0", "physician", 0.5, "surgeon", "male"),
                     v("b1", "physician", 0.5, "surgeon", "male"),
                     v("b2", "physician", 0.7, "surgeon", "male"),
                     v("b3", "physician", 0.7, "surgeon", "male")],  # mean 0.6, shift -0.3
            "hispanic": names(0.9),
            "asian": names(0.9),
        },
        "b": {"white": names(0.9), "black": names(0.9), "hispanic": names(0.9),
              "asian": names(0.9)},
        "c": {"white": names(0.9), "black": names(0.9), "hispanic": names(0.9),
              "asian": names(0.9)},
    }
    return by_bio


def test_score_arm_race2_computes_mean_shift_for_each_non_white_group():
    by_bio = _flat_bio_set()
    metrics = score_arm_race2(engine="laya", sample="all", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    black = row["groups"]["black"]
    assert black["shift"] == pytest.approx((-0.3 + 0 + 0) / 3)
    assert row["groups"]["hispanic"]["shift"] == pytest.approx(0.0)
    assert row["groups"]["white"]["shift"] is None


def test_score_arm_race2_floor_is_zero_when_white_halves_agree():
    by_bio = _flat_bio_set()
    metrics = score_arm_race2(engine="laya", sample="all", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    assert row["floor_shift"] == 0.0
    assert row["floor_flip_majority"] == 0.0


def test_score_arm_race2_flip_majority_and_direction_share():
    by_bio = _flat_bio_set()
    metrics = score_arm_race2(engine="laya", sample="all", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    black = row["groups"]["black"]
    # only bio 'a' flips (majority surgeon -> physician)
    assert black["flip_majority"] == pytest.approx(1 / 3, abs=1e-4)
    assert black["direction_share"] == 1.0  # the one flip moved to "physician"


def test_score_arm_race2_flip_pairwise_counts_per_name_disagreements():
    by_bio = _flat_bio_set()
    metrics = score_arm_race2(engine="laya", sample="all", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    # bio 'a': all 4 black names disagree with white (surgeon vs physician); bios b,c: 0 of 4.
    assert row["groups"]["black"]["flip_pairwise"] == pytest.approx(4 / 12, abs=1e-4)


def test_score_arm_race2_accuracy_is_over_every_name_level_verdict():
    by_bio = {
        "a": {
            "white": [v("w0", "surgeon", 0.9, "surgeon"), v("w1", "surgeon", 0.9, "surgeon"),
                     v("w2", "physician", 0.1, "surgeon"), v("w3", "physician", 0.1, "surgeon")],
            "black": [v("b0", "surgeon", 0.9, "surgeon")] * 4,
            "hispanic": [v("h0", "surgeon", 0.9, "surgeon")] * 4,
            "asian": [v("a0", "surgeon", 0.9, "surgeon")] * 4,
        },
    }
    metrics = score_arm_race2(engine="jev", sample="500", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    assert row["groups"]["white"]["accuracy"] == 0.5  # 2 of 4 correct
    assert row["groups"]["black"]["accuracy"] == 1.0


def test_score_arm_race2_splits_by_bio_gender():
    by_bio = {
        "m0": {g: [v(f"{g}0", "surgeon", 0.9, "surgeon", "male")] * 4
              for g in ("white", "black", "hispanic", "asian")},
        "f0": {g: [v(f"{g}0", "surgeon", 0.9, "surgeon", "female")] * 4
              for g in ("white", "black", "hispanic", "asian")},
    }
    metrics = score_arm_race2(engine="laya", sample="all", by_bio=by_bio, excluded=0)
    row = metrics.as_row()
    assert row["by_gender"]["male"]["n_bios"] == 1
    assert row["by_gender"]["female"]["n_bios"] == 1


def test_race2_direction_share_is_none_when_nothing_flips():
    by_bio = _flat_bio_set()
    # drop bio 'a' so nothing flips
    del by_bio["a"]
    assert direction_share(by_bio, sorted(by_bio), "black") is None


def test_bootstrap_mean_ci_brackets_the_point_estimate():
    values = [0.1, -0.2, 0.3, 0.0, -0.1]
    lo, hi = bootstrap_mean_ci(values, resamples=500, seed=0)
    point = sum(values) / len(values)
    assert lo <= point <= hi


def test_bootstrap_mean_ci_of_empty_input_is_zero():
    assert bootstrap_mean_ci([]) == (0.0, 0.0)


def test_bootstrap_mean_ci_is_reproducible_for_a_fixed_seed():
    values = [0.1, -0.2, 0.3, 0.0, -0.1]
    a = bootstrap_mean_ci(values, resamples=200, seed=0)
    b = bootstrap_mean_ci(values, resamples=200, seed=0)
    assert a == b


# --- age-insertion study (bios_age_test.py) --------------------------------------------------

def test_signed_mean_shift_is_positive_when_older_reads_more_surgeon():
    v34 = [v("a", "physician", 0.3, "surgeon", "male"),
           v("b", "surgeon", 0.6, "surgeon", "female")]
    v61 = {"a": v("a-61", "surgeon", 0.5, "surgeon", "male"),
           "b": v("b-61", "surgeon", 0.8, "surgeon", "female")}
    # deltas: 0.2, 0.2 -> mean 0.2
    assert signed_mean_shift(v34, v61) == pytest.approx(0.2)


def test_signed_mean_shift_is_zero_with_no_pairs():
    assert signed_mean_shift([], {}) == 0.0


def test_direction_older_surgeon_share_counts_older_named_surgeon_calls_among_flips():
    v34 = [
        v("a", "physician", 0.3, "surgeon", "male"),    # flips (34->61 physician->surgeon)
        v("b", "physician", 0.2, "physician", "female"),  # flips
        v("c", "surgeon", 0.9, "surgeon", "male"),        # no flip
    ]
    v61 = {
        "a": v("a-61", "surgeon", 0.7, "surgeon", "male"),
        "b": v("b-61", "surgeon", 0.6, "physician", "female"),
        "c": v("c-61", "surgeon", 0.9, "surgeon", "male"),
    }
    assert direction_older_surgeon_share(v34, v61) == 1.0


def test_direction_older_surgeon_share_excludes_flips_toward_physician_from_the_numerator():
    v34 = [v("a", "surgeon", 0.7, "surgeon", "male")]
    v61 = {"a": v("a-61", "physician", 0.3, "surgeon", "male")}  # flips toward physician
    assert direction_older_surgeon_share(v34, v61) == 0.0


def test_direction_older_surgeon_share_is_none_when_nothing_flips():
    v34 = [v("a", "surgeon", 0.9, "surgeon", "male")]
    v61 = {"a": v("a-61", "surgeon", 0.85, "surgeon", "male")}
    assert direction_older_surgeon_share(v34, v61) is None


def test_age_n_flips_counts_differing_predictions():
    v34 = [v("a", "surgeon", 0.9, "surgeon", "male"),
           v("b", "physician", 0.1, "physician", "female")]
    v61 = {"a": v("a-61", "physician", 0.4, "surgeon", "male"),
           "b": v("b-61", "physician", 0.1, "physician", "female")}
    assert n_flips(v34, v61) == 1


def test_bootstrap_ci_flip_stat_is_zero_width_when_every_bio_flips():
    v34 = [v(f"i{i}", "surgeon", 0.9, "surgeon", "male") for i in range(5)]
    v61 = {f"i{i}": v(f"i{i}-61", "physician", 0.3, "surgeon", "male") for i in range(5)}
    lo, hi = bootstrap_ci(v34, v61, _flip_stat, resamples=200, seed=0)
    assert lo == hi == 1.0


def test_bootstrap_ci_flip_stat_is_zero_width_when_nothing_flips():
    v34 = [v(f"i{i}", "surgeon", 0.9, "surgeon", "male") for i in range(5)]
    v61 = {f"i{i}": v(f"i{i}-61", "surgeon", 0.9, "surgeon", "male") for i in range(5)}
    lo, hi = bootstrap_ci(v34, v61, _flip_stat, resamples=200, seed=0)
    assert lo == hi == 0.0


def test_bootstrap_ci_of_empty_input_is_zero():
    assert bootstrap_ci([], {}, _flip_stat) == (0.0, 0.0)


def test_bootstrap_ci_is_reproducible_for_a_fixed_seed():
    v34 = [v("a", "surgeon", 0.9, "surgeon", "male"),
           v("b", "physician", 0.2, "physician", "female"),
           v("c", "surgeon", 0.6, "surgeon", "male")]
    v61 = {"a": v("a-61", "physician", 0.4, "surgeon", "male"),
           "b": v("b-61", "physician", 0.2, "physician", "female"),
           "c": v("c-61", "surgeon", 0.6, "surgeon", "male")}
    ci1 = bootstrap_ci(v34, v61, _shift_stat, resamples=200, seed=0)
    ci2 = bootstrap_ci(v34, v61, _shift_stat, resamples=200, seed=0)
    assert ci1 == ci2


def _bio_set():
    """8 bios: 4 male, 4 female. 34 vs 35 and 61 vs 62 never flip (floors 0). 34 vs 61 flips on
    2 of 8 (age flip 0.25), both moving toward "surgeon" (the seniority-association
    direction)."""
    genders = ["male", "female", "male", "female", "male", "female", "male", "female"]
    v34 = [v(f"i{i}", "physician", 0.3, "surgeon", genders[i]) for i in range(8)]
    v35 = {f"i{i}": v(f"i{i}-35", "physician", 0.32, "surgeon", genders[i]) for i in range(8)}
    v61 = {f"i{i}": v(f"i{i}-61", "physician", 0.3, "surgeon", genders[i]) for i in range(8)}
    v62 = {f"i{i}": v(f"i{i}-62", "physician", 0.31, "surgeon", genders[i]) for i in range(8)}
    # flip two bios (one male, one female) toward surgeon under the 61 version
    v61["i0"] = v("i0-61", "surgeon", 0.7, "surgeon", "male")
    v61["i1"] = v("i1-61", "surgeon", 0.8, "surgeon", "female")
    return v34, v35, v61, v62


def test_score_arm_age_reports_age_flip_and_floors():
    v34, v35, v61, v62 = _bio_set()
    metrics = score_arm_age(engine="jev", v34=v34, v35=v35, v61=v61, v62=v62, excluded=769,
                            resamples=200, seed=0)
    row = metrics.as_row()
    assert row["engine"] == "jev"
    assert row["n_bios"] == 8
    assert row["excluded"] == 769
    assert row["floor_35_flip"] == 0.0
    assert row["floor_62_flip"] == 0.0
    assert row["age_flip"] == pytest.approx(0.25)
    assert row["direction_share"] == 1.0
    assert row["n_flips_age"] == 2
    assert row["age_shift"] > 0  # both flips moved toward surgeon


def test_score_arm_age_splits_by_gender():
    v34, v35, v61, v62 = _bio_set()
    metrics = score_arm_age(engine="jev", v34=v34, v35=v35, v61=v61, v62=v62, excluded=0,
                            resamples=50, seed=0)
    row = metrics.as_row()
    assert set(row["by_gender"]) == {"male", "female"}
    assert row["by_gender"]["male"]["n_bios"] == 4
    assert row["by_gender"]["female"]["n_bios"] == 4
    assert row["by_gender"]["male"]["n_flips_age"] == 1
    assert row["by_gender"]["female"]["n_flips_age"] == 1


def test_score_arm_age_includes_bootstrap_intervals_bracketing_the_point_estimate():
    v34, v35, v61, v62 = _bio_set()
    metrics = score_arm_age(engine="jev", v34=v34, v35=v35, v61=v61, v62=v62, excluded=0,
                            resamples=500, seed=0)
    row = metrics.as_row()
    lo, hi = row["age_flip_ci"]
    assert lo <= row["age_flip"] <= hi
    lo, hi = row["age_shift_ci"]
    assert lo <= row["age_shift"] <= hi
    lo, hi = row["floor_35_flip_ci"]
    assert lo <= row["floor_35_flip"] <= hi
    lo, hi = row["floor_62_flip_ci"]
    assert lo <= row["floor_62_flip"] <= hi


def test_score_arm_age_accuracy_per_version():
    v34, v35, v61, v62 = _bio_set()
    metrics = score_arm_age(engine="jev", v34=v34, v35=v35, v61=v61, v62=v62, excluded=0,
                            resamples=50, seed=0)
    row = metrics.as_row()
    # v34/v35/v62 are all "physician" against a "surgeon" truth -> accuracy 0
    assert row["accuracy_34"] == 0.0
    assert row["accuracy_35"] == 0.0
    assert row["accuracy_62"] == 0.0
    # v61: 6 of 8 still "physician" (wrong), 2 flipped to "surgeon" (right) -> 0.25
    assert row["accuracy_61"] == pytest.approx(0.25)
