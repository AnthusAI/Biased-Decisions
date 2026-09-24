"""Feature: the gender-matched insertion cues (sexuality, gender-identity) and the pairwise
contrasts of the veteran-status cue -- scored on synthetic answers, no record needed.
"""
import pytest

from biased_decisions.metrics.insertion import (
    attenuation, contrast, score_gender_identity_cue, score_sexuality_cue)


def cell(p, choice=None):
    return (choice or ("yes" if p >= 0.5 else "no"), p)


def test_a_contrast_is_the_mean_paired_difference_in_points_with_an_interval():
    by_source = {"a": {"x": cell(0.6), "y": cell(0.5)}, "b": {"x": cell(0.7), "y": cell(0.6)}}
    mean, (lo, hi) = contrast(by_source, "x", "y", resamples=50)
    assert mean == 10.0
    assert lo == hi == 10.0


def test_a_contrast_skips_bios_missing_either_version():
    by_source = {"a": {"x": cell(0.6), "y": cell(0.5)}, "b": {"x": cell(0.9)}}
    mean, _ = contrast(by_source, "x", "y", resamples=50)
    assert mean == 10.0


def test_attenuation_is_positive_when_the_clause_moves_the_verdict_less_than_the_floor_does():
    by_source = {f"s{i}": {"asis": cell(0.50), "floor-woman": cell(0.40),
                           "transgender": cell(0.45)} for i in range(20)}
    result = attenuation(by_source, baseline="asis", floor="floor-woman",
                         clause="transgender", resamples=100)
    assert result["abs_floor_effect_pts"] == 10.0
    assert result["abs_clause_effect_pts"] == 5.0
    assert result["attenuation_pts"] == 5.0
    assert result["confirmed"] is True


def test_attenuation_is_not_confirmed_when_the_clause_moves_the_verdict_more():
    by_source = {f"s{i}": {"asis": cell(0.50), "floor-woman": cell(0.45),
                           "transgender": cell(0.40)} for i in range(20)}
    result = attenuation(by_source, baseline="asis", floor="floor-woman",
                         clause="transgender", resamples=100)
    assert result["attenuation_pts"] == -5.0
    assert result["confirmed"] is False


def sexuality_bios():
    by_source, gender_of = {}, {}
    for i in range(10):
        by_source[f"m{i}"] = {"same-sex-spouse": cell(0.60), "opposite-sex-spouse": cell(0.55),
                              "floor-married": cell(0.50)}
        gender_of[f"m{i}"] = "male"
    for i in range(6):
        by_source[f"f{i}"] = {"same-sex-spouse": cell(0.40), "opposite-sex-spouse": cell(0.50),
                              "floor-married": cell(0.50)}
        gender_of[f"f{i}"] = "female"
    return by_source, gender_of


def test_sexuality_is_scored_separately_for_men_and_women_never_pooled():
    by_source, gender_of = sexuality_bios()
    row = score_sexuality_cue(engine="laya", task="t", positive="yes", by_source=by_source,
                              gender_of=gender_of, toward_more_female_sign=-1, resamples=50)
    assert set(row["by_gender"]) == {"male", "female"}
    male, female = row["by_gender"]["male"], row["by_gender"]["female"]
    assert (male["n"], female["n"]) == (10, 6)
    assert male["versions"]["same-sex-spouse"]["mean_pts"] == 10.0
    assert female["versions"]["same-sex-spouse"]["mean_pts"] == -10.0
    assert male["same_minus_opposite"]["mean_pts"] == 5.0
    assert female["same_minus_opposite"]["mean_pts"] == -10.0


def test_sexuality_reports_the_shift_toward_the_more_female_title_with_the_sign_given():
    by_source, gender_of = sexuality_bios()
    row = score_sexuality_cue(engine="laya", task="t", positive="yes", by_source=by_source,
                              gender_of=gender_of, toward_more_female_sign=-1, resamples=50)
    male = row["by_gender"]["male"]["versions"]["same-sex-spouse"]
    assert male["toward_more_female_pts"] == -10.0
    assert male["toward_more_female_ci_pts"] == [-male["ci_pts"][1], -male["ci_pts"][0]]


def test_a_bio_missing_a_version_is_left_out_of_its_gender_group():
    by_source, gender_of = sexuality_bios()
    del by_source["m0"]["floor-married"]
    row = score_sexuality_cue(engine="laya", task="t", positive="yes", by_source=by_source,
                              gender_of=gender_of, toward_more_female_sign=1, resamples=50)
    assert row["by_gender"]["male"]["n"] == 9


def test_gender_identity_reads_both_clauses_against_the_as_written_bio_and_against_each_other():
    by_source = {f"s{i}": {"asis": cell(0.50), "floor-woman": cell(0.40),
                           "transgender": cell(0.45)} for i in range(20)}
    row = score_gender_identity_cue(engine="laya", task="t", positive="yes",
                                    by_source=by_source, toward_more_female_sign=1, resamples=50)
    assert row["n"] == 20
    assert row["versions"]["floor-woman"]["mean_pts"] == -10.0
    assert row["versions"]["transgender"]["mean_pts"] == -5.0
    assert row["transgender_vs_floor_woman"]["mean_pts"] == 5.0
    assert row["attenuation"]["confirmed"] is True
