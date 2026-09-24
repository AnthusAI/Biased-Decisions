"""``bd build``: write a cue's versions file from a task's ``items.jsonl``, deterministically.

Every builder here reads the task's held-out (``split == "test"``) items, sorted by id for a
reproducible draw, and writes exactly the rows Jev-Flywheel's own fixture-build scripts wrote
(``scripts/build_bios_race_fixtures.py``, ``build_bios_race2_fixtures.py``,
``build_bios_age_fixtures.py`` -- the gender-pronouns twins never had a separate build script;
they were written inline into ``items.jsonl`` by the batch build). Byte-for-byte reproduction of
the committed ``versions/*.jsonl`` files was checked against this exact code before it was
written here -- see the module docstrings on ``biased_decisions.cues`` for the algorithms
themselves; this module only supplies the seeding, sorting and row shape around them.

One finding worth recording: ``biased_decisions.cues.gender``'s own docstring says the published
``gender-pronouns`` twins were built with its *amended* rule. They were not -- empirically,
``swap_gender(text, rule=ORIGINAL_RULE)`` reproduces all 2,000 committed twins on every
milestone-1 task byte-for-byte, and the amended rule only agrees with ~99% of them (it diverges
on bios containing "Miss"/"Sir"/"Madam" or a protected medical phrase, the exact tokens the
amendment changed). ``build_gender_pronouns`` below uses ``ORIGINAL_RULE`` accordingly; see
``RESULTS.md``'s footnotes for the artefact rates this produced.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from biased_decisions.cues.age import eligible, insert_age
from biased_decisions.cues.antisemitism import CUES as ANTISEMITISM_INSERTION_CUES
from biased_decisions.cues.antisemitism import surname_versions
from biased_decisions.cues.antisemitism import versions_for as antisemitism_versions_for
from biased_decisions.cues.fullname import analyze_full_name, render_full_name
from biased_decisions.cues.gender import ORIGINAL_RULE, swap_gender
from biased_decisions.cues.insertion import eligible as insertion_eligible
from biased_decisions.cues.insertion import GENDERED_CUES, insert_clause, versions_for
from biased_decisions.cues.names import name_versions
from biased_decisions.cues.neutral import neutralize
from biased_decisions import stereotypes, stereotypes_batch3
from biased_decisions.tasks.base import Task
from biased_decisions.tasks.items import Item

RACE_NAME_VERSIONS: Tuple[str, ...] = ("white_a", "white_b", "black")
AGE_VALUES: Tuple[int, ...] = (34, 35, 61, 62)
FULLNAME_GROUPS: Tuple[str, ...] = ("white", "black", "hispanic", "asian")
FULLNAME_NAMES_PER_GROUP = 4
FULLNAME_SUBSAMPLE_SIZE = 500
ASK_TWICE_SUBSAMPLE_SIZE = 500
ASK_TWICE_SEED = 0

DEFAULT_POOLS_PATH = Path(__file__).resolve().parents[1] / "pools" / "name_pools.json"

CUES: Tuple[str, ...] = (
    "gender-pronouns", "race-name", "race-fullname", "age-inserted",
    "disability", "religion", "religion-v2", "veteran-status", "sexuality", "gender-identity",
    "ask-twice", "neutral",
) + ANTISEMITISM_INSERTION_CUES + ("antisemitism-surname",)


class BuildError(RuntimeError):
    """A cue could not be built -- a missing optional dependency, or a missing input file."""


@dataclass(frozen=True)
class BuildResult:
    """What one ``bd build`` call produced: the rows it wrote (in file order), how many test
    items had no insertion point for the cue and so carry no version, and -- for
    ``race-fullname`` only -- the 500-bio Jev subsample drawn alongside the versions."""

    rows: List[dict]
    excluded: int
    subsample: Optional[List[str]] = None


def _test_items_sorted(task: Task) -> List[Item]:
    items = [item for item in task.load_items() if item.metadata.get("split") == "test"]
    items.sort(key=lambda item: item.id)
    return items


def _test_items_in_file_order(task: Task) -> List[Item]:
    """Held-out items in ``items.jsonl``'s own row order (not sorted by id) -- the order
    batch-1's ``scripts/03_build_insertion_cues.py`` iterated in, which the committed
    ``disability``/``religion``/``religion-v2`` versions files preserve."""
    return [item for item in task.load_items() if item.metadata.get("split") == "test"]


def build_gender_pronouns(task: Task) -> BuildResult:
    """Every held-out bio's gender-pronouns twin, recomputed from ``items.jsonl`` with
    ``ORIGINAL_RULE`` -- see this module's docstring for why.

    Unlike ``build_race_name``/``build_age_inserted``, ``swap_gender`` never refuses a bio (it
    has no "no insertion point" case the way ``insert_name``/``insert_age`` do -- a bio with no
    gendered token to swap just comes back unchanged). Checked against the committed twins: a
    handful of bios do swap to nothing, and their twin is still committed, with text identical
    to the original. So every test item gets a twin here too, and ``excluded`` is always 0.
    """
    flip_gender = {"male": "female", "female": "male"}
    rows: List[dict] = []
    for item in _test_items_sorted(task):
        swap = swap_gender(item.text, rule=ORIGINAL_RULE)
        meta = dict(item.metadata)
        gender = meta.get("gender")
        meta.update({"split": "counterfactual", "counterfactual_of": item.id,
                     "swapped": swap.swapped, "her_resolved": swap.her_resolved,
                     "gender": flip_gender.get(gender, gender)})
        rows.append({"id": f"{item.id}-swapped", "text": swap.text, "metadata": meta})
    return BuildResult(rows=rows, excluded=0)


def build_race_name(task: Task, *, seed: int = 0) -> BuildResult:
    """The race-name (Bertrand & Mullainathan) versions: two white names and one Black name per
    eligible bio, drawn from one ``random.Random(seed)`` advanced in item-id order. Ported
    ordering from Jev-Flywheel's ``scripts/build_bios_race_fixtures.py``."""
    rng = random.Random(seed)
    rows: List[dict] = []
    excluded = 0
    for item in _test_items_sorted(task):
        versions = name_versions(item.text, item.metadata["gender"], rng)
        if versions is None:
            excluded += 1
            continue
        for version in RACE_NAME_VERSIONS:
            text = getattr(versions, version)
            name = versions.names[version]
            rows.append({
                "id": f"{item.id}-{version}",
                "text": text,
                "metadata": {
                    "version": version, "name": name, "source_id": item.id,
                    "occupation": item.metadata["occupation"], "gender": item.metadata["gender"],
                    "reference_label": item.metadata["reference_label"],
                },
            })
    return BuildResult(rows=rows, excluded=excluded)


def build_age_inserted(task: Task) -> BuildResult:
    """The age-inserted versions (34/35/61/62) for every eligible bio. Ported ordering from
    Jev-Flywheel's ``scripts/build_bios_age_fixtures.py``."""
    rows: List[dict] = []
    excluded = 0
    for item in _test_items_sorted(task):
        if not eligible(item.text):
            excluded += 1
            continue
        for age in AGE_VALUES:
            insertion = insert_age(item.text, age)
            assert insertion is not None, f"{item.id} passed eligible() but insert_age failed"
            rows.append({
                "id": f"{item.id}-age{age}",
                "text": insertion.text,
                "metadata": {
                    "age": age, "case": insertion.case, "source_id": item.id,
                    "occupation": item.metadata["occupation"], "gender": item.metadata["gender"],
                    "reference_label": item.metadata["reference_label"],
                },
            })
    return BuildResult(rows=rows, excluded=excluded)


def _load_pools(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))["groups"]
    except FileNotFoundError as error:
        raise BuildError(
            f"race-fullname needs the name pools ({path}); see pools/README.md") from error


def build_race_fullname(task: Task, *, pools_path: Path = DEFAULT_POOLS_PATH,
                        seed: int = 0, subsample_seed: int = 0) -> BuildResult:
    """The race-fullname (Rosenman/Census) versions: 4 names per group (white, black, hispanic,
    asian) for every bio with an insertion point, plus the 500-bio Jev subsample. Needs spaCy
    (``analyze_full_name``) and the committed name pools; raises ``BuildError`` with a clear
    message if either is missing. Ported ordering from Jev-Flywheel's
    ``scripts/build_bios_race2_fixtures.py``: names are drawn for every test bio, eligible or
    not, before eligibility is checked, so a later bio's names never shift because an earlier
    one turned out to have no insertion point.
    """
    pools = _load_pools(pools_path)
    try:
        from biased_decisions.cues.redaction import _load_nlp
        _load_nlp()
    except ImportError as error:
        raise BuildError(
            "race-fullname needs spaCy (pip install 'biased-decisions[build]')") from error

    rng = random.Random(seed)
    rows: List[dict] = []
    eligible_ids: List[str] = []
    excluded = 0

    for item in _test_items_sorted(task):
        gender = item.metadata["gender"]
        plan = analyze_full_name(item.text)

        drawn = []
        for group in FULLNAME_GROUPS:
            first_group = "white" if pools[group]["uses_white_first_pool"] else group
            first_pool = pools[first_group]["first"][gender]
            last_pool = pools[group]["last"]
            for k in range(1, FULLNAME_NAMES_PER_GROUP + 1):
                first = rng.choice(first_pool)
                last = rng.choice(last_pool)
                drawn.append((group, k, first, last))

        if not plan.has_insertion_point:
            excluded += 1
            continue

        eligible_ids.append(item.id)
        for group, k, first, last in drawn:
            result = render_full_name(plan, first, last)
            rows.append({
                "id": f"{item.id}-{group}-{k}",
                "text": result.text,
                "metadata": {
                    "group": group, "k": k, "first": first, "last": last,
                    "source_id": item.id, "occupation": item.metadata["occupation"],
                    "gender": gender, "reference_label": item.metadata["reference_label"],
                },
            })

    sub_rng = random.Random(subsample_seed)
    subsample = sub_rng.sample(sorted(eligible_ids),
                               min(FULLNAME_SUBSAMPLE_SIZE, len(eligible_ids)))
    subsample.sort()

    return BuildResult(rows=rows, excluded=excluded, subsample=subsample)


def build_insertion(task: Task, cue: str) -> BuildResult:
    """A cue whose versions file is a clause inserted before every eligible held-out bio's
    first subject pronoun (``disability``, ``religion``, ``religion-v2``). Ported ordering from
    batch-1's ``scripts/03_build_insertion_cues.py`` -- see ``biased_decisions.cues.insertion``
    for the eligibility rule and clause tables."""
    rows: List[dict] = []
    excluded = 0
    for item in _test_items_in_file_order(task):
        if not insertion_eligible(item.text):
            excluded += 1
            continue
        if cue in GENDERED_CUES and item.metadata.get("gender") not in ("male", "female"):
            raise BuildError(f"{cue!r} is gender-matched but {item.id} has gender "
                             f"{item.metadata.get('gender')!r}")
        for version, clause in versions_for(cue, item.metadata.get("gender")):
            rows.append({
                "id": f"{item.id}-{cue}-{version}",
                # a clause of None is the bio exactly as written (gender-identity's "asis")
                "text": item.text if clause is None else insert_clause(item.text, clause),
                "metadata": {
                    "cue": cue, "version": version, "source_id": item.id,
                    "occupation": item.metadata.get("occupation"),
                    "gender": item.metadata.get("gender"),
                    "reference_label": item.metadata.get("reference_label"),
                },
            })
    return BuildResult(rows=rows, excluded=excluded)


def build_disability(task: Task) -> BuildResult:
    return build_insertion(task, "disability")


def build_religion(task: Task) -> BuildResult:
    return build_insertion(task, "religion")


def build_religion_v2(task: Task) -> BuildResult:
    return build_insertion(task, "religion-v2")


def build_antisemitism_insertion(task: Task, cue: str) -> BuildResult:
    """One of the four antisemitic-tropes-in-depth clause-insertion cues (``antisemitism-secular``,
    ``antisemitism-religious``, ``antisemitism-nationality``, ``antisemitism-role`` -- see
    ``biased_decisions.cues.antisemitism`` for the clause tables and
    ``docs/antisemitic-tropes-preregistration.md`` for the study). Same mechanics as
    ``build_insertion`` (eligibility, clause insertion, file order), sourced from the new module's
    own tables instead of ``biased_decisions.cues.insertion``'s.
    """
    rows: List[dict] = []
    excluded = 0
    for item in _test_items_in_file_order(task):
        if not insertion_eligible(item.text):
            excluded += 1
            continue
        for version, clause in antisemitism_versions_for(cue):
            rows.append({
                "id": f"{item.id}-{cue}-{version}",
                "text": insert_clause(item.text, clause),
                "metadata": {
                    "cue": cue, "version": version, "source_id": item.id,
                    "occupation": item.metadata.get("occupation"),
                    "gender": item.metadata.get("gender"),
                    "reference_label": item.metadata.get("reference_label"),
                },
            })
    return BuildResult(rows=rows, excluded=excluded)


def build_antisemitism_secular(task: Task) -> BuildResult:
    return build_antisemitism_insertion(task, "antisemitism-secular")


def build_antisemitism_religious(task: Task) -> BuildResult:
    return build_antisemitism_insertion(task, "antisemitism-religious")


def build_antisemitism_nationality(task: Task) -> BuildResult:
    return build_antisemitism_insertion(task, "antisemitism-nationality")


def build_antisemitism_role(task: Task) -> BuildResult:
    return build_antisemitism_insertion(task, "antisemitism-role")


def build_antisemitism_surname(task: Task) -> BuildResult:
    """The antisemitic-tropes-in-depth surname cue: a Jewish-associated surname vs. a
    matched-frequency floor surname, first name held constant per bio (see
    ``biased_decisions.cues.antisemitism.surname_versions``). Sorted-id order (like
    ``race-fullname``, not file order), since the surname a bio receives depends on its position
    in the sorted draw, not on where it happens to sit in ``items.jsonl``.
    """
    rows: List[dict] = []
    excluded = 0
    for index, item in enumerate(_test_items_sorted(task)):
        gender = item.metadata.get("gender")
        versions = surname_versions(item.text, gender, index)
        if versions is None:
            excluded += 1
            continue
        for version, text, surname in (
            ("jewish", versions.jewish_text, versions.jewish_surname),
            ("floor", versions.floor_text, versions.floor_surname),
        ):
            rows.append({
                "id": f"{item.id}-antisemitism-surname-{version}",
                "text": text,
                "metadata": {
                    "cue": "antisemitism-surname", "version": version, "source_id": item.id,
                    "first": versions.first, "surname": surname,
                    "occupation": item.metadata.get("occupation"), "gender": gender,
                    "reference_label": item.metadata.get("reference_label"),
                },
            })
    return BuildResult(rows=rows, excluded=excluded)


def build_veteran_status(task: Task) -> BuildResult:
    return build_insertion(task, "veteran-status")


def build_sexuality(task: Task) -> BuildResult:
    return build_insertion(task, "sexuality")


def build_gender_identity(task: Task) -> BuildResult:
    return build_insertion(task, "gender-identity")


def build_ask_twice(task: Task, *, seed: int = ASK_TWICE_SEED,
                    size: int = ASK_TWICE_SUBSAMPLE_SIZE) -> BuildResult:
    """The ``ask-twice`` noise-floor subsample: 500 held-out ids drawn
    ``random.Random(0).sample(sorted(test_ids), 500)``, then sorted again for a stable file --
    the same method as ``race-fullname``'s Jev subsample and Jev-Flywheel's own
    ``race2_jev_subsample.txt``. Carries no rows of its own (there is no edited text -- the same
    bio is simply asked a second time); the 500 ids come back as ``BuildResult.subsample``, and
    ``write_versions`` writes them to ``versions/ask-twice.txt``, one id per line, instead of a
    ``.jsonl`` file."""
    test_ids = sorted(item.id for item in task.load_items()
                      if item.metadata.get("split") == "test")
    rng = random.Random(seed)
    subsample = rng.sample(test_ids, min(size, len(test_ids)))
    subsample.sort()
    return BuildResult(rows=[], excluded=len(test_ids) - len(subsample), subsample=subsample)


def build_neutral(task: Task) -> BuildResult:
    """Neutral-pronoun rewrites: two versions per held-out bio (blank and they).

    For each held-out item, computes neutralize(text, style) for style in ("blank", "they").
    If leftover is True (gendered tokens remain), skips that (item, version) pair and counts
    it in excluded. Emits rows with id f"{item.id}-neutral-{version}" and appropriate metadata.
    """
    rows: List[dict] = []
    excluded = 0
    excluded_by_version: Dict[str, int] = {"blank": 0, "they": 0}

    for item in _test_items_sorted(task):
        for version in ("blank", "they"):
            neutral = neutralize(item.text, version)
            if neutral.leftover:
                excluded += 1
                excluded_by_version[version] += 1
                continue
            rows.append({
                "id": f"{item.id}-neutral-{version}",
                "text": neutral.text,
                "metadata": {
                    "cue": "neutral",
                    "version": version,
                    "source_id": item.id,
                    "occupation": item.metadata.get("occupation"),
                    "gender": item.metadata.get("gender"),
                    "reference_label": item.metadata.get("reference_label"),
                },
            })

    return BuildResult(rows=rows, excluded=excluded)


BUILDERS = {
    "gender-pronouns": build_gender_pronouns,
    "race-name": build_race_name,
    "race-fullname": build_race_fullname,
    "age-inserted": build_age_inserted,
    "disability": build_disability,
    "religion": build_religion,
    "religion-v2": build_religion_v2,
    "veteran-status": build_veteran_status,
    "sexuality": build_sexuality,
    "gender-identity": build_gender_identity,
    "ask-twice": build_ask_twice,
    "neutral": build_neutral,
    "antisemitism-secular": build_antisemitism_secular,
    "antisemitism-religious": build_antisemitism_religious,
    "antisemitism-nationality": build_antisemitism_nationality,
    "antisemitism-role": build_antisemitism_role,
    "antisemitism-surname": build_antisemitism_surname,
}


def build_stereotype_items(task: Task) -> BuildResult:
    """The stereotypes pool (``items.jsonl``), drawn from the four source tasks under the task's
    root; see ``biased_decisions.stereotypes``. Written by ``write_stereotype_items``."""
    return BuildResult(rows=stereotypes.build_items(task.root), excluded=0)


def _stereotype_versions(axis: str):
    def builder(task: Task) -> BuildResult:
        items = [{"id": i.id, "text": i.text, "metadata": i.metadata} for i in task.load_items()]
        return BuildResult(rows=stereotypes.build_versions(items, axis), excluded=0)
    return builder


# Cues of the ``stereotypes`` task: ``bd``-style ``build("religion", task)`` on that task.
STEREOTYPE_BUILDERS = {"religion": _stereotype_versions("religion"),
                       "nationality": _stereotype_versions("nationality")}


def build_stereotype_batch3_items(task: Task) -> BuildResult:
    """The batch 3 pool: the same 2,000 bios as batch 2 (``stereotypes.build_items``), drawn from the
    four source tasks under the task's root."""
    return BuildResult(rows=stereotypes.build_items(task.root), excluded=0)


def _stereotype_batch3_versions(axis: str):
    def builder(task: Task) -> BuildResult:
        items = [{"id": i.id, "text": i.text, "metadata": i.metadata} for i in task.load_items()]
        return BuildResult(rows=stereotypes_batch3.build_versions(items, axis), excluded=0)
    return builder


# Axes of the ``stereotypes-batch3`` task, one versions file each.
STEREOTYPE_BATCH3_BUILDERS = {axis: _stereotype_batch3_versions(axis)
                              for axis in stereotypes_batch3.CLAUSES}


def write_stereotype_items(task: Task, result: BuildResult) -> Path:
    path = task.items_path
    with path.open("w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def build(cue: str, task: Task) -> BuildResult:
    if task.slug == stereotypes_batch3.SLUG:
        try:
            return STEREOTYPE_BATCH3_BUILDERS[cue](task)
        except KeyError as error:
            raise BuildError(f"unknown stereotypes-batch3 axis {cue!r}") from error
    if task.slug == stereotypes.SLUG:
        try:
            return STEREOTYPE_BUILDERS[cue](task)
        except KeyError as error:
            raise BuildError(f"unknown stereotypes axis {cue!r}") from error
    """Dispatch to the builder for ``cue``. Raises ``BuildError`` (never a bare ``KeyError``)
    for an unknown cue, so the CLI can print it without a traceback."""
    try:
        builder = BUILDERS[cue]
    except KeyError as error:
        raise BuildError(f"unknown cue {cue!r}; one of {tuple(BUILDERS)}") from error
    return builder(task)


def write_versions(task: Task, cue: str, result: BuildResult) -> Path:
    """Write ``result``'s rows to the cue's versions file (and, for ``race-fullname``, the
    subsample file alongside it), returning the versions file's path.

    ``ask-twice`` has no rows at all (see ``build_ask_twice``) -- only its 500-id subsample is
    written, to ``versions/ask-twice.txt``, and that path is what is returned.
    """
    if cue == "ask-twice":
        path = task.versions_dir() / "ask-twice.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(result.subsample or []) + "\n", encoding="utf-8")
        return path

    path = task.versions_path(cue)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if result.subsample is not None:
        sub_path = task.versions_dir() / f"{cue}_jev-subsample.txt"
        sub_path.write_text("\n".join(result.subsample) + "\n", encoding="utf-8")
    return path
