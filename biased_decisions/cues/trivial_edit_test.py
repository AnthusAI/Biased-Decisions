"""Tests for the trivial-edit floor cue."""
import pytest
from biased_decisions.cues.trivial_edit import swap_trivial


def test_determinism():
    """Building twice gives identical output."""
    bio = "He has practiced medicine and received awards. He also specializes in surgery."
    result1 = swap_trivial(bio)
    result2 = swap_trivial(bio)
    assert result1.text == result2.text
    assert result1.swapped == result2.swapped


def test_no_protected_words_touched():
    """Pronouns, gendered words, and occupations are never replaced."""
    # Test with pronouns
    bio1 = "He works as a surgeon. She performs surgery. They have research."
    result1 = swap_trivial(bio1)
    # "works" should be replaced (non-pronoun usage), but "He", "She", "They" should not
    assert "He" in result1.text
    assert "She" in result1.text
    assert "They" in result1.text
    # Occupations should not be touched
    assert "surgeon" in result1.text
    assert "surgery" in result1.text


def test_case_preservation():
    """Uppercase is preserved in replacements."""
    bio = "Also, received and has been trained."
    result = swap_trivial(bio)
    # "Also" should become "As well" (with capital A)
    assert "As well" in result.text
    # All three should be swapped
    assert result.swapped == 3


def test_coverage_fixture():
    """Test coverage on a fixture of 10 bios."""
    fixture = [
        "He has received awards and also practices medicine.",
        "She works as a physician and has published research.",
        "He graduated from university and currently works in Boston.",
        "She specializes in surgery and provides excellent care.",
        "He has been trained by experienced surgeons.",
        "She earned her degree and was awarded recognition.",
        "He located practice in a new hospital.",
        "She is affiliated with medical schools and performs procedures.",
        "He has received fellowship training and projects include research.",
        "She graduated from medical school and works in surgery.",
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
    # Average should be around 2+ tokens
    assert total_swaps / len(fixture) >= 1.5


def test_token_budget():
    """On average, ~2-3 tokens are swapped per bio that has any swaps."""
    bio1 = "He has received and currently works and also practices medicine."
    result1 = swap_trivial(bio1)
    assert result1.swapped == 3  # First 3 matches

    bio2 = "She received awards."
    result2 = swap_trivial(bio2)
    assert result2.swapped == 1

    bio3 = "Has received completed earned and performed work."
    result3 = swap_trivial(bio3)
    assert result3.swapped == 3  # Stops at 3


def test_idempotence_within_limit():
    """The three-replacement limit is enforced."""
    bio = "has has has has received received"
    result = swap_trivial(bio)
    # First 3 "has" should be replaced, but no more
    count_possesses = result.text.count("possesses")
    assert count_possesses == 3
    # Last "has" should remain unchanged
    assert "has" in result.text


def test_empty_and_edge_cases():
    """Handle edge cases: empty, no matches, all protected."""
    assert swap_trivial("").text == ""
    assert swap_trivial("").swapped == 0

    no_match = "He is a physician."
    result_no_match = swap_trivial(no_match)
    assert result_no_match.text == no_match
    assert result_no_match.swapped == 0

    protected_only = "He she him her his"
    result_protected = swap_trivial(protected_only)
    assert result_protected.text == protected_only
    assert result_protected.swapped == 0
