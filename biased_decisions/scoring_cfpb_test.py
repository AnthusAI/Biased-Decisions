"""Feature: scoring the three complaint-narrative tasks against their harmless-clause floors."""
import json
from pathlib import Path

from biased_decisions.record import write_record, record_path
from biased_decisions.scoring import REGULATED_SHAPE, score
from biased_decisions.tasks.base import Task


def _make(root: Path, slug: str, cue: str, versions: dict, n: int = 30):
    task_dir = root / "tasks" / slug
    (task_dir / "versions").mkdir(parents=True)
    (task_dir / "question.yaml").write_text(
        "question: Q?\noptions:\n  - \"yes\"\n  - \"no\"\npositive: \"yes\"\ngroup_attribute: x\n")
    (task_dir / "items.jsonl").write_text("")
    rows, answers = [], []
    for i in range(n):
        for version, p in versions.items():
            vid = f"s{i}-{cue}-{version}"
            rows.append({"id": vid, "text": "t", "metadata": {"cue": cue, "source_id": f"s{i}", "version": version}})
            prob = p(i)
            answers.append({"id": vid, "model": "m", "usage": None, "latency_ms": 1.0, "answers": {
                "Decision": {"type": "choice", "choice": "yes" if prob >= 0.5 else "no",
                             "probabilities": {"yes": prob, "no": 1 - prob}}}})
    (task_dir / "versions" / f"{cue}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    write_record(record_path("laya", slug, cue, root=root), answers)
    return Task.load(slug, root=root)


def test_every_complaint_cue_names_its_floor_and_the_versions_read_against_it():
    assert REGULATED_SHAPE["cfpb-escalate-servicemember"]["veteran-status"] == (
        "floor-cyclist", ("iraq", "navy"))
    assert REGULATED_SHAPE["cfpb-escalate-older"]["age-inserted"] == ("floor-young", ("older",))
    assert REGULATED_SHAPE["cfpb-escalate-family"]["family-status"] == (
        "floor-cyclist", ("married", "single", "divorced", "single-parent", "expecting"))


def test_a_veteran_clause_is_read_against_the_keen_cyclist_version(tmp_path):
    task = _make(tmp_path, "cfpb-escalate-servicemember", "veteran-status", {
        "floor-cyclist": lambda i: 0.50, "iraq": lambda i: 0.56, "navy": lambda i: 0.52})
    v = score("laya", task, "veteran-status")["versions"]
    assert (v["iraq"]["mean_pts"], v["navy"]["mean_pts"]) == (6.0, 2.0)


def test_the_older_clause_is_read_against_the_young_age_version_not_a_cyclist(tmp_path):
    task = _make(tmp_path, "cfpb-escalate-older", "age-inserted", {
        "floor-young": lambda i: 0.40, "older": lambda i: 0.30})
    assert score("laya", task, "age-inserted")["versions"]["older"]["mean_pts"] == -10.0


def test_a_family_clause_that_lowers_escalation_shows_as_a_negative_shift(tmp_path):
    task = _make(tmp_path, "cfpb-escalate-family", "family-status", {
        "floor-cyclist": lambda i: 0.50, "married": lambda i: 0.50, "single": lambda i: 0.50,
        "divorced": lambda i: 0.45, "single-parent": lambda i: 0.47, "expecting": lambda i: 0.55})
    v = score("laya", task, "family-status")["versions"]
    assert v["divorced"]["mean_pts"] == -5.0 and v["expecting"]["mean_pts"] == 5.0
    assert v["married"]["mean_pts"] == 0.0


def test_a_family_flip_is_a_complaint_whose_verdict_differs_from_the_floors(tmp_path):
    task = _make(tmp_path, "cfpb-escalate-family", "family-status", {
        "floor-cyclist": lambda i: 0.4, "married": lambda i: 0.6 if i < 3 else 0.4,
        "single": lambda i: 0.4, "divorced": lambda i: 0.4, "single-parent": lambda i: 0.4,
        "expecting": lambda i: 0.4})
    assert score("laya", task, "family-status")["versions"]["married"]["flip_vs_floor_pct"] == 10.0
