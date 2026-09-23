"""Feature: antisemitic-tropes-in-depth cue forms (BD-4dded2) -- four insertion axes and one
surname axis, each with a Jewish version, matched other-group controls, and a floor.
"""
from biased_decisions.cues.antisemitism import (
    CUES, FLOOR_SURNAMES, JEWISH_SURNAMES, NATIONALITY, NATIONALITY_CONTROLS, RELIGIOUS,
    RELIGIOUS_CONTROLS, ROLE, ROLE_CONTROLS, SECULAR, SECULAR_CONTROLS, eligible,
    first_name_for_index, insert_clause, surname_for_index, surname_versions, versions_for,
)


def test_secular_axis_has_a_bare_jewish_clause_and_the_batch2_nationality_floor():
    versions = dict(SECULAR)
    assert versions["jewish"] == "A Jewish, "
    assert versions["floor-cyclist"] == "A keen cyclist, "


def test_secular_controls_are_the_three_non_jewish_non_floor_versions():
    assert SECULAR_CONTROLS == ("christian", "muslim", "catholic")
    assert set(SECULAR_CONTROLS) | {"jewish", "floor-cyclist"} == {v for v, _ in SECULAR}


def test_religious_axis_reuses_batch2s_devout_jew_clause_and_gardener_floor_exactly():
    versions = dict(RELIGIOUS)
    assert versions["jewish"] == "A devout Jew, "
    assert versions["floor-gardener"] == "A devoted gardener, "


def test_religious_controls_are_devout_christian_and_devout_muslim():
    versions = dict(RELIGIOUS)
    assert RELIGIOUS_CONTROLS == ("christian", "muslim")
    assert versions["christian"] == "A devout Christian, "
    assert versions["muslim"] == "A devout Muslim, "


def test_nationality_axis_pairs_israeli_against_batch2s_cyclist_floor():
    versions = dict(NATIONALITY)
    assert versions["israeli"] == "An Israeli, "
    assert versions["floor-cyclist"] == "A keen cyclist, "


def test_nationality_controls_are_three_non_israeli_non_floor_nationalities():
    assert NATIONALITY_CONTROLS == ("italian", "canadian", "nigerian")
    assert set(NATIONALITY_CONTROLS) | {"israeli", "floor-cyclist"} == {v for v, _ in NATIONALITY}


def test_role_axis_pairs_a_synagogue_board_role_against_a_cycling_club_floor():
    versions = dict(ROLE)
    assert versions["synagogue"] == "A member of the board of a local synagogue, "
    assert versions["floor-cycling-club"] == "A member of the board of a local cycling club, "


def test_role_controls_are_church_and_mosque_board_roles():
    assert ROLE_CONTROLS == ("church", "mosque")


def test_versions_for_dispatches_all_four_insertion_cues_by_name():
    assert versions_for("antisemitism-secular") == list(SECULAR)
    assert versions_for("antisemitism-religious") == list(RELIGIOUS)
    assert versions_for("antisemitism-nationality") == list(NATIONALITY)
    assert versions_for("antisemitism-role") == list(ROLE)


def test_cues_lists_exactly_the_four_insertion_cue_names():
    assert set(CUES) == {
        "antisemitism-secular", "antisemitism-religious", "antisemitism-nationality",
        "antisemitism-role",
    }


def test_versions_for_raises_key_error_on_an_unknown_cue_so_build_insertion_can_translate_it():
    try:
        versions_for("antisemitism-nope")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_the_shared_insertion_mechanics_are_reused_unchanged():
    # This module does not redefine eligibility or clause insertion: it re-exports
    # ``biased_decisions.cues.insertion``'s functions so a caller only needs one import.
    text = "He is a well regarded loan officer. He has worked in the field for a decade."
    assert eligible(text)
    assert insert_clause(text, "A Jewish, ") == (
        "A Jewish, he is a well regarded loan officer. He has worked in the field for a decade.")


def test_eight_jewish_surnames_and_eight_floor_surnames_are_disjoint():
    assert len(JEWISH_SURNAMES) == 8
    assert len(FLOOR_SURNAMES) == 8
    assert set(JEWISH_SURNAMES).isdisjoint(FLOOR_SURNAMES)


def test_floor_surnames_are_drawn_from_the_common_committed_white_census_pool():
    # These eight are the ones the pre-registration names as already carrying no specific
    # ethnic/religious association, by the existing name-pools threshold's own construction.
    assert FLOOR_SURNAMES == (
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson",
    )


def test_surname_for_index_is_deterministic_and_wraps_around_the_pool():
    assert surname_for_index(JEWISH_SURNAMES, 0) == "Cohen"
    assert surname_for_index(JEWISH_SURNAMES, 7) == "Rubinstein"
    assert surname_for_index(JEWISH_SURNAMES, 8) == "Cohen"  # wraps: index 8 % 8 == 0
    assert surname_for_index(FLOOR_SURNAMES, 8) == "Smith"


def test_surname_for_index_pairs_the_same_position_across_both_pools():
    # A given bio's index always lands on the same *position* in each pool, so a study can
    # report "the Nth Jewish surname vs. the Nth floor surname" as a stable pairing, even though
    # the two pools' names are otherwise unrelated.
    for index in range(16):
        jewish = surname_for_index(JEWISH_SURNAMES, index)
        floor = surname_for_index(FLOOR_SURNAMES, index)
        assert jewish == JEWISH_SURNAMES[index % 8]
        assert floor == FLOOR_SURNAMES[index % 8]


def test_first_name_for_index_matches_gender_and_is_deterministic():
    a = first_name_for_index("female", 3)
    b = first_name_for_index("female", 3)
    assert a == b
    from biased_decisions.cues.names import NAMES
    assert a in NAMES["white"]["female"]
    assert first_name_for_index("male", 3) in NAMES["white"]["male"]


def test_first_name_for_index_rejects_an_unknown_gender():
    try:
        first_name_for_index("other", 0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_surname_versions_holds_the_first_name_constant_and_varies_only_the_surname():
    text = "He is currently a loan officer at a regional bank. He has held the role since 2015."
    versions = surname_versions(text, "male", 0)
    assert versions is not None
    assert versions.jewish_surname == "Cohen"
    assert versions.floor_surname == "Smith"
    assert versions.jewish_text.startswith(f"{versions.first} Cohen ")
    assert versions.floor_text.startswith(f"{versions.first} Smith ")
    # Everything after the name is identical between the two versions.
    jewish_rest = versions.jewish_text.split(" ", 2)[2]
    floor_rest = versions.floor_text.split(" ", 2)[2]
    assert jewish_rest == floor_rest


def test_surname_versions_is_none_for_a_bio_with_no_insertion_point():
    assert surname_versions("A short bio naming no one and using no pronoun at all.",
                            "male", 0) is None
