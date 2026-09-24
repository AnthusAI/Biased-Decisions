import hashlib
import json
from pathlib import Path

import pytest

from scripts.run_kev_study import collection_cue, main, run_pilot, validate_manifest


class FakeEngine:
    model_name = "kev-latest"
    model = "kev-latest"
    calls = 0
    fail_at = None

    async def answer(self, text, questions):
        self.calls += 1
        if self.fail_at == self.calls:
            raise RuntimeError("interrupted")
        name, question = next(iter(questions.items()))
        options = list(question["criteria"])
        return {name: {"type": "choice", "choice": options[0],
                       "probabilities": {options[0]: 0.7, options[1]: 0.3}}}


def make_root(tmp_path, *, count=20):
    root = tmp_path
    task = root / "tasks" / "surgeon-physician"
    task.mkdir(parents=True)
    (task / "question.yaml").write_text(
        "question: Pick an occupation.\noptions: [surgeon, physician]\npositive: surgeon\n"
        "group_attribute: gender\n",
        encoding="utf-8")
    lines = []
    for i in range(count):
        lines.append(json.dumps({"id": f"i{i}", "text": f"bio {i}",
                                 "metadata": {"split": "test"}}))
    # Add a counterfactual after the original test set; the pilot must exclude it.
    lines.append(json.dumps({"id": "twin", "text": "twin bio",
                             "metadata": {"split": "counterfactual"}}))
    (task / "items.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    files = {}
    for rel in ("tasks/surgeon-physician/question.yaml", "tasks/surgeon-physician/items.jsonl"):
        files[rel] = hashlib.sha256((root / rel).read_bytes()).hexdigest()
    manifest = {"schema": "kev-coverage@1", "cells": [
        {"task": "surgeon-physician", "cue": "as-written", "requests": count,
         "status": "ready", "files": files}
    ]}
    manifest_path = root / "coverage.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return root, manifest_path, manifest


def provenance():
    return {"checkpoint": "repo@" + "a" * 40, "server_revision": "b" * 40,
            "base_revision": "c" * 40, "backend": "mlx", "dtype": "bfloat16",
            "calibration": "temperature=2.406"}


def test_manifest_checkpoint_must_match_actual_selected_checkpoint():
    from scripts.run_kev_study import validate_pinned_checkpoint

    manifest = {"checkpoint": provenance()["checkpoint"]}
    validate_pinned_checkpoint(manifest, provenance())
    with pytest.raises(ValueError, match="manifest checkpoint"):
        validate_pinned_checkpoint(manifest, {**provenance(), "checkpoint": "other@" + "d" * 40})


def test_manifest_validation_checks_all_hashes_before_collection(tmp_path):
    root, manifest_path, manifest = make_root(tmp_path, count=1)
    assert validate_manifest(root, manifest_path, dry_run_cell=lambda *args: {"total": 1}) == 1
    (root / "tasks/surgeon-physician/items.jsonl").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        validate_manifest(root, manifest_path, dry_run_cell=lambda *args: pytest.fail("dry run called"))


def test_manifest_validation_checks_coverage_counts(tmp_path):
    root, manifest_path, manifest = make_root(tmp_path, count=1)
    with pytest.raises(ValueError, match="request count"):
        validate_manifest(root, manifest_path, dry_run_cell=lambda *args: {"total": 2})


def test_preregistered_option_order_maps_to_reversed_collection_cell():
    assert collection_cue("option-order") == "option-order-reversed"
    assert collection_cue("gender-pronouns") == "gender-pronouns"


def test_cli_dry_run_validates_without_creating_engine(tmp_path, capsys):
    root, manifest_path, _ = make_root(tmp_path, count=1)

    def no_engine(_args):
        pytest.fail("dry-run must not create a server client")

    assert main(["dry-run", "--root", str(root), "--manifest", str(manifest_path)],
                engine_factory=no_engine) == 0
    assert json.loads(capsys.readouterr().out)["requests"] == 1


def test_pilot_resumes_incrementally_and_only_uses_original_bios(tmp_path):
    root, _, _ = make_root(tmp_path, count=20)
    engine = FakeEngine()
    engine.calls = 0
    engine.fail_at = 6
    try:
        run_pilot(root, engine, provenance())
    except RuntimeError as error:
        assert str(error) == "interrupted"
    else:
        pytest.fail("expected interruption")
    pilot = root / "studies/kev/pilot.jsonl"
    assert len(pilot.read_text(encoding="utf-8").splitlines()) == 5
    engine.calls = 0
    engine.fail_at = None
    result = run_pilot(root, engine, provenance())
    assert result["complete"] is True
    rows = [json.loads(line) for line in pilot.read_text(encoding="utf-8").splitlines()]
    assert [row["id"] for row in rows] == [f"i{i}" for i in range(20)]
    assert engine.calls == 15
    assert (root / "studies/kev/pilot.metadata.json").exists()
    assert (root / "studies/kev/pilot.timing.json").exists()
    assert result["new_items"] == 15
    rows = [json.loads(line) for line in pilot.read_text(encoding="utf-8").splitlines()]
    assert all("wall_elapsed_ms" in row for row in rows)
    timing = json.loads((root / "studies/kev/pilot.timing.json").read_text(encoding="utf-8"))
    assert timing["total_observed_call_seconds"] == pytest.approx(
        sum(row["wall_elapsed_ms"] for row in rows) / 1000)
    assert "last_invocation_elapsed_seconds" in timing


def test_completed_pilot_refuses_changed_provenance(tmp_path):
    root, _, _ = make_root(tmp_path, count=20)
    engine = FakeEngine()
    engine.calls = 0
    engine.fail_at = None
    run_pilot(root, engine, provenance())
    calls_after_complete = engine.calls
    changed = {**provenance(), "server_revision": "d" * 40}
    with pytest.raises(ValueError, match="provenance"):
        run_pilot(root, engine, changed)
    assert engine.calls == calls_after_complete


def test_pilot_resume_requires_existing_rows_to_be_expected_prefix(tmp_path):
    root, _, _ = make_root(tmp_path, count=20)
    engine = FakeEngine()
    engine.calls = 0
    engine.fail_at = 4
    with pytest.raises(RuntimeError):
        run_pilot(root, engine, provenance())
    path = root / "studies/kev/pilot.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[1], rows[2] = rows[2], rows[1]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    engine.fail_at = None
    with pytest.raises(ValueError, match="prefix"):
        run_pilot(root, engine, provenance())


def test_pilot_fingerprint_includes_item_metadata_and_task_definition(tmp_path):
    root, _, _ = make_root(tmp_path, count=20)
    engine = FakeEngine()
    engine.calls = 0
    engine.fail_at = 2
    with pytest.raises(RuntimeError):
        run_pilot(root, engine, provenance())
    item_path = root / "tasks/surgeon-physician/items.jsonl"
    items = [json.loads(line) for line in item_path.read_text(encoding="utf-8").splitlines()]
    items[0]["metadata"]["reference_label"] = "changed"
    item_path.write_text("".join(json.dumps(item) + "\n" for item in items), encoding="utf-8")
    engine.fail_at = None
    with pytest.raises(ValueError, match="input_fingerprint"):
        run_pilot(root, engine, provenance())


def test_pilot_fingerprint_includes_parsed_task_question(tmp_path):
    root, _, _ = make_root(tmp_path, count=20)
    engine = FakeEngine()
    engine.calls = 0
    engine.fail_at = 2
    with pytest.raises(RuntimeError):
        run_pilot(root, engine, provenance())
    question_path = root / "tasks/surgeon-physician/question.yaml"
    question_path.write_text(
        "question: Pick an updated occupation.\noptions: [surgeon, physician]\n"
        "positive: surgeon\ngroup_attribute: gender\n", encoding="utf-8")
    engine.fail_at = None
    with pytest.raises(ValueError, match="input_fingerprint"):
        run_pilot(root, engine, provenance())
