"""Specs for the compliance block of the data contract (``biased_decisions.compliance``): the
regulated-practice mapping, the citations it rests on, and the evidence every warning, panel,
failure recipe and guidance insight on the site points to. Each spec names the failure it
prevents: a claim with no measured cell behind it, a citation the repository never verified, or
a number that drifted from the record."""
from __future__ import annotations

import json
import re

import pytest

from biased_decisions.compliance import _one_laya, mapping_for, normalise
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


# ---------------------------------------------------------------------------------------------
# Rules for the newer decisions: health care, comment removal, credit, housing, veterans.
# ---------------------------------------------------------------------------------------------

LEGAL_SOURCES = "docs/legal-sources.md"


def _entries(comp):
    """Every mapping entry, top-level or per-decision, with where it came from."""
    for m in comp["mapping"]:
        yield m["dimension"], None, m
        for d in m.get("decisions", []):
            yield m["dimension"], tuple(d["items"]), d


def test_every_quote_a_citation_took_from_the_legal_sources_page_occurs_there_verbatim(comp):
    source = normalise((DEFAULT_ROOT / LEGAL_SOURCES).read_text(encoding="utf-8"))
    checked = 0
    for c in comp["citations"]:
        if c["repo_ref"]["path"] != LEGAL_SOURCES:
            continue
        for q in c["quotes"]:
            assert normalise(q["text"]) in source, f"{c['id']}: {q['where']}"
            checked += 1
    assert checked >= 20


def test_a_rule_for_a_newer_decision_is_cited_only_once_its_primary_text_is_quoted(comp):
    ids = {c["id"] for c in comp["citations"]}
    assert {"aca-1557", "hhs-92-210", "eu-ai-act-5", "dsa-14-4", "dsa-20-21", "bostock",
            "userra", "ecoa", "reg-b", "fha"} <= ids
    for c in comp["citations"]:
        if c["repo_ref"]["path"] == LEGAL_SOURCES:
            hosts = ("law.cornell.edu", "uscode.house.gov", "ecfr.gov", "eur-lex.europa.eu",
                     "supremecourt.gov")
            for q in c["quotes"]:
                assert any(h in q["source_url"] for h in hosts), (c["id"], q["source_url"])


def test_every_per_decision_entry_meets_the_same_bar_as_a_whole_board_entry(doc, comp):
    cited = {c["id"] for c in comp["citations"]}
    recipes = {r["id"] for r in comp["recipes"]}
    insights = {i["id"] for i in comp["insights"]}
    practices = {p["id"] for p in comp["practices"]}
    dims = {d["id"]: {c["item"] for c in d["breakdown"]["cells"]} for d in doc["dimensions"]}
    for dim, items, m in _entries(comp):
        if items is None:
            continue
        for item in items:
            assert item in dims[dim] or (DEFAULT_ROOT / "tasks" / item).is_dir(), (dim, item)
        if not m["regulated"]:
            assert m["reason"], (dim, items)
            continue
        assert m["practice"] in practices
        assert m["citations"] and set(m["citations"]) <= cited, (dim, items)
        for key in ("decision", "attribute", "failure_mode", "who_harmed"):
            assert m[key], (dim, items, key)
        assert set(m["recipes"]) <= recipes and set(m["insights"]) <= insights, (dim, items)


def test_no_decision_is_claimed_twice_on_one_board(comp):
    for m in comp["mapping"]:
        seen = []
        for d in m.get("decisions", []):
            seen += d["items"]
        assert len(seen) == len(set(seen)), m["dimension"]


def test_a_board_entry_with_no_per_decision_field_still_answers_for_every_item(comp):
    m = next(m for m in comp["mapping"] if m["dimension"] == "age")
    assert "decisions" not in m
    assert mapping_for(comp["mapping"], "age", "surgeon-physician") is m


def test_the_mapping_for_a_decision_is_the_per_decision_entry_before_the_board_default(comp):
    opioid = mapping_for(comp["mapping"], "gender", "qpain-treatment")
    hiring = mapping_for(comp["mapping"], "gender", "paralegal-attorney")
    assert opioid["practice"] == "healthcare" and hiring["practice"] == "hiring"
    assert mapping_for(comp["mapping"], "gender", None) is hiring
    with pytest.raises(KeyError):
        mapping_for(comp["mapping"], "no-such-board", "x")


def test_opioid_prescribing_is_mapped_to_the_health_care_nondiscrimination_rules(comp):
    for dim in ("gender", "race", "disability"):
        m = mapping_for(comp["mapping"], dim, "qpain-treatment")
        assert m["regulated"] and m["practice"] == "healthcare", dim
        assert {"aca-1557", "hhs-92-210"} <= set(m["citations"]), dim


def test_comment_removal_is_mapped_to_the_digital_services_act_and_says_us_law_leaves_it_to_platforms(comp):
    for dim in ("sexuality", "race", "disability", "religion"):
        m = mapping_for(comp["mapping"], dim, "civil-comments-moderation")
        assert m["regulated"] and m["practice"] == "moderation", dim
        assert {"dsa-14-4", "dsa-20-21"} <= set(m["citations"]), dim
        assert "own policy" in m["us_note"]


def test_sexual_orientation_in_hiring_is_mapped_to_title_vii_as_read_in_bostock(comp):
    m = mapping_for(comp["mapping"], "sexuality", "paralegal-attorney")
    assert m["regulated"] and m["practice"] == "hiring"
    assert {"bostock", "eu-ai-act-4a"} <= set(m["citations"])
    bostock = next(c for c in comp["citations"] if c["id"] == "bostock")
    assert "590 U.S. 644" in bostock["name"]


def test_veteran_status_in_hiring_is_mapped_to_userra_and_in_opioid_prescribing_stays_unmapped(comp):
    hire = mapping_for(comp["mapping"], "veteran", "paralegal-attorney")
    assert hire["regulated"] and hire["citations"] == ["userra"]
    opioid = mapping_for(comp["mapping"], "veteran", "qpain-treatment")
    assert opioid["regulated"] is False
    assert "verified" in opioid["reason"] and "USERRA" in opioid["reason"]


def test_credit_and_housing_rules_are_listed_for_the_tests_being_added_and_never_warned_on(comp):
    pending = {p["practice"]: p for p in comp["pending"]}
    assert set(pending) == {"credit", "housing"}
    cited = {c["id"] for c in comp["citations"]}
    for p in pending.values():
        assert p["attributes"] and p["status"].startswith("no test yet")
        for a in p["attributes"]:
            assert a["citations"] and set(a["citations"]) <= cited
    marital = next(a for a in pending["credit"]["attributes"] if a["attribute"] == "marital status")
    familial = next(a for a in pending["housing"]["attributes"] if a["attribute"] == "familial status")
    assert {"ecoa", "reg-b"} <= set(marital["citations"]) and "fha" in familial["citations"]
    for m in comp["mapping"]:
        assert not set(m.get("citations", [])) & {"ecoa", "reg-b", "fha"}


def test_a_regime_with_a_verified_citation_is_no_longer_listed_as_unmeasured(comp):
    cited = {c["id"] for c in comp["citations"]}
    assert not cited & {u["id"] for u in comp["unmeasured"]}


def test_new_prose_uses_the_plain_words_and_no_banned_ones(comp):
    banned = re.compile(r"\b(engine|cue|floor|excess|trope|flip|flips|twin|vignette|cell|dimension)\b", re.I)
    digit = re.compile(r"\d")
    for dim, items, m in _entries(comp):
        for key in ("reason", "failure_mode", "who_harmed", "decision", "us_note"):
            text = m.get(key) or ""
            assert not banned.search(text), (dim, key, text)
            if key in ("failure_mode", "who_harmed", "us_note"):
                assert not digit.search(text.replace("4(a)", "")), (dim, key)
    for r in comp["recipes"]:
        if r["id"] in _NEW_RECIPES:
            for key in ("title", "pattern", "what_happens", "inverse"):
                assert not banned.search(r[key]), (r["id"], key)


_NEW_RECIPES = {"one-answer-for-every-patient", "remove-without-appeal"}


def test_the_new_evidence_copies_measured_cells_for_opioid_and_comment_removal(comp):
    ids = {e["id"] for e in comp["evidence"]}
    assert {"gender-laya-opioid", "sexuality-laya-gay-comments", "veteran-laya-iraq-opioid"} <= ids
