"""Scoring batch 3 from a record that covers only the registered first-pass subsample."""
import shutil
from pathlib import Path

import pytest

from biased_decisions.record import read_record, write_record
from biased_decisions.stereotypes_batch3 import score_stereotypes
from biased_decisions.subsample import subsample
from biased_decisions.tasks.base import Task

REPO = Path(__file__).resolve().parents[1]
SLUG = "stereotypes-batch3"
AXIS = "orientation"


def staged(tmp_path, keep):
    """A tmp root holding the real task and a Kev record made of Laya's real answers for the versions ``keep``."""
    shutil.copytree(REPO / "tasks" / SLUG, tmp_path / "tasks" / SLUG)
    task = Task.load(SLUG, root=tmp_path)
    versions = task.load_versions(AXIS)
    wanted = keep(versions)
    source = read_record(REPO / "answers" / "laya" / SLUG / f"{AXIS}.jsonl.gz")
    write_record(tmp_path / "answers" / "kev" / SLUG / f"{AXIS}.jsonl.gz", [r for r in source if r["id"] in wanted])
    return task, versions


def registered(versions):
    return {v.id for v in subsample(versions, SLUG, 500)}


def test_a_record_of_exactly_the_registered_subsample_scores_that_sample(tmp_path):
    task, versions = staged(tmp_path, registered)
    row = score_stereotypes("kev", task, AXIS)
    bios = {v.metadata["source_id"] for v in versions if v.id in registered(versions)}
    assert row["n"] == len(bios) and 0 < row["n"] < 2000


def test_a_complete_record_still_scores_every_bio(tmp_path):
    task, _ = staged(tmp_path, lambda versions: {v.id for v in versions})
    assert score_stereotypes("kev", task, AXIS)["n"] == 2000


def test_a_record_of_some_other_subsample_is_refused(tmp_path):
    def other(versions):
        keep = registered(versions)
        extra = [v.id for v in versions if v.id not in keep][:40]
        return set(sorted(keep)[40:]) | set(extra)
    task, _ = staged(tmp_path, other)
    with pytest.raises(KeyError, match="registered subsample"):
        score_stereotypes("kev", task, AXIS)
