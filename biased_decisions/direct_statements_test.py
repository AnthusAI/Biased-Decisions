from __future__ import annotations

from pathlib import Path

from biased_decisions import direct_statements as ds

ROOT = Path(__file__).resolve().parents[1]
PREREG = (ROOT / "docs" / "direct-statements-controlled-preregistration.md").read_text(encoding="utf-8")


def test_every_reversal_is_quoted_verbatim_from_the_preregistration():
    for text in ds.CLAIM_REVERSALS.values():
        assert f"| {text} |" in PREREG
    for rev in ds.GAZA_REVERSALS.values():
        if isinstance(rev, str):
            assert f"| {rev} |" in PREREG


def test_prompt_counts_match_the_plan():
    assert len(ds.claim_items()) == 60
    assert len(ds.gaza_items()) == 364


def test_the_committed_tasks_are_what_the_builder_writes(tmp_path):
    ds.write_tasks(tmp_path)
    for slug in (ds.CLAIMS_SLUG, ds.GAZA_SLUG):
        for name in ("items.jsonl", "question.yaml"):
            assert (tmp_path / "tasks" / slug / name).read_bytes() == (ROOT / "tasks" / slug / name).read_bytes()


def _row(probs):
    return {"model": "test", "answers": {"Decision": {"probabilities": probs}}}


def test_a_model_that_says_yes_to_everything_has_no_stance_and_full_acquiescence():
    answers = {r["id"]: _row({"A": 0.5, "B": 0.5}) for r in ds.claim_items()}
    for r in ds.claim_items():
        # always picks whichever option says Yes
        yes_letter = "A" if r["metadata"]["order"] == "yes-first" else "B"
        answers[r["id"]] = _row({yes_letter: 1.0})
    row = ds.score_claims("x", answers)
    for p in row["pairs"].values():
        assert p["stance"] == 0 and p["acquiescence"] == 1 and p["shown"] is False


def test_a_consistent_model_has_full_stance_and_no_acquiescence():
    answers = {}
    for r in ds.claim_items():
        agree = r["metadata"]["side"] == "R"
        yes_letter = "A" if r["metadata"]["order"] == "yes-first" else "B"
        no_letter = "B" if yes_letter == "A" else "A"
        answers[r["id"]] = _row({yes_letter if agree else no_letter: 1.0})
    row = ds.score_claims("x", answers)
    for p in row["pairs"].values():
        assert p["stance"] == -1 and p["acquiescence"] == 0 and p["shown"] is True
    assert all(d["shown"] for d in row["domains"].values())


def test_a_model_that_always_picks_the_first_letter_shows_an_order_effect_on_the_scale():
    answers = {r["id"]: _row({"A": 1.0}) for r in ds.gaza_items()}
    row = ds.score_gaza("x", answers)
    for p in row["pairs"].values():
        assert p["stance"] == 0 and p["acquiescence"] == 0 and p["order_effect"] == 1 and p["shown"] is False
