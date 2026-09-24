import asyncio
import json
import math

import pytest

from biased_decisions.engines.kev import KevEngine


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, payload, headers, timeout):
        self.calls.append((url, payload, headers, timeout))
        return self.response


def question():
    return {"Occupation": {"type": "choice", "instructions": "Choose exactly one.",
                            "criteria": {"physician": "Doctor", "surgeon": "Surgeon"}}}


def response(**overrides):
    value = {"model": "kev-4b@abc123", "usage": {"input_tokens": 3},
             "answers": {"Occupation": {"type": "choice", "choice": "surgeon",
                                          "probabilities": {"physician": 0.25, "surgeon": 0.75}}}}
    value.update(overrides)
    return value


def test_forwards_questions_unchanged_and_carries_actual_response_metadata():
    transport = FakeTransport(response())
    engine = KevEngine(base_url="http://localhost:8009", model="kev-latest", transport=transport)
    answers = asyncio.run(engine.answer("same bio", question()))
    url, payload, headers, timeout = transport.calls[0]
    assert url == "http://localhost:8009/v1/systemone"
    assert payload == {"state": "same bio", "model": "kev-latest", "questions": question()}
    assert answers["Occupation"]["probabilities"] == {"physician": 0.25, "surgeon": 0.75}
    assert engine.model == "kev-4b@abc123"
    assert engine.usage == {"input_tokens": 3}


def test_repeated_identical_inputs_make_fresh_requests():
    transport = FakeTransport(response())
    engine = KevEngine(base_url="http://localhost:8009", transport=transport)
    asyncio.run(engine.answer("same", question()))
    asyncio.run(engine.answer("same", question()))
    assert len(transport.calls) == 2


@pytest.mark.parametrize("probabilities", [
    {"physician": 1.01, "surgeon": -0.01},
    {"physician": float("nan"), "surgeon": 0.5},
    {"physician": 0.5},
    {"physician": 0.5, "surgeon": 0.5, "other": 0},
])
def test_rejects_invalid_probability_maps(probabilities):
    body = response()
    body["answers"]["Occupation"]["probabilities"] = probabilities
    engine = KevEngine(base_url="http://localhost:8009", transport=FakeTransport(body))
    with pytest.raises(ValueError):
        asyncio.run(engine.answer("x", question()))


def test_rejects_invalid_choice_or_answer_coverage():
    for answers in ({}, {"Occupation": {"type": "choice", "choice": "other",
                                        "probabilities": {"physician": .5, "surgeon": .5}}},
                    {"extra": {}}):
        body = response(answers=answers)
        engine = KevEngine(base_url="http://localhost:8009", transport=FakeTransport(body))
        with pytest.raises(ValueError):
            asyncio.run(engine.answer("x", question()))


def test_missing_url_configuration_fails_without_network():
    with pytest.raises(ValueError, match="KEV_BASE_URL"):
        KevEngine(base_url="")
