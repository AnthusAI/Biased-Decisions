"""Specs for the word-choice answer runner: each text is asked its own question, in its own option order."""
import asyncio
import json

from biased_decisions.record import read_record
from scripts.answer_wordchoice import run


class FakeEngine:
    def __init__(self):
        self.calls = []

    async def answer(self, text, questions):
        self.calls.append((text, questions))
        options = list(questions["Decision"]["criteria"])
        return {"Decision": {"choice": options[0], "probabilities": {options[0]: 0.6, options[1]: 0.4}}}


def _task(root, n=3):
    d = root / "tasks" / "gendered-word-choice"
    (d / "versions").mkdir(parents=True)
    (d / "question.yaml").write_text(
        "question: Q?\noptions:\n  - neutral\n  - loaded\npositive: loaded\ngroup_attribute: gender\n")
    (d / "items.jsonl").write_text("")
    rows = []
    for i in range(n):
        options = ["bossy", "assertive"] if i % 2 else ["assertive", "bossy"]
        rows.append({"id": f"r{i}", "text": f"t{i}", "metadata": {
            "options": options, "question": f"pick {options[0]} or {options[1]}"}})
    (d / "versions" / "assertive-bossy.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_each_text_is_asked_its_own_question_with_its_own_option_order(tmp_path):
    _task(tmp_path)
    engine = FakeEngine()
    asyncio.run(run(tmp_path, "assertive-bossy", engine=engine))
    asked = [(q["Decision"]["instructions"], list(q["Decision"]["criteria"])) for _, q in engine.calls]
    assert asked == [("pick assertive or bossy", ["assertive", "bossy"]),
                     ("pick bossy or assertive", ["bossy", "assertive"]),
                     ("pick assertive or bossy", ["assertive", "bossy"])]


def test_the_record_lands_under_the_build_and_holds_one_row_per_text(tmp_path):
    _task(tmp_path)
    asyncio.run(run(tmp_path, "assertive-bossy", engine=FakeEngine(), build="laya-mlx"))
    rows = read_record(tmp_path / "answers" / "laya-mlx" / "gendered-word-choice" / "assertive-bossy.jsonl.gz")
    assert [r["id"] for r in rows] == ["r0", "r1", "r2"]
    assert rows[1]["answers"]["Decision"]["probabilities"] == {"bossy": 0.6, "assertive": 0.4}


def test_a_rerun_skips_texts_already_answered(tmp_path):
    _task(tmp_path)
    out = tmp_path / "answers" / "laya" / "gendered-word-choice"
    out.mkdir(parents=True)
    (out / "assertive-bossy.jsonl.partial.jsonl").write_text(json.dumps(
        {"id": "r0", "model": "m", "usage": None, "latency_ms": 1.0, "answers": {}}) + "\n")
    engine = FakeEngine()
    asyncio.run(run(tmp_path, "assertive-bossy", engine=engine))
    assert len(engine.calls) == 2
    assert not (out / "assertive-bossy.jsonl.partial.jsonl").exists()
