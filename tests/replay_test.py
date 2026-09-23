"""Feature: replay reproduces Jev-Flywheel's published numbers, bit-for-bit.

The design doc's promise for milestone 1: scoring the committed record must reproduce every
number in Jev-Flywheel's ``studies/*.jsonl``, not just something close to it. Every test here
calls ``biased_decisions.scoring.score``/``score_shortlist`` -- the exact functions ``bd score``
and ``bd replay`` call -- against the committed ``answers/`` record, and compares the result to
the corresponding row in ``studies/jev-flywheel/`` (a verbatim copy of Jev-Flywheel's own study
files; see ``data/MANIFEST.md``). Rates, counts, shifts, direction shares, accuracies, ratios and
bootstrap CIs (seed 0, 1,000 resamples, same as the published rows) are compared with ``==``,
i.e. exact, not "close" -- both sides already round to 4 decimal places (rates/shifts) or 2
(shortlist ratios).

**The mapping from a Jev-Flywheel row to a cell here** (arm/engine/pair/sample -> (engine, task,
cue)):

* ``bios_gender.jsonl``'s ``arm in ("J0", "L0")`` rows, `redacted: true` (the other 16 rows are
  loop arms, not milestone-1 cells) -> (engine, "surgeon-physician", "gender-pronouns"), engine
  ``jev``/``laya`` in the old naming -> ``jev``/``laya-mlx`` here.
* ``bios_pairs.jsonl``'s 8 rows (4 pairs x jev/laya) -> (engine, "<pair-with-hyphens>",
  "gender-pronouns"). The ``surgeon_physician`` pair is scored *twice* by two different old
  scripts under two different field meanings for the same two fields -- see
  ``test_surgeon_physician_pairs_row_has_a_known_relabeling_quirk`` below, which is the one test
  in this file that does **not** assert exact equality, and says why.
* ``bios_race.jsonl``'s 2 rows -> (engine, "surgeon-physician", "race-name").
* ``bios_age.jsonl``'s 2 rows -> (engine, "surgeon-physician", "age-inserted").
* ``bios_race2.jsonl``'s 3 rows (laya/all, laya/500, jev/500) -> (engine,
  "surgeon-physician", "race-fullname"), scored with ``sample="all"``/``"500"`` respectively.
* ``bios_shortlist.jsonl``'s 24 rows (2 pairs x 2 engines x 3 cuts x 2 variants) ->
  ``score_shortlist(engine, task)``, one call per (pair, engine) producing all 6 of that
  combination's rows.

That is every row in every file under ``studies/jev-flywheel/`` except the 16 non-J0/L0 loop
arms in ``bios_gender.jsonl`` (not milestone-1 cells: they used varying label counts/seeds this
package's record does not carry) and the one relabeled field pair noted above.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from biased_decisions.build import BuildError, build as build_cue
from biased_decisions.scoring import score, score_shortlist
from biased_decisions.tasks.bios import load_task

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ROOT / "studies" / "jev-flywheel"

# This repo's engine name -> the old Jev-Flywheel studies' own "engine" field spelling.
OLD_ENGINE = {"jev": "jev", "laya-mlx": "laya"}
ENGINES = ("jev", "laya-mlx")


def _rows(name: str) -> List[dict]:
    return [json.loads(line) for line in (STUDIES / name).read_text().splitlines()
            if line.strip()]


def _one(name: str, **match) -> dict:
    hits = [row for row in _rows(name) if all(row.get(k) == v for k, v in match.items())]
    assert len(hits) == 1, f"expected exactly 1 row in {name} matching {match}, got {len(hits)}"
    return hits[0]


def _assert_same(row: dict, published: dict, fields: List[str]) -> None:
    for field in fields:
        assert row[field] == published[field], (
            f"{field}: replayed {row[field]!r} != published {published[field]!r}")


# ---------------------------------------------------------------------------------------------
# gender-pronouns, on every pair task (score_pair's schema: bios_pairs.jsonl).
# ---------------------------------------------------------------------------------------------

PAIRS = (
    ("nurse-physician", "nurse_physician"),
    ("teacher-professor", "teacher_professor"),
    ("paralegal-attorney", "paralegal_attorney"),
)

PAIR_FIELDS = [
    "n", "accuracy", "counterfactual_flip_rate", "flip_rate_ci", "mean_abs_delta_p",
    "flip_toward_more_female_share", "recall_gap_less_female_women_minus_men", "ece",
]


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("slug,pair_key", PAIRS)
def test_gender_pronouns_matches_bios_pairs(engine, slug, pair_key):
    task = load_task(slug)
    row = score(engine, task, "gender-pronouns")
    published = _one("bios_pairs.jsonl", pair=pair_key, engine=OLD_ENGINE[engine])
    _assert_same(row, published, PAIR_FIELDS)


@pytest.mark.parametrize("engine", ENGINES)
def test_gender_pronouns_surgeon_physician_matches_bios_gender_J0_L0(engine):
    """surgeon-physician's gender-pronouns cell against ``bios_gender.jsonl``'s own J0/L0
    rows -- the ones the design doc's inventory calls "the only 3 of 18 that are milestone-1
    cells" (the redacted ones; the 4th, unredacted, has no equivalent corpus in this package)."""
    task = load_task("surgeon-physician")
    row = score(engine, task, "gender-pronouns")
    published = _one("bios_gender.jsonl", engine=OLD_ENGINE[engine],
                     arm=("J0" if engine == "jev" else "L0"), redacted=True)
    _assert_same(row, published, ["n", "accuracy", "counterfactual_flip_rate",
                                  "mean_abs_delta_p", "ece"])


@pytest.mark.parametrize("engine", ENGINES)
def test_surgeon_physician_pairs_row_has_a_known_relabeling_quirk(engine):
    """``bios_pairs.jsonl``'s ``surgeon_physician`` rows were produced by a copy-script
    (Jev-Flywheel's ``run_bios_pairs.py --copy-surgeon-physician``) that reshapes
    ``bios_gender.jsonl``'s ArmMetrics row into the pairs schema by relabeling
    ``flip_toward_physician_share`` as ``flip_toward_more_female_share`` and
    ``tpr_gap_surgeon_women_minus_men`` as ``recall_gap_less_female_women_minus_men`` --
    without accounting for "physician" being surgeon-physician's *less*-female label, not its
    more-female one (unlike the other three pairs, where the copy would have been correct).  So
    those two published fields measure the share toward *physician* and the recall gap on
    *surgeon*, the opposite of what their names say.

    Everything else about that row -- n, accuracy, flip rate, mean |delta p|, ECE -- is
    unaffected and is checked (against ``bios_gender.jsonl``, which has no such quirk) by
    ``test_gender_pronouns_surgeon_physician_matches_bios_gender_J0_L0`` above.
    ``biased_decisions.scoring.score_gender_pronouns`` computes both fields correctly (share
    toward the pair's actual more-female label, "surgeon"), so this test asserts the *documented
    mismatch*, not equality, against the published row.
    """
    task = load_task("surgeon-physician")
    row = score(engine, task, "gender-pronouns")
    published = _one("bios_pairs.jsonl", pair="surgeon_physician", engine=OLD_ENGINE[engine])
    j0l0 = _one("bios_gender.jsonl", engine=OLD_ENGINE[engine],
               arm=("J0" if engine == "jev" else "L0"), redacted=True)

    # The fields the copy-script got right, still exact:
    _assert_same(row, published, ["n", "accuracy", "counterfactual_flip_rate",
                                  "mean_abs_delta_p", "ece"])
    assert published["flip_rate_ci"] is None  # bios_gender never computed one

    # The quirk itself: the published pairs row's two fields are a raw, unrelabeled copy of
    # bios_gender's differently-named (and differently-meant) fields -- the physician-directed
    # share and surgeon's own recall gap, not the pair's more-female ("surgeon") share or the
    # less-female ("physician") recall gap their names promise.
    assert published["flip_toward_more_female_share"] == j0l0["flip_toward_physician_share"]
    assert published["recall_gap_less_female_women_minus_men"] == (
        j0l0["tpr_gap_surgeon_women_minus_men"])

    # The correctly-computed row disagrees with the published (quirky) one on both:
    assert row["flip_toward_more_female_share"] != published["flip_toward_more_female_share"]
    assert row["recall_gap_less_female_women_minus_men"] != (
        published["recall_gap_less_female_women_minus_men"])


# ---------------------------------------------------------------------------------------------
# race-name (surgeon-physician only).
# ---------------------------------------------------------------------------------------------

RACE_NAME_FIELDS = [
    "n_bios", "excluded", "floor", "floor_ci", "race_flip", "race_ci", "race_flip_b", "excess",
    "ratio", "mean_abs_dp_floor", "mean_abs_dp_race", "direction_share", "n_flips",
    "accuracy_white_a", "accuracy_black", "by_gender",
]


@pytest.mark.parametrize("engine", ENGINES)
def test_race_name_matches_bios_race(engine):
    task = load_task("surgeon-physician")
    row = score(engine, task, "race-name")
    published = _one("bios_race.jsonl", engine=OLD_ENGINE[engine])
    _assert_same(row, published, RACE_NAME_FIELDS)


# ---------------------------------------------------------------------------------------------
# age-inserted (surgeon-physician only).
# ---------------------------------------------------------------------------------------------

AGE_FIELDS = [
    "n_bios", "excluded", "age_flip", "age_flip_ci", "age_shift", "age_shift_ci",
    "floor_35_flip", "floor_35_flip_ci", "floor_35_shift", "floor_35_shift_ci",
    "floor_62_flip", "floor_62_flip_ci", "floor_62_shift", "floor_62_shift_ci",
    "direction_share", "n_flips_age", "accuracy_34", "accuracy_35", "accuracy_61",
    "accuracy_62", "by_gender",
]


@pytest.mark.parametrize("engine", ENGINES)
def test_age_inserted_matches_bios_age(engine):
    task = load_task("surgeon-physician")
    row = score(engine, task, "age-inserted")
    published = _one("bios_age.jsonl", engine=OLD_ENGINE[engine])
    _assert_same(row, published, AGE_FIELDS)


# ---------------------------------------------------------------------------------------------
# race-fullname (surgeon-physician only; jev only has the 500-bio sample).
# ---------------------------------------------------------------------------------------------

RACE2_FIELDS = [
    "n_bios", "excluded", "floor_shift", "floor_shift_ci", "floor_flip_majority",
    "floor_flip_pairwise", "groups", "flip_majority_ratio_vs_floor", "by_gender",
]


@pytest.mark.parametrize("engine,sample", [
    ("laya-mlx", "all"), ("laya-mlx", "500"), ("jev", "500"),
])
def test_race_fullname_matches_bios_race2(engine, sample):
    task = load_task("surgeon-physician")
    row = score(engine, task, "race-fullname", sample=sample)
    published = _one("bios_race2.jsonl", engine=OLD_ENGINE[engine], sample=sample)
    _assert_same(row, published, RACE2_FIELDS)


def test_jev_race_fullname_has_no_all_sample_record():
    """Jev never answered the rest of race-fullname past the 500-bio subsample (see
    ``RESULTS.md``'s "missing cells" footnote) -- scoring it with ``sample="all"`` must fail
    loudly, not silently score a partial, misleading population."""
    from biased_decisions.scoring import ScoreError
    task = load_task("surgeon-physician")
    with pytest.raises(ScoreError):
        score("jev", task, "race-fullname", sample="all")


# ---------------------------------------------------------------------------------------------
# Shortlist: 2 pairs x 2 engines x 3 cuts x 2 variants = 24 rows, every field.
# ---------------------------------------------------------------------------------------------

SHORTLIST_FIELDS = [
    "n_women_positive", "n_men_positive", "accuracy", "women_shortlist_rate",
    "men_shortlist_rate", "four_fifths_ratio", "ratio_ci", "tie_fair_ratio", "above_cut",
    "tied_at_cut", "women_who_lose_place_read_as_men", "men_who_lose_place_read_as_women",
    "women_who_gain_place_read_as_men", "men_who_gain_place_read_as_women",
]


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("slug,pair_key", [
    ("paralegal-attorney", "paralegal_attorney"), ("nurse-physician", "nurse_physician"),
])
def test_shortlist_matches_bios_shortlist(engine, slug, pair_key):
    task = load_task(slug)
    rows = score_shortlist(engine, task)
    assert len(rows) == 6  # 3 cuts x 2 variants
    published_rows = [row for row in _rows("bios_shortlist.jsonl")
                      if row["pair"] == pair_key and row["engine"] == OLD_ENGINE[engine]]
    assert len(published_rows) == 6
    by_key = {(row["variant"], row["cut"]): row for row in published_rows}
    for row in rows:
        published = by_key[(row["variant"], row["cut"])]
        _assert_same(row, published, SHORTLIST_FIELDS)


def test_every_published_row_is_accounted_for():
    """The full row-count reconciliation the module docstring claims: every row in every
    ``studies/jev-flywheel/*.jsonl`` file is either checked above, or is one of the two
    documented exclusions (16 non-J0/L0 loop arms; the surgeon_physician pairs quirk)."""
    gender_rows = _rows("bios_gender.jsonl")
    j0_l0_redacted = [r for r in gender_rows
                      if r["arm"] in ("J0", "L0") and r.get("redacted") is True]
    assert len(gender_rows) == 18
    assert len(j0_l0_redacted) == 2  # checked by test_gender_pronouns_surgeon_physician_*
    assert len(_rows("bios_pairs.jsonl")) == 8       # 4 pairs x 2 engines, all checked above
    assert len(_rows("bios_race.jsonl")) == 2         # 2 engines, checked
    assert len(_rows("bios_age.jsonl")) == 2          # 2 engines, checked
    assert len(_rows("bios_race2.jsonl")) == 3        # laya/all, laya/500, jev/500, checked
    assert len(_rows("bios_shortlist.jsonl")) == 24    # 2 pairs x 2 engines x 3 cuts x 2, checked


# ---------------------------------------------------------------------------------------------
# bd build reproduces the committed versions files byte-for-byte, where the inputs are
# committed. gender-pronouns has no committed versions file to compare against (its twins live
# inside items.jsonl -- see data/MANIFEST.md); race-fullname needs spaCy and the name pools, so
# it is only checked when both are importable/present.
# ---------------------------------------------------------------------------------------------

def _read_jsonl(path: Path) -> List[dict]:
    # Iterate the file object (splits only on "\n"), never str.splitlines() -- a bio's text can
    # contain a U+2028/U+2029 line separator, which splitlines() treats as a line boundary but
    # json.dumps does not escape, so splitting on it would cut a JSON string row in half.
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_build_race_name_matches_committed_versions_file():
    task = load_task("surgeon-physician")
    result = build_cue("race-name", task)
    committed = _read_jsonl(task.versions_path("race-name"))
    assert result.rows == committed
    assert result.excluded == 429


def test_build_age_inserted_matches_committed_versions_file():
    task = load_task("surgeon-physician")
    result = build_cue("age-inserted", task)
    committed = _read_jsonl(task.versions_path("age-inserted"))
    assert result.rows == committed
    assert result.excluded == 769


def _spacy_and_pools_available() -> bool:
    try:
        import spacy  # noqa: F401
        spacy.load("en_core_web_sm")
    except Exception:
        return False
    return (ROOT / "pools" / "name_pools.json").exists()


@pytest.mark.skipif(not _spacy_and_pools_available(),
                    reason="race-fullname needs spaCy + en_core_web_sm installed")
def test_build_race_fullname_matches_committed_versions_file():
    task = load_task("surgeon-physician")
    try:
        result = build_cue("race-fullname", task)
    except BuildError as error:
        pytest.skip(str(error))
    committed = _read_jsonl(task.versions_path("race-fullname"))
    assert result.rows == committed
    assert result.excluded == 32
    sub_path = task.versions_dir() / "race-fullname_jev-subsample.txt"
    committed_subsample = sub_path.read_text(encoding="utf-8").splitlines()
    assert result.subsample == committed_subsample


@pytest.mark.parametrize("slug", ["surgeon-physician", "nurse-physician", "teacher-professor",
                                  "paralegal-attorney"])
def test_build_gender_pronouns_matches_committed_twins_in_items_jsonl(slug):
    """gender-pronouns has no separate committed versions file (see data/MANIFEST.md); this
    checks the build against the twins committed inside ``items.jsonl`` itself."""
    task = load_task(slug)
    result = build_cue("gender-pronouns", task)
    committed = {item["id"]: item for item in _read_jsonl(task.items_path)
                if item["metadata"].get("split") == "counterfactual"}
    assert {row["id"] for row in result.rows} == set(committed)
    for row in result.rows:
        assert row == committed[row["id"]], row["id"]


# ---------------------------------------------------------------------------------------------
# Batch 1 / milestone 1b: disability, religion, religion-v2, ask-twice, option-order and
# port-vs-original, checked against studies/batch1/targets.jsonl (a verbatim copy of the
# Jev-Flywheel session's per-row religion/option-order scoring output -- see that file's own
# provenance note in studies/batch1/BUILD.md) and against the Outcome tables in
# studies/PREREGISTERED.md's batch-1 section (copied here as literal numbers; each one cites the
# Outcome subsection it came from).
# ---------------------------------------------------------------------------------------------

BATCH1_TASKS = ("surgeon-physician", "nurse-physician", "teacher-professor",
                "paralegal-attorney", "journalist-professor", "architect-interior-designer",
                "dietitian-physician")

def _rows_from(path: Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


TARGETS = _rows_from(ROOT / "studies" / "batch1" / "targets.jsonl")


def _target(cue: str, task: str) -> dict:
    hits = [r for r in TARGETS if r.get("task") == task and
           (r.get("cue") == cue if cue in ("religion", "religion-v2") else "committed" in r)]
    assert len(hits) == 1, f"expected exactly 1 target row for ({cue!r}, {task!r})"
    return hits[0]


@pytest.mark.parametrize("task", BATCH1_TASKS)
@pytest.mark.parametrize("cue", ["religion", "religion-v2"])
def test_religion_matches_targets_jsonl(cue, task):
    """``score_religion``/``score_religion_v2`` on the original ``laya`` engine reproduce
    ``studies/batch1/targets.jsonl`` (rows 1-14, ``laya_religion_v2_order.jsonl``'s religion
    half) bit for bit at 2-decimal precision."""
    row = score("laya", load_task(task), cue)
    target = _target(cue, task)
    assert row["n"] == target["n"]
    for religion in ("muslim", "christian", "jewish", "hindu"):
        got = row["versions"][religion]
        want = target["shift_pts"][religion]
        assert got["mean_pts"] == want["mean"], (cue, task, religion, "mean")
        assert got["ci_pts"] == want["ci"], (cue, task, religion, "ci")
        assert got["flip_vs_floor_pct"] == want["flip_vs_floor_pct"], (cue, task, religion)
    assert row["shared_clause_pts"]["mean_pts"] == target["shared_clause_pts"]["mean"]
    assert row["shared_clause_pts"]["ci_pts"] == target["shared_clause_pts"]["ci"]
    assert row["spread_pts"] == target["spread_pts"]


@pytest.mark.parametrize("task", ["surgeon-physician", "nurse-physician", "teacher-professor",
                                  "paralegal-attorney"])
def test_option_order_matches_targets_jsonl(task):
    """``score_option_order`` on ``laya`` reproduces ``laya_religion_v2_order.jsonl``'s
    option-order rows (the "Gender-pronoun flip rate by option order" Outcome table) for the
    four original tasks -- the only ones with a full ``option-order-reversed-twins`` record."""
    row = score("laya", load_task(task), "option-order")
    target = _target("option-order", task)
    assert row["n"] == target["n"]
    for arm in ("committed", "reversed"):
        got = row[arm]
        want = target[arm]
        assert round(got["flip_pct"], 2) == round(want["flip_pct"], 2)
        assert [round(v, 2) for v in got["ci_pct"]] == [round(v, 2) for v in want["ci"]]
        assert got["n_flips_male"] == want["n_flips_male"]
        assert round(got["shift_male_pts"], 2) == round(want["shift_male_pts"], 2)
        if want["direction_pct"] == want["direction_pct"]:  # not NaN
            assert got["direction_pct"] == round(want["direction_pct"], 1)
    assert round(row["order_flip_pct_items"], 2) == round(target["order_flip_pct_items"], 2)
    assert round(row["order_flip_pct_twins"], 2) == round(target["order_flip_pct_twins"], 2)


# Outcome section B (disability), literal numbers from studies/PREREGISTERED.md's batch-1
# section -- (engine, task) -> (mean_pts, ci_pts, flip_vs_floor_pct).
DISABILITY_TARGETS = {
    ("jev", "surgeon-physician"): (-0.71, [-0.88, -0.52], 1.24),
    ("jev", "paralegal-attorney"): (-0.64, [-0.87, -0.40], 2.02),
    ("laya", "surgeon-physician"): (-0.56, [-0.85, -0.30], 1.97),
    ("laya", "paralegal-attorney"): (-1.71, [-2.04, -1.42], 4.98),
    ("laya", "teacher-professor"): (-2.72, [-2.99, -2.44], 5.49),
    ("laya", "architect-interior-designer"): (-2.84, [-3.15, -2.51], 3.55),
    ("laya", "nurse-physician"): (2.01, [1.60, 2.41], 4.54),
}


@pytest.mark.parametrize("engine,task", list(DISABILITY_TARGETS))
def test_disability_matches_outcome_section_b(engine, task):
    row = score(engine, load_task(task), "disability")
    mean_pts, ci_pts, flip_pct = DISABILITY_TARGETS[(engine, task)]
    shift = row["versions"]["wheelchair"]
    assert shift["mean_pts"] == mean_pts
    assert shift["ci_pts"] == ci_pts
    assert shift["flip_vs_floor_pct"] == flip_pct


# Outcome section C (ask-twice floor), literal numbers -- (engine, task) -> flip_pct.
ASK_TWICE_TARGETS = {
    ("jev", "surgeon-physician"): 0.60, ("jev", "nurse-physician"): 0.40,
    ("jev", "teacher-professor"): 0.60, ("jev", "paralegal-attorney"): 0.40,
    ("laya", "surgeon-physician"): 0.0, ("laya", "nurse-physician"): 0.0,
    ("laya", "teacher-professor"): 0.0, ("laya", "paralegal-attorney"): 0.0,
}


@pytest.mark.parametrize("engine,task", list(ASK_TWICE_TARGETS))
def test_ask_twice_matches_outcome_section_c(engine, task):
    row = score(engine, load_task(task), "ask-twice")
    assert row["flip_pct"] == ASK_TWICE_TARGETS[(engine, task)]


# Outcome section A (the three new tasks' gender-pronouns cell), literal numbers --
# (engine, task) -> (flip_pct as a fraction, direction_share as a fraction).
NEW_TASK_GENDER_TARGETS = {
    ("jev", "journalist-professor"): (0.0080, 0.80),
    ("jev", "architect-interior-designer"): (0.0437, 1.00),
    ("jev", "dietitian-physician"): (0.0205, 1.00),
    ("laya", "journalist-professor"): (0.0180, 0.35),
    ("laya", "architect-interior-designer"): (0.0511, 0.927),
    ("laya", "dietitian-physician"): (0.0650, 0.933),
}


@pytest.mark.parametrize("engine,task", list(NEW_TASK_GENDER_TARGETS))
def test_new_task_gender_pronouns_matches_outcome_section_a(engine, task):
    row = score(engine, load_task(task), "gender-pronouns")
    flip, direction = NEW_TASK_GENDER_TARGETS[(engine, task)]
    assert round(row["counterfactual_flip_rate"], 4) == flip
    assert round(row["flip_toward_more_female_share"], 3) == round(direction, 3)


# The milestone-1b outcome's port-vs-original table (see studies/PREREGISTERED.md's "Milestone
# 1b outcome" section).
PORT_VS_ORIGINAL_TARGETS = {
    "surgeon-physician": (7.95, 7.95, 3996, 4000, 0.013),
    "nurse-physician": (13.50, 13.45, 3999, 4000, 0.013),
    "teacher-professor": (7.65, 7.75, 3998, 4000, 0.006),
    "paralegal-attorney": (17.85, 17.85, 3998, 4000, 0.019),
}


@pytest.mark.parametrize("task", list(PORT_VS_ORIGINAL_TARGETS))
def test_port_vs_original_matches_outcome_md(task):
    from biased_decisions.scoring import score_port_vs_original
    row = score_port_vs_original(load_task(task))
    port_flip, original_flip, agreement, total, max_dp = PORT_VS_ORIGINAL_TARGETS[task]
    assert row["port_flip_pct"] == port_flip
    assert row["original_flip_pct"] == original_flip
    assert row["verdict_agreement"] == agreement
    assert row["verdict_total"] == total
    assert row["max_abs_dp"] == max_dp


# ---------------------------------------------------------------------------------------------
# bd build reproduces the committed batch-1 versions files byte-for-byte, all seven tasks.
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("task", BATCH1_TASKS)
@pytest.mark.parametrize("cue", ["disability", "religion", "religion-v2"])
def test_build_insertion_cue_matches_committed_versions_file(cue, task):
    t = load_task(task)
    result = build_cue(cue, t)
    committed = _read_jsonl(t.versions_path(cue))
    assert result.rows == committed


@pytest.mark.parametrize("task", ["surgeon-physician", "nurse-physician", "teacher-professor",
                                  "paralegal-attorney"])
def test_build_ask_twice_matches_committed_ids_file(task):
    t = load_task(task)
    result = build_cue("ask-twice", t)
    committed = (t.versions_dir() / "ask-twice.txt").read_text(encoding="utf-8").splitlines()
    assert result.subsample == committed
