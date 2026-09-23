"""Feature: gender-swapped counterfactuals.

Ported from Jev-Flywheel's ``jev_flywheel/counterfactual_test.py`` (the ``swap_gender`` half;
the ``redact_names`` half lives in ``redaction_test.py``). The swap rule is fixed before the
bias study runs, so these specs pin its behaviour: what it changes, what it leaves alone, and
how it resolves the ambiguous ``her``.
"""
from biased_decisions.cues.gender import ORIGINAL_RULE, swap_gender


def test_pronouns_and_reflexives_flip_both_ways():
    assert swap_gender("He said he did it himself.").text == "She said she did it herself."
    assert swap_gender("She said she did it herself.").text == "He said he did it himself."


def test_case_is_preserved():
    assert swap_gender("HE and He and he").text == "SHE and She and she"


def test_possessive_her_becomes_his():
    swap = swap_gender("Her research on her patients won her an award.")
    assert swap.text == "His research on his patients won him an award."
    assert swap.her_resolved == 3


def test_object_her_before_punctuation_or_preposition_becomes_him():
    assert swap_gender("They asked her.").text == "They asked him."
    assert swap_gender("They asked her to speak.").text == "They asked him to speak."
    assert swap_gender("Working with her, the team grew.").text == "Working with him, the team grew."


def test_his_and_him_collapse_onto_her():
    assert swap_gender("His work made him famous.").text == "Her work made her famous."


def test_role_nouns_and_titles_flip():
    assert swap_gender("Mr. Smith, a father of two, is a spokesman.").text == \
        "Ms. Smith, a mother of two, is a spokeswoman."


def test_names_and_everything_else_are_untouched():
    text = "Emanuel launched USM in 2009; the site is a one-stop shop for agencies."
    swap = swap_gender(text)
    assert swap.text == text
    assert swap.swapped == 0


def test_substrings_of_words_are_not_swapped():
    # "the", "hero", "shell", "themes", "history" all contain pronoun spellings.
    text = "The hero in the shell wrote themes about history."
    assert swap_gender(text).text == text


def test_medical_content_phrases_are_not_swapped():
    swap = swap_gender("She directs the Women's Health clinic and her men's health research.")
    assert swap.text == "He directs the Women's Health clinic and his men's health research."


def test_miss_sir_and_madam_are_swapped():
    assert swap_gender("Miss Jones and Sir John").text == "Mr Jones and Madam John"


def test_swap_count_is_reported():
    assert swap_gender("He and his wife").swapped == 3


def test_original_rule_has_no_miss_sir_madam_and_no_medical_protection():
    # The pre-amendment rule the published gender-pronouns twins were built with.
    assert swap_gender("Miss Jones", rule=ORIGINAL_RULE).text == "Miss Jones"
    swap = swap_gender("She directs the Women's Health clinic.", rule=ORIGINAL_RULE)
    assert swap.text == "He directs the Men's Health clinic."
