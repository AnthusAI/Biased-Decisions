"""Feature: replayable, priced single-profile proxy probe.

Given a committed pre-registration, when dry-run builds the schedule,
then exactly the 120 declared calls preserve qualifications and isolate questions.
Given a cap or failed response, when recording runs, then it stops safely and
preserves received evidence. Given recorded answers, when replay runs, then it
derives the same summary offline, including nulls and prediction misses.
"""
import asyncio
import json
from collections import Counter
from decimal import Decimal

import pytest

from biased_decisions import zonta_probe as probe


def test_given_preregistration_when_dry_run_then_fixed_bounded_schedule():
    schedule = probe.schedule()
    assert schedule == probe.schedule()
    assert len(schedule) == 120
    assert Counter((c["variant"], c["family"]) for c in schedule) == {
        (variant, family): 10 for variant in probe.SUFFIXES for family in probe.QUESTIONS
    }
    prereg = probe.PREREG.read_text()
    assert probe.QUALIFICATIONS in prereg
    for question in probe.QUESTIONS.values():
        assert question["instructions"] in prereg
    for call in schedule:
        assert call["payload"]["state"]["text"].startswith(probe.QUALIFICATIONS)
        assert len(call["payload"]["questions"]) == 1
        assert call["payload"]["model"] == "jev-1.13.0"
        assert probe.input_allowance(call["payload"]) <= 1500


def test_given_small_cap_when_reserving_then_no_call_allowed():
    with pytest.raises(probe.ProbeRefused, match="budget"):
        probe.reserve(Decimal("0"), Decimal("0.001"))
    with pytest.raises(probe.ProbeRefused, match="approval"):
        probe.reserve(Decimal("0"), Decimal("0.11"))


def fake_response(call, *, model="jev-1.13.0"):
    criteria = probe.QUESTIONS[call["family"]]["criteria"]
    probabilities = {key: float(i == 0) for i, key in enumerate(criteria)}
    return {"model": model, "usage": {"input_tokens": 300, "output_tokens": 20},
            "answers": {call["family"]: {"type": "choice", "choice": next(iter(criteria)),
            "confidence": 1.0, "probabilities": probabilities}}}


def test_given_wrong_model_when_received_then_record_before_abort(tmp_path):
    calls = []

    async def ask(call):
        calls.append(call)
        return fake_response(call, model="different-model")

    with pytest.raises(probe.ProbeRefused, match="model"):
        asyncio.run(probe.record(ask, tmp_path, Decimal("0.10")))
    rows = probe.read_rows(tmp_path)
    assert len(calls) == len(rows) == 1
    assert rows[0]["response"]["model"] == "different-model"


def test_given_records_when_replayed_then_all_cells_and_misses_preserved(tmp_path):
    async def ask(call):
        return fake_response(call)

    asyncio.run(probe.record(ask, tmp_path, Decimal("0.10")))
    summary = probe.summarize(probe.read_rows(tmp_path))
    assert summary["completed_calls"] == 120
    assert summary["input_tokens"] == 36000
    assert summary["estimated_charge_usd"] == "0.001512"
    assert len(summary["cells"]) == 12
    assert summary["contrasts"]["intact_minus_neutral_affiliation"]["P(woman)"] == 0
    assert not summary["predictions"]["H1"]["met"]
    assert not summary["predictions"]["H4"]["met"]
    encoded = probe.summary_bytes(summary)
    assert encoded == probe.summary_bytes(probe.summarize(probe.read_rows(tmp_path)))
    assert json.loads(encoded)["complete"] is True
    with pytest.raises(probe.ProbeRefused, match="existing"):
        asyncio.run(probe.record(ask, tmp_path, Decimal("0.10")))


def test_given_secret_in_error_when_recording_then_only_type_preserved(tmp_path):
    async def ask(call):
        raise ValueError("pretend-sensitive-credential")

    with pytest.raises(probe.ProbeRefused):
        asyncio.run(probe.record(ask, tmp_path, Decimal("0.10")))
    output = (tmp_path / "responses.jsonl").read_text()
    assert "pretend-sensitive" not in output
    assert "ValueError" in output
