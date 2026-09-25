"""Both Laya answer scripts honour the registered first-pass item cap (docs/subsample-preregistration.md)."""
import asyncio
import gzip
import json
from pathlib import Path

from biased_decisions.record import read_record
from biased_decisions.subsample import subsample
from biased_decisions.tasks.items import Item
from scripts.answer_task import run
from scripts.answer_tropes import answer_tropes

BIOS = 30


def build_task(root: Path, slug="t", tropes=False):
    folder = root / "tasks" / slug
    (folder / "versions").mkdir(parents=True)
    if tropes:
        (folder / "question.yaml").write_text(
            "questions:\n  q1:\n    question: Q?\n    trope_consistent_answer: yes\n    trope: t\n")
    else:
        (folder / "question.yaml").write_text(
            "question: Q?\noptions:\n  - yes\n  - no\npositive: yes\ngroup_attribute: x\n")
    (folder / "items.jsonl").write_text("\n".join(json.dumps(
        {"id": f"bios-{i:06d}", "text": f"bio {i}", "metadata": {"split": "test"}}) for i in range(BIOS)) + "\n")
    rows = [{"id": f"bios-{i:06d}-c{k}", "text": f"bio {i} c{k}",
             "metadata": {"source_id": f"bios-{i:06d}"}} for i in range(BIOS) for k in range(2)]
    (folder / "versions" / "c.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return [Item(id=r["id"], text=r["text"], metadata=r["metadata"]) for r in rows]


def planned(rows, slug, cap):
    return [i.id for i in subsample(rows, slug, cap)]


class TaskEngine:
    def __init__(self):
        self.calls = 0

    async def answer(self, text, questions):
        self.calls += 1
        return {"Decision": {"choice": "yes", "probabilities": {"yes": 0.7, "no": 0.3}}}


class TropeModel:
    def __init__(self):
        self.calls = 0

    def system_one(self, state, questions):
        self.calls += 1
        return {"usage": None, "answers": {k: {"type": "noul", "yes": 0.5} for k in questions}}


def write_partial(path: Path, ids):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps({"id": i, "model": "laya", "usage": None, "latency_ms": 1.0,
                                          "answers": {"Decision": {"choice": "yes",
                                                                   "probabilities": {"yes": 0.7, "no": 0.3}}}})
                              for i in ids) + "\n")


def test_answer_task_with_a_cap_answers_only_the_sample_in_plan_order(tmp_path):
    rows = build_task(tmp_path)
    engine = TaskEngine()
    asyncio.run(run(tmp_path, "t", "c", engine=engine, skip_as_written=True, item_cap=5))
    want = planned(rows, "t", 5)
    got = [r["id"] for r in read_record(tmp_path / "answers" / "laya" / "t" / "c.jsonl.gz")]
    assert got == want and len(want) == 10 and engine.calls == 10


def test_answer_task_never_writes_leftover_rows_outside_the_sample_into_the_record(tmp_path):
    rows = build_task(tmp_path)
    want = planned(rows, "t", 5)
    outside = [r.id for r in rows if r.id not in set(want)][:7]
    partial = tmp_path / "answers" / "laya" / "t" / "c.jsonl.partial.jsonl"
    write_partial(partial, want[:3] + outside)
    engine = TaskEngine()
    asyncio.run(run(tmp_path, "t", "c", engine=engine, skip_as_written=True, item_cap=5))
    got = [r["id"] for r in read_record(tmp_path / "answers" / "laya" / "t" / "c.jsonl.gz")]
    assert got == want and engine.calls == 7          # the 3 answered sample rows were reused


def test_answer_task_without_a_cap_still_answers_everything(tmp_path):
    rows = build_task(tmp_path)
    engine = TaskEngine()
    asyncio.run(run(tmp_path, "t", "c", engine=engine, skip_as_written=True))
    assert len(read_record(tmp_path / "answers" / "laya" / "t" / "c.jsonl.gz")) == len(rows) == engine.calls


def test_answer_tropes_with_a_cap_answers_only_the_sample_in_plan_order(tmp_path):
    rows = build_task(tmp_path, "stereotypes-x", tropes=True)
    model = TropeModel()
    answer_tropes(tmp_path, "stereotypes-x", "c", model=model, item_cap=5)
    want = planned(rows, "stereotypes-x", 5)
    got = [r["id"] for r in read_record(tmp_path / "answers" / "laya" / "stereotypes-x" / "c.jsonl.gz")]
    assert got == want and model.calls == 10


def test_answer_tropes_never_writes_leftover_rows_outside_the_sample_and_reuses_the_ones_inside(tmp_path):
    rows = build_task(tmp_path, "stereotypes-x", tropes=True)
    want = planned(rows, "stereotypes-x", 5)
    outside = [r.id for r in rows if r.id not in set(want)][:9]
    partial = tmp_path / "answers" / "laya" / "stereotypes-x" / "c.jsonl.partial.jsonl"
    write_partial(partial, want[:4] + outside)
    model = TropeModel()
    answer_tropes(tmp_path, "stereotypes-x", "c", model=model, item_cap=5)
    got = [r["id"] for r in read_record(tmp_path / "answers" / "laya" / "stereotypes-x" / "c.jsonl.gz")]
    assert got == want and model.calls == 6
