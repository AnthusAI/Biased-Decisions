"""Feature: the original upstream Laya package, called through its own ``system_one``.

New for Biased-Decisions (the upstream package has no Jev-Flywheel counterpart to port from).
The ``laya`` package is mocked throughout -- never imported for real, never loaded, no checkpoint,
no GPU -- so these specs run anywhere and never touch a network or an accelerator.
"""
import sys
import types

import pytest

from biased_decisions.engines.laya import (
    LayaEngine, LayaUpstreamClient, build_question)


def _install_fake_laya(monkeypatch, *, version="0.3.7", model=None):
    fake = types.ModuleType("laya")
    fake.__version__ = version
    fake.load = lambda: model
    monkeypatch.setitem(sys.modules, "laya", fake)
    return fake


def test_build_question_maps_each_option_to_itself():
    q = build_question("Is this person a surgeon or a physician?", ["surgeon", "physician"])
    assert q == {
        "type": "choice",
        "instructions": "Is this person a surgeon or a physician?",
        "criteria": {"surgeon": "surgeon", "physician": "physician"},
    }


def test_the_package_is_imported_lazily(monkeypatch):
    # Importing this module, or building a client, must never import the real package.
    monkeypatch.delitem(sys.modules, "laya", raising=False)
    LayaUpstreamClient()
    assert "laya" not in sys.modules


def test_a_missing_package_raises_a_clear_install_hint(monkeypatch):
    # The 'laya' package is not a core dependency, so it is genuinely absent in this test
    # environment; no import needs blocking to prove the hint fires.
    import importlib.util

    monkeypatch.delitem(sys.modules, "laya", raising=False)
    if importlib.util.find_spec("laya") is not None:
        pytest.skip("'laya' happens to be installed; skip this negative case")
    with pytest.raises(ImportError, match=r"pip install 'biased-decisions\[laya\]'"):
        LayaUpstreamClient().system_one(state="hi", questions={})


class FakeModel:
    """Stands in for what ``laya.load()`` returns: a model with a ``system_one`` method."""

    def __init__(self, probabilities):
        self.probabilities = probabilities
        self.calls = []

    def system_one(self, *, state, questions):
        self.calls.append((state, dict(questions)))
        choice = max(self.probabilities, key=self.probabilities.get)
        return {
            "answers": {
                "Occupation": {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": dict(self.probabilities),
                    "confidence": max(self.probabilities.values()),
                    "action": {"act_probability": 1.0},
                }
            },
            "usage": {"input_tokens": 149, "output_tokens": 0},
        }


def test_system_one_loads_once_and_calls_the_model_directly(monkeypatch):
    model = FakeModel({"surgeon": 0.2352, "physician": 0.7648})
    _install_fake_laya(monkeypatch, model=model)
    client = LayaUpstreamClient()
    q = build_question("Is this person a surgeon or a physician?", ["surgeon", "physician"])

    result = client.system_one(state="He is a surgeon.", questions={"Occupation": q})
    client.system_one(state="She is a surgeon.", questions={"Occupation": q})

    assert len(model.calls) == 2                          # loaded once, called per item
    assert model.calls[0][0] == "He is a surgeon."         # state is the raw text, not wrapped
    assert result["answers"]["Occupation"]["choice"] == "physician"
    assert result["answers"]["Occupation"]["probabilities"] == {
        "surgeon": 0.2352, "physician": 0.7648}
    assert result["usage"] == {"input_tokens": 149, "output_tokens": 0}
    assert "latency_ms" in result


def test_the_model_string_names_the_upstream_version(monkeypatch):
    _install_fake_laya(monkeypatch, version="0.3.7", model=FakeModel({"a": 1.0}))
    engine = LayaEngine()
    engine._client._load()  # trigger the lazy load so .version reads the fake module

    assert engine.model_string == "laya-upstream:0.3.7"


async def test_engine_answer_returns_just_the_answers_mapping(monkeypatch):
    model = FakeModel({"surgeon": 0.9, "physician": 0.1})
    _install_fake_laya(monkeypatch, model=model)
    engine = LayaEngine()
    q = build_question("Is this person a surgeon or a physician?", ["surgeon", "physician"])

    answers = await engine.answer("He is a surgeon.", {"Occupation": q})

    assert set(answers) == {"Occupation"}
    assert answers["Occupation"]["choice"] == "surgeon"


def test_answer_row_matches_the_committed_record_shape(monkeypatch):
    model = FakeModel({"surgeon": 0.2352, "physician": 0.7648})
    _install_fake_laya(monkeypatch, version="0.3.7", model=model)
    engine = LayaEngine()
    q = build_question("Is this person a surgeon or a physician?", ["surgeon", "physician"])

    row = engine.answer_row("bios-172325", "He studied at Charite University.",
                            {"Occupation": q})

    assert row["id"] == "bios-172325"
    assert row["model"] == "laya-upstream:0.3.7"
    assert set(row) == {"id", "model", "usage", "latency_ms", "answers"}
    assert row["answers"]["Occupation"]["probabilities"] == {
        "surgeon": 0.2352, "physician": 0.7648}
