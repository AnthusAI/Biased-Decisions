"""``bd score`` / ``bd replay``: turn a record's rows into a measurement row.

This module ports the scoring half of Jev-Flywheel's ``scripts/run_bios_*.py`` family (see
``import/docs/biased-decisions-inventory.md``): given a task's committed items and versions and
one engine's answer record, build the ``Verdict``\\ s ``biased_decisions.metrics`` needs and call
the right metrics function. Every function here was checked, before it was written, against the
actual committed record -- ``bd score`` reproduces every number in
``studies/jev-flywheel/*.jsonl`` this way (see ``tests/replay_test.py``), with one documented
exception: the ``surgeon_physician`` rows in ``bios_pairs.jsonl`` were built by a copy-script
that relabels ``bios_gender.jsonl``'s ``flip_toward_physician_share`` /
``tpr_gap_surgeon_women_minus_men`` fields as this schema's ``flip_toward_more_female_share`` /
``recall_gap_less_female_women_minus_men`` without noticing that "physician" is surgeon-physician's
*less*-female label, not its more-female one -- so those two fields in the published row measure
the opposite share/gap from what their names say. This module computes them correctly (share
toward "surgeon", the actual more-female label); see ``tests/replay_test.py`` for the mapping
this produces and ``RESULTS.md``'s footnotes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from biased_decisions.metrics import shortlist as shortlist_metrics
from biased_decisions.metrics.flips import Verdict, score_arm_race, score_pair
from biased_decisions.metrics.shifts import score_arm_age, score_arm_race2
from biased_decisions.record import read_record_by_id, record_path
from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.tasks.bios import BIOS_TASKS, split_test_and_twins

QUESTION_NAME = "Occupation"
FULLNAME_GROUPS = ("white", "black", "hispanic", "asian")

# Every milestone-1 task's cues, in the design doc's order. gender-pronouns is answered on all
# four tasks; the other three cues only exist for surgeon-physician (see data/MANIFEST.md).
TASK_CUES: Dict[str, tuple] = {
    "surgeon-physician": ("gender-pronouns", "race-name", "race-fullname", "age-inserted"),
    "nurse-physician": ("gender-pronouns",),
    "teacher-professor": ("gender-pronouns",),
    "paralegal-attorney": ("gender-pronouns",),
}

# The pairs bios_shortlist.jsonl (and this package's shortlist replay) studies: the two
# milestone-1 pairs with the largest gender skew. See biased_decisions.metrics.shortlist.
SHORTLIST_PAIRS: tuple = ("paralegal-attorney", "nurse-physician")

ENGINES: tuple = ("jev", "laya", "laya-mlx")


class ScoreError(RuntimeError):
    """A cell could not be scored -- usually a record with missing rows for this cue."""


def _answers(path: Path) -> Dict[str, dict]:
    """A record's rows, keyed by id, reduced to each row's ``Occupation`` answer body."""
    return {item_id: row["answers"][QUESTION_NAME] for item_id, row in
            read_record_by_id(path).items()}


def load_answers(engine: str, task_slug: str, cue: str, *, root: Path = DEFAULT_ROOT
                 ) -> Dict[str, dict]:
    return _answers(record_path(engine, task_slug, cue, root=root))


def _missing(ids: Sequence[str], answers: Dict[str, dict], *, engine: str, task_slug: str,
            cue: str) -> None:
    missing = [i for i in ids if i not in answers]
    if missing:
        raise ScoreError(
            f"{len(missing)} of {len(ids)} items have no {engine!r} answer for "
            f"({task_slug!r}, {cue!r}), e.g. {missing[:3]} -- this cell's record is incomplete")


def _excluded_count(task: Task, present_source_ids) -> int:
    """How many held-out bios have no version for a cue at all: the ones a versions file's own
    ``source_id`` set does not cover, out of every ``split == "test"`` item."""
    total_test = sum(1 for item in task.load_items() if item.metadata.get("split") == "test")
    return total_test - len(set(present_source_ids))


# ---------------------------------------------------------------------------------------------
# gender-pronouns: every task, via the generalised pairs metrics (score_pair).
# ---------------------------------------------------------------------------------------------

def score_gender_pronouns(engine: str, task: Task) -> dict:
    items = task.load_items()
    test_items, twin_of_source = split_test_and_twins(items)
    answers = load_answers(engine, task.slug, "gender-pronouns", root=task.root)
    _missing([item.id for item in test_items], answers, engine=engine, task_slug=task.slug,
             cue="gender-pronouns")
    _missing([twin.id for twin in twin_of_source.values()], answers, engine=engine,
             task_slug=task.slug, cue="gender-pronouns")

    def verdict(item_id: str, answer_id: str, meta: dict) -> Verdict:
        answer = answers[answer_id]
        return Verdict(item_id, answer["choice"], answer["probabilities"][task.positive],
                       meta["reference_label"], meta["gender"])

    verdicts = [verdict(item.id, item.id, item.metadata) for item in test_items]
    twins = {source_id: verdict(source_id, twin.id, twin.metadata)
            for source_id, twin in twin_of_source.items()}
    pair_key = task.slug.replace("-", "_")
    return score_pair(pair=pair_key, engine=engine, verdicts=verdicts, twins=twins).as_row()


# ---------------------------------------------------------------------------------------------
# race-name: surgeon-physician only.
# ---------------------------------------------------------------------------------------------

def score_race_name(engine: str, task: Task) -> dict:
    versions = {item.id: item for item in task.load_versions("race-name")}
    if not versions:
        raise ScoreError(f"no race-name versions for {task.slug!r}; run 'bd build "
                         f"{task.slug} --cue race-name' first")
    answers = load_answers(engine, task.slug, "race-name", root=task.root)
    _missing(list(versions), answers, engine=engine, task_slug=task.slug, cue="race-name")

    by_source: Dict[str, Dict[str, str]] = {}
    for version_id, item in versions.items():
        by_source.setdefault(item.metadata["source_id"], {})[item.metadata["version"]] = \
            version_id

    def verdict(source_id: str, version_id: str) -> Verdict:
        item = versions[version_id]
        answer = answers[version_id]
        return Verdict(source_id, answer["choice"], answer["probabilities"][task.positive],
                       item.metadata["reference_label"], item.metadata["gender"])

    white_a = [verdict(sid, ids["white_a"]) for sid, ids in by_source.items()]
    white_b = {sid: verdict(sid, ids["white_b"]) for sid, ids in by_source.items()}
    black = {sid: verdict(sid, ids["black"]) for sid, ids in by_source.items()}
    excluded = _excluded_count(task, by_source)

    return score_arm_race(engine=engine, white_a=white_a, white_b=white_b, black=black,
                          excluded=excluded).as_row()


# ---------------------------------------------------------------------------------------------
# age-inserted: surgeon-physician only.
# ---------------------------------------------------------------------------------------------

def score_age_inserted(engine: str, task: Task) -> dict:
    versions = {item.id: item for item in task.load_versions("age-inserted")}
    if not versions:
        raise ScoreError(f"no age-inserted versions for {task.slug!r}; run 'bd build "
                         f"{task.slug} --cue age-inserted' first")
    answers = load_answers(engine, task.slug, "age-inserted", root=task.root)
    _missing(list(versions), answers, engine=engine, task_slug=task.slug, cue="age-inserted")

    by_source: Dict[str, Dict[int, str]] = {}
    for version_id, item in versions.items():
        by_source.setdefault(item.metadata["source_id"], {})[item.metadata["age"]] = version_id

    def verdict(source_id: str, version_id: str) -> Verdict:
        item = versions[version_id]
        answer = answers[version_id]
        return Verdict(source_id, answer["choice"], answer["probabilities"][task.positive],
                       item.metadata["reference_label"], item.metadata["gender"])

    v34 = [verdict(sid, ids[34]) for sid, ids in by_source.items()]
    v35 = {sid: verdict(sid, ids[35]) for sid, ids in by_source.items()}
    v61 = {sid: verdict(sid, ids[61]) for sid, ids in by_source.items()}
    v62 = {sid: verdict(sid, ids[62]) for sid, ids in by_source.items()}
    excluded = _excluded_count(task, by_source)

    return score_arm_age(engine=engine, v34=v34, v35=v35, v61=v61, v62=v62,
                         excluded=excluded).as_row()


# ---------------------------------------------------------------------------------------------
# race-fullname: surgeon-physician only; sample "all" or "500" (the shared Jev subsample).
# ---------------------------------------------------------------------------------------------

def _subsample_ids(task: Task, cue: str) -> Set[str]:
    path = task.versions_dir() / f"{cue}_jev-subsample.txt"
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()}


def score_race_fullname(engine: str, task: Task, *, sample: Optional[str] = None) -> dict:
    versions = {item.id: item for item in task.load_versions("race-fullname")}
    if not versions:
        raise ScoreError(f"no race-fullname versions for {task.slug!r}; run 'bd build "
                         f"{task.slug} --cue race-fullname' first (needs spaCy and the pools)")
    answers = load_answers(engine, task.slug, "race-fullname", root=task.root)

    by_bio: Dict[str, Dict[str, List[Optional[Verdict]]]] = {}
    for version_id, item in versions.items():
        meta = item.metadata
        source_id = meta["source_id"]
        slots = by_bio.setdefault(source_id, {group: [None] * 4 for group in FULLNAME_GROUPS})
        if version_id in answers:
            answer = answers[version_id]
            slots[meta["group"]][meta["k"] - 1] = Verdict(
                source_id, answer["choice"], answer["probabilities"][task.positive],
                meta["reference_label"], meta["gender"])

    eligible_ids = set(by_bio)
    complete_ids = {sid for sid, groups in by_bio.items()
                    if all(v is not None for slots in groups.values() for v in slots)}
    subsample = _subsample_ids(task, "race-fullname")

    if sample is None:
        if complete_ids == eligible_ids:
            sample = "all"
        elif subsample and complete_ids == subsample:
            sample = "500"
        else:
            raise ScoreError(
                f"{engine!r}'s race-fullname record for {task.slug!r} covers "
                f"{len(complete_ids)} of {len(eligible_ids)} eligible bios, which is neither "
                f"all of them nor exactly the {len(subsample)}-bio Jev subsample -- pass "
                f"--sample explicitly")

    if sample == "all":
        bios = eligible_ids
    elif sample == "500":
        if not subsample:
            raise ScoreError(f"no race-fullname_jev-subsample.txt for {task.slug!r}")
        bios = subsample
    else:
        raise ScoreError(f"--sample must be 'all' or '500', got {sample!r}")

    incomplete = sorted(bios - complete_ids)
    if incomplete:
        raise ScoreError(
            f"{len(incomplete)} of {len(bios)} bios in sample {sample!r} have no complete "
            f"{engine!r} race-fullname answer, e.g. {incomplete[:3]}")

    restricted = {sid: by_bio[sid] for sid in bios}
    excluded = _excluded_count(task, by_bio)

    return score_arm_race2(engine=engine, sample=sample, by_bio=restricted,
                           excluded=excluded).as_row()


SCORERS = {
    "gender-pronouns": score_gender_pronouns,
    "race-name": score_race_name,
    "race-fullname": score_race_fullname,
    "age-inserted": score_age_inserted,
}


def score(engine: str, task: Task, cue: str, **kwargs) -> dict:
    try:
        scorer = SCORERS[cue]
    except KeyError as error:
        raise ScoreError(f"unknown cue {cue!r}; one of {tuple(SCORERS)}") from error
    if cue != "race-fullname":
        kwargs.pop("sample", None)
    return scorer(engine, task, **kwargs)


# ---------------------------------------------------------------------------------------------
# The shortlist block: paralegal-attorney and nurse-physician, engine_alone and twin_averaged.
# ---------------------------------------------------------------------------------------------

def score_shortlist(engine: str, task: Task) -> List[dict]:
    test_items = [item for item in task.load_items() if item.metadata.get("split") == "test"]
    items_map = {item.id: (item.metadata["reference_label"], item.metadata["gender"])
                for item in test_items}
    answers = load_answers(engine, task.slug, "gender-pronouns", root=task.root)
    _missing([item.id for item in test_items], answers, engine=engine, task_slug=task.slug,
             cue="gender-pronouns")
    scores = {item_id: float(answer["probabilities"][task.positive])
             for item_id, answer in answers.items()}
    pair_key = task.slug.replace("-", "_")

    rows = shortlist_metrics.score(items_map, scores, task.positive, engine, pair_key,
                                   "engine_alone")
    averaged = shortlist_metrics.twin_averaged_scores(items_map, scores)
    rows += shortlist_metrics.score(items_map, averaged, task.positive, engine, pair_key,
                                    "twin_averaged")
    return rows


def has_record(engine: str, task_slug: str, cue: str, *, root: Path = DEFAULT_ROOT) -> bool:
    return record_path(engine, task_slug, cue, root=root).exists()


def write_rows(path: Path, new_rows: Sequence[dict], key_fields: Tuple[str, ...]) -> None:
    """Write ``new_rows`` into ``path``, keeping every existing row whose ``key_fields`` do not
    match one of them and replacing (never appending onto) the ones that do.

    The file itself is always fully rewritten (``"w"`` mode) -- never the blind
    ``open(path, "a")`` Jev-Flywheel's own study scripts used, which could accumulate a stale
    duplicate row if a study were re-run after its method changed. A row's ``key_fields`` say
    which of its own fields make it "the same measurement" as another: ``("engine",)`` for the
    four per-cue studies, ``("engine", "sample")`` for race-fullname's two samples,
    ``("engine", "variant", "cut")`` for the shortlist block.
    """
    existing: List[dict] = []
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            existing = [json.loads(line) for line in handle if line.strip()]

    def key(row: dict) -> tuple:
        return tuple(row.get(field) for field in key_fields)

    new_keys = {key(row) for row in new_rows}
    kept = [row for row in existing if key(row) not in new_keys]
    all_rows = kept + list(new_rows)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def every_cell(*, root: Path = DEFAULT_ROOT):
    """Every ``(engine, task_slug, cue)`` that has a committed record, in a fixed, stable order
    -- what ``bd list``/``bd replay`` iterate over."""
    for task_slug in BIOS_TASKS:
        for cue in TASK_CUES[task_slug]:
            for engine in ENGINES:
                if has_record(engine, task_slug, cue, root=root):
                    yield engine, task_slug, cue
