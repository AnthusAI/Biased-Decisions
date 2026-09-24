import json

from scripts.make_kev_manifest import build_manifest, write_run_manifests


def make_root(tmp_path):
    for task, count in (("alpha", 8), ("beta", 8)):
        folder = tmp_path / "tasks" / task
        folder.mkdir(parents=True)
        (folder / "question.yaml").write_text(
            "question: Which?\noptions: [yes, no]\npositive: yes\ngroup_attribute: group\n")
        (folder / "items.jsonl").write_text("\n".join(
            json.dumps({"id": f"{task}-{i}", "text": f"text {i}", "metadata": {"split": "test"}})
            for i in range(count)) + "\n")
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"schema": "kev-coverage@1", "checkpoint": "repo@" + "a" * 40, "cells": [
        {"task": "alpha", "cue": "as-written", "requests": 8, "status": "ready", "files": {}},
        {"task": "beta", "cue": "as-written", "requests": 8, "status": "ready", "files": {}}]}))
    return frozen


def test_a_manifest_cell_records_its_item_cap_and_counts_the_capped_requests(tmp_path):
    frozen = make_root(tmp_path)
    manifest = build_manifest(tmp_path, [("alpha", "as-written")], frozen, item_cap=3)
    cell = manifest["cells"][0]
    assert cell["item_cap"] == 3 and cell["requests"] == 3
    assert "item_cap" not in build_manifest(tmp_path, [("alpha", "as-written")], frozen)["cells"][0]


def test_run_manifests_hold_only_the_cells_the_model_has_not_answered_one_file_per_task(tmp_path):
    frozen = make_root(tmp_path)
    answered = tmp_path / "answers" / "kev" / "alpha"
    answered.mkdir(parents=True)
    (answered / "as-written.jsonl.gz").write_bytes(b"")
    out = tmp_path / "runs"
    written = write_run_manifests(tmp_path, "kev", frozen, out, item_cap=4)
    assert [p.name for p in written] == ["beta.json"]
    manifest = json.loads((out / "beta.json").read_text())
    assert [(c["task"], c["cue"], c["requests"], c["item_cap"]) for c in manifest["cells"]] == \
        [("beta", "as-written", 4, 4)]
    assert manifest["checkpoint"] == "repo@" + "a" * 40
