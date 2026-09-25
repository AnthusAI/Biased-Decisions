"""Specs for the independent Civil Comments JEVPA replication corpus."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "civil_comments_jevpa_replication_build", Path(__file__).with_name("build.py"))
civil_build = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(civil_build)


def _rows(n: int = 80):
    return [{
        "row_index": index,
        "text": f"comment {index}",
        "toxicity": 0.8 if index % 2 else 0.0,
        "threat": 0.4 if index < 24 else 0.0,
        "identity_attack": 0.4 if 24 <= index < 48 else 0.0,
    } for index in range(n)]


def test_replication_excludes_every_row_in_the_original_working_sample():
    result = civil_build.freeze_rows(
        _rows(), original_sample_size=20, sample_size=40, discovery_size=8,
        selection_size=16, test_size=12, original_seed=7, seed=11, slice_size=6)

    original = civil_build.sample_ids(_rows(), size=20, seed=7)
    replicated = {row["id"] for split in result["splits"].values() for row in split}
    assert replicated.isdisjoint({f"civil-validation-{row_index:06d}" for row_index in original})


def test_replication_is_deterministic_disjoint_and_keeps_annotations_sealed():
    kwargs = dict(original_sample_size=20, sample_size=40, discovery_size=8,
                  selection_size=16, test_size=12, original_seed=7, seed=11, slice_size=6)
    first = civil_build.freeze_rows(_rows(), **kwargs)
    second = civil_build.freeze_rows(_rows(), **kwargs)

    assert first == second
    assert {name: len(rows) for name, rows in first["splits"].items()} == {
        "discovery": 8, "selection": 16, "test": 12,
    }
    assert set(first["analyst_items"][0]["metadata"]) == {"split", "reference_label"}
    assert "threat" not in str(first["analyst_items"])
    assert "identity_attack" not in str(first["analyst_items"])
    assert len(first["sealed_selection_slices"]["threat"]) >= 6
    assert len(first["sealed_selection_slices"]["identity_attack"]) >= 6


def test_replication_refuses_a_source_that_cannot_supply_two_disjoint_samples():
    try:
        civil_build.freeze_rows(_rows(59), original_sample_size=20, sample_size=40,
                                discovery_size=8, selection_size=16, test_size=12,
                                original_seed=7, seed=11, slice_size=6)
    except ValueError as error:
        assert "need at least 60" in str(error)
    else:
        raise AssertionError("expected insufficient source to be rejected")
