"""Feature: the batch 3 Kev manifest is committed, complete and consistent with the task's files."""
from pathlib import Path

from scripts.make_kev_manifest import build_manifest
from biased_decisions.collector import collect
from scripts.run_kev_study import collection_cue, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "kev-coverage-batch3.json"
CUES = ["as-written", "orientation", "race", "nationality-x", "china", "india", "africa", "family"]


def test_the_committed_manifest_passes_the_runners_own_validation_with_96000_requests():
    # Plan under an engine with no record: Kev's own (capped) first-pass records are not this manifest's subject.
    assert validate_manifest(ROOT, MANIFEST, dry_run_cell=lambda root, task, cue: collect(root, "spec-probe", task, collection_cue(cue), dry_run=True)) == 96000


def test_the_manifest_is_exactly_what_the_builder_makes_from_the_committed_files():
    import json
    built = build_manifest(ROOT, [("stereotypes-batch3", cue) for cue in CUES], plan_engine="spec-probe")
    assert json.loads(MANIFEST.read_text()) == built
