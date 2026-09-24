"""Feature: the brand and company tasks (docs/brand-bias-preregistration.md), built without network."""
import csv
import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from biased_decisions import brand_bias as bb
from biased_decisions import housing_lending as hl


class Words:
    """A stand-in tokenizer: one token per whitespace-separated word."""
    def count(self, text):
        return len(text.split())


def test_the_names_an_item_gets_do_not_depend_on_the_other_items():
    assert bb.bank_names("x-1") == bb.bank_names("x-1")
    assert bb.bank_names("x-1") != bb.bank_names("x-2") or bb.bank_names("x-1") != bb.bank_names("x-3")


def test_the_two_invented_names_of_an_item_are_different_and_never_a_listed_real_name():
    for i in range(200):
        names = bb.bank_names(f"item-{i}")
        assert names["floor-invented-a"] != names["invented-b"]
        assert names["large-bank"] in bb.LARGE_BANKS
        assert names["small-institution"] in bb.SMALL_INSTITUTIONS
        assert not {names["floor-invented-a"], names["invented-b"]} & set(bb.LARGE_BANKS)


def test_a_loan_brand_text_is_the_loan_text_with_one_clause_and_nothing_else_changed():
    items = bb.loan_items(20)
    assert [i["text"] for i in items] == [i["text"] for i in hl.generate(hl.LOAN, 20)]
    rows = bb.loan_versions("brand-name", items[0])
    names = bb.bank_names(items[0]["id"])
    assert [r["metadata"]["version"] for r in rows] == list(bb.LOAN_BRAND_VERSIONS)
    for r in rows:
        clause = f"As a customer of {names[r['metadata']['version']]}, "
        assert r["text"] == hl.prepend(clause, items[0]["text"])


def test_the_owner_descriptor_cue_has_a_plain_floor_and_an_invented_pair_of_descriptors():
    clauses = dict(bb.OWNER_DESCRIPTORS)
    assert clauses["floor-plain"] == "As a business, "
    assert clauses["guild-certified"] == "As a guild-certified business, "
    assert clauses["registry-listed"] == "As a registry-listed business, "
    assert clauses["immigrant-owned"] == "As an immigrant-owned business, "
    assert bb.shape_of(bb.LOAN_SLUG)["owner-descriptor"][0] == "floor-plain"
    assert {"guild-certified", "registry-listed"} <= set(bb.shape_of(bb.LOAN_SLUG)["owner-descriptor"][1])


def test_a_fund_family_name_keeps_its_ending_and_the_invented_one_has_the_same_shape():
    assert bb.tail_of("FIDELITY CONCORD STREET TRUST") == "Trust"
    assert bb.tail_of("BLACKROCK FUNDS II") == "Funds II"
    assert bb.tail_of("AMERICAN FUNDS GLOBAL BALANCED FUND") == "Fund"
    assert bb.title_name("AIM COUNSELOR SERIES TRUST (INVESCO COUNSELOR SERIES TRUST)") == \
        "Aim Counselor Series Trust"
    assert bb.title_name("FIDELITY INCOME FUND /MA/") == "Fidelity Income Fund"
    names = bb.fund_names("fund-1", "BLACKROCK FUNDS II")
    assert names["invented-b"].endswith("Funds II") and names["floor-invented-a"].endswith("Funds II")
    assert names["invented-b"] != names["floor-invented-a"]


def _sec_zip(path, sub, num):
    def tsv(rows, fields):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("sub.tsv", tsv(sub, ["adsh", "name"]))
        z.writestr("num.tsv", tsv(num, ["adsh", "tag", "otherdims", "value"]))
    return path


def _facts(adsh, cls, er, mf, net=None, load=None):
    rows = [{"adsh": adsh, "tag": "ExpensesOverAssets", "otherdims": f"Class={cls};", "value": er},
            {"adsh": adsh, "tag": "ManagementFeesOverAssets", "otherdims": f"Class={cls};", "value": mf}]
    if net:
        rows.append({"adsh": adsh, "tag": "NetExpensesOverAssets", "otherdims": f"Class={cls};", "value": net})
    if load:
        rows.append({"adsh": adsh, "tag": "MaximumSalesChargeImposedOnPurchasesOverOfferingPrice",
                     "otherdims": f"Class={cls};", "value": load})
    return rows


def test_only_the_named_fund_families_are_read_and_a_fund_with_no_fee_figures_is_dropped(tmp_path):
    sub = [{"adsh": "a-1", "name": "VANGUARD INDEX FUNDS"}, {"adsh": "a-2", "name": "SMALLTOWN GROWTH TRUST"}]
    num = (_facts("a-1", "C1", "0.0051", "0.0040", net="0.0045", load="0.0575") + _facts("a-2", "C2", "0.01", "0.008")
           + [{"adsh": "a-1", "tag": "ExpensesOverAssets", "otherdims": "Class=C9;", "value": "0.0100"}])
    funds = bb.read_funds(_sec_zip(tmp_path / "s.zip", sub, num))
    assert [f["family"] for f in funds] == ["VANGUARD INDEX FUNDS"]
    assert funds[0]["facts"] == ("Total annual fund operating expenses are 0.51% of assets, of which the "
                                 "management fee is 0.40%. After fee waivers the net expense ratio is 0.45%. "
                                 "The maximum front-end sales charge is 5.75% of the offering price.")


def test_fund_versions_share_one_set_of_figures_and_differ_only_in_the_name():
    fund = {"id": "fund-a-1-C1", "family": "VANGUARD INDEX FUNDS", "facts": "Total annual fund operating expenses are 0.51% of assets."}
    rows = bb.fund_versions(fund)
    names = bb.fund_names(fund["id"], fund["family"])
    assert [r["metadata"]["version"] for r in rows] == list(bb.FUND_VERSIONS)
    for r in rows:
        assert r["text"] == f"{names.get(r['metadata']['version'], 'Vanguard Index Funds')}. {fund['facts']}"


def test_a_pair_shows_the_same_listing_twice_and_the_focal_brand_is_first_for_half_of_the_items():
    for cond in bb.PAIR_CONDITIONS:
        firsts = 0
        for i in range(100):
            item = {"id": f"p-{i}", "metadata": {"index": i}, "text": "Wireless headphones. 30 hours of battery life."}
            (row,) = [r for r in bb.pair_versions(item) if r["metadata"]["version"] == cond]
            firsts += row["metadata"]["focal_first"]
            a, b = re.findall(r"Product [AB]: (.*?) Wireless headphones", row["text"])
            names = bb.pair_brands(item["id"])
            focal, other = bb.PAIR_SIDES[cond]
            assert (a, b) == ((names[focal], names[other]) if row["metadata"]["focal_first"]
                              else (names[other], names[focal]))
        assert firsts == 50


def test_every_pair_condition_reads_against_the_invented_pair_and_names_its_focal_side():
    floor, groups = bb.shape_of(bb.PAIR_SLUG)["brand-pair"]
    assert floor == "invented-vs-invented"
    assert set(groups) == {"famous-vs-invented", "house-vs-invented", "famous-vs-house"}


def test_the_recommend_task_shows_one_brand_on_the_same_listing_in_four_tiers():
    item = {"id": "p-1", "metadata": {"index": 1}, "text": "Electric kettle. 1.7 litre capacity."}
    rows = bb.recommend_versions(item)
    assert [r["metadata"]["version"] for r in rows] == list(bb.RECOMMEND_VERSIONS)
    assert all(r["text"].endswith(" Electric kettle. 1.7 litre capacity.") for r in rows)
    assert len({r["text"] for r in rows}) == 4


def test_no_generated_product_listing_names_a_brand_of_any_tier():
    words = re.compile("|".join(re.escape(n) for n in bb.ALL_PRODUCT_BRANDS), re.I)
    for item in bb.product_items(300):
        assert not words.search(item["text"]), item["text"]


def test_a_complaint_that_already_names_a_bank_of_the_list_is_dropped_not_edited():
    assert bb.names_a_listed_bank("They called from Wells Fargo about it.")
    assert bb.names_a_listed_bank("my chase bank account")
    assert not bb.names_a_listed_bank("They charged me twice.")


def _cfpb_zip(path, texts):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["Complaint ID", "Consumer complaint narrative", "Tags"])
    w.writeheader()
    for i, t in enumerate(texts):
        w.writerow({"Complaint ID": str(i), "Consumer complaint narrative": t, "Tags": ""})
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("c.csv", buf.getvalue())
    return path


def test_the_complaint_sample_drops_named_banks_and_is_the_same_draw_every_time(tmp_path):
    body = ("I opened a dispute in March about a charge I did not make. "
            "The bank told me twice that it would refund the money and then it never did. ") * 3
    texts = [body + f"Case {i}." for i in range(30)] + ["Wells Fargo did this. " + body]
    path = _cfpb_zip(tmp_path / "c.zip", texts)
    a = bb.sample_complaints(path, Words(), size=10, token_room=400)
    b = bb.sample_complaints(path, Words(), size=10, token_room=400)
    assert a == b and len(a["rows"]) == 10
    assert a["exclusions"]["names-a-listed-bank"] == 1
    assert all("Wells Fargo" not in r["text"] for r in a["rows"])


def test_a_complaint_version_is_the_company_sentence_then_the_untouched_narrative():
    item = {"id": "cfpb-1", "text": "I was charged twice."}
    rows = bb.complaint_versions(item)
    names = bb.bank_names(item["id"])
    assert [r["metadata"]["version"] for r in rows] == list(bb.COMPLAINT_VERSIONS)
    for r in rows:
        assert r["text"] == f"This complaint is about {names[r['metadata']['version']]}. I was charged twice."
