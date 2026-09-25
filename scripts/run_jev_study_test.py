import json

import pytest

from biased_decisions.record import read_record
from scripts.run_jev_study import run_manifest
from scripts.run_kev_study_test import make_root


class MetaEngine:
    model = "jev-test"

    def __init__(self):
        self.calls = 0
        self.in_flight = 0
        self.peak = 0

    async def answer_with_meta(self, text, questions):
        import asyncio
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        await asyncio.sleep(0.005)
        self.in_flight -= 1
        self.calls += 1
        name, question = next(iter(questions.items()))
        options = list(question["criteria"])
        return ({name: {"type": "choice", "choice": options[0],
                        "probabilities": {options[0]: 0.6, options[1]: 0.4}}},
                {"usage": {"input_tokens": 10, "output_tokens": 2}, "model": "jev-test"})


def capped_manifest(tmp_path, cap):
    root, manifest_path, manifest = make_root(tmp_path, count=20)
    manifest["cells"][0].update({"item_cap": cap, "requests": cap})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return root, manifest_path


def test_a_capped_manifest_is_collected_concurrently_into_the_jev_record(tmp_path):
    root, manifest_path = capped_manifest(tmp_path, 8)
    engine = MetaEngine()
    result = run_manifest(root, manifest_path, engine_factory=lambda: engine, model="jev-test", concurrency=4)
    assert result == {"cells": 1, "requests": 8, "complete": True}
    rows = read_record(root / "answers" / "jev" / "surgeon-physician" / "as-written.jsonl.gz")
    assert len(rows) == 8 and engine.calls == 8 and engine.peak > 1
    assert {r["model"] for r in rows} == {"jev-test"} and rows[0]["usage"]["input_tokens"] == 10


def test_a_rerun_of_a_finished_manifest_sends_no_requests(tmp_path):
    root, manifest_path = capped_manifest(tmp_path, 5)
    run_manifest(root, manifest_path, engine_factory=MetaEngine, model="jev-test", concurrency=3)
    again = MetaEngine()
    run_manifest(root, manifest_path, engine_factory=lambda: again, model="jev-test", concurrency=3)
    assert again.calls == 0


def test_a_manifest_whose_pinned_inputs_changed_is_refused_before_any_request(tmp_path):
    root, manifest_path = capped_manifest(tmp_path, 5)
    (root / "tasks" / "surgeon-physician" / "items.jsonl").write_text("{}\n")
    engine = MetaEngine()
    with pytest.raises(ValueError):
        run_manifest(root, manifest_path, engine_factory=lambda: engine, model="jev-test", concurrency=3)
    assert engine.calls == 0


def test_each_cell_gets_its_own_engine_because_a_hosted_client_belongs_to_one_event_loop(tmp_path):
    root, manifest_path, manifest = make_root(tmp_path, count=20)
    second = dict(manifest["cells"][0], cue="as-written")
    second["cue"] = "as-written"
    made = []
    def factory():
        made.append(MetaEngine())
        return made[-1]
    manifest["cells"][0].update({"item_cap": 4, "requests": 4})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    run_manifest(root, manifest_path, engine_factory=factory, model="jev-test", concurrency=2)
    assert len(made) == 1                      # one cell, one engine
