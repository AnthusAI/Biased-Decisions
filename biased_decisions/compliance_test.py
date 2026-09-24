"""Specs for the compliance block of the data contract (``biased_decisions.compliance``): the
regulated-practice mapping, the citations it rests on, and the evidence every warning, panel,
failure recipe and guidance insight on the site points to. Each spec names the failure it
prevents: a claim with no measured cell behind it, a citation the repository never verified, or
a number that drifted from the record."""
from __future__ import annotations

import json
import re

import pytest

from biased_decisions.compliance import _one_laya, normalise
from biased_decisions.leaderboard import generate_json
from biased_decisions.tasks.base import DEFAULT_ROOT


@pytest.fixture(scope="module")
def doc():
    return generate_json(DEFAULT_ROOT, date="2026-09-23")


@pytest.fixture(scope="module")
def comp(doc):
    return doc["compliance"]


def _facet(doc, ev):
    dim = next(d for d in doc["dimensions"] if d["id"] == ev["dimension"])
    cell = next(c for c in dim["breakdown"]["cells"]
                if c["group"] == ev["group"] and c["item"] == ev["item"])
    return dim, cell, cell["engines"][ev["engine"]]


def test_the_contract_carries_a_compliance_block_under_a_new_schema(doc):
    assert doc["schema"] == "biased-decisions/leaderboard@4"
    for key in ("notice", "citations", "practices", "mapping", "evidence", "shortlist",
                "recipes", "insights", "checklist", "articles", "unmeasured", "inversion"):
        assert key in doc["compliance"], key


def test_the_notice_says_plainly_that_this_is_not_legal_advice(comp):
    assert "not legal advice" in comp["notice"].lower()


def test_every_citation_is_one_the_repository_already_names_verbatim(comp):
    for c in comp["citations"]:
        ref = c["repo_ref"]
        source = normalise((DEFAULT_ROOT / ref["path"]).read_text(encoding="utf-8"))
        assert normalise(ref["text"]) in source, f"{c['id']}: {ref['text']!r} not in {ref['path']}"
        assert c["primary_url"].startswith("https://"), c["id"]
        assert c["quotes"], f"{c['id']}: no quoted primary text"
        for q in c["quotes"]:
            assert q["text"] and q["where"] and q["source_url"].startswith("https://")


def test_a_regime_the_repository_only_names_is_listed_as_unmeasured_never_warned_on(comp):
    cited = {c["id"] for c in comp["citations"]}
    for u in comp["unmeasured"]:
        source = normalise((DEFAULT_ROOT / u["repo_ref"]["path"]).read_text(encoding="utf-8"))
        assert normalise(u["repo_ref"]["text"]) in source, u["id"]
        assert u["id"] not in cited
    for m in comp["mapping"]:
        assert not set(m.get("citations", [])) & {u["id"] for u in comp["unmeasured"]}


def test_every_dimension_is_mapped_once_and_every_regulated_one_cites_a_verified_rule(doc, comp):
    ids = [m["dimension"] for m in comp["mapping"]]
    assert sorted(ids) == sorted(d["id"] for d in doc["dimensions"])
    cited = {c["id"] for c in comp["citations"]}
    practices = {p["id"] for p in comp["practices"]}
    recipes = {r["id"] for r in comp["recipes"]}
    insights = {i["id"] for i in comp["insights"]}
    for m in comp["mapping"]:
        if not m["regulated"]:
            assert m["reason"], m["dimension"]
            continue
        assert m["practice"] in practices
        assert m["citations"] and set(m["citations"]) <= cited, m["dimension"]
        for key in ("decision", "attribute", "failure_mode", "who_harmed"):
            assert m[key], (m["dimension"], key)
        assert m["recipes"] and set(m["recipes"]) <= recipes, m["dimension"]
        assert m["insights"] and set(m["insights"]) <= insights, m["dimension"]


def test_option_order_is_not_flagged_as_a_regulated_decision(comp):
    m = next(m for m in comp["mapping"] if m["dimension"] == "option-order")
    assert m["regulated"] is False


def test_every_cell_evidence_entry_copies_a_measured_facet_number_for_number(doc, comp):
    for ev in comp["evidence"]:
        if ev["kind"] != "cell":
            continue
        dim, cell, f = _facet(doc, ev)
        assert f["status"] == "measured", ev["id"]
        assert (ev["value"], ev["lo"], ev["hi"]) == (f["raw"]["value"], f["raw"]["lo"],
                                                     f["raw"]["hi"]), ev["id"]
        assert ev["n"] == f["n"] and ev["floor"] == f["floor"]["value"], ev["id"]
        assert ev["excess"] == f["excess"] and ev["detected"] == f["detected"], ev["id"]
        assert ev["has_example"] == bool(cell["example"]), ev["id"]


def test_the_shortlist_block_is_the_replayed_record_row_for_row(comp):
    rows = []
    for block in comp["shortlist"]["pairs"]:
        path = DEFAULT_ROOT / block["study"]
        want = _one_laya([json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line])
        assert block["rows"] == want, block["task"]
        rows.extend(block["rows"])
    assert rows
    assert comp["shortlist"]["line"] == 0.8


def test_every_shortlist_and_prereg_evidence_entry_resolves(comp):
    rows = {(b["task"], r["engine"], r["variant"], r["cut"])
            for b in comp["shortlist"]["pairs"] for r in b["rows"]}
    prereg = (DEFAULT_ROOT / "studies/PREREGISTERED.md").read_text(encoding="utf-8")
    for ev in comp["evidence"]:
        if ev["kind"] == "shortlist":
            assert (ev["task"], ev["engine"], ev["variant"], ev["cut"]) in rows, ev["id"]
        elif ev["kind"] == "prereg":
            for key in ("measurement", "prediction", "observed", "verdict"):
                assert ev[key], (ev["id"], key)
            assert ev["measurement"] in prereg.replace("**", "")
        elif ev["kind"] == "floor":
            assert ev["value"] is not None and ev["n"]
        else:
            assert ev["kind"] == "cell", ev["id"]


def test_every_recipe_and_insight_stands_on_evidence_and_links_both_ways(comp):
    evidence = {e["id"] for e in comp["evidence"]}
    insights = {i["id"] for i in comp["insights"]}
    practices = {p["id"] for p in comp["practices"]}
    slug = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    seen = set()
    for r in comp["recipes"]:
        assert slug.match(r["id"]) and r["id"] not in seen, r["id"]
        seen.add(r["id"])
        assert r["evidence"] and set(r["evidence"]) <= evidence, r["id"]
        assert r["practices"] and set(r["practices"]) <= practices | {"any"}, r["id"]
        assert r["pattern"] and r["what_happens"] and r["inverse"], r["id"]
        assert r["insight"] in insights, r["id"]
    for i in comp["insights"]:
        assert slug.match(i["id"]) and i["id"] not in seen, i["id"]
        seen.add(i["id"])
        assert (set(i["evidence"]) <= evidence) and (i["evidence"] or i["links"]), i["id"]
    for c in comp["checklist"]:
        assert c["insight"] in insights, c["text"]


def test_prose_carries_no_numbers_so_every_number_on_a_compliance_page_comes_from_evidence(comp):
    digit = re.compile(r"\d")
    for r in comp["recipes"]:
        for key in ("title", "pattern", "what_happens", "inverse"):
            assert not digit.search(r[key]), (r["id"], key, r[key])
    for i in comp["insights"]:
        assert not digit.search(i["title"]) and not digit.search(i["text"]), i["id"]
    for m in comp["mapping"]:
        for key in ("failure_mode", "who_harmed"):
            if m.get(key):
                assert not digit.search(m[key].replace("4(a)", "").replace("4(b)", "")), (m["dimension"], key)


def test_risks_are_phrased_as_exposure_never_as_findings_of_illegality(comp):
    banned = re.compile(r"\b(is|are|was|were) (illegal|unlawful)\b|\bviolat(es|ed|ion)\b|\bbreaks the law\b", re.I)
    prose = [comp["notice"], comp["inversion"]["lede"]]
    prose += [r[k] for r in comp["recipes"] for k in ("title", "pattern", "what_happens", "inverse")]
    prose += [i["text"] for i in comp["insights"]]
    prose += [m.get(k) or "" for m in comp["mapping"] for k in ("failure_mode", "who_harmed", "reason")]
    for text in prose:
        assert not banned.search(text), text


def test_the_inversion_attribution_is_sourced(comp):
    inv = comp["inversion"]
    assert inv["quote"] == "Invert, always invert."
    assert "Jacobi" in inv["attribution"] and "Munger" in inv["attribution"]
    assert inv["source_url"].startswith("https://")


def test_the_companion_articles_are_linked(comp):
    urls = {a["url"] for a in comp["articles"]}
    assert {"https://anth.us/blog/encoding-prejudice/", "https://anth.us/blog/one-word-test/",
            "https://anth.us/blog/can-you-fix-it/"} <= urls
