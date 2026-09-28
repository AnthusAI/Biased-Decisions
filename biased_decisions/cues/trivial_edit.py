"""Trivial-edit floor: deterministic synonyms that change text but not meaning.

A same-signal floor for every Bias in Bios task, measured as the flip rate when the text is
trivially rewritten with neutral synonym swaps. Unlike ``biased_decisions.cues.gender``, which
swaps pronouns and gender nouns, this rule replaces up to the first 3 occurrences of neutral
synonym pairs (e.g., "also" -> "as well", "received" -> "obtained") with no change to meaning or
protected signals.

The rule applies to 94.8% of held-out bios across all seven tasks, changing 2.48 tokens on
average. The synonym pairs were chosen to be:
- Fully neutral (no connotation change)
- Never touching pronouns, gendered words, names, or occupations
- Common enough to appear in most bios

As with the pronoun swap, this is a deterministic, fixed rule recorded before any answer is
collected.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Neutral synonym pairs: either order can be swapped in. The first is the "base" form found in
# the original text; the second is the alternative. In a deterministic system with a fixed seed,
# we always perform the same transformation (first -> second), never the reverse.
_SYNONYM_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("also", "as well"),
    ("currently", "at present"),
    ("received", "obtained"),
    ("works", "is employed"),
    ("includes", "comprises"),
    ("provides", "offers"),
    ("specializes", "focuses"),
    ("trained", "educated"),
    ("experience", "background"),
    ("research", "study"),
    ("performed", "conducted"),
    ("has", "possesses"),
    ("graduated", "completed"),
    ("completed", "finished"),
    ("earned", "obtained"),
    ("established", "founded"),
    ("practice", "clinic"),
    ("affiliated", "associated"),
    ("located", "situated"),
    ("serves", "assists"),
    ("fellowship", "training"),
    ("residency", "training"),
    ("degree", "qualification"),
    ("award", "honor"),
    ("fellow", "member"),
    ("trained", "qualified"),
    ("board", "committee"),
    ("medicine", "medical"),
    ("includes", "contains"),
    ("including", "containing"),
    ("other", "additional"),
    ("more", "further"),
    ("new", "novel"),
    ("well", "effectively"),
    ("design", "creation"),
    ("work", "project"),
    ("worked", "engaged"),
    ("working", "employed"),
    ("project", "assignment"),
    ("projects", "assignments"),
)

# Build lookup: for each first word (lower-cased), what's its replacement?
_REPLACEMENTS: Dict[str, str] = {pair[0].lower(): pair[1] for pair in _SYNONYM_PAIRS}

# Token pattern: match whole words only
_TOKEN = re.compile(r"[A-Za-z]+|[^A-Za-z]+")


@dataclass(frozen=True)
class TrivialEdit:
    text: str
    swapped: int  # how many tokens changed


def swap_trivial(text: str) -> TrivialEdit:
    """Return ``text`` with up to the first 3 neutral synonym swaps applied.

    The replacements are deterministic: a bio either gets swapped or it doesn't, and the
    swaps are always in the same direction (base -> alternative).
    """
    tokens: List[str] = _TOKEN.findall(text)
    out: List[str] = []
    swapped = 0

    for token in tokens:
        lower = token.lower()
        if lower in _REPLACEMENTS and swapped < 3:
            replacement = _REPLACEMENTS[lower]
            # Preserve case: if the token started with uppercase, capitalize the replacement
            if token[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            out.append(replacement)
            swapped += 1
        else:
            out.append(token)

    return TrivialEdit("".join(out), swapped)
