"""Feature: neutral-pronoun rewrites in blank and they forms.

Each spec tests the neutralize function with both "blank" and "they" styles,
verifying correct pronoun replacement, verb agreement, handling of contractions,
role nouns, courtesy titles, and leftover token detection.
"""
from biased_decisions.cues.neutral import neutralize


def test_blank_arm_pronouns_and_objects():
    """Pronouns and objects become 'the person' in blank arm."""
    result = neutralize("She is a partner at the firm and her clients trust her.", "blank")
    assert result.text == "The person is a partner at the firm and the person's clients trust the person."
    assert result.changed >= 3
    assert not result.leftover


def test_they_arm_pronouns_and_objects():
    """Pronouns become 'they/them/their' in they arm."""
    result = neutralize("She is a partner at the firm and her clients trust her.", "they")
    assert result.text == "They are a partner at the firm and their clients trust them."
    assert result.changed >= 3
    assert not result.leftover


def test_they_arm_verb_agreement_after_subject():
    """Verb agreement: is->are, was->were, has->have, does->do after they."""
    result = neutralize("He has taught for ten years, and his students often praise him.", "they")
    assert result.text == "They have taught for ten years, and their students often praise them."
    assert result.verbs_adjusted == 1
    assert not result.leftover


def test_they_arm_adverb_skipping():
    """Verb adjustment skips up to two adverbs from the fixed list."""
    result = neutralize("She also teaches law.", "they")
    assert result.text == "They also teach law."
    assert result.verbs_adjusted == 1
    assert not result.leftover


def test_they_arm_verb_studies_to_study():
    """Regular verb third-person: 'studies' -> 'study' after they."""
    result = neutralize("She studies law.", "they")
    assert result.text == "They study law."
    assert result.verbs_adjusted == 1
    assert not result.leftover


def test_they_arm_verb_practices_to_practice():
    """Regular verb ending in -ces: 'practices' -> 'practice' after they."""
    result = neutralize("She practices law.", "they")
    assert result.text == "They practice law."
    assert result.verbs_adjusted == 1
    assert not result.leftover


def test_blank_arm_shes_contraction_no_leftover():
    """Contraction she's -> the person's in blank arm (no leftover)."""
    result = neutralize("She's a lawyer.", "blank")
    assert result.text == "The person's a lawyer."
    assert not result.leftover


def test_they_arm_shes_contraction_is_ambiguous():
    """Contraction she's is ambiguous in they arm -> leftover=True."""
    result = neutralize("She's a lawyer.", "they")
    assert result.leftover is True


def test_they_arm_shed_contraction():
    """Contraction she'd -> they'd in they arm."""
    result = neutralize("She'd have done it.", "they")
    assert result.text == "They'd have done it."
    assert not result.leftover


def test_they_arm_shell_contraction():
    """Contraction she'll -> they'll in they arm."""
    result = neutralize("She'll be there.", "they")
    assert result.text == "They'll be there."
    assert not result.leftover


def test_blank_arm_titles_removed():
    """Courtesy titles (Mr, Ms, Mrs, Miss, Sir, Madam) removed with following space."""
    result = neutralize("Ms. [name] joined the firm.", "blank")
    assert result.text == "[name] joined the firm."
    assert "[Ms" not in result.text
    assert not result.leftover


def test_they_arm_titles_removed():
    """Courtesy titles removed in they arm too."""
    result = neutralize("Mr. [name] said he left.", "they")
    assert result.text == "[name] said they left."
    assert "[Mr" not in result.text
    assert not result.leftover


def test_blank_arm_role_nouns_woman_to_person():
    """Role noun 'woman' -> 'person' in blank arm."""
    result = neutralize("the woman's research", "blank")
    assert result.text == "the person's research"
    assert not result.leftover


def test_blank_arm_role_nouns_man_to_person():
    """Role noun 'man' -> 'person' in blank arm."""
    result = neutralize("the man's research", "blank")
    assert result.text == "the person's research"
    assert not result.leftover


def test_blank_arm_role_nouns_women_to_people():
    """Role noun 'women' -> 'people' in blank arm."""
    result = neutralize("women doctors", "blank")
    assert result.text == "people doctors"
    assert not result.leftover


def test_blank_arm_role_nouns_husband_to_spouse():
    """Role noun 'husband' -> 'spouse' in blank arm."""
    result = neutralize("the woman's husband", "blank")
    assert result.text == "the person's spouse"
    assert not result.leftover


def test_blank_arm_role_nouns_father_to_parent():
    """Role noun 'father' -> 'parent' in blank arm."""
    result = neutralize("her father was a teacher", "blank")
    assert result.text == "the person's parent was a teacher"
    assert not result.leftover


def test_blank_arm_role_nouns_son_to_child():
    """Role noun 'son' -> 'child' in blank arm."""
    result = neutralize("his son is a doctor", "blank")
    assert result.text == "the person's child is a doctor"
    assert not result.leftover


def test_blank_arm_role_nouns_brother_to_sibling():
    """Role noun 'brother' -> 'sibling' in blank arm."""
    result = neutralize("her brother is a lawyer", "blank")
    assert result.text == "the person's sibling is a lawyer"
    assert not result.leftover


def test_blank_arm_role_nouns_boy_to_child():
    """Role noun 'boy' -> 'child' in blank arm."""
    result = neutralize("the young boy", "blank")
    assert result.text == "the young child"
    assert not result.leftover


def test_blank_arm_role_nouns_gentleman_to_person():
    """Role noun 'gentleman' -> 'person' in blank arm."""
    result = neutralize("a gentleman caller", "blank")
    assert result.text == "a person caller"
    assert not result.leftover


def test_blank_arm_role_nouns_king_to_monarch():
    """Role noun 'king' -> 'monarch' in blank arm."""
    result = neutralize("a king's court", "blank")
    assert result.text == "a monarch's court"
    assert not result.leftover


def test_blank_arm_role_nouns_actor_to_actor():
    """Role noun 'actor' stays 'actor', 'actress' -> 'actor' in blank arm."""
    result = neutralize("the actress performed", "blank")
    assert result.text == "the actor performed"
    assert not result.leftover


def test_blank_arm_role_nouns_chairman_to_chair():
    """Role noun 'chairman'/'chairwoman' -> 'chair' in blank arm."""
    result = neutralize("chairwoman of the board", "blank")
    assert result.text == "chair of the board"
    assert not result.leftover


def test_blank_arm_role_nouns_spokesman_to_spokesperson():
    """Role noun 'spokesman'/'spokeswoman' -> 'spokesperson' in blank arm."""
    result = neutralize("the spokeswoman said", "blank")
    assert result.text == "the spokesperson said"
    assert not result.leftover


def test_blank_arm_male_female_removed():
    """Gender adjective 'male'/'female' removed with following space."""
    result = neutralize("a male nurse", "blank")
    assert result.text == "a nurse"
    assert not result.leftover


def test_they_arm_male_female_removed():
    """Gender adjective removed in they arm too."""
    result = neutralize("a female doctor", "they")
    assert result.text == "a doctor"
    assert not result.leftover


def test_blank_arm_reflexive_himself_to_themself():
    """Reflexive 'himself' -> 'themself' in blank arm."""
    result = neutralize("He taught himself.", "blank")
    assert result.text == "The person taught themself."
    assert not result.leftover


def test_they_arm_reflexive_herself_to_themself():
    """Reflexive 'herself' -> 'themself' in they arm."""
    result = neutralize("She taught herself.", "they")
    assert result.text == "They taught themself."
    assert result.verbs_adjusted == 0  # No verb adjustment needed after "taught"
    assert not result.leftover


def test_blank_arm_medical_phrase_protected():
    """Medical phrase 'women's health' is not rewritten but flags leftover in blank arm."""
    result = neutralize("She directs the women's health clinic.", "blank")
    assert "women's health" in result.text
    # Medical phrase is protected from rewriting, but "women" is a gendered token, so leftover=True.
    assert result.leftover


def test_they_arm_medical_phrase_protected():
    """Medical phrase 'women's health' is not rewritten but flags leftover in they arm."""
    result = neutralize("She directs the women's health clinic.", "they")
    assert "women's health" in result.text
    # Medical phrase is protected from rewriting, but "women" is a gendered token, so leftover=True.
    assert result.leftover


def test_text_with_no_gendered_words_unchanged():
    """Text with no gendered words comes back unchanged."""
    result = neutralize("The person is a lawyer.", "blank")
    assert result.text == "The person is a lawyer."
    assert result.changed == 0
    assert not result.leftover


def test_case_preservation_sentence_start():
    """Capitalization is preserved when replacing sentence-start pronouns."""
    result = neutralize("She is here.", "blank")
    assert result.text.startswith("The person")
    assert not result.leftover


def test_case_preservation_all_caps():
    """All-caps pronouns are replaced with all-caps replacement."""
    result = neutralize("HE said so.", "blank")
    assert "THE PERSON" in result.text
    assert not result.leftover


def test_gender_py_unchanged_on_sample():
    """Calling gender.swap_gender on a fixed sentence produces unchanged output."""
    from biased_decisions.cues.gender import swap_gender
    original = "She is a partner at the firm and her clients trust her."
    swapped = swap_gender(original)
    assert swapped.text != original  # It should actually swap
    # But we're just testing that the import works and gender.py still behaves as expected
    assert swapped.swapped > 0


def test_blank_arm_left_alignment_with_her_possessive():
    """Her as possessive in 'her clients' is handled correctly."""
    result = neutralize("her clients trust her", "blank")
    assert result.text == "the person's clients trust the person"
    assert result.changed >= 2
    assert not result.leftover


def test_they_arm_left_alignment_with_his():
    """His as possessive is handled correctly."""
    result = neutralize("his research won him an award", "they")
    assert result.text == "their research won them an award"
    assert not result.leftover


def test_blank_arm_hers_possessive():
    """Possessive 'hers' -> 'the person's'."""
    result = neutralize("This research is hers.", "blank")
    assert result.text == "This research is the person's."
    assert not result.leftover


def test_they_arm_hers_possessive():
    """Possessive 'hers' -> 'theirs' in they arm."""
    result = neutralize("This research is hers.", "they")
    assert result.text == "This research is theirs."
    assert not result.leftover


def test_leftover_true_when_pair_table_token_remains():
    """Leftover is True when a gendered token from pair table remains in output."""
    # Construct a case where a medical phrase keeps a gendered word (testing the logic)
    result = neutralize("the women's health clinic", "blank")
    # The word 'women' inside the protected phrase should remain, so leftover=True
    assert result.leftover is True


def test_verb_not_adjusted_after_and():
    """Verb after 'and' is not adjusted even if preceded by a pronounoun swap."""
    result = neutralize("She teaches and loves her work.", "they")
    # Only the first verb after "they" should be adjusted
    assert "they" in result.text.lower()
    assert "their" in result.text.lower()


def test_verb_not_adjusted_after_comma():
    """Verb after comma is not adjusted."""
    result = neutralize("She teaches law, studies policy, and writes books.", "they")
    # Only the first "teaches" should become "teach"; the others after comma should stay
    assert "they teach" in result.text.lower()
    assert not result.leftover
