"""Feature: the committed brand and company tasks are what their READMEs say they are."""
import json
import re
from pathlib import Path

import pytest

from biased_decisions import brand_bias as bb
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parent.parent


def _rows(slug, name):
    return [json.loads(line) for line in open(ROOT / "tasks" / slug / name)]


def _cues(slug):
    return list(bb.shape_of(slug))


def _tokens_or_skip():
    try:
        return bb.Tokens()
    except SystemExit:
        pytest.skip("Laya's tokenizer is not in the local model cache")


@pytest.mark.parametrize("slug", bb.TASKS)
def test_every_task_has_its_question_a_readme_a_licence_note_and_a_shape_floor_among_its_versions(slug):
    task = Task.load(slug, root=ROOT)
    assert task.question == bb.QUESTIONS[slug][0] and task.positive == bb.QUESTIONS[slug][2]
    assert (ROOT / "tasks" / slug / "README.md").read_text().strip()
    assert (ROOT / "tasks" / slug / "LICENSE").read_text().strip()
    for cue, (floor, groups) in bb.shape_of(slug).items():
        versions = {r["metadata"]["version"] for r in _rows(slug, f"versions/{cue}.jsonl")}
        assert {floor, *groups} == versions, (slug, cue)


@pytest.mark.parametrize("slug", bb.TASKS)
def test_every_item_is_held_out_and_every_source_id_of_a_version_is_an_item(slug):
    items = _rows(slug, "items.jsonl")
    ids = {i["id"] for i in items}
    assert len(ids) == len(items) and {i["metadata"]["split"] for i in items} == {"test"}
    for cue in _cues(slug):
        rows = _rows(slug, f"versions/{cue}.jsonl")
        assert {r["metadata"]["source_id"] for r in rows} == ids
        assert len(rows) == len(ids) * len(bb.shape_of(slug)[cue][1]) + len(ids)


@pytest.mark.parametrize("slug", [bb.COMPLAINT_SLUG, bb.FUND_SLUG])
def test_the_real_text_tasks_state_their_source_checksum_and_licence(slug):
    readme = (ROOT / "tasks" / slug / "README.md").read_text()
    sha = bb.SEC_SOURCE_SHA256 if slug == bb.FUND_SLUG else "a74190517eea0fabffda3219d2c863441469ae045797b2d4923ee0cf0bd2d9a1"
    assert sha in readme and "licence" in readme.lower()


@pytest.mark.parametrize("slug", [bb.LOAN_SLUG, bb.PAIR_SLUG, bb.RECOMMEND_SLUG])
def test_the_synthetic_tasks_say_so(slug):
    assert "synthetic" in (ROOT / "tasks" / slug / "README.md").read_text().lower()


def test_a_complaint_text_never_names_a_bank_of_the_list_except_in_the_inserted_sentence():
    for item in _rows(bb.COMPLAINT_SLUG, "items.jsonl"):
        assert not bb.names_a_listed_bank(item["text"]), item["id"]


def test_the_two_invented_names_of_a_committed_row_are_never_a_real_listed_name():
    for slug, cue in ((bb.COMPLAINT_SLUG, "company-name"), (bb.LOAN_SLUG, "brand-name")):
        for r in _rows(slug, f"versions/{cue}.jsonl"):
            if r["metadata"]["version"] in ("invented-b", "floor-invented-a"):
                assert not bb.names_a_listed_bank(r["text"]), r["id"]


def test_the_pair_task_shows_the_focal_brand_first_for_exactly_half_the_items_in_every_condition():
    rows = _rows(bb.PAIR_SLUG, "versions/brand-pair.jsonl")
    for cond in bb.PAIR_CONDITIONS:
        flags = [r["metadata"]["focal_first"] for r in rows if r["metadata"]["version"] == cond]
        assert len(flags) == 1000 and sum(flags) == 500


def test_no_fund_version_differs_from_another_except_in_the_name():
    rows = _rows(bb.FUND_SLUG, "versions/fund-family.jsonl")
    by_item = {}
    for r in rows:
        by_item.setdefault(r["metadata"]["source_id"], []).append(r)
    for versions in by_item.values():
        tails = {r["text"][len(r["metadata"]["name"]):].lstrip(". ") for r in versions}
        assert len(tails) == 1


def test_every_version_fits_layas_window_beside_the_question():
    tokens = _tokens_or_skip()
    for slug in bb.TASKS:
        q, options, _, _ = bb.QUESTIONS[slug]
        room = tokens.room(q, options)
        for cue in _cues(slug):
            worst = max(tokens.count(r["text"]) for r in _rows(slug, f"versions/{cue}.jsonl"))
            assert worst <= room, (slug, cue, worst, room)


def test_the_synthetic_tasks_rebuild_byte_for_byte(tmp_path):
    tokens = _tokens_or_skip()
    for slug in (bb.LOAN_SLUG, bb.PAIR_SLUG, bb.RECOMMEND_SLUG):
        bb.build(slug, root=tmp_path, tokens=tokens)
        for path in (tmp_path / "tasks" / slug).rglob("*"):
            if path.is_file():
                assert (ROOT / path.relative_to(tmp_path)).read_bytes() == path.read_bytes(), path


def test_the_sec_task_rebuilds_byte_for_byte_when_the_source_is_present(tmp_path):
    source = ROOT / "var" / "sec" / "2025q4_rr1.zip"
    if not source.exists():
        pytest.skip("the SEC data set is not downloaded (see the task README)")
    tokens = _tokens_or_skip()
    bb.build(bb.FUND_SLUG, root=tmp_path, tokens=tokens, sec_source=source)
    for path in (tmp_path / "tasks" / bb.FUND_SLUG).rglob("*"):
        if path.is_file():
            assert (ROOT / path.relative_to(tmp_path)).read_bytes() == path.read_bytes(), path
