"""Specs for tasks/discrim-eval/build.py: the checksum guard, the rebuild and the window. The fetch
itself is not run here (no network in specs); specs that need the downloaded file skip without it."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("discrim_build", TASK / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

SOURCE = build.VAR_DIR / "explicit.jsonl"
needs_source = pytest.mark.skipif(not SOURCE.exists(), reason="run build.py --fetch first")
TOKENIZERS = sorted(glob.glob(str(Path.home() / ".cache/huggingface/hub/models--aac6fef--laya-mlx/snapshots/*/tokenizer/tokenizer.json")))


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_a_source_file_with_the_wrong_checksum_stops_the_build(tmp_path):
    (tmp_path / "explicit.jsonl").write_text("{}\n")
    with pytest.raises(SystemExit):
        build.verify(tmp_path)


def test_the_pinned_source_is_a_revision_not_a_moving_branch():
    assert "/resolve/main/" not in build.BASE_URL
    assert len(build.REVISION) == 40


@needs_source
def test_the_downloaded_file_matches_its_recorded_checksum():
    build.verify(build.VAR_DIR)


@needs_source
def test_rebuilding_from_the_downloaded_file_reproduces_every_committed_file_byte_for_byte(tmp_path):
    build.build(out_dir=tmp_path)
    committed = sorted(p.relative_to(TASK) for p in TASK.rglob("*.jsonl")) + [Path("sampling.json")]
    assert committed
    for relative in committed:
        assert (tmp_path / relative).read_bytes() == (TASK / relative).read_bytes(), relative


def test_the_committed_counts_are_seventy_scenarios_and_eight_backgrounds_per_scenario_and_cue():
    assert len(_rows(TASK / "items.jsonl")) == 70
    for cue, values in (("race", 5), ("gender", 3), ("age", 9)):
        rows = _rows(TASK / "versions" / f"{cue}.jsonl")
        assert len(rows) == 70 * 8 * values
        assert len({r["id"] for r in rows}) == len(rows)
        sources = {r["metadata"]["source_id"] for r in rows}
        assert len(sources) == 70 * 8


@needs_source
def test_every_committed_text_is_a_text_the_dataset_itself_contains_unchanged():
    source = {json.loads(l)["filled_template"] for l in SOURCE.read_text(encoding="utf-8").splitlines()}
    for path in [TASK / "items.jsonl"] + sorted((TASK / "versions").glob("*.jsonl")):
        assert all(r["text"] in source for r in _rows(path)), path.name


def test_every_version_of_a_source_differs_from_its_reference_only_in_the_changed_attribute():
    for cue, key in (("race", "race"), ("gender", "gender"), ("age", "age")):
        by_source = {}
        for r in _rows(TASK / "versions" / f"{cue}.jsonl"):
            by_source.setdefault(r["metadata"]["source_id"], []).append(r["metadata"])
        for metas in by_source.values():
            for other in [a for a in ("age", "gender", "race") if a != key]:
                assert len({m[other] for m in metas}) == 1


@pytest.mark.skipif(not TOKENIZERS, reason="Laya's tokenizer is not in the local model cache")
def test_every_text_fits_the_models_512_token_window_beside_the_question():
    from tokenizers import Tokenizer
    tk = Tokenizer.from_file(TOKENIZERS[0])

    class Tokens:
        def count(self, text):
            return len(tk.encode(text, add_special_tokens=False).ids)
    from biased_decisions import discrim_bbq
    texts = [r["text"] for p in [TASK / "items.jsonl"] + sorted((TASK / "versions").glob("*.jsonl")) for r in _rows(p)]
    assert discrim_bbq.check_fits(texts, Tokens(), discrim_bbq.DISCRIM_QUESTION) > 0
