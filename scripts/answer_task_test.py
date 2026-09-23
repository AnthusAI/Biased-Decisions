"""Tests for the answer runner script."""
import asyncio
import gzip
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

from scripts.answer_task import run
from biased_decisions.record import read_record


class FakeEngine:
    """A fake engine that does not call Laya."""

    def __init__(self):
        self.call_count = 0

    async def answer(self, text: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, dict]:
        """Return a fixed fake answer."""
        self.call_count += 1
        return {
            "Decision": {
                "choice": "yes",
                "probabilities": {"yes": 0.7, "no": 0.3}
            }
        }


def test_it_answers_as_written_items_and_every_version_of_a_cue():
    """Run the answer script on test items and all versions of a cue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create the task structure.
        task_dir = root / "tasks" / "t"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Write question.yaml.
        question_file = task_dir / "question.yaml"
        question_file.write_text("question: Q?\noptions:\n  - yes\n  - no\npositive: yes\ngroup_attribute: x\n")

        # Write items.jsonl with 2 test items.
        items_file = task_dir / "items.jsonl"
        items_file.write_text(
            json.dumps({"id": "item1", "text": "text1", "metadata": {"split": "test"}}) + "\n"
            + json.dumps({"id": "item2", "text": "text2", "metadata": {"split": "test"}}) + "\n"
        )

        # Write versions/c.jsonl with 3 items.
        versions_dir = task_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)
        versions_file = versions_dir / "c.jsonl"
        versions_file.write_text(
            json.dumps({"id": "v1", "text": "vtext1", "metadata": {}}) + "\n"
            + json.dumps({"id": "v2", "text": "vtext2", "metadata": {}}) + "\n"
            + json.dumps({"id": "v3", "text": "vtext3", "metadata": {}}) + "\n"
        )

        # Create a temporary output directory.
        out_dir = root / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Run the script with a fake engine.
        fake_engine = FakeEngine()
        asyncio.run(run(root, "t", "c", engine=fake_engine, out_dir=out_dir))

        # Check that both output files exist and contain the right number of rows.
        answers_dir = out_dir / "answers" / "laya" / "t"
        assert answers_dir.exists()

        # Check as-written file.
        as_written_path = answers_dir / "as-written.jsonl.gz"
        assert as_written_path.exists()
        as_written_rows = read_record(as_written_path)
        assert len(as_written_rows) == 2, f"Expected 2 as-written rows, got {len(as_written_rows)}"

        # Check cue file.
        cue_path = answers_dir / "c.jsonl.gz"
        assert cue_path.exists()
        cue_rows = read_record(cue_path)
        assert len(cue_rows) == 3, f"Expected 3 cue rows, got {len(cue_rows)}"

        # Check all rows have required keys.
        for row in as_written_rows + cue_rows:
            assert "id" in row
            assert "model" in row
            assert "usage" in row
            assert "latency_ms" in row
            assert "answers" in row


def test_it_resumes_from_a_partial_file():
    """Run the script twice, resuming from a partial file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create the task structure.
        task_dir = root / "tasks" / "t"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Write question.yaml.
        question_file = task_dir / "question.yaml"
        question_file.write_text("question: Q?\noptions:\n  - yes\n  - no\npositive: yes\ngroup_attribute: x\n")

        # Write items.jsonl with no test items (empty file).
        items_file = task_dir / "items.jsonl"
        items_file.write_text("")

        # Write versions/c.jsonl with 3 items.
        versions_dir = task_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)
        versions_file = versions_dir / "c.jsonl"
        versions_file.write_text(
            json.dumps({"id": "v1", "text": "vtext1", "metadata": {}}) + "\n"
            + json.dumps({"id": "v2", "text": "vtext2", "metadata": {}}) + "\n"
            + json.dumps({"id": "v3", "text": "vtext3", "metadata": {}}) + "\n"
        )

        # Create a temporary output directory.
        out_dir = root / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Pre-write a partial file with 1 row.
        answers_dir = out_dir / "answers" / "laya" / "t"
        answers_dir.mkdir(parents=True, exist_ok=True)
        partial_path = answers_dir / "c.jsonl.partial.jsonl"
        partial_path.write_text(
            json.dumps({"id": "v1", "model": "laya-upstream:0.3.7", "usage": None, "latency_ms": 100.0, "answers": {"Decision": {"choice": "yes"}}}) + "\n"
        )

        # Run the script with a fake engine.
        fake_engine = FakeEngine()
        asyncio.run(run(root, "t", "c", engine=fake_engine, out_dir=out_dir))

        # Check that the fake engine was called only 2 times (v2 and v3, not v1).
        assert fake_engine.call_count == 2, f"Expected 2 calls, got {fake_engine.call_count}"

        # Check that the final file exists.
        cue_path = answers_dir / "c.jsonl.gz"
        assert cue_path.exists()
        cue_rows = read_record(cue_path)
        assert len(cue_rows) == 3, f"Expected 3 cue rows, got {len(cue_rows)}"

        # Check that the partial file is gone.
        assert not partial_path.exists(), "Partial file should be deleted after completion"
