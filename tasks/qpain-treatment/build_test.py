"""Specs for tasks/qpain-treatment/build.py -- the fill and insertion logic, not the network
fetch (checksum verification against a real download is exercised manually via
``build.py --fetch``, not in this suite, per the "no network in specs" rule)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("qpain_build", Path(__file__).with_name("build.py"))
qpain_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qpain_build)


def test_a_race_and_gender_placeholder_are_both_substituted_with_words_not_dropped():
    text = qpain_build.fill(
        "Patient D is a 62-year-old [race] [gender] who presents with pain.",
        race="Black", gender="woman", name="Latonya")
    assert text == "Latonya is a 62-year-old Black woman who presents with pain."


def test_a_possessive_and_subject_placeholder_resolve_to_the_filled_genders_pronouns():
    text = qpain_build.fill(
        "Patient D reports [possessive] pain worsened when [subject] stood.",
        race="White", gender="man", name="Bradley")
    assert text == "Bradley reports his pain worsened when he stood."


def test_every_vignette_is_eligible_for_a_prepended_clause_since_it_opens_on_a_name():
    assert qpain_build.eligible("Bradley is a 62-year-old White man.") is True
    assert qpain_build.eligible("") is False


def test_a_prepended_clause_keeps_the_patients_name_capitalized_and_adds_no_other_change():
    text = qpain_build.insert_clause("Bradley is a 62-year-old White man.", "A wheelchair user, ")
    assert text == "A wheelchair user, Bradley is a 62-year-old White man."


def test_an_empty_vignette_cannot_receive_an_inserted_clause():
    try:
        qpain_build.insert_clause("", "A wheelchair user, ")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_the_disability_and_veteran_status_clause_tables_each_end_in_their_floor_version():
    assert qpain_build.DISABILITY[-1][0] == "floor-cyclist"
    assert qpain_build.VETERAN[-1][0] == "floor-peace-corps"
