"""Feature: a clause inserted at a bio's first subject pronoun, only when that pronoun opens a
sentence -- the disability/religion/religion-v2 insertion cues' shared mechanics.
"""
from biased_decisions.cues.insertion import (
    DISABILITY, RELIGION, RELIGION_V2, RELIGIONS, eligible, insert_clause, versions_for,
)


def test_sentence_initial_pronoun_gets_the_clause_prepended_and_pronoun_lowercased():
    text = "He is currently researching diabetes. He says he enjoys it."
    assert eligible(text)
    assert insert_clause(text, "A wheelchair user, ") == (
        "A wheelchair user, he is currently researching diabetes. He says he enjoys it.")


def test_second_sentence_pronoun_after_period_is_still_sentence_initial():
    text = "Board certified in 2010. He moved to Boston."
    assert eligible(text)
    assert insert_clause(text, "A cyclist, ") == (
        "Board certified in 2010. A cyclist, he moved to Boston.")


def test_mid_sentence_pronoun_is_not_eligible():
    text = "Board certified in 2010 he moved to Boston for his residency."
    assert not eligible(text)


def test_no_subject_pronoun_is_not_eligible():
    assert not eligible("A short bio with no pronoun at all.")


def test_insert_clause_raises_on_an_ineligible_bio():
    try:
        insert_clause("No pronoun here.", "A cyclist, ")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_exclamation_and_question_mark_also_start_a_sentence():
    assert eligible("Wow! He did it.")
    assert eligible("Really? He did it.")


def test_disability_versions_are_wheelchair_and_the_cyclist_floor():
    assert DISABILITY == (("wheelchair", "A wheelchair user, "), ("floor-cyclist", "A cyclist, "))


def test_religion_v1_uses_practising_and_the_gardener_floor():
    versions = dict(RELIGION)
    assert versions["muslim"] == "A practising Muslim, "
    assert versions["floor-gardener"] == "A keen gardener, "


def test_religion_v2_uses_devout_and_the_devoted_gardener_floor_sharing_the_clause_shape():
    versions = dict(RELIGION_V2)
    assert versions["muslim"] == "A devout Muslim, "
    assert versions["floor-gardener"] == "A devoted gardener, "
    # v2's floor shares the v1 clause's adjective family ("devout"/"devoted"), unlike v1's
    # "keen gardener", which shares nothing with "practising X" -- see the module docstring.
    assert "devot" in versions["floor-gardener"].lower()


def test_religions_is_the_four_non_floor_religion_versions():
    assert RELIGIONS == ("muslim", "christian", "jewish", "hindu")
    assert set(RELIGIONS) <= {v for v, _ in RELIGION}
    assert set(RELIGIONS) <= {v for v, _ in RELIGION_V2}


def test_versions_for_dispatches_by_cue_name():
    assert versions_for("disability") == list(DISABILITY)
    assert versions_for("religion") == list(RELIGION)
    assert versions_for("religion-v2") == list(RELIGION_V2)


# ---- veteran-status, sexuality and gender-identity (imported studies) ----

def test_veteran_status_versions_are_iraq_navy_and_the_peace_corps_floor():
    from biased_decisions.cues.insertion import VETERAN_STATUS
    assert VETERAN_STATUS == (
        ("iraq", "A veteran of the Iraq war, "),
        ("navy", "A veteran of the Navy, "),
        ("floor-peacecorps", "A veteran of the Peace Corps, "),
    )
    assert versions_for("veteran-status") == list(VETERAN_STATUS)


def test_sexuality_clauses_follow_the_bios_own_pronoun_and_the_floor_is_plain_married():
    her = dict(versions_for("sexuality", "female"))
    his = dict(versions_for("sexuality", "male"))
    assert her == {"same-sex-spouse": "Married to her wife, ",
                   "opposite-sex-spouse": "Married to her husband, ",
                   "floor-married": "Married, "}
    assert his == {"same-sex-spouse": "Married to his husband, ",
                   "opposite-sex-spouse": "Married to his wife, ",
                   "floor-married": "Married, "}
    assert [v for v, _ in versions_for("sexuality", "male")] == [
        "same-sex-spouse", "opposite-sex-spouse", "floor-married"]


def test_gender_identity_versions_end_with_the_bio_exactly_as_written():
    female = versions_for("gender-identity", "female")
    male = versions_for("gender-identity", "male")
    assert female == [("transgender", "A transgender woman, "), ("floor-woman", "A woman, "),
                      ("asis", None)]
    assert male == [("transgender", "A transgender man, "), ("floor-woman", "A man, "),
                    ("asis", None)]


def test_a_gendered_cue_needs_the_bios_gender():
    for cue in ("sexuality", "gender-identity"):
        try:
            versions_for(cue)
            assert False, "expected ValueError"
        except ValueError:
            pass
        try:
            versions_for(cue, "unknown")
            assert False, "expected ValueError"
        except ValueError:
            pass
