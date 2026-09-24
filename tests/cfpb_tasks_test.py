"""Feature: the committed complaint-narrative tasks are what their README says they are."""
import glob
import json
import re
from pathlib import Path

import pytest

from biased_decisions import cfpb
from biased_decisions.tasks.base import Task

ROOT = Path(__file__).resolve().parent.parent


def _items(task):
    return [json.loads(line) for line in open(ROOT / "tasks" / cfpb.SLUG[task] / "items.jsonl")]


def _versions(task):
    return [json.loads(line) for line in
            open(ROOT / "tasks" / cfpb.SLUG[task] / "versions" / f"{cfpb.CUE[task]}.jsonl")]


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_each_task_has_a_thousand_distinct_held_out_narratives(task):
    items = _items(task)
    assert len(items) == cfpb.SIZE == len({i["id"] for i in items})
    assert {i["metadata"]["split"] for i in items} == {"test"}


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_the_question_is_the_registered_wording_and_yes_is_the_positive_answer(task):
    loaded = Task.load(cfpb.SLUG[task], root=ROOT)
    assert loaded.question == cfpb.QUESTION and loaded.positive == "yes"


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_no_narrative_is_cut_mid_sentence_or_longer_than_the_stated_limit(task):
    for item in _items(task):
        assert len(item["text"]) <= cfpb.CUT_CHARS
        if item["metadata"]["truncated"]:
            assert re.search(r"[.!?][\"')\]]*$", item["text"]), item["id"]
        else:
            assert item["metadata"]["original_chars"] == len(item["text"])


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_no_text_names_the_tag_it_was_sampled_around(task):
    for item in _items(task):
        assert not re.search(r"servicemember|older american", item["text"], re.I), item["id"]
        assert not re.search(r"\b(veterans?|military)\b", item["text"], re.I) or task != "servicemember"


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_every_version_is_its_clause_plus_the_untouched_narrative_and_the_floor_comes_last(task):
    clauses = dict(cfpb.CLAUSES[task])
    by_id = {i["id"]: i["text"] for i in _items(task)}
    versions = _versions(task)
    assert len(versions) == len(by_id) * len(clauses)
    for v in versions:
        meta = v["metadata"]
        assert v["text"] == clauses[meta["version"]] + by_id[meta["source_id"]]
    last = [v for v in versions if v["metadata"]["source_id"] == next(iter(by_id))]
    assert [v["metadata"]["version"] for v in last] == list(clauses)
    assert list(clauses)[-1].startswith("floor-")


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_every_version_fits_layas_window_beside_the_question(task):
    paths = glob.glob(cfpb.TOKENIZER_GLOB)
    if not paths:
        pytest.skip("Laya's tokenizer is not in the local model cache")
    tokens = cfpb.LayaTokens(paths[0])
    room = tokens.room()
    worst = max(tokens.count(v["text"]) for v in _versions(task))
    assert worst <= room, f"{worst} tokens exceed the {room} available"


@pytest.mark.parametrize("task", cfpb.TASKS)
def test_the_readme_states_the_source_checksum_the_cut_limit_and_the_licence(task):
    readme = (ROOT / "tasks" / cfpb.SLUG[task] / "README.md").read_text()
    assert cfpb.SOURCE_SHA256 in readme
    assert f"{cfpb.CUT_CHARS:,}" in readme and "public domain" in readme.lower()
    assert (ROOT / "tasks" / cfpb.SLUG[task] / "LICENSE").exists()
