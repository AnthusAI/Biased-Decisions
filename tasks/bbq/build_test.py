"""Specs for tasks/bbq/build.py: the checksum guard, the rebuild, the balance and the window. The
fetch is not run here (no network in specs); specs that need the downloaded files skip without them."""
from __future__ import annotations

import glob
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("bbq_build", TASK / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

needs_source = pytest.mark.skipif(not (build.VAR_DIR / "Age.jsonl").exists(), reason="run build.py --fetch first")
TOKENIZERS = sorted(glob.glob(str(Path.home() / ".cache/huggingface/hub/models--aac6fef--laya-mlx/snapshots/*/tokenizer/tokenizer.json")))


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_a_source_file_with_the_wrong_checksum_stops_the_build(tmp_path):
    for name in build.SHA256:
        (tmp_path / name).write_text("x")
    with pytest.raises(SystemExit):
        build.verify(tmp_path)


def test_the_pinned_source_is_a_commit_not_a_moving_branch():
    assert "/main/" not in build.BASE_URL and len(build.COMMIT) == 40


def test_every_category_file_and_the_metadata_file_has_a_checksum():
    for category in build.discrim_bbq.BBQ_CATEGORIES:
        assert f"{category}.jsonl" in build.SHA256
    assert "additional_metadata.csv" in build.SHA256 and "LICENSE" in build.SHA256


@needs_source
def test_the_downloaded_files_match_their_recorded_checksums():
    build.verify(build.VAR_DIR)


@needs_source
def test_rebuilding_from_the_downloaded_files_reproduces_every_committed_file_byte_for_byte(tmp_path):
    build.build(out_dir=tmp_path)
    committed = sorted(p.relative_to(TASK) for p in TASK.rglob("*.jsonl")) + [Path("sampling.json")]
    assert committed
    for relative in committed:
        assert (tmp_path / relative).read_bytes() == (TASK / relative).read_bytes(), relative


def test_the_committed_counts_are_150_per_stratum_two_strata_per_category_and_condition():
    items = _rows(TASK / "items.jsonl")
    assert len(items) == 11 * 2 * 300
    counts = Counter((i["metadata"]["category"], i["metadata"]["context_condition"]) for i in items)
    assert set(counts.values()) == {300}
    for cue in build.discrim_bbq.bbq_cues():
        rows = _rows(TASK / "versions" / f"{cue}.jsonl")
        assert len(rows) == 600 and len({r["metadata"]["source_id"] for r in rows}) == 300


def test_ambiguous_items_are_half_negative_questions_and_informative_ones_half_bias_consistent():
    items = _rows(TASK / "items.jsonl")
    for category in build.discrim_bbq.BBQ_CATEGORIES:
        ambig = [i["metadata"] for i in items if i["metadata"]["category"] == category
                 and i["metadata"]["context_condition"] == "ambig"]
        dis = [i["metadata"] for i in items if i["metadata"]["category"] == category
               and i["metadata"]["context_condition"] == "disambig"]
        assert sum(m["question_polarity"] == "neg" for m in ambig) == 150
        assert sum(m["correct_role"] == "bias-consistent" for m in dis) == 150
        assert all(m["correct_role"] == "unknown" for m in ambig)


@needs_source
def test_every_context_and_question_is_the_datasets_own_unchanged():
    contexts = set()
    for category in build.discrim_bbq.BBQ_CATEGORIES:
        for line in (build.VAR_DIR / f"{category}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            contexts.add((r["context"], r["question"]))
    for r in _rows(TASK / "items.jsonl"):
        context, rest = r["text"].split("\nQuestion: ", 1)
        assert (context, rest.split("\nProposed answer: ", 1)[0]) in contexts


@pytest.mark.skipif(not TOKENIZERS, reason="Laya's tokenizer is not in the local model cache")
def test_every_text_fits_the_models_512_token_window_beside_the_question():
    from tokenizers import Tokenizer
    tk = Tokenizer.from_file(TOKENIZERS[0])

    class Tokens:
        def count(self, text):
            return len(tk.encode(text, add_special_tokens=False).ids)
    texts = [r["text"] for p in [TASK / "items.jsonl"] + sorted((TASK / "versions").glob("*.jsonl")) for r in _rows(p)]
    assert build.discrim_bbq.check_fits(texts, Tokens(), build.discrim_bbq.BBQ_QUESTION) > 0
