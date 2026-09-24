"""Specs for choosing between the two Laya builds."""
import pytest

from biased_decisions.engines.builds import BUILDS, DEFAULT_BUILD, MlxModel, check_build, model_tag


def test_both_builds_are_selectable_and_the_default_stays_the_pytorch_one():
    assert set(BUILDS) == {"laya", "laya-mlx"}
    assert DEFAULT_BUILD == "laya"
    assert check_build("laya-mlx") == "laya-mlx"


def test_an_unknown_build_is_refused_by_name():
    with pytest.raises(ValueError, match="unknown build 'jev'"):
        check_build("jev")


def test_the_model_string_names_the_build_and_its_version():
    assert model_tag("laya", "0.3.7") == "laya-upstream:0.3.7"
    assert model_tag("laya-mlx", "0.1.0") == "laya-mlx:0.1.0"


class FakeAgent:
    def __init__(self):
        self.seen = []

    def system_one(self, state, questions):
        self.seen.append((state, questions))
        return {"usage": {"input_tokens": 1}, "answers": {k: {"type": "noul", "yes": 0.25} for k in questions}}


def test_the_mlx_model_unwraps_the_text_envelope_and_answers_every_question():
    agent, checked = FakeAgent(), []
    model = MlxModel(agent, check=lambda a, s, q: checked.append((s, sorted(q))))
    result = model.system_one({"text": "hello"}, {"q1": {"type": "noul", "instructions": "Is it?"},
                                                  "q2": {"type": "noul", "instructions": "Or is it?"}})
    assert agent.seen[0][0] == "hello"
    assert sorted(result["answers"]) == ["q1", "q2"]
    assert checked == [("hello", ["q1", "q2"])]


def test_the_mlx_model_refuses_a_request_the_budget_check_rejects_before_answering():
    agent = FakeAgent()

    def refuse(*_):
        raise RuntimeError("would truncate")

    with pytest.raises(RuntimeError):
        MlxModel(agent, check=refuse).system_one("x", {"q": {"type": "noul", "instructions": "?"}})
    assert agent.seen == []
