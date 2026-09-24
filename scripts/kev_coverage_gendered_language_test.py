"""Feature: the gendered-language Kev manifest is committed, complete and consistent with the task files."""
import json
from pathlib import Path

from scripts.make_kev_manifest import build_manifest
from scripts.run_kev_study import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "kev-coverage-gendered-language.json"
CELLS = [("gendered-management", c) for c in (
    "assertive-bossy", "direct-abrasive", "confident-aggressive", "calm-emotional",
    "decisive-pushy", "independent-selfish")] + [("gendered-advance", "agentic-communal")]


def test_the_committed_manifest_passes_the_runners_own_validation_with_52416_requests():
    assert validate_manifest(ROOT, MANIFEST) == 52416


def test_the_manifest_is_exactly_what_the_builder_makes_from_the_committed_files():
    assert json.loads(MANIFEST.read_text()) == build_manifest(ROOT, CELLS)


def test_the_word_choice_task_is_not_in_the_manifest_because_it_asks_a_question_per_row():
    assert all(c["task"] != "gendered-word-choice" for c in json.loads(MANIFEST.read_text())["cells"])


def test_the_amendment_is_registered_in_the_amendments_file():
    text = (ROOT / "docs" / "kev-amendments.md").read_text()
    assert "kev-coverage-gendered-language.json" in text and "52,416" in text
