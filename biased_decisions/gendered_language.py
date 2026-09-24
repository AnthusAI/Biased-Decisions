"""The gendered-language tasks (``docs/gendered-language-preregistration.md``).

Three tasks share one pool of 2,000 real biographies (a byte-identical copy of
``tasks/stereotypes/items.jsonl``) and one insertion rule: a new sentence goes immediately after
the biography's first sentence. Every biography is read in two gender versions, the text as written
or its pronoun swap (``swap_gender`` with the rule the published twins used), and the inserted
sentence uses the pronoun that agrees with whichever version it sits in.

- ``gendered-management`` (Design 1), one cue per word pair (``assertive-bossy`` ...): "Colleagues
  describe her/him as <word>." with either word of the pair, so a bio has four versions:
  ``neutral-female``, ``loaded-female``, ``neutral-male``, ``loaded-male``.
- ``gendered-advance`` (Design 3), cue ``agentic-communal``: a communal or an agentic descriptor
  sentence, four versions likewise.
- ``gendered-word-choice`` (Design 2), one cue per pair: a short scene sentence and a two-option
  question that names both words, ``female`` and ``male`` versions, the loaded word listed first
  for half the bios (by position in the id-sorted eligible list; both genders of a bio share the
  order).

A bio with no first-sentence boundary is excluded from every design (and counted), so the same
bios carry every cell. A boundary is a full stop, ``!`` or ``?`` followed by space and a capital,
digit or opening quote, where the word before it is not a title or a single initial (a tightening of
the registered "first ``. `` boundary", which would split "Dr. Li"; recorded under Deviations).
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from biased_decisions.cues.gender import ORIGINAL_RULE, swap_gender

MANAGEMENT = "gendered-management"
ADVANCE = "gendered-advance"
WORD_CHOICE = "gendered-word-choice"
ADVANCE_CUE = "agentic-communal"
TASKS: Tuple[str, ...] = (MANAGEMENT, ADVANCE, WORD_CHOICE)
GENDERS: Tuple[str, ...] = ("female", "male")
POOL_TASK = "stereotypes"

OBJECT_PRONOUN = {"female": "her", "male": "him"}
SUBJECT_PRONOUN = {"female": "she", "male": "he"}


@dataclass(frozen=True)
class Pair:
    key: str
    neutral: str
    loaded: str
    scene: str                # the behaviour sentence for Design 2, with {S} for the subject pronoun
    source_verified: bool     # the pair's source wording was read first-hand (see the README)
    jev_pair: bool            # one of the three strongest-sourced pairs, the only ones planned for Jev


PAIRS: Tuple[Pair, ...] = (
    Pair("assertive-bossy", "assertive", "bossy",
         "In a recent team meeting, {S} pushed the group to change direction over two colleagues' objections.",
         True, True),
    Pair("direct-abrasive", "direct", "abrasive",
         "In a recent team meeting, {S} told a colleague plainly that the proposal would not work.",
         True, True),
    Pair("confident-aggressive", "confident", "aggressive",
         "In a recent team meeting, {S} argued for the plan and held to it when two colleagues objected.",
         True, True),
    Pair("calm-emotional", "calm", "emotional",
         "In a recent team meeting, {S} objected to a decision the group had already made.",
         True, False),
    Pair("decisive-pushy", "decisive", "pushy",
         "In a recent team meeting, {S} settled the question at once and moved the group to the next item.",
         False, False),
    Pair("independent-selfish", "independent", "selfish",
         "In a recent team meeting, {S} took on the project alone instead of sharing it out with the team.",
         False, False),
)
PAIR_BY_KEY: Dict[str, Pair] = {p.key: p for p in PAIRS}

DESCRIPTORS: Dict[str, str] = {
    "communal": "warm, supportive, and a team player",
    "agentic": "confident, independent, and a natural leader",
}
ADVANCE_STYLES: Tuple[str, str] = ("communal", "agentic")

_ABBREVIATIONS = {"dr", "mr", "mrs", "ms", "prof", "st", "jr", "sr", "mt", "fr", "rev", "hon", "gen",
                  "col", "capt", "lt", "sgt", "inc", "ltd", "co", "vs", "no", "dept", "univ", "ph",
                  "esq", "md", "mrs", "messrs", "sen", "rep", "gov", "cpl", "maj", "corp"}
_BOUNDARY = re.compile(r"[.!?][\"')\]]*\s+(?=[A-Z0-9\"'(\[])")


def first_sentence_end(text: str) -> Optional[int]:
    """The index just after the first sentence (its full stop and any closing quote), or None."""
    for match in _BOUNDARY.finditer(text):
        word = re.search(r"(\S+)$", text[:match.start()])
        token = re.sub(r"^\W+", "", word.group(1)) if word else ""
        if match.group()[0] == ".":
            if token.lower() in _ABBREVIATIONS or re.fullmatch(r"[A-Za-z]", token) \
                    or re.fullmatch(r"(?:[A-Za-z]\.)+[A-Za-z]", token):
                continue
        return match.start() + len(match.group().rstrip())
    return None


def insert_sentence(text: str, sentence: str) -> Optional[str]:
    end = first_sentence_end(text)
    if end is None:
        return None
    return text[:end] + " " + sentence + text[end:]


def gendered_texts(text: str, gender: str) -> Dict[str, str]:
    """The bio as a woman's and as a man's: the as-written text for its own gender, the pronoun
    swap (the rule the published twins used) for the other."""
    other = "male" if gender == "female" else "female"
    return {gender: text, other: swap_gender(text, rule=ORIGINAL_RULE).text}


def word_sentence(word: str, gender: str) -> str:
    return f"Colleagues describe {OBJECT_PRONOUN[gender]} as {word}."


def descriptor_sentence(style: str, gender: str) -> str:
    return f"Colleagues describe {OBJECT_PRONOUN[gender]} as {DESCRIPTORS[style]}."


def scene_sentence(pair_key: str, gender: str) -> str:
    return PAIR_BY_KEY[pair_key].scene.replace("{S}", SUBJECT_PRONOUN[gender])


def word_choice_question(first: str, second: str) -> str:
    return ("Which word better describes this person's behavior in that meeting: "
            f"'{first}' or '{second}'?")


def _eligible(items: Sequence[dict]) -> List[dict]:
    return [item for item in items if first_sentence_end(item["text"]) is not None]


def excluded_count(items: Sequence[dict]) -> int:
    return len(items) - len(_eligible(items))


def _meta(item: dict, cue: str, version: str, gender: str) -> dict:
    meta = item["metadata"]
    return {"cue": cue, "version": version, "source_id": item["id"], "gender": gender,
            "bio_gender": meta.get("gender"), "occupation": meta.get("occupation"),
            "source_task": meta.get("source_task")}


def _crossed(items: Sequence[dict], cue: str, words: Tuple[Tuple[str, str], ...], sentence) -> List[dict]:
    """Rows in item order: for each version name in ``words`` (label, word or style) x gender."""
    rows: List[dict] = []
    for item in _eligible(items):
        texts = gendered_texts(item["text"], item["metadata"]["gender"])
        for gender in GENDERS:
            for label, word in words:
                version = f"{label}-{gender}"
                meta = _meta(item, cue, version, gender)
                meta.update({"word": label, "word_text": word})
                rows.append({"id": f"{item['id']}-{cue}-{version}",
                             "text": insert_sentence(texts[gender], sentence(word, gender)),
                             "metadata": meta})
    return rows


def build_management_versions(items: Sequence[dict], cue: str) -> List[dict]:
    pair = PAIR_BY_KEY[cue]
    return _crossed(items, cue, (("neutral", pair.neutral), ("loaded", pair.loaded)), word_sentence)


def build_advance_versions(items: Sequence[dict]) -> List[dict]:
    rows = _crossed(items, ADVANCE_CUE, (("communal", "communal"), ("agentic", "agentic")),
                    descriptor_sentence)
    for row in rows:
        row["metadata"]["word_text"] = DESCRIPTORS[row["metadata"]["word"]]
    return rows


def build_word_choice_versions(items: Sequence[dict], cue: str) -> List[dict]:
    pair = PAIR_BY_KEY[cue]
    rows: List[dict] = []
    for position, item in enumerate(sorted(_eligible(items), key=lambda i: i["id"])):
        loaded_first = position % 2 == 1
        options = [pair.loaded, pair.neutral] if loaded_first else [pair.neutral, pair.loaded]
        texts = gendered_texts(item["text"], item["metadata"]["gender"])
        for gender in GENDERS:
            meta = _meta(item, cue, gender, gender)
            meta.update({"options": options, "order": "loaded-first" if loaded_first else "loaded-second",
                         "loaded": pair.loaded, "neutral": pair.neutral,
                         "question": word_choice_question(*options)})
            rows.append({"id": f"{item['id']}-{cue}-{gender}",
                         "text": insert_sentence(texts[gender], scene_sentence(cue, gender)),
                         "metadata": meta})
    rows.sort(key=lambda r: (r["metadata"]["source_id"], GENDERS.index(r["metadata"]["gender"])))
    return rows


def versions_for(slug: str, cue: str, items: Sequence[dict]) -> List[dict]:
    if slug == MANAGEMENT:
        return build_management_versions(items, cue)
    if slug == ADVANCE:
        return build_advance_versions(items)
    if slug == WORD_CHOICE:
        return build_word_choice_versions(items, cue)
    raise ValueError(f"not a gendered-language task: {slug!r}")


def cues_of(slug: str) -> Tuple[str, ...]:
    return (ADVANCE_CUE,) if slug == ADVANCE else tuple(p.key for p in PAIRS)


def write_all(root: Path) -> Dict[str, int]:
    """Copy the pool into each task and write every versions file; returns rows per file."""
    root = Path(root)
    pool_path = root / "tasks" / POOL_TASK / "items.jsonl"
    items = [json.loads(line) for line in pool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    written: Dict[str, int] = {}
    for slug in TASKS:
        task_dir = root / "tasks" / slug
        (task_dir / "versions").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pool_path, task_dir / "items.jsonl")
        for cue in cues_of(slug):
            rows = versions_for(slug, cue, items)
            with (task_dir / "versions" / f"{cue}.jsonl").open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            written[f"{slug}/{cue}"] = len(rows)
    return written


if __name__ == "__main__":  # pragma: no cover
    from biased_decisions.tasks.base import DEFAULT_ROOT
    for name, count in write_all(DEFAULT_ROOT).items():
        print(f"{name}: {count} rows")
