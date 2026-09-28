"""Tests for the trivial-edit floor cue."""
import pytest
from biased_decisions.cues.trivial_edit import swap_trivial


def test_determinism():
    """Building twice gives identical output."""
    bio = "She received training and was located at a hospital. She performed work and assisted patients."
    result1 = swap_trivial(bio)
    result2 = swap_trivial(bio)
    assert result1.text == result2.text
    assert result1.swapped == result2.swapped


def test_no_protected_words_touched():
    """Protected role, credential, field, and action words never change.

    The floor must never touch: practice, clinic, fellowship, residency, medicine, degree,
    board, research, design, work, project, specializes, trained, experience, has, graduated,
    completed, works, serves, award, fellow, medicine, includes, completing, new.
    """
    bio = (
        "She has a degree in medicine and fellowship in surgery. She works at a clinic and "
        "works on research projects. She specializes in design. She has completed training. "
        "She serves as board member. She has new ideas and award experience. She includes "
        "patients and has graduate degree."
    )
    result = swap_trivial(bio)

    # These words should never appear changed
    protected = [
        "practice", "clinic", "fellowship", "residency", "medicine", "degree", "board",
        "research", "design", "work", "project", "specializes", "trained", "experience",
        "has", "graduated", "completed", "works", "serves", "award", "fellow", "includes"
    ]

    # Only check words that actually appear in the bio
    protected_in_bio = [
        "clinic", "fellowship", "medicine", "degree", "board",
        "research", "design", "work", "project", "specializes",
        "completed", "works", "serves", "award", "includes"
    ]

    for word in protected_in_bio:
        # Verify word still appears in result unchanged
        assert word.lower() in result.text.lower(), f"protected word {word!r} was changed"


def test_case_preservation():
    """Uppercase is preserved in replacements."""
    bio = "Also, she received awards Currently affiliated."
    result = swap_trivial(bio)
    # "Also" should become "As well" (with capital A)
    assert "As well" in result.text
    # "received" should become "obtained"
    assert "obtained" in result.text
    # "Currently" should become "At present" (capital A)
    assert "At present" in result.text


def test_multi_word_phrases():
    """Multi-word phrases like 'affiliated with' are matched and replaced."""
    bio = "She is affiliated with the hospital and worked prior to 2015."
    result = swap_trivial(bio)
    assert "associated with" in result.text
    assert "before" in result.text
    assert result.swapped == 2


def test_case_insensitive_matching():
    """Matching is case-insensitive but replacement preserves case."""
    bio = "ALSO here is CURRENTLY LOCATED there."
    result = swap_trivial(bio)
    # Should match "ALSO" and "CURRENTLY" (case-insensitive)
    # and preserve case in output
    assert "AS WELL" in result.text
    assert "AT PRESENT" in result.text
    assert "SITUATED" in result.text
    assert result.swapped == 3


def test_three_replacement_limit():
    """At most 3 replacements are applied per bio."""
    bio = ("received a degree, earned recognition, assisted patients, performed work, "
           "provided care, and also was located here.")
    result = swap_trivial(bio)
    assert result.swapped == 3  # Stops at 3, doesn't replace all 6


def test_whole_word_match_only():
    """Only whole words/phrases are matched, not substrings."""
    bio = "The assistant was established in addition to additional facilities."
    result = swap_trivial(bio)
    # "established" -> "founded", "in addition" -> "additionally"
    # But "assistant" should not match "assisted", and "additional" is not in the list
    assert "assistant" in result.text  # should not change
    assert "founded" in result.text
    assert "additionally" in result.text
    assert result.swapped == 2


def test_coverage_fixture():
    """Test coverage on a fixture of realistic bios."""
    fixture = [
        "He received awards and was located in Boston.",
        "She earned credentials and is currently affiliated with hospitals.",
        "He was established as a physician prior to 2010.",
        "She performed numerous procedures in addition to research.",
        "He provided care and assisted patients with various conditions.",
        "She received funding and earned recognition.",
        "He was located at multiple hospitals and provided services.",
        "She is affiliated with schools and performed studies.",
        "He received grants and assisted researchers.",
        "She was established there and provides support."
    ]

    swapped_count = 0
    total_swaps = 0

    for bio in fixture:
        result = swap_trivial(bio)
        if result.swapped > 0:
            swapped_count += 1
            total_swaps += result.swapped

    # Should cover most of the fixture
    assert swapped_count >= 8  # At least 8 out of 10
    # Average should be around 1.5+ per bio in fixture
    assert total_swaps / len(fixture) >= 1.5


def test_empty_and_edge_cases():
    """Handle edge cases: empty, no matches."""
    assert swap_trivial("").text == ""
    assert swap_trivial("").swapped == 0

    # Bio with no matching words
    no_match = "He is a physician and practices medicine."
    result_no_match = swap_trivial(no_match)
    assert result_no_match.text == no_match
    assert result_no_match.swapped == 0


def test_no_chaining():
    """Replacements do not chain over each other."""
    # If we replaced "located" -> "situated" in a single pass, and then
    # tried to match "situated" against the pattern for "located", that would be chaining.
    # Our implementation processes all replacements in reverse order from the original
    # text only, so this shouldn't happen.
    bio = "She was located and situated there. He located many sites and was established."
    result = swap_trivial(bio)
    # "located" appears twice, "established" once = 3 max replacements
    # "situated" is not in our pair list, so it shouldn't change
    assert "situated" in result.text  # should remain unchanged (not in pair list)
    assert result.swapped == 3  # 2x "located" + 1x "established"
