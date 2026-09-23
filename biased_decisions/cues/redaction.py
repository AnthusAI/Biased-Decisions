"""First-name redaction: strip the gender cue a first name carries before swapping pronouns.

Ported unchanged from Jev-Flywheel's ``jev_flywheel/counterfactual.py`` (``redact_names`` and
``redact_names_batch``). A token counts as a redactable name only when *both* signals agree:
spaCy's NER says it is part of a person's name, and the token is on the committed US-first-name
list. Either signal alone over-redacts -- spaCy's ``PERSON`` label catches institutions ("Baylor
College") and plans, and the name list alone catches surnames and hospital names that happen to
share a first name ("Mercy Hospital"). The intersection is what removes the gender cue without
also eating the rest of the bio.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Sequence

DEFAULT_NAME_LIST = Path(__file__).resolve().parents[2] / "pools" / "first_names.txt"


from dataclasses import dataclass


@dataclass(frozen=True)
class Redaction:
    text: str
    redacted: int      # how many tokens were replaced with "[name]"


@lru_cache(maxsize=4)
def _load_names(path: str) -> frozenset:
    """The committed first-name list, lower-cased. Cached per path so a batch job that redacts
    thousands of bios reads the file once."""
    names = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(line.lower())
    return frozenset(names)


@lru_cache(maxsize=1)
def _load_nlp():
    """The spaCy pipeline, loaded once per process. Imported lazily so the rest of this module,
    and everything that only calls ``swap_gender``, works without spaCy installed."""
    import spacy
    return spacy.load("en_core_web_sm")


def _redact_doc(doc, names: frozenset) -> Redaction:
    """Replace every token that is both inside a ``PERSON`` entity span and on ``names`` with
    ``[name]``, preserving the token's own leading/trailing whitespace and punctuation. Because
    spaCy already splits a possessive off as its own ``'s`` token (``Alysson's`` -> ``Alysson``,
    ``'s``), redacting only the name token and leaving the ``'s`` token untouched is enough to
    turn ``Alysson's`` into ``[name]'s`` without any special-casing here."""
    person_token_ids = {tok.i for ent in doc.ents if ent.label_ == "PERSON" for tok in ent}
    out: List[str] = []
    redacted = 0
    for tok in doc:
        if tok.i in person_token_ids and tok.text.lower() in names:
            out.append("[name]")
            redacted += 1
        else:
            out.append(tok.text)
        out.append(tok.whitespace_)
    return Redaction("".join(out), redacted)


def redact_names(text: str, *, name_list: Path = DEFAULT_NAME_LIST) -> Redaction:
    """Replace first names spaCy tags as ``PERSON`` and that are on ``name_list`` with
    ``[name]``. See ``redact_names_batch`` for many texts at once -- it is the one to use for
    a corpus, since ``nlp.pipe`` batches spaCy's own work across documents.
    """
    nlp = _load_nlp()
    names = _load_names(str(name_list))
    return _redact_doc(nlp(text), names)


def redact_names_batch(texts: Sequence[str], *, name_list: Path = DEFAULT_NAME_LIST,
                        batch_size: int = 200) -> List[Redaction]:
    """``redact_names`` for many texts, batched through ``nlp.pipe`` for speed (about 8s per
    1,000 bios on the corpus this study uses, vs. calling ``redact_names`` in a loop)."""
    nlp = _load_nlp()
    names = _load_names(str(name_list))
    return [_redact_doc(doc, names) for doc in nlp.pipe(texts, batch_size=batch_size)]
