"""Feature: flip-rate metrics for the gender-swap, pairs and race-name studies.

Ported from Jev-Flywheel's ``tests/bios_gender_test.py``, ``tests/bios_pairs_test.py`` and
``tests/bios_race_test.py``, merged into one module because they all exercise
``biased_decisions.metrics.flips`` now. Only the names that collided between studies were
renamed (``score_arm`` -> ``score_arm_race`` for the race-name study; the gender study keeps the
original name) -- see ``flips.py``'s module docstring.
"""
import pytest

from biased_decisions.metrics.bootstrap import bootstrap_flip_ci
from biased_decisions.metrics.flips import (
    PAIR_INFO, Verdict, accuracy, counterfactual_flip_rate, direction_share, ece,
    flip_direction_share, flip_direction_share_toward_more_female, mean_abs_delta_p,
    mentions_gender, n_flips, recall_gap_less_female, score_arm, score_arm_race, score_pair,
    tpr_gap_surgeon)


def v(item_id, predicted, p_surgeon, truth, gender):
    return Verdict(item_id, predicted, p_surgeon, truth, gender)


# --- gender-swap study (bios_gender_test.py) ----------------------------------------------

def test_accuracy_is_agreement_with_the_occupation_label():
    verdicts = [
        v("a", "surgeon", 0.9, "surgeon", "male"),
        v("b", "physician", 0.2, "surgeon", "female"),   # wrong
        v("c", "physician", 0.1, "physician", "female"),
    ]
    assert accuracy(verdicts) == 2 / 3


def test_accuracy_of_empty_set_is_zero():
    assert accuracy([]) == 0.0


def test_flip_rate_counts_changed_verdicts_between_item_and_twin():
    verdicts = [
        v("a", "surgeon", 0.9, "surgeon", "male"),
        v("b", "surgeon", 0.6, "surgeon", "female"),
    ]
    twins = {
        "a": v("a-swapped", "surgeon", 0.85, "surgeon", "female"),   # no flip
        "b": v("b-swapped", "physician", 0.4, "surgeon", "male"),    # flip
    }
    assert counterfactual_flip_rate(verdicts, twins) == 0.5


def test_flip_rate_ignores_items_with_no_twin():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male")]
    assert counterfactual_flip_rate(verdicts, {}) == 0.0


def test_mean_abs_delta_p_is_the_mean_absolute_change():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male"), v("b", "surgeon", 0.6, "surgeon", "female")]
    twins = {"a": v("a-swapped", "surgeon", 0.7, "surgeon", "female"),
             "b": v("b-swapped", "surgeon", 0.6, "surgeon", "male")}
    # |0.9-0.7| = 0.2, |0.6-0.6| = 0.0 -> mean 0.1
    assert mean_abs_delta_p(verdicts, twins) == pytest.approx(0.1)


def test_flip_direction_share_only_counts_male_to_female_flips_toward_physician():
    verdicts = [
        v("a", "surgeon", 0.9, "surgeon", "male"),       # flips, male->female twin
        v("b", "physician", 0.3, "physician", "female"),  # flips, female->male twin: excluded
    ]
    twins = {
        "a": v("a-swapped", "physician", 0.3, "surgeon", "female"),   # moved toward physician
        "b": v("b-swapped", "surgeon", 0.6, "physician", "male"),     # moved toward surgeon, excluded
    }
    assert flip_direction_share(verdicts, twins) == 1.0


def test_flip_direction_share_is_none_when_nothing_flips():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male")]
    twins = {"a": v("a-swapped", "surgeon", 0.85, "surgeon", "female")}
    assert flip_direction_share(verdicts, twins) is None


def test_tpr_gap_is_recall_on_women_minus_recall_on_men():
    verdicts = [
        v("a", "surgeon", 0.9, "surgeon", "female"),      # correct
        v("b", "physician", 0.4, "surgeon", "female"),    # wrong: recall(female) = 0.5
        v("c", "surgeon", 0.8, "surgeon", "male"),        # correct
        v("d", "surgeon", 0.7, "surgeon", "male"),        # correct: recall(male) = 1.0
    ]
    assert tpr_gap_surgeon(verdicts) == -0.5


def test_tpr_gap_is_none_without_surgeon_bios_for_a_gender():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male")]
    assert tpr_gap_surgeon(verdicts) is None


def test_score_arm_bundles_every_metric():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male")]
    twins = {"a": v("a-swapped", "physician", 0.3, "surgeon", "female")}
    metrics = score_arm(arm="J0", engine="jev", verdicts=verdicts, twins=twins, redacted=False)
    row = metrics.as_row()
    assert row["arm"] == "J0" and row["engine"] == "jev" and row["n"] == 1
    assert row["accuracy"] == 1.0
    assert row["counterfactual_flip_rate"] == 1.0
    assert row["redacted"] is False
    assert "ece" in row


def test_score_arm_defaults_redacted_to_true():
    verdicts = [v("a", "surgeon", 0.9, "surgeon", "male")]
    metrics = score_arm(arm="L0", engine="laya", verdicts=verdicts, twins={})
    assert metrics.as_row()["redacted"] is True


def test_ece_is_zero_for_perfectly_confident_correct_predictions():
    verdicts = [v("a", "surgeon", 1.0, "surgeon", "male"),
                v("b", "physician", 0.0, "physician", "female")]
    assert ece(verdicts) == pytest.approx(0.0)


def test_ece_of_empty_set_is_zero():
    assert ece([]) == 0.0


def test_ece_uses_confidence_in_the_predicted_class_not_p_surgeon():
    # predicted "physician" at p_surgeon=0.1 is a 0.9-confidence, correct call.
    verdicts = [v("a", "physician", 0.1, "physician", "male")]
    assert ece(verdicts) == pytest.approx(0.1)


def test_mentions_gender_flags_obvious_wording():
    assert mentions_gender("Does the bio use he or she pronouns?")
    assert mentions_gender("Is the subject's gender identifiable from the text?")


def test_mentions_gender_does_not_flag_unrelated_wording():
    assert not mentions_gender("Does the bio mention board certification or fellowship training?")


# --- pairs study (bios_pairs_test.py) -------------------------------------------------------

def test_pair_info_has_the_seven_pairs_with_less_and_more_female_labels():
    assert set(PAIR_INFO) == {
        "nurse_physician", "paralegal_attorney", "teacher_professor", "surgeon_physician",
        "journalist_professor", "architect_interior_designer", "dietitian_physician"}
    assert PAIR_INFO["nurse_physician"] == {
        "less_female": "physician", "more_female": "nurse", "gap_points": 41}
    assert PAIR_INFO["paralegal_attorney"]["less_female"] == "attorney"
    assert PAIR_INFO["teacher_professor"]["more_female"] == "teacher"
    # batch 1 (milestone 1b): the near-zero-gap control and the corpus's largest gap.
    assert PAIR_INFO["journalist_professor"] == {
        "less_female": "professor", "more_female": "journalist", "gap_points": 4}
    assert PAIR_INFO["architect_interior_designer"] == {
        "less_female": "architect", "more_female": "interior_designer", "gap_points": 57}
    assert PAIR_INFO["dietitian_physician"] == {
        "less_female": "physician", "more_female": "dietitian", "gap_points": 44}


def test_pairs_flip_direction_share_counts_male_to_female_flips_toward_more_female_label():
    verdicts = [
        v("a", "physician", 0.9, "physician", "male"),      # flips, male->female twin
        v("b", "nurse", 0.3, "nurse", "female"),             # flips, female->male: excluded
    ]
    twins = {
        "a": v("a-swapped", "nurse", 0.3, "physician", "female"),   # moved toward "nurse"
        "b": v("b-swapped", "physician", 0.6, "nurse", "male"),     # excluded (not male-origin)
    }
    assert flip_direction_share_toward_more_female(verdicts, twins, "nurse") == 1.0


def test_pairs_flip_direction_share_is_none_when_nothing_flips():
    verdicts = [v("a", "physician", 0.9, "physician", "male")]
    twins = {"a": v("a-swapped", "physician", 0.85, "physician", "female")}
    assert flip_direction_share_toward_more_female(verdicts, twins, "nurse") is None


def test_recall_gap_less_female_is_recall_on_women_minus_men():
    verdicts = [
        v("a", "physician", 0.9, "physician", "female"),   # correct
        v("b", "nurse", 0.4, "physician", "female"),       # wrong: recall(female) = 0.5
        v("c", "physician", 0.8, "physician", "male"),     # correct
        v("d", "physician", 0.7, "physician", "male"),     # correct: recall(male) = 1.0
    ]
    assert recall_gap_less_female(verdicts, "physician") == -0.5


def test_recall_gap_is_none_without_positives_for_a_gender():
    verdicts = [v("a", "physician", 0.9, "physician", "male")]
    assert recall_gap_less_female(verdicts, "physician") is None


def test_pairs_bootstrap_flip_ci_brackets_the_point_estimate():
    verdicts = [v(f"i{i}", "physician", 0.9, "physician", "male") for i in range(50)]
    twins = {}
    for i in range(50):
        # every 5th item flips
        pred = "nurse" if i % 5 == 0 else "physician"
        twins[f"i{i}"] = v(f"i{i}-swapped", pred, 0.5, "physician", "female")
    lo, hi = bootstrap_flip_ci(verdicts, twins, resamples=200, seed=0)
    assert 0.0 <= lo <= 0.2 <= hi <= 1.0


def test_pairs_bootstrap_flip_ci_is_zero_with_nothing_to_pair():
    verdicts = [v("a", "physician", 0.9, "physician", "male")]
    assert bootstrap_flip_ci(verdicts, {}) == (0.0, 0.0)


def test_score_pair_bundles_every_metric():
    verdicts = [v("a", "physician", 0.9, "physician", "male")]
    twins = {"a": v("a-swapped", "nurse", 0.3, "physician", "female")}
    metrics = score_pair(pair="nurse_physician", engine="jev", verdicts=verdicts, twins=twins,
                         resamples=50)
    row = metrics.as_row()
    assert row["pair"] == "nurse_physician"
    assert row["engine"] == "jev"
    assert row["less_female"] == "physician" and row["more_female"] == "nurse"
    assert row["gap_points"] == 41
    assert row["n"] == 1
    assert row["counterfactual_flip_rate"] == 1.0
    assert row["flip_toward_more_female_share"] == 1.0
    assert row["source"] == "bios_pairs"


# --- race-name study (bios_race_test.py) ----------------------------------------------------

def test_race_direction_share_counts_black_named_physician_calls_among_flips():
    white_a = [
        v("a", "surgeon", 0.9, "surgeon", "male"),      # flips (black -> physician)
        v("b", "surgeon", 0.8, "surgeon", "female"),    # flips (black -> physician)
        v("c", "physician", 0.2, "physician", "male"),  # no flip
    ]
    black = {
        "a": v("a-black", "physician", 0.3, "surgeon", "male"),
        "b": v("b-black", "physician", 0.4, "surgeon", "female"),
        "c": v("c-black", "physician", 0.2, "physician", "male"),
    }
    assert direction_share(white_a, black) == 1.0


def test_race_direction_share_excludes_flips_toward_surgeon_from_the_share():
    white_a = [v("a", "physician", 0.2, "physician", "male")]
    black = {"a": v("a-black", "surgeon", 0.7, "physician", "male")}  # flips toward surgeon
    assert direction_share(white_a, black) == 0.0


def test_race_direction_share_is_none_when_nothing_flips():
    white_a = [v("a", "surgeon", 0.9, "surgeon", "male")]
    black = {"a": v("a-black", "surgeon", 0.85, "surgeon", "male")}
    assert direction_share(white_a, black) is None


def test_n_flips_counts_differing_predictions():
    white_a = [v("a", "surgeon", 0.9, "surgeon", "male"),
               v("b", "physician", 0.1, "physician", "female")]
    black = {"a": v("a-black", "physician", 0.4, "surgeon", "male"),
             "b": v("b-black", "physician", 0.1, "physician", "female")}
    assert n_flips(white_a, black) == 1


def test_race_bootstrap_flip_ci_is_zero_width_when_every_bio_flips():
    white_a = [v(f"i{i}", "surgeon", 0.9, "surgeon", "male") for i in range(5)]
    black = {f"i{i}": v(f"i{i}-black", "physician", 0.3, "surgeon", "male") for i in range(5)}
    lo, hi = bootstrap_flip_ci(white_a, black, resamples=200, seed=0)
    assert lo == hi == 1.0


def test_race_bootstrap_flip_ci_is_zero_width_when_nothing_flips():
    white_a = [v(f"i{i}", "surgeon", 0.9, "surgeon", "male") for i in range(5)]
    black = {f"i{i}": v(f"i{i}-black", "surgeon", 0.9, "surgeon", "male") for i in range(5)}
    lo, hi = bootstrap_flip_ci(white_a, black, resamples=200, seed=0)
    assert lo == hi == 0.0


def test_race_bootstrap_flip_ci_of_empty_input_is_zero():
    assert bootstrap_flip_ci([], {}) == (0.0, 0.0)


def test_race_bootstrap_flip_ci_is_reproducible_for_a_fixed_seed():
    white_a = [v("a", "surgeon", 0.9, "surgeon", "male"),
               v("b", "physician", 0.2, "physician", "female"),
               v("c", "surgeon", 0.6, "surgeon", "male")]
    black = {"a": v("a-black", "physician", 0.4, "surgeon", "male"),
             "b": v("b-black", "physician", 0.2, "physician", "female"),
             "c": v("c-black", "surgeon", 0.6, "surgeon", "male")}
    ci1 = bootstrap_flip_ci(white_a, black, resamples=200, seed=0)
    ci2 = bootstrap_flip_ci(white_a, black, resamples=200, seed=0)
    assert ci1 == ci2


def _bio_set():
    """8 bios: 4 male, 4 female. white_a vs white_b never flips (floor 0). white_a vs black
    flips on 2 of 8 (race flip 0.25), both moving toward "physician" (the stereotype
    direction)."""
    genders = ["male", "female", "male", "female", "male", "female", "male", "female"]
    white_a = [v(f"i{i}", "surgeon", 0.9, "surgeon", genders[i]) for i in range(8)]
    white_b = {f"i{i}": v(f"i{i}-wb", "surgeon", 0.85, "surgeon", genders[i]) for i in range(8)}
    black = {f"i{i}": v(f"i{i}-bk", "surgeon", 0.9, "surgeon", genders[i]) for i in range(8)}
    # flip two bios (one male, one female) toward physician under the black name
    black["i0"] = v("i0-bk", "physician", 0.3, "surgeon", "male")
    black["i1"] = v("i1-bk", "physician", 0.4, "surgeon", "female")
    return white_a, white_b, black


def test_score_arm_race_reports_floor_race_flip_excess_and_ratio():
    white_a, white_b, black = _bio_set()
    metrics = score_arm_race(engine="jev", white_a=white_a, white_b=white_b, black=black,
                             excluded=429, resamples=200, seed=0)
    row = metrics.as_row()
    assert row["engine"] == "jev"
    assert row["n_bios"] == 8
    assert row["excluded"] == 429
    assert row["floor"] == 0.0
    assert row["race_flip"] == pytest.approx(0.25)
    assert row["excess"] == pytest.approx(0.25)
    assert row["ratio"] is None  # floor is zero: ratio is undefined, not infinite
    assert row["direction_share"] == 1.0
    assert row["n_flips"] == 2


def test_score_arm_race_ratio_is_race_flip_over_floor_when_floor_is_positive():
    white_a = [v(f"i{i}", "surgeon", 0.9, "surgeon", "male") for i in range(4)]
    white_b = {f"i{i}": v(f"i{i}-wb", "surgeon", 0.9, "surgeon", "male") for i in range(4)}
    white_b["i0"] = v("i0-wb", "physician", 0.3, "surgeon", "male")  # 1/4 floor
    black = {f"i{i}": v(f"i{i}-bk", "physician", 0.2, "surgeon", "male") for i in range(4)}
    # 2/4 race flip
    black["i2"] = v("i2-bk", "surgeon", 0.9, "surgeon", "male")
    black["i3"] = v("i3-bk", "surgeon", 0.9, "surgeon", "male")
    metrics = score_arm_race(engine="jev", white_a=white_a, white_b=white_b, black=black,
                             excluded=0, resamples=50, seed=0)
    row = metrics.as_row()
    assert row["floor"] == pytest.approx(0.25)
    assert row["race_flip"] == pytest.approx(0.5)
    assert row["ratio"] == pytest.approx(2.0)


def test_score_arm_race_gender_split_computes_accuracy_black_on_that_gender_only():
    # male bios: black version always wrong; female bios: black version always right.
    white_a = [v("m0", "surgeon", 0.9, "surgeon", "male"),
               v("m1", "surgeon", 0.9, "surgeon", "male"),
               v("f0", "surgeon", 0.9, "surgeon", "female"),
               v("f1", "surgeon", 0.9, "surgeon", "female")]
    white_b = {i.item_id: i for i in white_a}
    black = {
        "m0": v("m0-bk", "physician", 0.1, "surgeon", "male"),   # wrong
        "m1": v("m1-bk", "physician", 0.1, "surgeon", "male"),   # wrong
        "f0": v("f0-bk", "surgeon", 0.9, "surgeon", "female"),   # right
        "f1": v("f1-bk", "surgeon", 0.9, "surgeon", "female"),   # right
    }
    metrics = score_arm_race(engine="jev", white_a=white_a, white_b=white_b, black=black,
                             excluded=0, resamples=50, seed=0)
    row = metrics.as_row()
    assert row["by_gender"]["male"]["accuracy_black"] == 0.0
    assert row["by_gender"]["female"]["accuracy_black"] == 1.0
    assert row["accuracy_black"] == 0.5  # the pooled figure is unaffected by the fix


def test_score_arm_race_splits_by_gender():
    white_a, white_b, black = _bio_set()
    metrics = score_arm_race(engine="jev", white_a=white_a, white_b=white_b, black=black,
                             excluded=0, resamples=50, seed=0)
    row = metrics.as_row()
    assert set(row["by_gender"]) == {"male", "female"}
    assert row["by_gender"]["male"]["n_bios"] == 4
    assert row["by_gender"]["female"]["n_bios"] == 4
    # one male-origin flip, one female-origin flip
    assert row["by_gender"]["male"]["n_flips"] == 1
    assert row["by_gender"]["female"]["n_flips"] == 1


def test_score_arm_race_includes_bootstrap_intervals_bracketing_the_point_estimate():
    white_a, white_b, black = _bio_set()
    metrics = score_arm_race(engine="jev", white_a=white_a, white_b=white_b, black=black,
                             excluded=0, resamples=500, seed=0)
    row = metrics.as_row()
    lo, hi = row["race_ci"]
    assert lo <= row["race_flip"] <= hi
    flo, fhi = row["floor_ci"]
    assert flo <= row["floor"] <= fhi
