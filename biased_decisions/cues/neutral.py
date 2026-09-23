"""Neutral-pronoun rewrites: blank and they forms.

Each bio is rewritten to replace gendered language with neutral forms. Two arms:
- blank: pronouns -> "the person", role nouns -> "person"/"people", etc.
- they: pronouns -> they/them/their, with verb agreement (is->are, was->were, etc.)

Reuses gender.py's tokenizer, her-possessive heuristic, protected medical phrases,
and pair table. If any item still contains a gendered token after rewriting,
leftover is set to True and that item is dropped from its arm during build.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from biased_decisions.cues.gender import (
    _PAIRS, _OBJECT_FOLLOWERS, _TOKEN, _PROTECTED, _match_case
)


# The neutral-pronoun pair table: each gendered token -> its neutral form in blank arm.
# In they arm, these are redirected to they/them/their etc.
_NEUTRAL_BLANK: Dict[str, str] = {
    # Pronouns: subject, object, possessive (adjective and pronoun), reflexive
    "he": "the person", "she": "the person",
    "him": "the person", "her": "the person",
    "his": "the person's",
    "himself": "themself", "herself": "themself",
    "hers": "the person's",
    # Role nouns
    "man": "person", "woman": "person",
    "men": "people", "women": "people",
    "father": "parent", "mother": "parent",
    "husband": "spouse", "wife": "spouse",
    "son": "child", "daughter": "child",
    "brother": "sibling", "sister": "sibling",
    "boy": "child", "girl": "child",
    "gentleman": "person", "lady": "person",
    "king": "monarch", "queen": "monarch",
    "actor": "actor", "actress": "actor",
    "chairman": "chair", "chairwoman": "chair",
    "spokesman": "spokesperson", "spokeswoman": "spokesperson",
}

_NEUTRAL_THEY: Dict[str, str] = {
    # Pronouns: subject, object, possessive
    "he": "they", "she": "they",
    "him": "them", "her": "them",
    "his": "their",
    "himself": "themself", "herself": "themself",
    "hers": "theirs",
}

# Verbs that change after "they": irregular and regular rules.
_VERB_IRREGULAR: Dict[str, str] = {
    "is": "are",
    "was": "were",
    "has": "have",
    "does": "do",
    "isn't": "aren't",
    "wasn't": "weren't",
    "doesn't": "don't",
    "hasn't": "haven't",
}

# Adverbs to skip when looking for the verb after a subject pronoun.
# Fixed list per the pre-registration.
_ADVERBS_TO_SKIP = {
    "also", "currently", "now", "still", "often", "always", "never",
    "recently", "previously", "then", "later", "first", "once",
}

# Courtesy titles to remove (with optional trailing period).
_TITLES = {"mr", "ms", "mrs", "miss", "sir", "madam"}

# Role noun and title mappings for blank arm (both feminine and masculine become neutral).
_ROLE_NOUNS_BLANK = {
    # Pronouns
    "he": "the person", "she": "the person",
    "him": "the person", "her": "the person",
    "his": "the person's", "hers": "the person's",
    "himself": "themself", "herself": "themself",
    # Role nouns
    "man": "person", "woman": "person",
    "men": "people", "women": "people",
    "father": "parent", "mother": "parent",
    "husband": "spouse", "wife": "spouse",
    "son": "child", "daughter": "child",
    "brother": "sibling", "sister": "sibling",
    "boy": "child", "girl": "child",
    "gentleman": "person", "lady": "person",
    "king": "monarch", "queen": "monarch",
    "actor": "actor", "actress": "actor",
    "chairman": "chair", "chairwoman": "chair",
    "spokesman": "spokesperson", "spokeswoman": "spokesperson",
}

_ROLE_NOUNS_THEY = {
    # Pronouns
    "he": "they", "she": "they",
    "him": "them", "her": "them",
    "his": "their", "hers": "theirs",
    "himself": "themself", "herself": "themself",
    # Role nouns (same as blank)
    "man": "person", "woman": "person",
    "men": "people", "women": "people",
    "father": "parent", "mother": "parent",
    "husband": "spouse", "wife": "spouse",
    "son": "child", "daughter": "child",
    "brother": "sibling", "sister": "sibling",
    "boy": "child", "girl": "child",
    "gentleman": "person", "lady": "person",
    "king": "monarch", "queen": "monarch",
    "actor": "actor", "actress": "actor",
    "chairman": "chair", "chairwoman": "chair",
    "spokesman": "spokesperson", "spokeswoman": "spokesperson",
}


@dataclass(frozen=True)
class Neutral:
    """Result of neutralizing a bio text."""
    text: str                    # Rewritten text
    changed: int                 # Count of replaced tokens
    verbs_adjusted: int          # Count of verbs re-inflected (they arm only)
    leftover: bool              # True if gendered tokens remain or contraction is ambiguous


def _is_subject_pronoun(token: str) -> bool:
    """Check if token is a subject pronoun (he/she)."""
    return token.lower() in ("he", "she")


def _adjust_verb(verb: str) -> Optional[str]:
    """Return the base form of a verb for they-subject agreement, or None if unchanged."""
    lower = verb.lower()

    # Check irregular verbs first.
    if lower in _VERB_IRREGULAR:
        return _match_case(verb, _VERB_IRREGULAR[lower])

    # Regular verb rules:
    # - ends in "ies" -> "y"
    # - ends in "sses", "shes", "ches", "xes", "zes" -> drop "es"
    # - ends in "oes" -> drop "es"
    # - ends in "s" but not "ss" -> drop "s"
    # - else unchanged (already base form, past tense, or modal)

    if lower.endswith("ies"):
        return _match_case(verb, lower[:-3] + "y")
    elif lower.endswith(("sses", "shes", "ches", "xes", "zes")):
        return _match_case(verb, lower[:-2])
    elif lower.endswith("oes"):
        return _match_case(verb, lower[:-2])
    elif lower.endswith("s") and not lower.endswith("ss"):
        return _match_case(verb, lower[:-1])

    # Unchanged (base form, past tense, modal, or already correct).
    return None


def neutralize(text: str, style: str) -> Neutral:
    """Rewrite text with neutral pronouns: 'blank' or 'they' style.

    Args:
        text: The bio text to rewrite.
        style: Either "blank" (-> "the person") or "they" (-> they/them/their).

    Returns:
        Neutral: Rewritten text and metadata (changed count, verbs_adjusted, leftover).
    """
    if style not in ("blank", "they"):
        raise ValueError(f"style must be 'blank' or 'they', got {style!r}")

    # Tokenize the text using gender.py's tokenizer.
    tokens: list[str] = _TOKEN.findall(text)

    # Identify protected spans (medical phrases).
    protected = set()
    position = 0
    spans = [m.span() for m in _PROTECTED.finditer(text)]
    for i, token in enumerate(tokens):
        if any(start <= position < end for start, end in spans):
            protected.add(i)
        position += len(token)

    # Build word index for her-possessive-vs-object heuristic and for verb lookups.
    words: list[Tuple[int, str]] = [(i, t) for i, t in enumerate(tokens) if t[:1].isalpha()]
    next_word = {i: words[k + 1][1] for k, (i, _) in enumerate(words) if k + 1 < len(words)}

    # Output tokens, change count, and verb adjustments.
    out: list[str] = []
    changed = 0
    verbs_adjusted = 0
    subject_pronouns_seen = False  # Track if we've seen a subject pronoun to adjust the next verb.
    skip_count = 0  # Track how many tokens to skip (for ambiguous contractions).
    found_ambiguous_contraction = False  # Track if we found an ambiguous contraction.

    for idx, token in enumerate(tokens):
        # Skip tokens marked for skipping (apostrophe and s after she/he).
        if skip_count > 0:
            skip_count -= 1
            continue

        lower = token.lower()

        # Skip protected phrases.
        if idx in protected:
            out.append(token)
            continue

        # Handle titles (remove with following space).
        if lower in _TITLES or (lower.endswith('.') and lower[:-1] in _TITLES):
            out.append(token)
            continue

        # Handle her (ambiguous: object vs. possessive).
        if lower == "her":
            following = next_word.get(idx, "").lower()
            ends_clause = idx + 1 >= len(tokens) or not tokens[idx + 1][0].isspace() or following == ""
            is_possessive = not ends_clause and following not in _OBJECT_FOLLOWERS

            if style == "blank":
                replacement = "the person's" if is_possessive else "the person"
            else:  # they
                replacement = "their" if is_possessive else "them"

            out.append(_match_case(token, replacement))
            changed += 1
            subject_pronouns_seen = False
            continue

        # Handle subject pronouns (he/she).
        # Check for ambiguous contractions (she's/he's) in they arm BEFORE converting pronoun.
        if _is_subject_pronoun(token) and style == "they":
            # Look ahead: if next two tokens are apostrophe + s, this is ambiguous.
            if (idx + 2 < len(tokens) and tokens[idx + 1].lower() == "'" and
                tokens[idx + 2].lower() == "s"):
                # Leave pronoun unchanged (will output as-is).
                out.append(token)
                skip_count = 2  # Skip apostrophe and s in next iterations.
                found_ambiguous_contraction = True  # Mark as ambiguous.
                subject_pronouns_seen = False
                # For now, just continue to output the apostrophe and s normally.
                continue

        # Convert subject pronouns.
        if _is_subject_pronoun(token):
            if style == "blank":
                out.append(_match_case(token, "the person"))
            else:  # they
                out.append(_match_case(token, "they"))
            changed += 1
            subject_pronouns_seen = True
            continue

        # Handle other pronouns and role nouns from pair table.
        if lower in _PAIRS:
            mapping = _ROLE_NOUNS_BLANK if style == "blank" else _ROLE_NOUNS_THEY
            if lower in mapping:
                replacement = mapping[lower]
                out.append(_match_case(token, replacement))
                changed += 1
                subject_pronouns_seen = False
                continue

        # Verb adjustment (they arm only, after a subject pronoun).
        if style == "they" and subject_pronouns_seen and token[:1].isalpha():
            # Check if this is an adverb to skip.
            if lower not in _ADVERBS_TO_SKIP:
                # This is the verb to adjust.
                adjusted = _adjust_verb(token)
                if adjusted and adjusted.lower() != token.lower():
                    out.append(adjusted)
                    verbs_adjusted += 1
                    subject_pronouns_seen = False
                    continue

        # Handle comma and "and" (reset subject_pronouns_seen).
        if lower in ("and", ","):
            subject_pronouns_seen = False

        # Not a special token, keep as-is.
        out.append(token)

    # Join the output.
    result_text = "".join(out)

    # Post-process: remove titles and following space.
    # Match Mr, Mr., Mrs, Mrs., Ms, Ms., Miss, Miss., Sir, Sir., Madam, Madam.
    # followed by optional dots and whitespace.
    for title in _TITLES:
        # Match title with optional dots (match any number of dots), then space(s).
        # Pattern: \b + title + optional dots + \s+
        title_pattern = re.compile(r"\b" + re.escape(title) + r"\.* +", re.I)
        result_text = title_pattern.sub("", result_text)

    # Remove male/female gender adjectives followed by space.
    result_text = re.sub(r"\b(male|female)\s+", "", result_text, flags=re.I)

    # Check for ambiguous contractions in they arm.
    leftover = found_ambiguous_contraction

    # Neutral outputs that are not gendered (safe to appear in output).
    neutral_outputs = {
        "the person", "they", "them", "their", "theirs", "themself",
        "person", "people", "parent", "spouse", "child", "sibling",
        "monarch", "chair", "spokesperson", "actor",
    }

    # Check if any gendered token still appears in the output.
    # Exclude false positives: "ms" in "500ms" (milliseconds), "mr" in email addresses.
    # Re-tokenize the result to check.
    result_tokens = _TOKEN.findall(result_text)

    for i, token in enumerate(result_tokens):
        lower = token.lower()
        # Flag as leftover if:
        # 1. It's a gendered token from _PAIRS (a KEY, not a value)
        # 2. It's not a known neutral output
        if lower in _PAIRS and lower not in neutral_outputs:
            # Check for false positives:
            # - "ms" in milliseconds (e.g., "500ms"): check if previous token is a digit
            # - "mr" in email addresses (e.g., "mr_shirazi@..."): check if surrounded by email-like chars
            if lower == "ms" and i > 0:
                prev_token = result_tokens[i - 1].lower() if i > 0 else ""
                next_token = result_tokens[i + 1].lower() if i + 1 < len(result_tokens) else ""
                # If preceded by a digit, it's likely "milliseconds"
                if prev_token and prev_token[-1].isdigit():
                    continue

            if lower == "mr" and i + 1 < len(result_tokens):
                # If followed by underscore, it's likely part of email (e.g., "mr_...")
                next_token = result_tokens[i + 1]
                if next_token == "_" or next_token.startswith("_"):
                    continue

            leftover = True
            break

    return Neutral(text=result_text, changed=changed, verbs_adjusted=verbs_adjusted, leftover=leftover)
