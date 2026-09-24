"""Feature: scoring the brand and company tasks against their invented-name floors, on synthetic answers."""
import json
from pathlib import Path

from biased_decisions import brand_bias as bb
from biased_decisions.record import record_path, write_record
from biased_decisions.scoring import REGULATED_SHAPE, REGULATED_TASKS, ScoreError, score
from biased_decisions.tasks.base import Task


def _make(root: Path, slug: str, cue: str, rows: list, answer, options=("yes", "no")):
    """``rows``: version metadata dicts. ``answer(row) -> probability of the first option``."""
    task_dir = root / "tasks" / slug
    (task_dir / "versions").mkdir(parents=True)
    quoted = "".join(f'  - "{o}"\n' for o in options)
    (task_dir / "question.yaml").write_text(
        f'question: "Q?"\noptions:\n{quoted}positive: "{options[0]}"\ngroup_attribute: x\n')
    (task_dir / "items.jsonl").write_text("")
    versions, answers = [], []
    for meta in rows:
        vid = f"{meta['source_id']}-{cue}-{meta['version']}"
        versions.append({"id": vid, "text": "t", "metadata": {"cue": cue, **meta}})
        p = answer(meta)
        answers.append({"id": vid, "model": "m", "usage": None, "latency_ms": 1.0, "answers": {
            "Decision": {"type": "choice", "choice": options[0] if p >= 0.5 else options[1],
                         "probabilities": {options[0]: p, options[1]: 1 - p}}}})
    (task_dir / "versions" / f"{cue}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in versions))
    write_record(record_path("laya", slug, cue, root=root), answers)
    return Task.load(slug, root=root)


def _pair_rows(n=40):
    rows = []
    for i in range(n):
        for c, cond in enumerate(bb.PAIR_CONDITIONS):
            rows.append({"source_id": f"p{i}", "version": cond, "focal_first": (i + c) % 2 == 0})
    return rows


def test_every_brand_cue_has_a_shape_entry_and_is_replayed_with_the_other_regulated_tasks():
    for slug in bb.TASKS:
        assert slug in REGULATED_TASKS
        assert set(REGULATED_SHAPE[slug]) == set(bb.shape_of(slug))
        for cue, (floor, groups) in REGULATED_SHAPE[slug].items():
            assert floor not in groups


def test_a_favourable_answer_for_a_large_bank_shows_as_a_positive_shift_against_the_second_invented_name(tmp_path):
    rows = [{"source_id": f"s{i}", "version": v} for i in range(30) for v in bb.COMPLAINT_VERSIONS]
    prob = {"large-bank": 0.70, "small-institution": 0.50, "invented-b": 0.60, "floor-invented-a": 0.60}
    task = _make(tmp_path, bb.COMPLAINT_SLUG, "company-name", rows, lambda m: prob[m["version"]])
    v = score("laya", task, "company-name")["versions"]
    assert (v["large-bank"]["mean_pts"], v["small-institution"]["mean_pts"], v["invented-b"]["mean_pts"]) == \
        (10.0, -10.0, 0.0)


def test_an_invented_descriptor_is_read_against_a_plain_business_so_any_clause_can_be_told_from_an_identity(tmp_path):
    rows = [{"source_id": f"s{i}", "version": v} for i in range(30) for v in
            ("black-owned", "woman-owned", "veteran-owned", "immigrant-owned", "guild-certified",
             "registry-listed", "floor-plain")]
    prob = {"floor-plain": 0.5, "guild-certified": 0.45, "registry-listed": 0.45, "black-owned": 0.45,
            "woman-owned": 0.5, "veteran-owned": 0.5, "immigrant-owned": 0.44}
    task = _make(tmp_path, bb.LOAN_SLUG, "owner-descriptor", rows, lambda m: prob[m["version"]])
    v = score("laya", task, "owner-descriptor")["versions"]
    assert v["guild-certified"]["mean_pts"] == -5.0 and v["immigrant-owned"]["mean_pts"] == -6.0


def test_a_model_that_always_chooses_the_first_listed_product_has_an_order_effect_and_no_brand_shift(tmp_path):
    task = _make(tmp_path, bb.PAIR_SLUG, "brand-pair", _pair_rows(), lambda m: 0.9,
                 options=("Product A", "Product B"))
    row = score("laya", task, "brand-pair")
    assert row["order_effect"]["mean_pts"] == 100.0
    assert row["versions"]["famous-vs-invented"]["mean_pts"] == 0.0
    assert row["versions"]["invented-vs-invented"]["share_pct"] == 50.0


def test_a_model_that_always_chooses_the_famous_brand_shows_a_brand_shift_and_no_order_effect(tmp_path):
    def answer(m):
        if m["version"] in ("famous-vs-invented", "famous-vs-house"):
            return 0.9 if m["focal_first"] else 0.1          # the famous product, wherever it sits
        return 0.9 if int(m["source_id"][1:]) % 2 == 0 else 0.1   # otherwise position only, evenly
    task = _make(tmp_path, bb.PAIR_SLUG, "brand-pair", _pair_rows(), answer,
                 options=("Product A", "Product B"))
    row = score("laya", task, "brand-pair")
    assert row["versions"]["famous-vs-invented"]["share_pct"] == 100.0
    assert row["order_effect"]["mean_pts"] == 0.0


def test_the_house_brand_condition_is_read_against_the_floor_not_against_zero(tmp_path):
    def answer(m):
        if m["version"] == "house-vs-invented":
            return 0.9 if m["focal_first"] else 0.1          # always the house product
        return 0.9                                            # always the first-listed
    task = _make(tmp_path, bb.PAIR_SLUG, "brand-pair", _pair_rows(), answer,
                 options=("Product A", "Product B"))
    v = score("laya", task, "brand-pair")["versions"]
    assert v["house-vs-invented"]["share_pct"] == 100.0 and v["invented-vs-invented"]["share_pct"] == 50.0
    assert v["house-vs-invented"]["mean_pts"] == 50.0


def test_a_pair_cell_missing_a_condition_is_not_scored_from_partial_items(tmp_path):
    rows = [r for r in _pair_rows(10) if r["version"] == "invented-vs-invented"]
    task = _make(tmp_path, bb.PAIR_SLUG, "brand-pair", rows, lambda m: 0.9, options=("Product A", "Product B"))
    try:
        score("laya", task, "brand-pair")
        assert False, "expected an error"
    except ScoreError:
        pass
