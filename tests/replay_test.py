"""Feature: replay reproduces Jev-Flywheel's published numbers, bit-for-bit.

The design doc's promise for milestone 1: scoring the committed record with the ported metrics
must reproduce every number in Jev-Flywheel's ``studies/*.jsonl``, not just something close to
it. These specs score every committed (engine, task, cue) cell this repo carries and compare the
result against the corresponding row in ``studies/jev-flywheel/`` (a verbatim copy of those
files -- see ``data/MANIFEST.md``).

Jev-Flywheel's rows use the engine name ``laya``; this repo's committed record for the same
numbers is filed under the engine name ``laya-mlx`` (the design doc's "Milestone 1b" split --
see ``biased_decisions.engines.laya_mlx``). ``ENGINE_LABEL`` below is the published row's own
``engine`` field for each of this repo's engine names.
"""
import json
from pathlib import Path

import pytest

from biased_decisions.metrics.flips import Verdict, score_arm, score_arm_race, score_pair
from biased_decisions.metrics.shifts import score_arm_age
from biased_decisions.record import read_record_by_id, record_path
from biased_decisions.tasks.bios import load_task, split_test_and_twins

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ROOT / "studies" / "jev-flywheel"
ENGINE_LABEL = {"jev": "jev", "laya-mlx": "laya"}


def _published(path, **match):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    hits = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
    assert hits, f"no row in {path} matches {match}"
    return hits[-1]  # the most recent row when several match (e.g. a re-run)


def _verdict_from_answer(item_id, answer, meta, positive):
    return Verdict(item_id, answer["choice"], answer["probabilities"][positive],
                   meta["reference_label"], meta["gender"])


def _gender_verdicts(task):
    items = task.load_items()
    test_items, twin_items = split_test_and_twins(items)
    by_id = {item.id: item for item in items}

    def build(engine):
        answers = read_record_by_id(record_path(engine, task.slug, "gender-pronouns"))
        def verdict(item_id):
            a = answers[item_id]["answers"]["Occupation"]
            return _verdict_from_answer(item_id, a, by_id[item_id].metadata, task.positive)
        verdicts = [verdict(i.id) for i in test_items if i.id in answers]
        twins = {source_id: verdict(twin.id) for source_id, twin in
                (lambda: [(i.metadata["counterfactual_of"], i) for i in items
                          if i.metadata.get("split") == "counterfactual"])()
                if source_id in answers and twin.id in answers}
        return verdicts, twins
    return build


@pytest.mark.parametrize("engine", ["jev", "laya-mlx"])
def test_gender_pronouns_replay_matches_bios_gender_jsonl(engine):
    task = load_task("surgeon-physician")
    verdicts, twins = _gender_verdicts(task)(engine)
    row = score_arm(arm="replay", engine=engine, verdicts=verdicts, twins=twins).as_row()

    arm = "J0" if engine == "jev" else "L0"
    published = _published(STUDIES / "bios_gender.jsonl", engine=ENGINE_LABEL[engine],
                           arm=arm, redacted=True)
    assert row["n"] == published["n"]
    assert row["accuracy"] == published["accuracy"]
    assert row["counterfactual_flip_rate"] == published["counterfactual_flip_rate"]
    assert row["mean_abs_delta_p"] == published["mean_abs_delta_p"]


@pytest.mark.parametrize("engine", ["jev", "laya-mlx"])
@pytest.mark.parametrize("slug,pair_key", [
    ("nurse-physician", "nurse_physician"),
    ("teacher-professor", "teacher_professor"),
    ("paralegal-attorney", "paralegal_attorney"),
])
def test_pairs_replay_matches_bios_pairs_jsonl(engine, slug, pair_key):
    task = load_task(slug)
    verdicts, twins = _gender_verdicts(task)(engine)
    row = score_pair(pair=pair_key, engine=engine, verdicts=verdicts, twins=twins).as_row()

    published = _published(STUDIES / "bios_pairs.jsonl", pair=pair_key, engine=ENGINE_LABEL[engine])
    assert row["n"] == published["n"]
    assert row["accuracy"] == published["accuracy"]
    assert row["counterfactual_flip_rate"] == published["counterfactual_flip_rate"]


@pytest.mark.parametrize("engine", ["jev", "laya-mlx"])
def test_race_name_replay_matches_bios_race_jsonl(engine):
    task = load_task("surgeon-physician")
    versions = task.load_versions("race-name")
    by_id = {i.id: i for i in versions}
    answers = read_record_by_id(record_path(engine, "surgeon-physician", "race-name"))

    by_source = {}
    for item in versions:
        by_source.setdefault(item.metadata["source_id"], {})[item.metadata["version"]] = item.id

    def verdict(source_id, version_id):
        a = answers[version_id]["answers"]["Occupation"]
        return _verdict_from_answer(source_id, a, by_id[version_id].metadata, task.positive)

    white_a = [verdict(sid, ids["white_a"]) for sid, ids in by_source.items()
              if ids["white_a"] in answers]
    white_b = {sid: verdict(sid, ids["white_b"]) for sid, ids in by_source.items()
              if ids["white_b"] in answers}
    black = {sid: verdict(sid, ids["black"]) for sid, ids in by_source.items()
            if ids["black"] in answers}

    row = score_arm_race(engine=engine, white_a=white_a, white_b=white_b, black=black,
                         excluded=429).as_row()
    published = _published(STUDIES / "bios_race.jsonl", engine=ENGINE_LABEL[engine])
    assert row["n_bios"] == published["n_bios"]
    assert row["floor"] == published["floor"]
    assert row["race_flip"] == published["race_flip"]
    assert row["excess"] == published["excess"]


@pytest.mark.parametrize("engine", ["jev", "laya-mlx"])
def test_age_inserted_replay_matches_bios_age_jsonl(engine):
    task = load_task("surgeon-physician")
    versions = task.load_versions("age-inserted")
    by_id = {i.id: i for i in versions}
    answers = read_record_by_id(record_path(engine, "surgeon-physician", "age-inserted"))

    by_source = {}
    for item in versions:
        by_source.setdefault(item.metadata["source_id"], {})[item.metadata["age"]] = item.id

    def verdict(source_id, version_id):
        a = answers[version_id]["answers"]["Occupation"]
        return _verdict_from_answer(source_id, a, by_id[version_id].metadata, task.positive)

    v34 = [verdict(sid, ids[34]) for sid, ids in by_source.items() if ids.get(34) in answers]
    v35 = {sid: verdict(sid, ids[35]) for sid, ids in by_source.items() if ids.get(35) in answers}
    v61 = {sid: verdict(sid, ids[61]) for sid, ids in by_source.items() if ids.get(61) in answers}
    v62 = {sid: verdict(sid, ids[62]) for sid, ids in by_source.items() if ids.get(62) in answers}

    row = score_arm_age(engine=engine, v34=v34, v35=v35, v61=v61, v62=v62, excluded=769).as_row()
    published = _published(STUDIES / "bios_age.jsonl", engine=ENGINE_LABEL[engine])
    assert row["n_bios"] == published["n_bios"]
    assert row["age_flip"] == published["age_flip"]
    assert row["age_shift"] == published["age_shift"]
    assert row["floor_35_flip"] == published["floor_35_flip"]
    assert row["floor_62_flip"] == published["floor_62_flip"]
