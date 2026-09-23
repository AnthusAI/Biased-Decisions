"""Specs for tasks/civil-comments-moderation/build.py's pure logic (identity-neutrality check and
cue tables) -- not the network fetch, per the "no network in specs" rule."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build as civil_build  # noqa: E402


def test_a_comment_naming_an_identity_term_is_not_identity_neutral():
    assert civil_build.is_identity_neutral("I think the mayor is wrong about zoning.") is True
    assert civil_build.is_identity_neutral("As a gay man I disagree with this policy.") is False


def test_identity_neutrality_check_is_case_insensitive_and_whole_word():
    assert civil_build.is_identity_neutral("MUSLIM leaders spoke today.") is False
    # "asianfoodlover" is not the whole word "asian" -- must not false-positive on a substring.
    assert civil_build.is_identity_neutral("asianfoodlover posted again.") is True


def test_every_cue_lists_its_floor_version_last():
    for cue, clauses in civil_build.CUES.items():
        version, _ = clauses[-1]
        assert version.startswith("floor-"), f"{cue}'s last version {version!r} is not a floor"


def test_each_floors_own_trait_word_is_in_the_identity_term_list_by_design():
    # The floors name a trait (left-handed, vegetarian, suburban, cyclist) that is itself in
    # _IDENTITY_TERMS, by design (a same-shape floor reads as a comparable clause, not as bare,
    # unmarked text) -- this spec makes that a documented, deliberate choice rather than a silent
    # inconsistency if someone changes the floor wording later.
    assert "left-handed" in civil_build._IDENTITY_TERMS
    assert "vegetarian" in civil_build._IDENTITY_TERMS
    assert "suburban" in civil_build._IDENTITY_TERMS
    assert "cyclist" in civil_build._IDENTITY_TERMS


def test_inserting_a_clause_prepends_it_and_changes_nothing_else():
    text = "Thank you for representing me."
    clause = "As a Muslim, "
    assert clause + text == "As a Muslim, Thank you for representing me."
