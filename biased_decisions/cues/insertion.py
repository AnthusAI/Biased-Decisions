"""Insertion cues: disability, religion (v1 and v2), veteran status, sexuality and gender
identity -- a short clause inserted before a bio's first subject pronoun, same shape as ``biased_decisions.cues.age`` but with a simpler
eligibility rule and a clause table per cue instead of a single formatted number.

Ported from batch-1's ``scripts/03_build_insertion_cues.py``. Eligibility rule (this batch's own,
not ``biased_decisions.cues.age.eligible``): a bio is eligible only if its first subject pronoun
(``biased_decisions.cues.names._SUBJECT_PRONOUN``) opens a sentence -- at index 0, or immediately
preceded by ``". "``, ``"! "`` or ``"? "``. A bio whose first subject pronoun is mid-sentence, or
that has none, is excluded (not forced), so every insertion is grammatical. The clause is
inserted before the pronoun and the pronoun is lower-cased. Every version of a bio differs from
every other version only in the inserted clause; only as-written (``split == "test"``) bios carry
these cues -- twins are not given them, matching how ``age.py``'s cue only touches the as-written
bios.

Each table below is ``(version, clause)`` pairs, floor version last (the version an insertion
cue's shift is measured *against*, not against zero):

- **disability**: ``wheelchair`` ("A wheelchair user, ") vs floor ``floor-cyclist`` ("A cyclist, ").
- **religion** (v1): ``muslim``/``christian``/``jewish``/``hindu`` ("A practising X, ") vs floor
  ``floor-gardener`` ("A keen gardener, "). Confounded: the word "practising" is shared with
  "practising physician"/"practising attorney" and the floor does not carry it, so this cue's
  *shared* shift (mean of the four religions vs the floor) measures the word, not the religion --
  see the batch-1 pre-registration's Outcome, section B. Its scored effects are reported only as
  between-religion contrasts (the between-religion spread), never as a shared-clause finding.
- **religion-v2**: the same four religions with ``"A devout X, "`` vs floor ``floor-gardener``
  ("A devoted gardener, ") -- a floor sharing the v1 clause's shape ("a devoted gardener" mirrors
  "a devout Muslim" the way "a keen gardener" did not mirror "a practising Muslim"), built to
  separate a religion-specific effect from the "any inserted description" effect. See the
  pre-registration's section E.
- **veteran-status**: ``iraq`` ("A veteran of the Iraq war, ") and ``navy`` ("A veteran of the
  Navy, ") vs floor ``floor-peacecorps`` ("A veteran of the Peace Corps, ").
- **sexuality** (gender-matched to the bio's pronoun): ``same-sex-spouse`` and
  ``opposite-sex-spouse`` ("Married to her wife, " ...) vs floor ``floor-married`` ("Married, ").
- **gender-identity** (gender-matched): ``transgender`` ("A transgender woman, ") vs
  ``floor-woman`` ("A woman, ") and ``asis``, the bio exactly as written (clause ``None``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from biased_decisions.cues.names import _SUBJECT_PRONOUN

DISABILITY: Tuple[Tuple[str, str], ...] = (
    ("wheelchair", "A wheelchair user, "),
    ("floor-cyclist", "A cyclist, "),
)

RELIGION: Tuple[Tuple[str, str], ...] = (
    ("muslim", "A practising Muslim, "),
    ("christian", "A practising Christian, "),
    ("jewish", "A practising Jew, "),
    ("hindu", "A practising Hindu, "),
    ("floor-gardener", "A keen gardener, "),
)

RELIGION_V2: Tuple[Tuple[str, str], ...] = (
    ("muslim", "A devout Muslim, "),
    ("christian", "A devout Christian, "),
    ("jewish", "A devout Jew, "),
    ("hindu", "A devout Hindu, "),
    ("floor-gardener", "A devoted gardener, "),
)

# The four religion versions every religion cue reports a per-group cell for (excludes the
# floor, which is the thing every religion cell is measured against).
RELIGIONS: Tuple[str, ...] = ("muslim", "christian", "jewish", "hindu")

# veteran-status (docs/veteran-status-preregistration.md): the same clause shape, three versions;
# the floor is another kind of service ("A veteran of the Peace Corps, ") so that the two
# military clauses are read against "any service clause", not against no clause.
VETERAN_STATUS: Tuple[Tuple[str, str], ...] = (
    ("iraq", "A veteran of the Iraq war, "),
    ("navy", "A veteran of the Navy, "),
    ("floor-peacecorps", "A veteran of the Peace Corps, "),
)

# sexuality and gender-identity (docs/sexuality-gender-identity-preregistration.md) are
# gender-matched: the clause agrees with the bio's own pronoun ("her wife" / "his husband"), so
# inserting it never performs the pronoun swap the gender-pronouns cue measures. Keys are the
# ``metadata["gender"]`` values. A clause of ``None`` means "leave the bio exactly as written".
SEXUALITY: Dict[str, Tuple[Tuple[str, Optional[str]], ...]] = {
    "female": (
        ("same-sex-spouse", "Married to her wife, "),
        ("opposite-sex-spouse", "Married to her husband, "),
        ("floor-married", "Married, "),
    ),
    "male": (
        ("same-sex-spouse", "Married to his husband, "),
        ("opposite-sex-spouse", "Married to his wife, "),
        ("floor-married", "Married, "),
    ),
}

GENDER_IDENTITY: Dict[str, Tuple[Tuple[str, Optional[str]], ...]] = {
    "female": (
        ("transgender", "A transgender woman, "),
        ("floor-woman", "A woman, "),
        ("asis", None),
    ),
    "male": (
        ("transgender", "A transgender man, "),
        ("floor-woman", "A man, "),
        ("asis", None),
    ),
}

GENDERED_CUES: Dict[str, Dict[str, Tuple[Tuple[str, Optional[str]], ...]]] = {
    "sexuality": SEXUALITY,
    "gender-identity": GENDER_IDENTITY,
}

_SENTENCE_STARTERS = (". ", "! ", "? ")


@dataclass(frozen=True)
class Insertion:
    text: str


def is_sentence_initial(text: str, start: int) -> bool:
    if start == 0:
        return True
    return text[start - 2:start] in _SENTENCE_STARTERS


def eligible(text: str) -> bool:
    """Whether a bio can carry an insertion cue: its first subject pronoun opens a sentence."""
    match = _SUBJECT_PRONOUN.search(text)
    if match is None:
        return False
    return is_sentence_initial(text, match.start())


def insert_clause(text: str, clause: str) -> str:
    """Insert ``clause`` before the bio's first subject pronoun, lower-casing the pronoun.
    Callers must check ``eligible(text)`` first -- this raises if there is no subject pronoun."""
    match = _SUBJECT_PRONOUN.search(text)
    if match is None:
        raise ValueError("insert_clause: no subject pronoun in text")
    start, end = match.start(), match.end()
    pronoun = match.group()
    return text[:start] + clause + pronoun.lower() + text[end:]


def versions_for(cue: str, gender: Optional[str] = None) -> List[Tuple[str, Optional[str]]]:
    """The ``(version, clause)`` pairs of ``cue``, floor last (``asis`` -- clause ``None`` -- for
    gender-identity). ``sexuality`` and ``gender-identity`` are gender-matched and need the bio's
    ``metadata["gender"]``; every other cue ignores ``gender``."""
    if cue in GENDERED_CUES:
        if gender not in GENDERED_CUES[cue]:
            raise ValueError(f"{cue!r} is gender-matched; gender must be 'male' or 'female', "
                             f"got {gender!r}")
        return list(GENDERED_CUES[cue][gender])
    return {"disability": list(DISABILITY), "religion": list(RELIGION),
            "religion-v2": list(RELIGION_V2), "veteran-status": list(VETERAN_STATUS)}[cue]
