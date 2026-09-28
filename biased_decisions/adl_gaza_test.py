"""Checks for the fixed ADL Gaza/Israel–Hamas response scorer."""
from biased_decisions import adl_gaza


def _answers():
    return {
        f"s{number:02d}-{persona}": {
            "model": "laya", "answers": {"Decision": {
                "choice": "A", "probabilities": {"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1}
            }}
        }
        for number in range(1, 16) for persona in adl_gaza.PERSONAS
    }


def test_the_scorer_keeps_every_statement_and_persona_response():
    result = adl_gaza.score_adl_gaza("laya", _answers())
    assert len(result["statements"]) == 15
    assert set(result["statements"]["s01"]["variants"]) == set(adl_gaza.PERSONAS)
    generic = result["statements"]["s01"]["variants"]["generic"]
    assert generic["choice"] == "A"
    assert generic["agree_pct"] == 70.0
    assert generic["mean_response"] == 2.0
