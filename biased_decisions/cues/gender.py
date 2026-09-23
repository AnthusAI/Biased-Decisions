"""Gender-swapped counterfactuals: the same bio with the pronouns flipped.

Ported unchanged from Jev-Flywheel's ``jev_flywheel/counterfactual.py`` (function ``swap_gender``
and its supporting tables). The test this module supports is causal rather than correlational. A
gap in recall between men's and women's bios can come from the bios being written differently; a
change in an engine's answer when nothing but the pronouns change cannot. So every held-out item
is asked about twice, once as written and once through ``swap_gender``, and a *flip* is an item
whose verdict differs between the two.

The rule is deliberately small and fixed before any run (see ``studies/PREREGISTERED.md``):
personal pronouns, the reflexives, and a short list of gendered role nouns. Names are handled
separately, by ``biased_decisions.cues.redaction.redact_names`` (see its docstring for why): the
flip rate ``swap_gender`` alone produces is a **lower bound** on an engine's sensitivity to
gender, not an estimate of it, because a first name left in place is itself a gender cue.

The one genuinely ambiguous token is ``her``, which is both the object pronoun (``asked her``)
and the possessive (``her research``). The rule treats it as possessive when the next token is
a plain word and as the object form when it ends the sentence or is followed by punctuation,
a preposition, or a determiner. That is wrong occasionally; each swap records how many
``her`` tokens it resolved so the noise is visible.

The amended rule (below, used by ``swap_gender``) protects medical-content phrases ("women's
health") from the swap and adds Miss/Sir/Madam to the pair table. The published gender-pronons
twins in ``tasks/*/items.jsonl`` were built with this amended rule. ``ORIGINAL_RULE`` reproduces
the *pre-amendment* pair table and disables the protected-phrase carve-out, so a caller that needs
to replay results built before the amendment can select it explicitly; see
``swap_gender(text, rule=ORIGINAL_RULE)``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# The amended pair table (current rule): adds miss/sir/madam beyond the original mr/ms/mrs.
_PAIRS: Dict[str, str] = {
    "he": "she", "she": "he",
    "him": "her", "his": "her",
    "himself": "herself", "herself": "himself",
    "hers": "his",
    "man": "woman", "woman": "man",
    "men": "women", "women": "men",
    "father": "mother", "mother": "father",
    "husband": "wife", "wife": "husband",
    "son": "daughter", "daughter": "son",
    "brother": "sister", "sister": "brother",
    "mr": "ms", "ms": "mr", "mrs": "mr", "miss": "mr",
    "sir": "madam", "madam": "sir",
    "boy": "girl", "girl": "boy",
    "male": "female", "female": "male",
    "gentleman": "lady", "lady": "gentleman",
    "king": "queen", "queen": "king",
    "actor": "actress", "actress": "actor",
    "chairman": "chairwoman", "chairwoman": "chairman",
    "spokesman": "spokeswoman", "spokeswoman": "spokesman",
}

# The pre-amendment pair table: no miss/sir/madam. Reproduced here, verbatim, so a replay of
# twins built before the 2026-09-22 amendment (commit e2225e7 in Jev-Flywheel) can select it.
_ORIGINAL_PAIRS: Dict[str, str] = {
    "he": "she", "she": "he",
    "him": "her", "his": "her",
    "himself": "herself", "herself": "himself",
    "hers": "his",
    "man": "woman", "woman": "man",
    "men": "women", "women": "men",
    "father": "mother", "mother": "father",
    "husband": "wife", "wife": "husband",
    "son": "daughter", "daughter": "son",
    "brother": "sister", "sister": "brother",
    "mr": "ms", "ms": "mr", "mrs": "mr",
    "boy": "girl", "girl": "boy",
    "male": "female", "female": "male",
    "gentleman": "lady", "lady": "gentleman",
    "king": "queen", "queen": "king",
    "actor": "actress", "actress": "actor",
    "chairman": "chairwoman", "chairwoman": "chairman",
    "spokesman": "spokeswoman", "spokeswoman": "spokesman",
}

# Words after ``her`` that mark it as the object pronoun rather than a possessive.
_OBJECT_FOLLOWERS = {
    "a", "an", "the", "this", "that", "these", "those", "to", "for", "with", "at", "in",
    "on", "of", "by", "from", "as", "and", "or", "but", "into", "about", "after", "before",
    "while", "when", "where", "who", "which", "if", "so", "up", "out", "over", "off",
}

_TOKEN = re.compile(r"[A-Za-z]+|[^A-Za-z]+")

# Phrases whose gendered word is medical content, not the person's gender: a gynaecologist's
# bio is about women whatever the doctor's gender. Tokens inside these spans are left alone.
# Only the amended rule applies this carve-out.
_PROTECTED = re.compile(r"\b(?:wo)?men'?s (?:health|medicine|hospital|clinic|center|centre)\b", re.I)


@dataclass(frozen=True)
class SwapRule:
    """Which pair table and which carve-outs a call to ``swap_gender`` uses."""

    pairs: Dict[str, str]
    protect_medical_phrases: bool


AMENDED_RULE = SwapRule(pairs=_PAIRS, protect_medical_phrases=True)
# The rule the published gender-pronouns twins were built with before the 2026-09-22 amendment:
# no Miss/Sir/Madam, and no protected-phrase carve-out. Select it explicitly to replay a record
# built with it.
ORIGINAL_RULE = SwapRule(pairs=_ORIGINAL_PAIRS, protect_medical_phrases=False)

DEFAULT_RULE = AMENDED_RULE


@dataclass(frozen=True)
class Swap:
    text: str
    swapped: int          # how many tokens changed
    her_resolved: int     # how many ambiguous ``her`` tokens the heuristic decided


def _match_case(source: str, replacement: str) -> str:
    if source.isupper() and len(source) > 1:
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def swap_gender(text: str, *, rule: SwapRule = DEFAULT_RULE) -> Swap:
    """Return ``text`` with its gendered pronouns and role nouns flipped.

    The mapping is an involution except for ``her``, whose two readings collapse onto ``him``
    and ``his``; swapping twice is therefore not guaranteed to return the original text.

    ``rule`` defaults to the amended rule (``AMENDED_RULE``, an alias for ``DEFAULT_RULE``); pass
    ``ORIGINAL_RULE`` to reproduce the pre-amendment behaviour used to build the published
    gender-pronouns twins before 2026-09-22.
    """
    tokens: List[str] = _TOKEN.findall(text)
    protected = set()
    if rule.protect_medical_phrases:
        position = 0
        spans = [m.span() for m in _PROTECTED.finditer(text)]
        for i, token in enumerate(tokens):
            if any(start <= position < end for start, end in spans):
                protected.add(i)
            position += len(token)
    out: List[str] = []
    swapped = her_resolved = 0
    words: List[Tuple[int, str]] = [(i, t) for i, t in enumerate(tokens) if t[:1].isalpha()]
    next_word = {i: words[k + 1][1] for k, (i, _) in enumerate(words) if k + 1 < len(words)}
    for i, token in enumerate(tokens):
        lower = token.lower()
        if i in protected:
            out.append(token)
        elif lower == "her":
            her_resolved += 1
            following = next_word.get(i, "").lower()
            ends_clause = i + 1 >= len(tokens) or not tokens[i + 1].isspace() or following == ""
            possessive = not ends_clause and following not in _OBJECT_FOLLOWERS
            out.append(_match_case(token, "his" if possessive else "him"))
            swapped += 1
        elif lower in rule.pairs:
            out.append(_match_case(token, rule.pairs[lower]))
            swapped += 1
        else:
            out.append(token)
    return Swap("".join(out), swapped, her_resolved)
