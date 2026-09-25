"""Specs for the sealed Civil Comments JEVPA corpus builder.

These tests exercise only in-memory rows. Fetching the public parquet is an
explicit build step and is never part of the test suite.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "civil_comments_jevpa_build", Path(__file__).with_name("build.py"))
civil_build = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(civil_build)


def _rows(n: int = 40):
    return [
        {
            "row_index": index,
            "text": f"comment {index}",
            "toxicity": 0.8 if index % 2 else 0.0,
            "threat": 0.4 if index < 12 else 0.0,
            "identity_attack": 0.4 if 12 <= index < 24 else 0.0,
        }
        for index in range(n)
    ]


def test_a_frozen_split_is_deterministic_disjoint_and_has_registered_sizes():
    first = civil_build.freeze_rows(_rows(), sample_size=40, discovery_size=4,
                                    selection_size=12, test_size=8, seed=7,
                                    slice_size=4)
    second = civil_build.freeze_rows(_rows(), sample_size=40, discovery_size=4,
                                     selection_size=12, test_size=8, seed=7,
                                     slice_size=4)

    assert first == second
    assert {name: len(first["splits"][name]) for name in ("discovery", "selection", "test")} == {
        "discovery": 4, "selection": 12, "test": 8,
    }
    used = [row["id"] for name in ("discovery", "selection", "test")
            for row in first["splits"][name]]
    assert len(used) == len(set(used))


def test_selection_is_enriched_with_each_pre_registered_slice():
    result = civil_build.freeze_rows(_rows(), sample_size=40, discovery_size=4,
                                     selection_size=12, test_size=8, seed=7,
                                     slice_size=4)

    assert len(result["sealed_selection_slices"]["threat"]) >= 4
    assert len(result["sealed_selection_slices"]["identity_attack"]) >= 4


def test_analyst_items_have_only_text_label_and_split():
    result = civil_build.freeze_rows(_rows(), sample_size=40, discovery_size=4,
                                     selection_size=12, test_size=8, seed=7,
                                     slice_size=4)

    assert len(result["analyst_items"]) == 4
    assert set(result["analyst_items"][0]) == {"id", "text", "metadata"}
    assert result["analyst_items"][0]["metadata"].keys() == {"split", "reference_label"}
    assert "threat" not in str(result["analyst_items"])
    assert "identity_attack" not in str(result["analyst_items"])


def test_sealed_selection_slices_are_never_part_of_analyst_items():
    result = civil_build.freeze_rows(_rows(), sample_size=40, discovery_size=4,
                                     selection_size=12, test_size=8, seed=7,
                                     slice_size=4)

    assert set(result["sealed_selection_slices"]) == {"threat", "identity_attack"}
    assert all("row_index" in row for rows in result["sealed_selection_slices"].values()
               for row in rows)
    assert not any("row_index" in row for row in result["analyst_items"])


def test_freezing_refuses_an_insufficient_source():
    try:
        civil_build.freeze_rows(_rows(39), sample_size=40, discovery_size=4,
                                 selection_size=12, test_size=8, seed=7, slice_size=4)
    except ValueError as error:
        assert "need 40" in str(error)
    else:
        raise AssertionError("expected insufficient source to be rejected")
