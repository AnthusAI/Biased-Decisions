import asyncio

import pytest

from biased_decisions.engines.kev import KevEngine


class FakeTransport:
    def __init__(self, response=None, models=None):
        self.response = response
        self.models = models
        self.calls = []

    def post(self, url, payload, headers, timeout):
        self.calls.append((url, payload, headers, timeout))
        return self.response

    def get(self, url, headers, timeout):
        self.calls.append((url, None, headers, timeout))
        return self.models


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
    assert list(payload["questions"]["Occupation"]["criteria"]) == ["physician", "surgeon"]
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


def test_multiple_questions_and_type_are_preserved():
    qs = question()
    qs["Confidence"] = {"type": "noul", "instructions": "Is the answer clear?"}
    body = response(answers={
        "Occupation": {"type": "choice", "choice": "surgeon",
                       "probabilities": {"surgeon": 0.749, "physician": 0.251}},
        "Confidence": {"type": "noul", "noul": 0.8},
    })
    transport = FakeTransport(body)
    result = asyncio.run(KevEngine(base_url="http://localhost:8009", transport=transport).answer("x", qs))
    assert list(result) == ["Occupation", "Confidence"]
    assert list(result["Occupation"]["probabilities"]) == ["physician", "surgeon"]


def test_rejects_wrong_answer_type_and_bad_probability_total():
    for answer in (
        {"type": "noul", "choice": "surgeon", "probabilities": {"physician": .5, "surgeon": .5}},
        {"type": "choice", "choice": "surgeon", "probabilities": {"physician": 0, "surgeon": 0}},
    ):
        engine = KevEngine(base_url="http://localhost:8009",
                           transport=FakeTransport(response(answers={"Occupation": answer})))
        with pytest.raises(ValueError):
            asyncio.run(engine.answer("x", question()))


def test_accepts_upstream_four_decimal_probability_rounding():
    qs = {"Q": {"type": "choice", "instructions": "Pick one",
                 "criteria": {"a": "A", "b": "B", "c": "C"}}}
    body = response(answers={"Q": {"type": "choice", "choice": "a",
                                    "probabilities": {"a": .3333, "b": .3333, "c": .3333}}})
    result = asyncio.run(KevEngine(base_url="http://localhost:8009",
                                   transport=FakeTransport(body)).answer("x", qs))
    assert result["Q"]["probabilities"]["c"] == .3333


def test_missing_url_configuration_fails_without_network():
    with pytest.raises(ValueError, match="KEV_BASE_URL"):
        KevEngine(base_url="")


def test_factory_registry_and_report_metadata_include_kev(monkeypatch):
    from biased_decisions.answering import _engine_factory, _check_engine_installed, AnswerRefused
    from biased_decisions.report import ENGINE_LABELS, GENDER_PRONOUNS_ENGINES
    from biased_decisions.scoring import ENGINES

    monkeypatch.delenv("KEV_BASE_URL", raising=False)
    with pytest.raises(AnswerRefused, match="KEV_BASE_URL"):
        _check_engine_installed("kev")
    monkeypatch.setenv("KEV_BASE_URL", "http://127.0.0.1:8009")
    assert isinstance(_engine_factory("kev"), KevEngine)
    assert "kev" in ENGINES and "kev" in GENDER_PRONOUNS_ENGINES
    assert ENGINE_LABELS["kev"] == "Kev"


def test_provenance_pins_models_endpoint_and_excludes_dynamic_cache_counters():
    sha = "a" * 40
    transport = FakeTransport(models={"models": [{
        "name": "kev-latest", "run": f"jaredpalmer/kev-0.8b@{sha}",
        "base": "Qwen/Qwen3.5-0.8B", "backend": "mlx", "dtype": "bfloat16",
        "temperature": 2.406050072164233,
        "prefix_cache": {"enabled": False, "size": 4, "min_state_tokens": 80,
                          "hits": 11, "misses": 3},
    }]})
    engine = KevEngine(base_url="http://localhost:8009", transport=transport)
    provenance = engine.provenance(server_revision=sha, base_revision="b" * 40,
                                   backend="mlx", dtype="bfloat16",
                                   calibration="2.406050072164233")
    assert provenance["checkpoint"] == f"jaredpalmer/kev-0.8b@{sha}"
    assert provenance["base_revision"] == "b" * 40
    assert provenance["calibration"] == "temperature=2.406050072164233"
    assert provenance["prefix_cache"] == {"enabled": False, "size": 4,
                                           "min_state_tokens": 80}
    assert "hits" not in provenance["prefix_cache"]


def test_provenance_rejects_unpinned_checkpoint():
    transport = FakeTransport(models={"models": [{"name": "kev-latest", "run": "jaredpalmer/kev-0.8b"}]})
    engine = KevEngine(base_url="http://localhost:8009", transport=transport)
    with pytest.raises(ValueError, match="40-hex"):
        engine.provenance(server_revision="a" * 40, base_revision="b" * 40,
                          backend="mlx", dtype="bfloat16", calibration="2.4")


@pytest.mark.parametrize("value", [float("nan"), -0.1, 1.1, True])
def test_noul_values_must_be_finite_and_bounded(value):
    qs = {"greed_q1": {"type": "noul", "instructions": "Is this greed?"}}
    engine = KevEngine(base_url="http://localhost:8009", transport=FakeTransport(
        response(answers={"greed_q1": {"type": "noul", "noul": value}})))
    with pytest.raises(ValueError, match="noul"):
        asyncio.run(engine.answer("x", qs))
