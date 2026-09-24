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

from biased_decisions.cues.insertion import RELIGIONS
from biased_decisions.metrics import insertion as insertion_metrics
from biased_decisions.metrics import neutral as neutral_metrics
from biased_decisions.metrics import shortlist as shortlist_metrics
from biased_decisions.metrics.flips import Verdict, score_arm_race, score_pair
from biased_decisions.metrics.shifts import score_arm_age, score_arm_race2
from biased_decisions import stereotypes, stereotypes_batch3
from biased_decisions.record import read_record_by_id, record_path
from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.tasks.bios import BIOS_TASKS, ORIGINAL_BIOS_TASKS, split_test_and_twins

QUESTION_NAME = "Occupation"
FULLNAME_GROUPS = ("white", "black", "hispanic", "asian")

# Every task's cues, in the design doc's order. gender-pronouns is answered on all seven tasks;
# race-name/race-fullname/age-inserted only exist for surgeon-physician (milestone 1, see
# data/MANIFEST.md). Batch 1 (milestone 1b) adds disability/religion/religion-v2 on all seven
# tasks, and ask-twice/option-order on the four original ones (they reuse the original tasks'
# 500-bio noise-floor subsample -- see docs/design.md's "Milestone 1b" section and
# studies/batch1/BUILD.md). Not every (task, cue) pair in this table has a record for every
# engine -- has_record() is what actually gates a cell; e.g. Jev's disability record exists only
# for surgeon-physician and paralegal-attorney, and religion/religion-v2 were never sent to Jev.
INSERTION_CUES: tuple = ("disability", "religion", "religion-v2")
NOISE_FLOOR_CUES: tuple = ("ask-twice", "option-order")
NEUTRAL_CUES: tuple = ("neutral",)
TASK_CUES: Dict[str, tuple] = {
    "surgeon-physician": (("gender-pronouns", "race-name", "race-fullname", "age-inserted")
                         + INSERTION_CUES + NOISE_FLOOR_CUES + NEUTRAL_CUES),
    "nurse-physician": ("gender-pronouns",) + INSERTION_CUES + NOISE_FLOOR_CUES + NEUTRAL_CUES,
    "teacher-professor": ("gender-pronouns",) + INSERTION_CUES + NOISE_FLOOR_CUES + NEUTRAL_CUES,
    "paralegal-attorney": ("gender-pronouns",) + INSERTION_CUES + NOISE_FLOOR_CUES + NEUTRAL_CUES,
    "journalist-professor": ("gender-pronouns",) + INSERTION_CUES + NEUTRAL_CUES,
    "architect-interior-designer": ("gender-pronouns",) + INSERTION_CUES + NEUTRAL_CUES,
    "dietitian-physician": ("gender-pronouns",) + INSERTION_CUES + NEUTRAL_CUES,
}

# The pairs bios_shortlist.jsonl (and this package's shortlist replay) studies: the two
# milestone-1 pairs with the largest gender skew. See biased_decisions.metrics.shortlist.
SHORTLIST_PAIRS: tuple = ("paralegal-attorney", "nurse-physician")

ENGINES: tuple = ("jev", "laya", "laya-mlx", "kev")

# The regulated-decision tasks (docs/regulated-tasks-preregistration.md): each cue's floor (or
# reference) version and the versions read against it. Race and gender on Q-Pain are read against
# the White and the man version of the same vignette; the others against a same-shape neutral clause.
REGULATED_SHAPE: Dict[str, Dict[str, tuple]] = {
    "qpain-treatment": {
        "race": ("white", ("black", "asian", "hispanic")),
        "gender": ("man", ("woman",)),
        "disability": ("floor-cyclist", ("wheelchair",)),
        "veteran-status": ("floor-peace-corps", ("iraq", "navy")),
    },
    "civil-comments-moderation": {
        "race": ("floor-suburban", ("black", "asian")),
        "religion": ("floor-vegetarian", ("muslim", "christian", "jewish")),
        "sexual-orientation": ("floor-left-handed", ("gay", "lesbian")),
        "disability": ("floor-cyclist", ("wheelchair",)),
    },
    # Batch 2's trope axes: floor version, then the groups read against it. Scored by
    # ``score_stereotypes`` (one row per engine, not the regulated shape's rows).
    stereotypes.SLUG: {axis: (spec.floor, spec.groups) for axis, spec in stereotypes.AXES.items()},
    stereotypes_batch3.SLUG: {axis: (spec.floor, spec.groups)
                              for axis, spec in stereotypes_batch3.AXES.items()},
}
REGULATED_TASKS: tuple = tuple(REGULATED_SHAPE)


class ScoreError(RuntimeError):
    """A cell could not be scored -- usually a record with missing rows for this cue."""


def _answers(path: Path) -> Dict[str, dict]:
    """A record's rows, keyed by id, reduced to each row's one answer body: ``Occupation`` for the
    bios tasks, ``Decision`` for the regulated-decision tasks."""
    return {item_id: row["answers"].get(QUESTION_NAME) or row["answers"]["Decision"]
            for item_id, row in read_record_by_id(path).items()}


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
# Insertion cues (disability, religion, religion-v2): batch 1 / milestone 1b.
# ---------------------------------------------------------------------------------------------

# cue -> (floor version, the non-floor versions it is measured against).
_INSERTION_SHAPE: Dict[str, tuple] = {
    "disability": ("floor-cyclist", ("wheelchair",)),
    "religion": ("floor-gardener", RELIGIONS),
    "religion-v2": ("floor-gardener", RELIGIONS),
}


def _insertion_by_source(task: Task, cue: str, answers: Dict[str, dict]) -> Dict[str, Dict]:
    versions = task.load_versions(cue)
    by_source: Dict[str, Dict[str, tuple]] = {}
    for item in versions:
        if item.id not in answers:
            continue
        answer = answers[item.id]
        by_source.setdefault(item.metadata["source_id"], {})[item.metadata["version"]] = (
            answer["choice"], float(answer["probabilities"][task.positive]))
    return by_source


def score_insertion(engine: str, task: Task, cue: str) -> dict:
    if not task.load_versions(cue):
        raise ScoreError(f"no {cue!r} versions for {task.slug!r}; run 'bd build {task.slug} "
                         f"--cue {cue}' first")
    answers = load_answers(engine, task.slug, cue, root=task.root)
    by_source = _insertion_by_source(task, cue, answers)
    floor_version, non_floor = _INSERTION_SHAPE[cue]
    # disability has no surviving batch-1 script; its committed Outcome numbers match the house
    # bootstrap convention, not 06_score.py's -- see biased_decisions.metrics.insertion's
    # module docstring.
    bootstrap_fn = (insertion_metrics.bootstrap_diffs_house if cue == "disability"
                    else insertion_metrics.bootstrap_diffs_local)
    metrics = insertion_metrics.score_insertion_cue(
        engine=engine, task=task.slug, cue=cue, positive=task.positive,
        floor_version=floor_version, non_floor_versions=non_floor, by_source=by_source,
        bootstrap_fn=bootstrap_fn)
    if metrics.n == 0:
        raise ScoreError(f"no complete {cue!r} answers for ({engine!r}, {task.slug!r}) -- every "
                         f"eligible bio needs an answer for the floor and every other version")
    return metrics.as_row()


def score_disability(engine: str, task: Task) -> dict:
    return score_insertion(engine, task, "disability")


def score_religion(engine: str, task: Task) -> dict:
    return score_insertion(engine, task, "religion")


def score_religion_v2(engine: str, task: Task) -> dict:
    return score_insertion(engine, task, "religion-v2")


# ---------------------------------------------------------------------------------------------
# ask-twice: the noise floor -- the same held-out bio, asked a second time, unchanged.
# ---------------------------------------------------------------------------------------------

def score_ask_twice(engine: str, task: Task) -> dict:
    ids_path = task.versions_dir() / "ask-twice.txt"
    if not ids_path.exists():
        raise ScoreError(f"no ask-twice.txt for {task.slug!r}; run 'bd build {task.slug} "
                         f"--cue ask-twice' first")
    ids = [line.strip() for line in ids_path.read_text(encoding="utf-8").splitlines()
          if line.strip()]
    first = load_answers(engine, task.slug, "gender-pronouns", root=task.root)
    second = load_answers(engine, task.slug, "ask-twice", root=task.root)

    def cell(answer: dict) -> tuple:
        return answer["choice"], float(answer["probabilities"][task.positive])

    first_cells = {i: cell(a) for i, a in first.items()}
    second_cells = {i: cell(a) for i, a in second.items()}
    metrics = insertion_metrics.score_ask_twice(
        engine=engine, task=task.slug, ids=ids, first=first_cells, second=second_cells)
    if metrics.n == 0:
        raise ScoreError(f"no ask-twice record for ({engine!r}, {task.slug!r})")
    return metrics.as_row()


# ---------------------------------------------------------------------------------------------
# option-order: does the answer change when the two options are listed the other way round?
# Reuses the gender-pronouns record for the committed order; needs the two
# option-order-reversed[-twins] records for the reversed one.
# ---------------------------------------------------------------------------------------------

# Ported verbatim from batch-1's 06_score_laya_religion_v2_and_order.py's own ``MORE_FEMALE``
# dict, used only for option-order's male-origin direction/shift stats -- deliberately NOT read
# from ``biased_decisions.metrics.flips.PAIR_INFO``: that table's ``surgeon_physician`` entry has
# ``more_female="surgeon"``, which disagrees with the corpus's own population share (physician is
# surgeon-physician's more-female label, 49.4% women vs surgeon's 14.8% -- see the batch-1
# pre-registration's section A and ``docs/design.md``). ``06_score.py``'s independently-written
# dict got this right, and every published option-order number for surgeon-physician was computed
# against it; this module matches it so ``bd replay`` reproduces those numbers, without touching
# ``PAIR_INFO`` itself (a pre-existing milestone-1 table, out of batch 1's scope -- see
# ``RESULTS.md``'s footnotes).
MORE_FEMALE_BY_TASK: Dict[str, str] = {
    "surgeon-physician": "physician", "nurse-physician": "nurse", "teacher-professor": "teacher",
    "paralegal-attorney": "paralegal", "journalist-professor": "journalist",
    "architect-interior-designer": "interior_designer", "dietitian-physician": "dietitian",
}


def score_option_order(engine: str, task: Task) -> dict:
    more_female = MORE_FEMALE_BY_TASK[task.slug]

    def cells(cue: str) -> Dict[str, tuple]:
        answers = load_answers(engine, task.slug, cue, root=task.root)
        return {i: (a["choice"], float(a["probabilities"][task.positive]))
               for i, a in answers.items()}

    committed = cells("gender-pronouns")  # holds both as-written and "-swapped" twin ids
    reversed_items = cells("option-order-reversed")
    reversed_twins = cells("option-order-reversed-twins")  # {} for an engine with no twins record
    if not committed or not reversed_items:
        raise ScoreError(f"no option-order record for ({engine!r}, {task.slug!r}) -- needs at "
                         f"least gender-pronouns and option-order-reversed")

    genders = {item.id: item.metadata.get("gender") for item in task.load_items()}
    metrics = insertion_metrics.score_option_order(
        engine=engine, task=task.slug, positive=task.positive, more_female=more_female,
        committed_items=committed, committed_twins=committed, reversed_items=reversed_items,
        reversed_twins=reversed_twins, genders=genders)
    if metrics.n == 0:
        raise ScoreError(f"no overlapping option-order ids for ({engine!r}, {task.slug!r})")
    return metrics.as_row()


# ---------------------------------------------------------------------------------------------
# Port vs original: laya-mlx (the Apple-silicon port) vs laya (the original upstream package),
# gender-pronouns, the four original tasks only -- see import/laya-record/OUTCOME.md.
# ---------------------------------------------------------------------------------------------

def score_port_vs_original(task: Task) -> dict:
    if task.slug not in ORIGINAL_BIOS_TASKS:
        raise ScoreError(f"port-vs-original is only scored for the four original tasks, not "
                         f"{task.slug!r}")
    port_row = score_gender_pronouns("laya-mlx", task)
    original_row = score_gender_pronouns("laya", task)
    port_cells = {i: (a["choice"], float(a["probabilities"][task.positive])) for i, a in
                 load_answers("laya-mlx", task.slug, "gender-pronouns", root=task.root).items()}
    original_cells = {i: (a["choice"], float(a["probabilities"][task.positive])) for i, a in
                      load_answers("laya", task.slug, "gender-pronouns", root=task.root).items()}
    metrics = insertion_metrics.score_port_vs_original(
        task=task.slug, port=port_cells, original=original_cells,
        port_flip_pct=round(port_row["counterfactual_flip_rate"] * 100, 2),
        original_flip_pct=round(original_row["counterfactual_flip_rate"] * 100, 2))
    return metrics.as_row()


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


def score_neutral(engine: str, task: Task) -> dict:
    """The neutral-pronoun control: the male-pronoun and female-pronoun versions (the as-written bio
    and its pronoun-swapped twin, by the bio's own gender) against the two neutral rewrites."""
    test_items = [item for item in task.load_items() if item.metadata.get("split") == "test"]
    gender = load_answers(engine, task.slug, "gender-pronouns", root=task.root)
    neutral = load_answers(engine, task.slug, "neutral", root=task.root)
    by_source: Dict[str, Dict[str, float]] = {}
    for item in test_items:
        g = item.metadata.get("gender")
        if g not in ("male", "female"):
            continue
        written, swapped = gender.get(item.id), gender.get(f"{item.id}-swapped")
        if written is None or swapped is None:
            continue
        p_written = float(written["probabilities"][task.positive])
        p_swapped = float(swapped["probabilities"][task.positive])
        arms = {"he": p_written, "she": p_swapped} if g == "male" else {"he": p_swapped, "she": p_written}
        for version in ("blank", "they"):
            answer = neutral.get(f"{item.id}-neutral-{version}")
            if answer is not None:
                arms[version] = float(answer["probabilities"][task.positive])
        by_source[item.id] = arms
    if not by_source:
        raise ScoreError(f"no gender-pronouns answers for ({engine!r}, {task.slug!r})")
    dropped = {v: sum(1 for arms in by_source.values() if v not in arms) for v in ("blank", "they")}
    metrics = neutral_metrics.score_neutral_cue(engine=engine, task=task.slug, positive=task.positive,
                                                by_source=by_source, dropped=dropped)
    if metrics.n == 0:
        raise ScoreError(f"no bio has all four arms for ({engine!r}, {task.slug!r})")
    return metrics.as_row()


def score_regulated(engine: str, task: Task, cue: str) -> dict:
    shape = REGULATED_SHAPE.get(task.slug, {}).get(cue)
    if shape is None:
        raise ScoreError(f"no scoring shape for cue {cue!r} on {task.slug!r}")
    floor_version, non_floor = shape
    answers = load_answers(engine, task.slug, cue, root=task.root)
    by_source = _insertion_by_source(task, cue, answers)
    metrics = insertion_metrics.score_insertion_cue(
        engine=engine, task=task.slug, cue=cue, positive=task.positive,
        floor_version=floor_version, non_floor_versions=non_floor, by_source=by_source,
        bootstrap_fn=insertion_metrics.bootstrap_diffs_house)
    if metrics.n == 0:
        raise ScoreError(f"no complete {cue!r} answers for ({engine!r}, {task.slug!r})")
    return metrics.as_row()


SCORERS = {
    "neutral": score_neutral,
    "gender-pronouns": score_gender_pronouns,
    "race-name": score_race_name,
    "race-fullname": score_race_fullname,
    "age-inserted": score_age_inserted,
    "disability": score_disability,
    "religion": score_religion,
    "religion-v2": score_religion_v2,
    "ask-twice": score_ask_twice,
    "option-order": score_option_order,
}


def score_stereotypes(engine: str, task: Task, cue: str) -> dict:
    if cue not in stereotypes.AXES:
        raise ScoreError(f"no trope axis {cue!r} on {task.slug!r}; one of {tuple(stereotypes.AXES)}")
    try:
        return stereotypes.score_stereotypes(engine, task, cue)
    except KeyError as error:
        raise ScoreError(f"({engine!r}, {task.slug!r}, {cue!r}) has no answer for {error}") from error


def score_stereotypes_batch3(engine: str, task: Task, cue: str) -> dict:
    if cue not in stereotypes_batch3.AXES:
        raise ScoreError(f"no trope axis {cue!r} on {task.slug!r}; one of {tuple(stereotypes_batch3.AXES)}")
    try:
        return stereotypes_batch3.score_stereotypes(engine, task, cue)
    except KeyError as error:
        raise ScoreError(f"({engine!r}, {task.slug!r}, {cue!r}) has no answer for {error}") from error


def score(engine: str, task: Task, cue: str, **kwargs) -> dict:
    if task.slug == stereotypes_batch3.SLUG:
        return score_stereotypes_batch3(engine, task, cue)
    if task.slug == stereotypes.SLUG:
        return score_stereotypes(engine, task, cue)
    if task.slug in REGULATED_SHAPE:
        return score_regulated(engine, task, cue)
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
    if record_path(engine, task.slug, "neutral", root=task.root).exists():
        neutral = load_answers(engine, task.slug, "neutral", root=task.root)
        for version in ("blank", "they"):
            arm_scores = {}
            for item_id in items_map:
                answer = neutral.get(f"{item_id}-neutral-{version}")
                if answer is not None:
                    arm_scores[item_id] = float(answer["probabilities"][task.positive])
            arm_items = {i: items_map[i] for i in arm_scores}
            # No twin exists for a neutral rewrite: the counterfactual columns are not meaningful.
            arm_scores.update({f"{i}-swapped": arm_scores[i] for i in arm_items})
            rows += shortlist_metrics.score(arm_items, arm_scores, task.positive, engine, pair_key,
                                            f"neutral_{version}")
    return rows


def has_record(engine: str, task_slug: str, cue: str, *, root: Path = DEFAULT_ROOT) -> bool:
    """Whether an ``(engine, task_slug, cue)`` cell has a record to score. ``option-order`` has
    no ``option-order.jsonl.gz`` of its own -- it is scored from ``gender-pronouns`` (the
    committed order) and ``option-order-reversed`` (the reversed one); those two are required.
    ``option-order-reversed-twins`` is not -- Jev never answered the reversed order on the
    gender-swapped twins, so its cell scores the fields that do not need them (see
    ``biased_decisions.metrics.insertion.OptionOrderMetrics``)."""
    if cue == "option-order":
        return all(record_path(engine, task_slug, c, root=root).exists() for c in
                   ("gender-pronouns", "option-order-reversed"))
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
    for task_slug in REGULATED_TASKS:
        for cue in REGULATED_SHAPE[task_slug]:
            for engine in ENGINES:
                if has_record(engine, task_slug, cue, root=root):
                    yield engine, task_slug, cue
