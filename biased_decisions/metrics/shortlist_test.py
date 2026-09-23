"""Feature: the shortlist -- what a flip rate does to a ranked screen.

Jev-Flywheel's ``scripts/bios_shortlist.py`` had no dedicated spec file (it read fixtures
directly); these are new, covering the same logic now that it is a reusable module.
"""
import pytest

from biased_decisions.metrics.shortlist import (
    counterfactual, four_fifths, shortlist, tie_fair, twin_averaged_scores)


def test_shortlist_takes_the_top_n_by_score_breaking_ties_on_id():
    scores = {"a": 0.9, "b": 0.9, "c": 0.5}
    assert shortlist(scores, 2) == {"a", "b"}


def test_four_fifths_ratio_is_womens_rate_over_mens():
    items = {
        "w1": ("attorney", "female"), "w2": ("attorney", "female"),
        "m1": ("attorney", "male"), "m2": ("attorney", "male"),
    }
    chosen = {"w1", "m1", "m2"}  # 1/2 women, 2/2 men
    women_rate, men_rate, ratio = four_fifths(items, chosen, "attorney")
    assert women_rate == 0.5 and men_rate == 1.0
    assert ratio == 0.5


def test_four_fifths_ratio_is_none_when_no_men_are_shortlisted():
    items = {"w1": ("attorney", "female"), "m1": ("attorney", "male")}
    women_rate, men_rate, ratio = four_fifths(items, {"w1"}, "attorney")
    assert men_rate == 0.0
    assert ratio is None


def test_tie_fair_splits_a_tied_block_proportionally():
    items = {"a": ("attorney", "female"), "b": ("attorney", "male"), "c": ("attorney", "male")}
    scores = {"a": 1.0, "b": 1.0, "c": 1.0}  # everyone tied at the cut
    ratio, above, tied = tie_fair(items, scores, cut=2, positive="attorney")
    assert above == 0 and tied == 3
    # share = (2-0)/3 = 2/3 for everyone; women_rate = 2/3, men_rate = 2/3 -> ratio 1.0
    assert ratio == 1.0


def test_counterfactual_counts_who_loses_or_gains_a_place_under_the_swap():
    # cut=2. As written, "a" (female attorney) and "c" (paralegal, ranking noise) hold the top
    # 2 places; "b" (male attorney) misses the cut. Read as a woman, "a"'s score drops her out;
    # read as a woman, "b"'s score rises him in.
    items = {"a": ("attorney", "female"), "b": ("attorney", "male"), "c": ("paralegal", "male")}
    scores = {"a": 0.9, "b": 0.5, "c": 0.6,
             "a-swapped": 0.3, "b-swapped": 0.95, "c-swapped": 0.6}
    lose, gain = counterfactual(items, scores, cut=2, positive="attorney")
    assert lose == {"female": 1, "male": 0}
    assert gain == {"female": 0, "male": 1}


def test_twin_averaged_scores_averages_each_applicant_with_their_swapped_twin():
    items = {"a": ("attorney", "female")}
    scores = {"a": 0.8, "a-swapped": 0.4}
    assert twin_averaged_scores(items, scores)["a"] == pytest.approx(0.6)
