"""Trivial-edit floor: deterministic meaning-preserving rewrites.

A same-signal floor for every Bias in Bios task, measured as the flip rate when the text is
trivially rewritten with neutral synonym swaps. This rule replaces up to the first 3 occurrences
of meaning-preserving synonym pairs (e.g., "also" -> "as well", "located" -> "situated",
"affiliated with" -> "associated with") in a deterministic left-to-right pass over the original
text, never over already-replaced text.

The pairs are strictly neutral: they never touch pronouns, gendered words, names, roles,
credentials (fellowship, residency, degree, board), institutions, fields (medicine, research,
design), or actions that define the person (works, works on, works at, serves, serves as, etc.).
They address only timing, quantity, modality, and location.

The floor flip rate is computed and reported over only the bios the rule touched, and coverage
(percentage of bios touched) is published alongside it.

As with the pronoun swap, this is a deterministic, fixed rule recorded before any answer is
collected.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

# Meaning-preserving synonym pairs (15 total): timing, quantity, modality, location.
# Replacements are applied left-to-right over the original text, first 3 matches only, in one
# pass (never over already-replaced text). All whole-word/phrase matches; case-preserving.
_SYNONYM_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("also", "as well"),
    ("currently", "at present"),
    ("received", "obtained"),
    ("earned", "obtained"),
    ("located", "situated"),
    ("affiliated with", "associated with"),
    ("established", "founded"),
    ("other", "additional"),
    ("performed", "conducted"),
    ("provides", "offers"),
    ("prior to", "before"),
    ("in addition", "additionally"),
    ("numerous", "many"),
    ("various", "several"),
    ("assisted", "helped"),
)

# Build regex patterns for whole-word matching (handles both single and multi-word phrases)
# Pattern: each (base, alternative) pair becomes a regex matching the base as whole words/phrases
_PATTERNS: List[Tuple[re.Pattern, str, str]] = []
for base, alternative in _SYNONYM_PAIRS:
    # Escape special regex chars and build a pattern matching the phrase at word boundaries
    escaped = re.escape(base)
    # Word boundary: start of string or non-word char, end of string or non-word char
    pattern = re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)
    _PATTERNS.append((pattern, base, alternative))


def _match_case_phrase(original: str, replacement: str) -> str:
    """Apply case pattern from original phrase to replacement phrase.

    If original starts with capital, capitalize the replacement.
    If original is all-caps, uppercase the replacement.
    """
    if not original or not replacement:
        return replacement

    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


@dataclass(frozen=True)
class TrivialEdit:
    text: str
    swapped: int  # how many phrase tokens changed


def swap_trivial(text: str) -> TrivialEdit:
    """Return ``text`` with up to the first 3 meaning-preserving synonym swaps applied.

    Replacements are made in a single left-to-right pass over the original text (never over
    already-replaced text). This ensures no chaining and deterministic behavior. Case is
    preserved from the original text.
    """
    result = text
    swapped = 0

    for pattern, base, alternative in _PATTERNS:
        if swapped >= 3:
            break

        # Find all matches in the current result
        matches = list(pattern.finditer(result))

        # Process matches in reverse order so positions don't shift as we replace
        for match in reversed(matches):
            if swapped >= 3:
                break

            matched_text = match.group()
            # Preserve case from the matched text
            replacement = _match_case_phrase(matched_text, alternative)
            result = result[:match.start()] + replacement + result[match.end():]
            swapped += 1

    return TrivialEdit(result, swapped)
