"""Feature: building a Kev coverage manifest for newly registered task/cue cells."""
import json
from pathlib import Path

from scripts.make_kev_manifest import build_manifest
from scripts.run_kev_study import load_coverage, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_a_cell_the_frozen_manifest_already_registers_comes_out_identical():
    frozen = {(c["task"], c["cue"]): c for c in load_coverage(ROOT / "docs" / "kev-coverage.json")["cells"]}
    built = build_manifest(ROOT, [("surgeon-physician", "gender-pronouns"), ("qpain-treatment", "race")])
    for cell in built["cells"]:
        assert cell == frozen[(cell["task"], cell["cue"])]


def test_the_manifest_names_the_frozen_checkpoint_and_the_schema_the_runner_reads():
    built = build_manifest(ROOT, [("surgeon-physician", "gender-pronouns")])
    frozen = load_coverage(ROOT / "docs" / "kev-coverage.json")
    assert built["schema"] == "kev-coverage@1" and built["checkpoint"] == frozen["checkpoint"]


def test_a_multi_question_task_counts_one_request_per_text(tmp_path):
    built = build_manifest(ROOT, [("stereotypes-antisemitism", "as-written")])
    cell = built["cells"][0]
    assert cell["requests"] == 2000 and cell["status"] == "ready"
    assert set(cell["files"]) == {"tasks/stereotypes-antisemitism/question.yaml",
                                  "tasks/stereotypes-antisemitism/items.jsonl"}


def test_the_built_manifest_passes_the_runners_own_validation(tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps(build_manifest(ROOT, [("stereotypes-antisemitism", "antisemitism-religious")])))
    assert validate_manifest(ROOT, path) == 5512


def test_an_unregistered_cue_is_refused_and_not_guessed():
    import pytest
    with pytest.raises(Exception):
        build_manifest(ROOT, [("stereotypes-antisemitism", "no-such-cue")])
