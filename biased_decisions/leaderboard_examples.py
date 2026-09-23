"""One real example per breakdown cell, for the leaderboard's drill-down pages.

A number like "+2.3 pts" means little to a lay reader until they see the bio it came from. For
every (dimension, group, item) cell whose answer record is in this repository, this module picks
one committed bio, shows it in the two versions the cue compares (the edited words marked), and
lists what each engine answered on each version, straight from ``answers/``.

The pick is a fixed rule, not a judgement, and the page says so: for the engine that is most
biased on that cell (else the one with the largest excess), the bio with the largest change in the
engine's own probability for the task's positive label, among bios whose verdict flipped if any
did; for a shift measure, only bios that moved in the direction of the engine's average shift. It
is the clearest case, not a typical one, and the page puts the cell's average beside it.

Batch 2's stereotype cells have no example: their record is not in this repository (see
``studies/batch2/README.md``); the pages show their question wording and mean probabilities
instead.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from biased_decisions.record import read_record
from biased_decisions.tasks.base import Task

_TOKEN = re.compile(r"\w+|[^\w\s]+|\s+")


def mark(a: str, b: str) -> Tuple[List[list], List[list]]:
    """Word-level diff of two versions of a bio: each as ``[[text, changed], ...]`` with
    ``changed`` 1 for the words that differ from the other version, 0 elsewhere."""
    ta, tb = _TOKEN.findall(a), _TOKEN.findall(b)
    sa: List[list] = []
    sb: List[list] = []

    def push(out: List[list], tokens: List[str], changed: int) -> None:
        if not tokens:
            return
        text = "".join(tokens)
        if changed and not text.strip():
            changed = 0
        if out and out[-1][1] == changed:
            out[-1][0] += text
        else:
            out.append([text, changed])

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ta, b=tb, autojunk=False).get_opcodes():
        flag = 0 if tag == "equal" else 1
        push(sa, ta[i1:i2], flag)
        push(sb, tb[j1:j2], flag)
    return sa, sb


class _Texts:
    """Bio texts by id, from a task's items.jsonl or a cue's versions file, read once."""

    def __init__(self, root: Path):
        self.root = root
        self._cache: Dict[Tuple[str, str], Dict[str, dict]] = {}

    def get(self, task: str, source: str) -> Dict[str, dict]:
        key = (task, source)
        if key not in self._cache:
            path = self.root / "tasks" / task / ("items.jsonl" if source == "items"
                                                 else f"versions/{source}.jsonl")
            rows: Dict[str, dict] = {}
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        rows[row["id"]] = row
            self._cache[key] = rows
        return self._cache[key]


class _Records:
    """Answer records by (engine, task, cue), keyed by item id (first row wins)."""

    def __init__(self, root: Path):
        self.root = root
        self._cache: Dict[Tuple[str, str, str], Dict[str, dict]] = {}

    def get(self, engine: str, task: str, cue: str) -> Dict[str, dict]:
        key = (engine, task, cue)
        if key not in self._cache:
            rows: Dict[str, dict] = {}
            for row in read_record(self.root / "answers" / engine / task / f"{cue}.jsonl.gz"):
                rows.setdefault(row["id"], row)
            self._cache[key] = rows
        return self._cache[key]


class Pair:
    """How one cell's two versions are found: the text source, the record each version's answer
    is in, and the ids of the two versions of a source bio."""

    def __init__(self, *, texts: str, base_cue: str, cue_cue: str,
                 base_id: Callable[[str], str], cue_id: Callable[[str], str],
                 base_label: str, cue_label: str, sources: Callable[[Dict[str, dict]], List[str]],
                 signed: bool, reverse_options: bool = False):
        self.texts, self.base_cue, self.cue_cue = texts, base_cue, cue_cue
        self.base_id, self.cue_id = base_id, cue_id
        self.base_label, self.cue_label = base_label, cue_label
        self.sources, self.signed, self.reverse_options = sources, signed, reverse_options


def _test_ids(rows: Dict[str, dict]) -> List[str]:
    return [i for i, r in rows.items() if r.get("metadata", {}).get("split") == "test"]


def _source_ids(rows: Dict[str, dict]) -> List[str]:
    seen: Dict[str, None] = {}
    for r in rows.values():
        src = r.get("metadata", {}).get("source_id")
        if src:
            seen.setdefault(src, None)
    return list(seen)


def pair_for(dim: str, group: Optional[str], facet: dict) -> Optional[Pair]:
    """The version pair a cell compares, or None where the record is not in this repository."""
    if dim == "gender-pronouns":
        return Pair(texts="items", base_cue="gender-pronouns", cue_cue="gender-pronouns",
                    base_id=lambda s: s, cue_id=lambda s: f"{s}-swapped",
                    base_label="As written", cue_label="Pronouns swapped",
                    sources=_test_ids, signed=False)
    if dim == "option-order":
        return Pair(texts="items", base_cue="gender-pronouns", cue_cue="option-order-reversed",
                    base_id=lambda s: s, cue_id=lambda s: s,
                    base_label="Options in the committed order",
                    cue_label="Options listed the other way round",
                    sources=_test_ids, signed=False, reverse_options=True)
    if dim == "race-name":
        return Pair(texts="race-name", base_cue="race-name", cue_cue="race-name",
                    base_id=lambda s: f"{s}-white_a", cue_id=lambda s: f"{s}-black",
                    base_label="White first name", cue_label="Black first name",
                    sources=_source_ids, signed=False)
    if dim == "race-fullname":
        return Pair(texts="race-fullname", base_cue="race-fullname", cue_cue="race-fullname",
                    base_id=lambda s: f"{s}-white-1", cue_id=lambda s, g=group: f"{s}-{g}-1",
                    base_label="White full name", cue_label=f"{group.capitalize()} full name",
                    sources=_source_ids, signed=True)
    if dim == "age-inserted":
        return Pair(texts="age-inserted", base_cue="age-inserted", cue_cue="age-inserted",
                    base_id=lambda s: f"{s}-age34", cue_id=lambda s: f"{s}-age61",
                    base_label="Stated age 34", cue_label="Stated age 61",
                    sources=_source_ids, signed=False)
    if dim == "disability":
        return Pair(texts="disability", base_cue="disability", cue_cue="disability",
                    base_id=lambda s: f"{s}-disability-floor-cyclist",
                    cue_id=lambda s: f"{s}-disability-wheelchair",
                    base_label="Floor: a cyclist", cue_label="A wheelchair user",
                    sources=_source_ids, signed=True)
    if dim == "religion":
        hi, lo = facet["extra"]["highest"], facet["extra"]["lowest"]
        return Pair(texts="religion", base_cue="religion", cue_cue="religion",
                    base_id=lambda s: f"{s}-religion-{lo}", cue_id=lambda s: f"{s}-religion-{hi}",
                    base_label=f"Practising {lo.capitalize()} (lowest)",
                    cue_label=f"Practising {hi.capitalize()} (highest)",
                    sources=_source_ids, signed=True)
    if dim == "religion-v2" and group:
        return Pair(texts="religion-v2", base_cue="religion-v2", cue_cue="religion-v2",
                    base_id=lambda s: f"{s}-religion-v2-floor-gardener",
                    cue_id=lambda s, g=group: f"{s}-religion-v2-{g}",
                    base_label="Floor: a devoted gardener",
                    cue_label=f"Devout {'Jew' if group == 'jewish' else group.capitalize()}",
                    sources=_source_ids, signed=True)
    return None


def _answer(row: Optional[dict], positive: str) -> Optional[dict]:
    if row is None:
        return None
    body = next(iter(row["answers"].values()))
    return {"p": round(float(body["probabilities"][positive]) * 100, 2), "choice": body["choice"]}


class Examples:
    def __init__(self, root: Path, engines: List[str], labels: Dict[str, str]):
        self.root = root
        self.engines = engines
        self.labels = labels
        self.texts = _Texts(root)
        self.records = _Records(root)

    def build(self, dim: str, group: Optional[str], task: str,
              facets: Dict[str, dict]) -> Optional[dict]:
        ref = _reference_engine(facets)
        if ref is None:
            return None
        pair = pair_for(dim, group, facets[ref])
        if pair is None:
            return None
        t = Task.load(task, root=self.root)
        texts = self.texts.get(task, pair.texts)
        base_rec = self.records.get(ref, task, pair.base_cue)
        cue_rec = self.records.get(ref, task, pair.cue_cue)
        if not base_rec or not cue_rec:
            return None
        cands = []
        for src in pair.sources(texts):
            b, c = base_rec.get(pair.base_id(src)), cue_rec.get(pair.cue_id(src))
            if b is None or c is None or pair.base_id(src) not in texts \
                    or pair.cue_id(src) not in texts:
                continue
            ab, ac = _answer(b, t.positive), _answer(c, t.positive)
            cands.append((src, ac["p"] - ab["p"], ab["choice"] != ac["choice"]))
        if not cands:
            return None
        rule = f"the largest change in {self.labels[ref]}'s P({t.positive})"
        if pair.signed:
            mean = sum(d for _, d, _ in cands) / len(cands)
            sign = 1 if mean >= 0 else -1
            same = [c for c in cands if c[1] * sign > 0]
            cands = same or cands
            rule += (f" in the direction of its average shift "
                     f"({'toward' if sign > 0 else 'away from'} {t.positive})")
        flips = [c for c in cands if c[2]]
        pool = flips or cands
        src, delta, _ = max(pool, key=lambda c: (abs(c[1]), [-ord(ch) for ch in c[0]]))
        chosen = ("Chosen by a fixed rule: among the bios whose verdict flipped, " + rule
                  if flips else "No bio's verdict flipped; chosen as the bio with " + rule)
        base_text = texts[pair.base_id(src)]["text"]
        cue_text = texts[pair.cue_id(src)]["text"]
        sb, sc = mark(base_text, cue_text)
        options = list(t.options)
        answers = {}
        for e in self.engines:
            br, cr = self.records.get(e, task, pair.base_cue), self.records.get(e, task,
                                                                                pair.cue_cue)
            pb = _answer(br.get(pair.base_id(src)), t.positive)
            pc = _answer(cr.get(pair.cue_id(src)), t.positive)
            if pb is not None and pc is not None:
                answers[e] = [pb, pc]
        return {
            "task": task, "source_id": src, "engine": ref, "positive": t.positive,
            "question": t.question, "chosen": chosen + ".",
            "versions": [
                {"id": pair.base_id(src), "label": pair.base_label, "segments": sb,
                 "options": options},
                {"id": pair.cue_id(src), "label": pair.cue_label, "segments": sc,
                 "options": list(reversed(options)) if pair.reverse_options else options},
            ],
            "answers": answers,
            "records": sorted({f"answers/{e}/{task}/{c}.jsonl.gz" for e in answers
                               for c in (pair.base_cue, pair.cue_cue)}),
            "texts": sorted({f"tasks/{task}/" + ("items.jsonl" if pair.texts == "items"
                                                  else f"versions/{pair.texts}.jsonl")}),
        }


def _reference_engine(facets: Dict[str, dict]) -> Optional[str]:
    """The engine whose example is shown: most biased on the cell, else the largest excess."""
    measured = [(e, f) for e, f in facets.items()
                if f["status"] == "measured" and f.get("records")]
    if not measured:
        return None
    detected = [(e, f) for e, f in measured if f["detected"]]
    pool = detected or measured
    return max(pool, key=lambda ef: ef[1]["excess"]["value"])[0]
