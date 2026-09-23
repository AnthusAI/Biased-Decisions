"""Feature: synthetic small-business loan narratives (Pool B), deterministic and gender-balanced.
"""
from biased_decisions.cues.insertion import eligible
from biased_decisions.tasks.loan_narratives import N_NARRATIVES, build_narratives


def test_build_narratives_returns_the_requested_count():
    assert len(build_narratives(50)) == 50
    assert len(build_narratives()) == N_NARRATIVES


def test_narratives_alternate_gender_and_start_with_the_matching_pronoun():
    narratives = build_narratives(4)
    assert [n.gender for n in narratives] == ["male", "female", "male", "female"]
    assert narratives[0].text.startswith("He ")
    assert narratives[1].text.startswith("She ")


def test_the_draw_is_reproducible_from_the_seed():
    a = build_narratives(30, seed=0)
    b = build_narratives(30, seed=0)
    assert [n.text for n in a] == [n.text for n in b]


def test_a_different_seed_changes_the_filled_in_details():
    a = build_narratives(30, seed=0)
    b = build_narratives(30, seed=1)
    assert [n.text for n in a] != [n.text for n in b]


def test_every_narrative_is_eligible_for_clause_insertion():
    # The identity clause is inserted before the bio's first subject pronoun; every narrative
    # must open with that pronoun for the study's cue mechanism to apply to it.
    for narrative in build_narratives(N_NARRATIVES):
        assert eligible(narrative.text), narrative.id


def test_ids_are_stable_and_zero_padded():
    narratives = build_narratives(3)
    assert [n.id for n in narratives] == ["loan-0000", "loan-0001", "loan-0002"]


def test_narratives_mention_no_real_person_or_business():
    # A loose sanity check: the generator only ever fills from its own fixed word lists, never
    # from free text, so nothing resembling a real name should appear.
    for narrative in build_narratives(20):
        assert "Cohen" not in narrative.text
        assert "Smith" not in narrative.text
