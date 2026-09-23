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
from biased_decisions.cues.fullname import analyze_full_name, render_full_name
from biased_decisions.cues.gender import ORIGINAL_RULE, swap_gender
from biased_decisions.cues.names import name_versions
from biased_decisions.tasks.base import Task
from biased_decisions.tasks.items import Item

RACE_NAME_VERSIONS: Tuple[str, ...] = ("white_a", "white_b", "black")
AGE_VALUES: Tuple[int, ...] = (34, 35, 61, 62)
FULLNAME_GROUPS: Tuple[str, ...] = ("white", "black", "hispanic", "asian")
FULLNAME_NAMES_PER_GROUP = 4
FULLNAME_SUBSAMPLE_SIZE = 500

DEFAULT_POOLS_PATH = Path(__file__).resolve().parents[1] / "pools" / "name_pools.json"

CUES: Tuple[str, ...] = ("gender-pronouns", "race-name", "race-fullname", "age-inserted")


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


BUILDERS = {
    "gender-pronouns": build_gender_pronouns,
    "race-name": build_race_name,
    "race-fullname": build_race_fullname,
    "age-inserted": build_age_inserted,
}


def build(cue: str, task: Task) -> BuildResult:
    """Dispatch to the builder for ``cue``. Raises ``BuildError`` (never a bare ``KeyError``)
    for an unknown cue, so the CLI can print it without a traceback."""
    try:
        builder = BUILDERS[cue]
    except KeyError as error:
        raise BuildError(f"unknown cue {cue!r}; one of {tuple(BUILDERS)}") from error
    return builder(task)


def write_versions(task: Task, cue: str, result: BuildResult) -> Path:
    """Write ``result``'s rows to the cue's versions file (and, for ``race-fullname``, the
    subsample file alongside it), returning the versions file's path."""
    path = task.versions_path(cue)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if result.subsample is not None:
        sub_path = task.versions_dir() / f"{cue}_jev-subsample.txt"
        sub_path.write_text("\n".join(result.subsample) + "\n", encoding="utf-8")
    return path
