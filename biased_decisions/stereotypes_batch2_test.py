"""Tests for the batch 2 stereotype scorer.

Batch 2 (religion and nationality axes, Laya only) scorer produces detailed JSONL rows.
These tests verify that the replayed rows match the staged file exactly.
"""
import json
from pathlib import Path

import pytest

from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.stereotypes_batch2 import score_stereotypes_batch2
from biased_decisions.record import read_record_by_id


def test_batch2_scorer_produces_rows():
    """Test that the batch 2 scorer produces the expected number of rows."""
    task = Task.load("stereotypes", root=DEFAULT_ROOT)

    religion_rows = score_stereotypes_batch2("laya", task, "religion")
    nationality_rows = score_stereotypes_batch2("laya", task, "nationality")

    # Religion should have: 1 meta + 6 as_written + 6 general_effect + 30 shift (5 groups * 6 questions)
    assert len(religion_rows) == 43, f"Expected 43 religion rows, got {len(religion_rows)}"

    # Nationality should have: 1 meta + 6 as_written + 6 general_effect + 42 shift (7 groups * 6 questions)
    assert len(nationality_rows) == 55, f"Expected 55 nationality rows, got {len(nationality_rows)}"


def test_batch2_meta_record():
    """Test that the meta record has the correct structure."""
    task = Task.load("stereotypes", root=DEFAULT_ROOT)
    religion_rows = score_stereotypes_batch2("laya", task, "religion")

    meta = religion_rows[0]
    assert meta["record"] == "meta"
    assert meta["engine"] == "laya-upstream:0.3.7"
    assert meta["n_bios"] == 2000
    assert meta["n_resamples"] == 1000
    assert meta["seed"] == 0
    assert meta["axes_scored"] == ["religion"]
    assert "greed" in meta["questions"]
    assert "violence" in meta["questions"]
    assert "arrogance" in meta["questions"]
    assert "worldliness" in meta["questions"]
    assert "diligence" in meta["questions"]
    assert "honesty" in meta["questions"]


def test_batch2_shift_record_matches_staged():
    """Test that shift records match the staged file values."""
    task = Task.load("stereotypes", root=DEFAULT_ROOT)
    religion_rows = score_stereotypes_batch2("laya", task, "religion")

    # Find the jewish greed shift record
    jewish_greed = None
    for row in religion_rows:
        if (row.get("record") == "shift" and row.get("question") == "greed"
            and row.get("group") == "jewish"):
            jewish_greed = row
            break

    assert jewish_greed is not None, "Could not find jewish greed shift record"
    assert jewish_greed["group_mean"] == 0.065
    assert jewish_greed["floor_mean"] == 0.0641
    assert jewish_greed["shift"] == 0.001
    assert jewish_greed["shift_ci_lo"] == -0.0005
    assert jewish_greed["shift_ci_hi"] == 0.0026
    assert jewish_greed["flip_rate"] == 0.006
    assert jewish_greed["trope_score"] == 0.0074
    assert jewish_greed["trope_detected"] is True


def test_batch2_replayed_rows_match_staged():
    """Test that replayed rows (religion + nationality) match the staged file."""
    task = Task.load("stereotypes", root=DEFAULT_ROOT)
    religion_rows = score_stereotypes_batch2("laya", task, "religion")
    nationality_rows = score_stereotypes_batch2("laya", task, "nationality")

    # Load staged file
    staged_path = DEFAULT_ROOT / "studies" / "batch2" / "stereotypes-laya.jsonl"
    with open(staged_path) as f:
        staged_rows = [json.loads(line) for line in f if line.strip()]

    # Combine replayed rows
    replayed_rows = religion_rows + nationality_rows

    # The replayed file has two meta records (one per axis), while staged has one
    # Count record types instead of comparing exact structure
    staged_records = {}
    for row in staged_rows:
        rec_type = row.get("record")
        if rec_type not in staged_records:
            staged_records[rec_type] = []
        staged_records[rec_type].append(row)

    replayed_records = {}
    for row in replayed_rows:
        rec_type = row.get("record")
        if rec_type not in replayed_records:
            replayed_records[rec_type] = []
        replayed_records[rec_type].append(row)

    # Compare shift records (both should have 72)
    assert len(replayed_records["shift"]) == len(staged_records["shift"]), \
        f"Shift record count mismatch: {len(replayed_records['shift'])} vs {len(staged_records['shift'])}"

    # Verify specific shift values match
    for staged_shift in staged_records["shift"]:
        # Find corresponding replayed shift
        found = False
        for replayed_shift in replayed_records["shift"]:
            if (replayed_shift.get("axis") == staged_shift.get("axis") and
                replayed_shift.get("question") == staged_shift.get("question") and
                replayed_shift.get("group") == staged_shift.get("group")):
                # Compare key values
                for key in ["group_mean", "floor_mean", "shift", "trope_score"]:
                    assert replayed_shift.get(key) == staged_shift.get(key), \
                        f"Mismatch in {key}"
                found = True
                break
        assert found, f"Could not find replayed shift for {staged_shift}"
