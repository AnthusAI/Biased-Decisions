import json
from pathlib import Path

import pytest

from biased_decisions.collector import CollectionError, collect
from biased_decisions.record import read_record
from biased_decisions.tasks.base import Task


class FakeEngine:
    name = "fake"
    model_name = "fake-v1"
    model = "kev-latest"
    provenance_data = {"checkpoint": "abc", "backend": "cpu", "model": "kev-latest"}

    def __init__(self, fail_after=None):
        self.calls = []
        self.fail_after = fail_after

    async def answer(self, text, questions):
        self.calls.append((text, questions))
        if self.fail_after is not None and len(self.calls) > self.fail_after:
            raise RuntimeError("interrupted")
        result = {}
        for name, question in questions.items():
            if question["type"] == "noul":
                result[name] = {"type": "noul", "noul": 0.7}
                continue
            options = list(question["criteria"])
            option = options[0]
            p = 0.7
            result[name] = {"type": "choice", "choice": option,
                             "probabilities": {o: p if o == option else (1-p)/(len(options)-1)
                                               for o in options}}
        return result


def make_task(root: Path):
    folder = root / "tasks" / "new-task"
    folder.mkdir(parents=True)
    (folder / "question.yaml").write_text(
        "question: Which action?\noptions: [approve, reject]\npositive: approve\ngroup_attribute: group\n")
    (folder / "items.jsonl").write_text("\n".join([
        json.dumps({"id": "i1", "text": "one", "metadata": {"split": "test"}}),
        json.dumps({"id": "i2", "text": "two", "metadata": {"split": "test"}}),
        json.dumps({"id": "i1-swapped", "text": "one twin", "metadata": {
            "split": "counterfactual", "counterfactual_of": "i1"}}),
    ]) + "\n")
    (folder / "versions").mkdir()
    (folder / "versions" / "cue.jsonl").write_text(json.dumps(
        {"id": "v1", "text": "version", "metadata": {}}) + "\n")
    (folder / "versions" / "ask-twice.txt").write_text("i1\n")


def test_dry_run_new_generic_task_keeps_decision_name_and_makes_no_calls(tmp_path):
    make_task(tmp_path)
    engine = FakeEngine()
    plan = collect(tmp_path, "kev", "new-task", "cue", engine=engine, dry_run=True)
    assert plan["pending"] == 1
    assert not engine.calls
    assert collect(tmp_path, "kev", "new-task", "cue", engine=engine)["complete"]
    assert engine.calls[0][1].keys() == {"Decision"}


def test_interrupted_collection_resumes_and_completed_rerun_makes_zero_calls(tmp_path):
    make_task(tmp_path)
    engine = FakeEngine(fail_after=1)
    with pytest.raises(RuntimeError, match="interrupted"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=engine)
    plan = collect(tmp_path, "kev", "new-task", "as-written", dry_run=True)
    assert plan["pending"] == 1
    resumed = FakeEngine()
    assert collect(tmp_path, "kev", "new-task", "as-written", engine=resumed)["complete"]
    assert len(engine.calls) == 2
    assert len(resumed.calls) == 1
    again = FakeEngine()
    collect(tmp_path, "kev", "new-task", "as-written", engine=again)
    assert again.calls == []
    rows = read_record(tmp_path / "answers" / "kev" / "new-task" / "as-written.jsonl.gz")
    assert [r["id"] for r in rows] == ["i1", "i2"]


def test_partial_refuses_changed_input_model_or_provenance(tmp_path):
    make_task(tmp_path)
    first = FakeEngine(fail_after=0)
    with pytest.raises(RuntimeError):
        collect(tmp_path, "kev", "new-task", "as-written", engine=first)
    changed_model = FakeEngine(fail_after=0)
    changed_model.model_name = "fake-v2"
    with pytest.raises(CollectionError, match="changed"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=changed_model)
    changed_prov = FakeEngine(fail_after=0)
    changed_prov.provenance_data = {"checkpoint": "def", "backend": "cpu"}
    with pytest.raises(CollectionError, match="changed"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=changed_prov)
    (tmp_path / "tasks" / "new-task" / "items.jsonl").write_text(json.dumps(
        {"id": "i1", "text": "changed", "metadata": {"split": "test"}}) + "\n")
    with pytest.raises(CollectionError, match="inputs"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=first)


def test_reversed_options_keep_labels_and_order(tmp_path):
    make_task(tmp_path)
    engine = FakeEngine()
    collect(tmp_path, "kev", "new-task", "option-order-reversed", engine=engine)
    question = engine.calls[0][1]["Decision"]
    assert list(question["criteria"]) == ["reject", "approve"]
    assert list(question["criteria"].values()) == ["reject", "approve"]


def test_gender_collection_includes_twins_and_reversed_twin_cell_is_separate(tmp_path):
    make_task(tmp_path)
    original = FakeEngine()
    collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=original)
    assert len(original.calls) == 3
    twins = FakeEngine()
    collect(tmp_path, "kev", "new-task", "option-order-reversed-twins", engine=twins)
    assert [call[0] for call in twins.calls] == ["one twin"]


def test_ask_twice_uses_committed_selection_and_pilot_limit_resumes_full_cell(tmp_path):
    make_task(tmp_path)
    twice = FakeEngine()
    collect(tmp_path, "kev", "new-task", "ask-twice", engine=twice)
    assert [call[0] for call in twice.calls] == ["one"]
    baseline = FakeEngine()
    result = collect(tmp_path, "kev", "new-task", "as-written", engine=baseline,
                     max_new_items=1, progress=False)
    assert result["complete"] is False and result["pending"] == 1
    resume = FakeEngine()
    complete = collect(tmp_path, "kev", "new-task", "as-written", engine=resume,
                       progress=False)
    assert complete["complete"] and len(resume.calls) == 1


def test_resume_fingerprint_includes_ordered_options(tmp_path):
    make_task(tmp_path)
    engine = FakeEngine(fail_after=0)
    with pytest.raises(RuntimeError):
        collect(tmp_path, "kev", "new-task", "as-written", engine=engine)
    qfile = tmp_path / "tasks" / "new-task" / "question.yaml"
    qfile.write_text("question: Which action?\noptions: [reject, approve]\npositive: approve\ngroup_attribute: group\n")
    with pytest.raises(CollectionError, match="inputs"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=FakeEngine())


def test_resume_refuses_positive_label_edit(tmp_path):
    make_task(tmp_path)
    with pytest.raises(RuntimeError):
        collect(tmp_path, "kev", "new-task", "as-written", engine=FakeEngine(fail_after=0))
    (tmp_path / "tasks" / "new-task" / "question.yaml").write_text(
        "question: Which action?\noptions: [approve, reject]\npositive: reject\n"
        "group_attribute: group\n")
    with pytest.raises(CollectionError, match="inputs"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=FakeEngine())


@pytest.mark.parametrize("field,value", [
    ("metadata", {"split": "test", "reference_label": "reject", "extra": "changed"}),
    ("external_id", "external-changed"),
    ("identifiers", [{"name": "source", "value": "changed", "url": "https://example.test"}]),
])
def test_resume_fingerprint_includes_full_item_definition(tmp_path, field, value):
    make_task(tmp_path)
    with pytest.raises(RuntimeError):
        collect(tmp_path, "kev", "new-task", "as-written", engine=FakeEngine(fail_after=0))
    items_path = tmp_path / "tasks" / "new-task" / "items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines()]
    rows[0][field] = value
    items_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(CollectionError, match="inputs"):
        collect(tmp_path, "kev", "new-task", "as-written", engine=FakeEngine())


def test_version_cue_resume_refuses_changed_original_item_metadata(tmp_path):
    make_task(tmp_path)
    interrupted = FakeEngine(fail_after=0)
    with pytest.raises(RuntimeError, match="interrupted"):
        collect(tmp_path, "kev", "new-task", "cue", engine=interrupted)
    items_path = tmp_path / "tasks" / "new-task" / "items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["metadata"]["reference_label"] = "changed"
    items_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    resume = FakeEngine()
    with pytest.raises(CollectionError, match="inputs"):
        collect(tmp_path, "kev", "new-task", "cue", engine=resume)
    assert resume.calls == []


def test_generated_record_is_consumable_by_existing_offline_regulated_scorer(tmp_path):
    from biased_decisions.scoring import score
    slug = "qpain-treatment"
    folder = tmp_path / "tasks" / slug
    (folder / "versions").mkdir(parents=True)
    (folder / "question.yaml").write_text(
        'question: Prescribe?\noptions: ["yes", "no"]\npositive: "yes"\ngroup_attribute: race\n')
    (folder / "items.jsonl").write_text("")
    rows = []
    for version in ("white", "black", "asian", "hispanic"):
        item_id = f"case-{version}"
        rows.append({"id": item_id, "text": version, "metadata": {
            "source_id": "case", "version": version}})
    (folder / "versions" / "race.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    collect(tmp_path, "kev", slug, "race", engine=FakeEngine(), progress=False)
    scored = score("kev", Task.load(slug, root=tmp_path), "race")
    assert scored["engine"] == "kev" and scored["task"] == slug and scored["n"] == 1


def test_explicit_multi_noul_schema_preserves_question_ids_and_order(tmp_path):
    folder = tmp_path / "tasks" / "multi-task"
    (folder / "versions").mkdir(parents=True)
    (folder / "question.yaml").write_text(
        'questions:\n  greed_q1:\n    question: "Does the text describe greed?"\n'
        '    trope_consistent_answer: yes\n'
        '  competence_q2:\n    question: "Does the text describe competence?"\n'
        '    trope_consistent_answer: no\n')
    (folder / "items.jsonl").write_text(json.dumps({"id": "x", "text": "one"}) + "\n")
    engine = FakeEngine()
    collect(tmp_path, "kev", "multi-task", "as-written", engine=engine, progress=False)
    assert list(engine.calls[0][1]) == ["greed_q1", "competence_q2"]
    row = read_record(tmp_path / "answers" / "kev" / "multi-task" / "as-written.jsonl.gz")[0]
    assert list(row["answers"]) == ["greed_q1", "competence_q2"]


def test_an_item_cap_plans_only_the_first_families_and_the_dry_run_counts_them(tmp_path):
    make_task(tmp_path)
    full = collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), dry_run=True)
    capped = collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), dry_run=True,
                     item_cap=1)
    assert full["total"] == 3
    assert capped["total"] in (1, 2)          # one family: i2 alone, or i1 with its twin
    assert collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), dry_run=True,
                   item_cap=2)["total"] == 3


def test_a_capped_collection_answers_only_the_sample_and_a_rerun_makes_no_calls(tmp_path):
    make_task(tmp_path)
    engine = FakeEngine()
    result = collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=engine, item_cap=1,
                     provenance=FakeEngine.provenance_data | {"server_revision": "s", "base_revision": "b",
                                                            "dtype": "f", "calibration": "1"})
    assert result["complete"] and len(engine.calls) == result["total"]
    rows = read_record(result["path"])
    assert len(rows) == result["total"] < 3
    again = FakeEngine()
    collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=again, item_cap=1,
            provenance=FakeEngine.provenance_data | {"server_revision": "s", "base_revision": "b",
                                                   "dtype": "f", "calibration": "1"})
    assert again.calls == []


def test_a_capped_record_is_not_silently_reused_for_the_full_cell(tmp_path):
    make_task(tmp_path)
    provenance = FakeEngine.provenance_data | {"server_revision": "s", "base_revision": "b",
                                               "dtype": "f", "calibration": "1"}
    collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), item_cap=1,
            provenance=provenance)
    with pytest.raises(CollectionError):
        collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), provenance=provenance)


def test_an_item_cap_below_one_is_refused(tmp_path):
    make_task(tmp_path)
    with pytest.raises(ValueError):
        collect(tmp_path, "kev", "new-task", "gender-pronouns", engine=FakeEngine(), dry_run=True, item_cap=0)


class MetaEngine(FakeEngine):
    """An engine that reports usage and model per request, so it can be called concurrently."""
    model = "jev-test"

    def __init__(self, fail_on=None, delay=0.01):
        super().__init__()
        self.in_flight = 0
        self.peak = 0
        self.fail_on = fail_on
        self.delay = delay

    async def answer(self, text, questions):
        import asyncio
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            return await FakeEngine.answer(self, text, questions)
        finally:
            self.in_flight -= 1

    async def answer_with_meta(self, text, questions):
        import asyncio
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            if self.fail_on == text:
                raise RuntimeError("request failed")
            answers = await FakeEngine.answer(self, text, questions)     # records one call
            return answers, {"usage": {"input_tokens": len(text), "output_tokens": 3}, "model": "jev-test"}
        finally:
            self.in_flight -= 1


def concurrent_root(tmp_path, count=12):
    folder = tmp_path / "tasks" / "new-task"
    folder.mkdir(parents=True)
    (folder / "question.yaml").write_text(
        "question: Which action?\noptions: [approve, reject]\npositive: approve\ngroup_attribute: group\n")
    (folder / "items.jsonl").write_text("\n".join(
        json.dumps({"id": f"i{n}", "text": f"text {n}", "metadata": {"split": "test"}})
        for n in range(count)) + "\n")
    (folder / "versions").mkdir()


def test_a_concurrent_collection_keeps_item_order_and_records_usage_and_model_per_request(tmp_path):
    concurrent_root(tmp_path)
    engine = MetaEngine()
    result = collect(tmp_path, "jev", "new-task", "as-written", engine=engine, model="jev-test",
                     concurrency=4, provenance={"model": "jev-test"})
    assert result["complete"] and engine.peak > 1
    rows = read_record(result["path"])
    assert [r["id"] for r in rows] == [f"i{n}" for n in range(12)]
    assert rows[0]["usage"] == {"input_tokens": len("text 0"), "output_tokens": 3}
    assert {r["model"] for r in rows} == {"jev-test"} and all(r["latency_ms"] >= 0 for r in rows)


def test_a_failed_request_keeps_the_rows_that_succeeded_and_the_rerun_asks_only_for_the_rest(tmp_path):
    concurrent_root(tmp_path)
    bad = MetaEngine(fail_on="text 7")
    with pytest.raises(CollectionError, match="failed"):
        collect(tmp_path, "jev", "new-task", "as-written", engine=bad, model="jev-test", concurrency=4,
                provenance={"model": "jev-test"})
    partial = tmp_path / "answers" / "jev" / "new-task" / "as-written.jsonl.gz.partial.jsonl"
    saved = {json.loads(line)["id"] for line in partial.read_text().splitlines()}
    assert "i0" in saved and "i7" not in saved
    good = MetaEngine()
    result = collect(tmp_path, "jev", "new-task", "as-written", engine=good, model="jev-test", concurrency=4,
                     provenance={"model": "jev-test"})
    assert result["complete"] and len(good.calls) == 12 - len(saved)


def test_the_default_is_still_one_request_at_a_time(tmp_path):
    concurrent_root(tmp_path, count=6)
    engine = MetaEngine()
    collect(tmp_path, "jev", "new-task", "as-written", engine=engine, model="jev-test",
            provenance={"model": "jev-test"})
    assert engine.peak == 1
