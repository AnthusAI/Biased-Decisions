"""Feature: antisemitic-tropes-in-depth cue versions, built over a plain item pool instead of a
occupation ``Task``.
"""
from biased_decisions.tasks.items import Item
from biased_decisions.tasks.stereotype_versions import (
    ALL_CUES, SURNAME_CUE, build_insertion_versions, build_surname_versions, build_versions,
)

ELIGIBLE = Item(id="p-1", text="He is a loan officer. He has worked here for years.",
               metadata={"gender": "male"})
INELIGIBLE = Item(id="p-2", text="Board certified in 2010 he moved to Boston.",
                  metadata={"gender": "male"})


def test_insertion_versions_writes_one_row_per_version_for_an_eligible_item():
    rows, excluded = build_insertion_versions([ELIGIBLE], "antisemitism-secular")
    assert excluded == 0
    assert len(rows) == 5  # jewish + 3 controls + floor
    ids = {row["id"] for row in rows}
    assert "p-1-antisemitism-secular-jewish" in ids
    assert "p-1-antisemitism-secular-floor-cyclist" in ids


def test_insertion_versions_excludes_and_counts_an_ineligible_item():
    rows, excluded = build_insertion_versions([INELIGIBLE], "antisemitism-religious")
    assert rows == []
    assert excluded == 1


def test_insertion_versions_carries_the_source_items_own_metadata_forward():
    rows, _ = build_insertion_versions([ELIGIBLE], "antisemitism-nationality")
    assert rows[0]["metadata"]["gender"] == "male"
    assert rows[0]["metadata"]["source_id"] == "p-1"


def test_surname_versions_writes_two_rows_per_eligible_item():
    rows, excluded = build_surname_versions([ELIGIBLE])
    assert excluded == 0
    assert len(rows) == 2
    versions = {row["metadata"]["version"] for row in rows}
    assert versions == {"jewish", "floor"}


def test_surname_versions_excludes_an_item_with_no_insertion_point():
    no_point = Item(id="p-3", text="A short bio naming no one and using no pronoun at all.",
                    metadata={"gender": "male"})
    rows, excluded = build_surname_versions([no_point])
    assert rows == []
    assert excluded == 1


def test_build_versions_dispatches_to_the_right_builder():
    insertion_rows, _ = build_versions([ELIGIBLE], "antisemitism-role")
    surname_rows, _ = build_versions([ELIGIBLE], SURNAME_CUE)
    assert len(insertion_rows) == 4  # synagogue + church + mosque + floor
    assert len(surname_rows) == 2


def test_build_versions_rejects_an_unknown_cue():
    try:
        build_versions([ELIGIBLE], "antisemitism-nope")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_all_cues_lists_the_four_insertion_cues_plus_the_surname_cue():
    assert set(ALL_CUES) == {
        "antisemitism-secular", "antisemitism-religious", "antisemitism-nationality",
        "antisemitism-role", "antisemitism-surname",
    }
