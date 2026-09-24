"""Feature: the discrim-eval and BBQ Kev manifest is committed, complete and consistent with the files."""
import json
from pathlib import Path

from biased_decisions import discrim_bbq
from scripts.make_kev_manifest import build_manifest
from scripts.run_kev_study import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "kev-coverage-discrim-bbq.json"
CELLS = ([("discrim-eval", cue) for cue in ("race", "gender", "age")]
         + [("bbq", cue) for cue in discrim_bbq.bbq_cues()])


def test_the_committed_manifest_passes_the_runners_own_validation_with_22720_requests():
    assert validate_manifest(ROOT, MANIFEST) == 22720


def test_the_manifest_is_exactly_what_the_builder_makes_from_the_committed_files():
    assert json.loads(MANIFEST.read_text()) == build_manifest(ROOT, CELLS)


def test_the_manifest_covers_three_discrim_cues_and_twenty_two_bbq_cues():
    cells = json.loads(MANIFEST.read_text())["cells"]
    assert len(cells) == 25 and sum(c["task"] == "bbq" for c in cells) == 22
