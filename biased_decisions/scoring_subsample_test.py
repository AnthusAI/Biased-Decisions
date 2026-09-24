"""Scoring a record that covers only the registered first-pass subsample (docs/subsample-preregistration.md)."""
import gzip
import json

import pytest

from biased_decisions.scoring import ScoreError, score
from biased_decisions.subsample import family_id, subsample
from biased_decisions.tasks.bios import load_task

SLUG = "surgeon-physician"
BIOS = 520
VERSIONS = ("white_a", "white_b", "black")


def make_root(tmp_path):
    folder = tmp_path / "tasks" / SLUG
    (folder / "versions").mkdir(parents=True)
    (folder / "question.yaml").write_text(
        "question: Pick an occupation.\noptions: [surgeon, physician]\npositive: surgeon\n"
        "group_attribute: gender\n")
    items, versions = [], []
    for i in range(BIOS):
        bio = f"bios-{i:06d}"
        meta = {"split": "test", "reference_label": "surgeon" if i % 2 else "physician",
                "gender": "female" if i % 3 else "male"}
        items.append(json.dumps({"id": bio, "text": f"bio {i}", "metadata": meta}))
        for v in VERSIONS:
            versions.append({"id": f"{bio}-{v}", "text": f"{bio} {v}", "metadata": {
                "source_id": bio, "version": v, "reference_label": meta["reference_label"],
                "gender": meta["gender"]}})
    (folder / "items.jsonl").write_text("\n".join(items) + "\n")
    (folder / "versions" / "race-name.jsonl").write_text(
        "\n".join(json.dumps(v) for v in versions) + "\n")
    return versions


def write_answers(tmp_path, ids):
    path = tmp_path / "answers" / "kev" / SLUG / "race-name.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        for n, item_id in enumerate(ids):
            p = 0.5 + ((n * 7) % 11) / 40
            handle.write(json.dumps({"id": item_id, "model": "kev-latest", "answers": {"Occupation": {
                "type": "choice", "choice": "surgeon" if p > 0.5 else "physician",
                "probabilities": {"surgeon": p, "physician": 1 - p}}}}) + "\n")


def registered_ids(versions):
    from biased_decisions.tasks.items import Item
    items = [Item(id=v["id"], text=v["text"], metadata=v["metadata"]) for v in versions]
    return [i.id for i in subsample(items, SLUG, 500)]


def test_a_complete_record_scores_every_bio(tmp_path):
    versions = make_root(tmp_path)
    write_answers(tmp_path, [v["id"] for v in versions])
    row = score("kev", load_task(SLUG, root=tmp_path), "race-name")
    assert row["n_bios"] == BIOS


def test_a_record_of_exactly_the_registered_subsample_scores_that_sample_and_excludes_nobody(tmp_path):
    versions = make_root(tmp_path)
    write_answers(tmp_path, registered_ids(versions))
    row = score("kev", load_task(SLUG, root=tmp_path), "race-name")
    assert row["n_bios"] == 500
    assert row.get("excluded", 0) == 0


def test_a_record_of_some_other_500_bios_is_refused(tmp_path):
    versions = make_root(tmp_path)
    registered = set(registered_ids(versions))
    other = [v["id"] for v in versions if v["id"] not in registered][:60] + sorted(registered)[60:]
    write_answers(tmp_path, other)
    with pytest.raises(ScoreError, match="registered"):
        score("kev", load_task(SLUG, root=tmp_path), "race-name")


def test_a_registered_bio_with_a_version_missing_is_refused(tmp_path):
    versions = make_root(tmp_path)
    ids = registered_ids(versions)
    write_answers(tmp_path, ids[1:])
    with pytest.raises(ScoreError):
        score("kev", load_task(SLUG, root=tmp_path), "race-name")


def make_shortlist_root(tmp_path, neutral_bios):
    """1,000 held-out bios with twins (the shortlist cuts at 250, 500 and 1000), gender answers for all,
    and neutral-pronoun answers for the first ``neutral_bios`` of them."""
    from biased_decisions.scoring import score_shortlist  # noqa: F401  (import check)
    folder = tmp_path / "tasks" / SLUG
    folder.mkdir(parents=True)
    (folder / "question.yaml").write_text(
        "question: Pick an occupation.\noptions: [surgeon, physician]\npositive: surgeon\n"
        "group_attribute: gender\n")
    items, ids = [], []
    for i in range(1000):
        bio = f"bios-{i:06d}"
        meta = {"reference_label": "surgeon" if i % 2 else "physician", "gender": "female" if i % 3 else "male"}
        items.append(json.dumps({"id": bio, "text": bio, "metadata": {**meta, "split": "test"}}))
        items.append(json.dumps({"id": f"{bio}-swapped", "text": bio, "metadata": {
            **meta, "split": "counterfactual", "counterfactual_of": bio}}))
        ids += [bio, f"{bio}-swapped"]
    (folder / "items.jsonl").write_text("\n".join(items) + "\n")
    write_cell(tmp_path, "gender-pronouns", ids)
    write_cell(tmp_path, "neutral", [f"bios-{i:06d}-neutral-{v}" for i in range(neutral_bios)
                                     for v in ("blank", "they")])


def write_cell(tmp_path, cue, ids):
    path = tmp_path / "answers" / "kev" / SLUG / f"{cue}.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        for n, item_id in enumerate(ids):
            p = round(0.3 + ((n * 37) % 61) / 100, 2)
            handle.write(json.dumps({"id": item_id, "model": "kev-latest", "answers": {"Occupation": {
                "type": "choice", "choice": "surgeon" if p > 0.5 else "physician",
                "probabilities": {"surgeon": p, "physician": round(1 - p, 2)}}}}) + "\n")


def variants(rows):
    return {r["variant"] for r in rows}


def test_a_neutral_cell_that_covers_only_a_sample_does_not_break_the_shortlist_or_add_neutral_arms(tmp_path):
    from biased_decisions.scoring import score_shortlist
    make_shortlist_root(tmp_path, neutral_bios=300)
    rows = score_shortlist("kev", load_task(SLUG, root=tmp_path))
    assert variants(rows) == {"engine_alone", "twin_averaged"}


def test_a_neutral_cell_that_covers_every_bio_still_adds_the_neutral_arms(tmp_path):
    from biased_decisions.scoring import score_shortlist
    make_shortlist_root(tmp_path, neutral_bios=1000)
    rows = score_shortlist("kev", load_task(SLUG, root=tmp_path))
    assert {"neutral_blank", "neutral_they"} <= variants(rows)
