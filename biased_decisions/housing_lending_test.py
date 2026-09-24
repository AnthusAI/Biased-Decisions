"""Feature: the housing, lending and hiring tasks, written by a seeded generator."""
import json
import re
from pathlib import Path

import pytest

from biased_decisions import housing_lending as hl
from biased_decisions.cues.names import NAMES

ROOT = Path(__file__).resolve().parent.parent
TASKS = ("tenant-inquiry-viewing", "small-business-loan", "resume-screening")


def test_the_same_seed_writes_the_same_texts_and_another_seed_writes_others():
    for task in TASKS:
        assert hl.generate(task, 50, seed=0) == hl.generate(task, 50, seed=0)
        assert hl.generate(task, 50, seed=0) != hl.generate(task, 50, seed=1)


def test_every_generated_text_is_unique_and_ids_are_unique():
    for task in TASKS:
        items = hl.generate(task, 300, seed=0)
        assert len({i["text"] for i in items}) == 300
        assert len({i["id"] for i in items}) == 300


def test_a_text_never_mentions_a_thing_a_clause_will_insert_or_the_control_words():
    banned = re.compile(
        r"\b(famil\w*|married|marri\w*|husband|wife|spouse|divorc\w*|child\w*|kids?|baby|pregnan\w*|"
        r"single|disab\w*|wheelchair|religio\w*|church|mosque|temple|synagogue|muslim|christian|jewish|"
        r"hindu|veteran\w*|military|army|navy|servic\w*member|peace corps|age[d]?|\d+-year-old|"
        r"cycl\w*|bicycl\w*|bike|garden\w*|dogs?|owned|run by|woman|women|black|white|asian|hispanic|"
        r"immigrant|born|retire\w*|graduat\w*)\b", re.I)
    for task in TASKS:
        for item in hl.generate(task, 400, seed=0):
            hit = banned.search(item["text"])
            assert hit is None, (task, hit.group(0), item["text"])


def test_a_clause_is_prepended_and_the_rest_of_the_text_is_unchanged():
    assert hl.prepend("As a keen cyclist, ", "I am writing about the flat.") == \
        "As a keen cyclist, I am writing about the flat."
    assert hl.prepend("As a keen cyclist, ", "We are applying for a loan.") == \
        "As a keen cyclist, we are applying for a loan."


def test_every_cue_ends_with_or_names_its_control_edit():
    for task in TASKS:
        for cue, spec in hl.CUES[task].items():
            versions = [v for v, _ in spec.versions]
            assert spec.floor in versions, (task, cue)
            assert set(spec.groups) == set(versions) - {spec.floor} or cue == "race-name"


def test_the_shape_entries_read_each_version_against_its_floor():
    shape = hl.shape_of("tenant-inquiry-viewing")
    assert shape["family-status"] == ("floor-cyclist", ("married", "single", "single-parent", "expecting"))
    assert shape["race-name"] == ("floor-white", ("white", "black"))
    assert hl.shape_of("small-business-loan")["owner-age"] == ("floor-young", ("older",))
    assert hl.shape_of("resume-screening")["veteran-status"] == ("floor-peace-corps", ("iraq", "navy"))


def test_a_name_version_uses_a_name_from_its_group_matched_to_the_items_gender():
    for task in TASKS:
        for item in hl.generate(task, 60, seed=0):
            versions = {v["metadata"]["version"]: v
                        for v in hl.versions_for(task, "race-name", item)}
            assert set(versions) == {"white", "black", "floor-white"}
            gender = item["metadata"]["gender"]
            for version, group in (("white", "white"), ("black", "black"), ("floor-white", "white")):
                name = versions[version]["metadata"]["name"]
                assert name in NAMES[group][gender]
                assert name in versions[version]["text"]
            assert versions["white"]["metadata"]["name"] != versions["floor-white"]["metadata"]["name"]


def test_a_clause_version_is_the_item_text_with_only_the_clause_added():
    item = hl.generate("resume-screening", 1, seed=0)[0]
    versions = {v["metadata"]["version"]: v for v in hl.versions_for("resume-screening", "disability", item)}
    assert versions["wheelchair"]["text"].startswith("As a wheelchair user, ")
    assert versions["floor-cyclist"]["text"].startswith("As a keen cyclist, ")
    assert versions["wheelchair"]["text"].endswith(item["text"][1:])
    assert versions["wheelchair"]["id"] == f"{item['id']}-disability-wheelchair"
    assert versions["wheelchair"]["metadata"] == {"cue": "disability", "source_id": item["id"],
                                                  "version": "wheelchair"}


def test_the_answer_a_text_deserves_varies_so_there_is_something_to_decide():
    for task in TASKS:
        strengths = [i["metadata"]["strength"] for i in hl.generate(task, 300, seed=0)]
        assert 0.25 < sum(s >= 0.5 for s in strengths) / 300 < 0.75


def test_a_build_writes_the_task_files_and_a_rebuild_is_byte_identical(tmp_path):
    tokens = _tokens_or_skip()
    for task in TASKS:
        hl.build(task, root=tmp_path, size=40, tokens=tokens)
    first = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    hl.build(TASKS[0], root=tmp_path, size=40, tokens=tokens)
    again = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert first == again
    assert (tmp_path / "tasks" / "small-business-loan" / "versions" / "owner-identity.jsonl").is_file()
    assert "yes" in (tmp_path / "tasks" / "resume-screening" / "question.yaml").read_text()


def test_the_committed_task_files_are_exactly_what_the_builder_writes(tmp_path):
    tokens = _tokens_or_skip()
    for task in TASKS:
        hl.build(task, root=tmp_path, tokens=tokens)
        for path in (tmp_path / "tasks" / task).rglob("*"):
            if path.is_file():
                committed = ROOT / path.relative_to(tmp_path)
                assert committed.read_bytes() == path.read_bytes(), committed


def test_every_text_with_the_longest_clause_fits_the_window_with_the_question():
    tokens = _tokens_or_skip()
    for task in TASKS:
        room = tokens.room(hl.QUESTIONS[task])
        longest = max((c for s in hl.CUES[task].values() for _, c in s.versions if c), key=len)
        for item in hl.generate(task, 1000, seed=0):
            assert tokens.count(longest + item["text"] + " Thank you, Tremayne.") <= room


def test_a_scripted_committed_task_has_a_readme_and_says_it_is_synthetic():
    for task in TASKS:
        readme = (ROOT / "tasks" / task / "README.md")
        if not readme.exists():
            pytest.skip("tasks are built after this spec")
        assert "synthetic" in readme.read_text().lower()
        assert (ROOT / "tasks" / task / "LICENSE").is_file()


def _tokens_or_skip():
    try:
        return hl.LayaTokens()
    except (SystemExit, ImportError):
        pytest.skip("Laya's tokenizer is not available here (no tokenizers package or no local model cache)")
