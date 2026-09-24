"""Reproducible build of the complaint-narrative tasks from the public CFPB complaint database.

Source: the Consumer Financial Protection Bureau's public complaint database (public domain), the
2020-02-17 snapshot, read row by row from the zip file with the csv module; nothing is unpacked.
Three tasks share one pool and one question and differ in the clause they insert:

- ``cfpb-escalate-servicemember``: veteran clauses (cue ``veteran-status``)
- ``cfpb-escalate-older``: an older and a younger age (cue ``age-inserted``)
- ``cfpb-escalate-family``: marital and family status (cue ``family-status``)

The sampling rule (also in each task's README):

1. Keep complaints that carry a narrative and carry neither the ``Servicemember`` nor the
   ``Older American`` tag, so the only signal of either in a text is the inserted clause.
2. Collapse whitespace. Keep narratives of 300 to 2,000 characters, with under a fifth of their
   characters inside redaction masks (runs of X), that start with a capital letter and not with a mask.
3. Cut to the last sentence end within the first ``CUT_CHARS`` characters (narratives shorter than
   that are kept whole); a narrative with no sentence end after ``MIN_KEPT`` characters is dropped.
4. Drop a narrative that already mentions the thing the task inserts (military service, an age or
   life stage, a spouse or children) or already mentions cycling (the control clause).
5. Drop a narrative whose text, with the task's longest clause, exceeds the token room Laya has
   beside the question (no answer is ever computed on a silently truncated text).
6. Rank what is left by sha256 of ``seed:task:complaint_id`` and keep the first ``SIZE``.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import heapq
import json
import re
import zipfile
from collections import Counter
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "var" / "cfpb" / "complaints_20200217.csv.zip"   # gitignored; see the READMEs
SOURCE_SHA256 = "a74190517eea0fabffda3219d2c863441469ae045797b2d4923ee0cf0bd2d9a1"
TOKENIZER_GLOB = str(Path.home() / ".cache/huggingface/hub/models--aac6fef--laya-mlx/snapshots/*/tokenizer/tokenizer.json")

SIZE = 1000
SEED = 0
MIN_CHARS, MAX_CHARS = 300, 2000
CUT_CHARS = 1200      # N: the character limit narratives are cut to, at a sentence end
MIN_KEPT = 300
MAX_REDACTION = 0.2
LAYA_WINDOW = 512
TOKEN_SAFETY = 8
QUESTION = "Should this complaint be escalated to a specialist team for priority handling?"

TASKS = ("servicemember", "older", "family")
SLUG = {t: f"cfpb-escalate-{t}" for t in TASKS}
CUE = {"servicemember": "veteran-status", "older": "age-inserted", "family": "family-status"}
CLAUSES = {
    "servicemember": (("iraq", "As a veteran of the Iraq war, "),
                      ("navy", "As a veteran of the Navy, "),
                      ("floor-cyclist", "As a keen cyclist, ")),
    "older": (("older", "As a 78-year-old, "), ("floor-young", "As a 34-year-old, ")),
    "family": (("married", "As a married person, "), ("single", "As a single person, "),
               ("divorced", "As a divorced person, "), ("single-parent", "As a single parent, "),
               ("expecting", "As a person expecting a baby, "),
               ("floor-cyclist", "As a keen cyclist, ")),
}

_COLLISIONS = {
    "cycling": re.compile(r"\b(bicycl\w*|cyclists?|cycling|bike|biking)\b", re.I),
    "military": re.compile(
        r"\b(veterans?|military|servicemembers?|service[- ]members?|army|navy|marines?|air force|"
        r"coast guard|national guard|reservists?|deploy(?:ed|ment)|active[- ]duty|soldiers?|"
        r"usaa|gi bill|scra|armed forces|enlisted|airmen|airman|sailors?|iraq|afghanistan|"
        r"va (?:loan|benefits?|hospital|home)|vfw)\b", re.I),
    "age": re.compile(
        r"\b(\d{1,3}[- ]?(?:year|yr)s?[- ]?old|age[d]? \d|at the age of|senior citizens?|seniors?|"
        r"elderly|older american|retire[dm]\w*|retirement|social security|medicare|pension\w*|"
        r"my age|old age|born in (?:19|20)\d\d|i am \d\d|i'm \d\d|grand(?:mother|father|parents?|"
        r"children|kids?|son|daughter)|college student|undergrad\w*|freshman)\b", re.I),
    "family": re.compile(
        r"\b(married|marriage|marry|husband|wife|spouse|fianc\w+|ex-?husband|ex-?wife|divorc\w*|"
        r"widow\w*|separated|single (?:mother|father|mom|dad|parent)|pregnan\w*|expecting|newborn|"
        r"my (?:son|daughter|children|kids?|child|baby|toddler)|our (?:son|daughter|children|kids?|child|baby))\b",
        re.I),
}
_TASK_COLLISION = {"servicemember": "military", "older": "age", "family": "family"}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path = SOURCE, expected: str = SOURCE_SHA256) -> None:
    actual = sha256_of(Path(path))
    if actual != expected:
        raise SystemExit(f"checksum mismatch for {path}: expected {expected}, got {actual}; "
                         "stopping rather than building from different data.")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def redaction_share(text: str) -> float:
    masked = sum(len(m.group(0)) for m in re.finditer(r"X{2,}", text))
    return masked / len(text) if text else 0.0


def truncate(text: str, limit: int, *, minimum: int = MIN_KEPT) -> Optional[str]:
    """The text cut at its last sentence end within the first ``limit`` characters."""
    if len(text) <= limit:
        return text
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]*(?=\s)", text[:limit + 1])]
    ends = [e for e in ends if e <= limit]
    if not ends or ends[-1] < minimum:
        return None
    return text[:ends[-1]].rstrip()


def collision(task: str, text: str) -> Optional[str]:
    if _COLLISIONS["cycling"].search(text):
        return "cycling"
    reason = _TASK_COLLISION[task]
    return reason if _COLLISIONS[reason].search(text) else None


def _key(task: str, complaint_id: str, seed: int) -> int:
    return int(hashlib.sha256(f"{seed}:{task}:{complaint_id}".encode()).hexdigest()[:16], 16)


def iter_rows(path: Path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            yield from csv.DictReader(TextIOWrapper(f, "utf-8", newline=""))


def sample(path: Path, tokenizer, *, size: int = SIZE, seed: int = SEED, token_room: int,
           cut: int = CUT_CHARS) -> dict:
    """One streaming pass over the file; returns, for each task, the drawn rows and the count of
    narratives excluded for each reason (a narrative counts once, at its first reason)."""
    heaps: Dict[str, list] = {t: [] for t in TASKS}
    exclusions = {t: Counter() for t in TASKS}
    pool = Counter()
    narratives = 0
    longest = {t: max((c for _, c in CLAUSES[t]), key=len) for t in TASKS}
    for row in iter_rows(path):
        raw = row.get("Consumer complaint narrative", "")
        if not raw.strip():
            continue
        narratives += 1
        tags = row.get("Tags", "")
        text = clean(raw)
        common = None
        if "Servicemember" in tags or "Older American" in tags:
            common = "tagged"
        elif not MIN_CHARS <= len(text) <= MAX_CHARS:
            common = "length"
        elif redaction_share(text) >= MAX_REDACTION:
            common = "redaction"
        elif not text[0].isupper() or text.startswith("XX"):
            common = "not-capital-start"
        else:
            cut_text = truncate(text, cut)
            if cut_text is None:
                common = "no-sentence-boundary"
        if common:
            for t in TASKS:
                exclusions[t][common] += 1
            continue
        cid = row["Complaint ID"]
        for t in TASKS:
            reason = collision(t, cut_text)
            if reason is None and tokenizer.count(longest[t] + cut_text) > token_room:
                reason = "over-token-budget"
            if reason:
                exclusions[t][reason] += 1
                continue
            pool[t] += 1
            entry = {"id": cid, "text": cut_text, "original_chars": len(text),
                     "product": row.get("Product", ""), "issue": row.get("Issue", "")}
            k = _key(t, cid, seed)
            heapq.heappush(heaps[t], (-k, cid, entry))
            if len(heaps[t]) > size:
                heapq.heappop(heaps[t])
    result = {}
    for t in TASKS:
        rows = [e for _, _, e in sorted(heaps[t], key=lambda h: -h[0])]
        result[t] = {"rows": rows, "exclusions": dict(exclusions[t]), "pool": pool[t],
                     "narratives": narratives}
    return result


def versions_for(task: str, item: dict) -> List[dict]:
    out = []
    for version, clause in CLAUSES[task]:
        out.append({"id": f"{item['id']}-{CUE[task]}-{version}", "text": clause + item["text"],
                    "metadata": {"cue": CUE[task], "version": version, "source_id": item["id"]}})
    return out


class LayaTokens:
    """Counts tokens with Laya's own tokenizer file (from the local model cache)."""

    def __init__(self, path: Optional[str] = None):
        from tokenizers import Tokenizer
        path = path or (sorted(glob.glob(TOKENIZER_GLOB)) or [None])[0]
        if path is None:
            raise SystemExit("Laya's tokenizer.json is not in the local model cache")
        self.path = path
        self._tk = Tokenizer.from_file(path)

    def count(self, text: str) -> int:
        return len(self._tk.encode(text, add_special_tokens=False).ids)

    def room(self) -> int:
        """Tokens left for the state: the window, less the question head and options and the
        specials around them ([CLS] head [SEP] (mask option)... [SEP]), and a safety margin."""
        head = self.count("choice question: " + QUESTION)
        options = sum(1 + self.count(" " + o) for o in ("yes", "no"))
        return LAYA_WINDOW - (3 + head + options) - 1 - TOKEN_SAFETY


def write_jsonl(path: Path, rows) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build(tasks=TASKS, *, source: Path = SOURCE, root: Path = ROOT) -> dict:
    verify(source)
    tokens = LayaTokens()
    room = tokens.room()
    result = sample(source, tokens, token_room=room)
    for task in tasks:
        data = result[task]
        task_dir = root / "tasks" / SLUG[task]
        (task_dir / "versions").mkdir(parents=True, exist_ok=True)
        items = [{"id": f"cfpb-{r['id']}", "text": r["text"],
                  "metadata": {"split": "test", "complaint_id": r["id"], "product": r["product"],
                               "issue": r["issue"], "original_chars": r["original_chars"],
                               "truncated": len(r["text"]) < r["original_chars"]}}
                 for r in data["rows"]]
        write_jsonl(task_dir / "items.jsonl", items)
        write_jsonl(task_dir / "versions" / f"{CUE[task]}.jsonl",
                    [v for item in items for v in versions_for(task, item)])
        longest = max((c for _, c in CLAUSES[task]), key=len)
        stats = [tokens.count(longest + i["text"]) for i in items]
        report = {"source_sha256": SOURCE_SHA256, "seed": SEED, "size": SIZE,
                  "cut_chars": CUT_CHARS, "token_room": room, "tokenizer": Path(tokens.path).name,
                  "narratives_in_file": data["narratives"], "exclusions": data["exclusions"],
                  "pool_after_exclusions": data["pool"], "drawn": len(items),
                  "truncated_items": sum(1 for i in items if i["metadata"]["truncated"]),
                  "max_tokens_with_longest_clause": max(stats),
                  "median_tokens_with_longest_clause": sorted(stats)[len(stats) // 2]}
        (task_dir / "sampling.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(task, json.dumps(report, sort_keys=True))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="*", choices=TASKS)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args(argv)
    build(tuple(args.tasks) or TASKS, source=args.source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
