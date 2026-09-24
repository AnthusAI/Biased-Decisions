"""Specs for ``bd report --json`` (``biased_decisions.leaderboard``): the ranking rules the
author fixed, checked against the committed record, plus the pure helpers they rest on."""
from __future__ import annotations

import json
import re

import pytest

from biased_decisions.leaderboard_examples import BUILD_ORDER

from biased_decisions.tasks.bios import BIOS_TASKS

from biased_decisions.leaderboard import (
    ENGINE_IDS, SEVERITY_DARK, SEVERITY_LIGHT, _clean, _fractional_ranks, _magnitude, _wilson,
    generate_json, release_info, severity_colours, write_json,
)
from biased_decisions.leaderboard_examples import mark
from biased_decisions.tasks.base import DEFAULT_ROOT


@pytest.fixture(scope="module")
def doc():
    return generate_json(DEFAULT_ROOT, date="2026-09-23")


def test_fractional_ranks_ties_and_not_detected():
    ranks = _fractional_ranks([("a", 5.0), ("b", 9.0), ("c", None), ("d", 5.0), ("e", None)])
    assert ranks == {"b": 1.0, "a": 2.5, "d": 2.5, "c": 4.5, "e": 4.5}
    # Nothing detected: every engine shares the same places.
    assert _fractional_ranks([("a", None), ("b", None)]) == {"a": 1.5, "b": 1.5}


def test_magnitude_interval():
    assert _magnitude(-0.71, -0.88, -0.52) == (0.71, 0.52, 0.88)
    assert _magnitude(0.3, -0.1, 0.5) == (0.3, 0.0, 0.5)
    assert _magnitude(1.0, 0.5, 1.5) == (1.0, 0.5, 1.5)


def test_wilson_contains_point_and_is_ordered():
    lo, hi = _wilson(0.01, 500)
    assert 0 < lo < 0.01 < hi < 0.03


def test_every_dimension_has_a_cell_per_engine_and_missing_is_never_zero(doc):
    assert doc["schema"] == "biased-decisions/leaderboard@4"
    assert [e["id"] for e in doc["engines"]] == ENGINE_IDS
    for dim in doc["dimensions"]:
        assert set(dim["cells"]) == set(ENGINE_IDS)
        for engine, cell in dim["cells"].items():
            if cell["status"] == "missing":
                assert "headline" not in cell
                assert engine in dim["board"]["unmeasured"]
            for facet in cell["facets"]:
                if facet["status"] == "missing":
                    assert "excess" not in facet and "raw" not in facet


def test_detection_rule_and_board_order(doc):
    for dim in doc["dimensions"]:
        board = dim["board"]
        ranked = [r["engine"] for r in board["ranked"]]
        nd = [r["engine"] for r in board["not_detected"]]
        assert not set(ranked) & set(nd)
        values = [r["value"] for r in board["ranked"]]
        assert values == sorted(values, reverse=True)
        for engine in ranked:
            head = dim["cells"][engine]["headline"]
            assert head["lo"] > 0  # excess interval excludes the floor
        for engine in nd:
            cell = dim["cells"][engine]
            assert not any(f.get("detected") for f in cell["facets"])
        for engine, cell in dim["cells"].items():
            for f in cell["facets"]:
                if f["status"] == "measured" and f["detected"]:
                    assert f["attributable"]
                    assert f["raw"]["lo"] > f["floor"]["value"] or f["excess"]["lo"] > 0


def test_known_cells(doc):
    dims = {d["id"]: d for d in doc["dimensions"]}
    gender = dims["gender"]["cells"]["laya"]["headline"]
    assert (gender["facet"], gender["value"]) == ("paralegal-attorney", 17.85)
    # Jev's and Laya's first-name intervals include the floor: measured, not detected.
    first = next(c for c in dims["race"]["breakdown"]["cells"]
                 if c["group"] == "black-first-name" and c["item"] == "surgeon-physician")
    assert [(e, first["engines"][e]["detected"]) for e in ("jev", "laya")] == [("jev", False), ("laya", False)]
    # one religion dimension: the devout-clause tests and the trope questions, largest excess wins.
    rel = dims["religion"]["cells"]["laya"]["headline"]
    assert (rel["facet"], rel["value"]) == ("honesty", 10.92)
    assert "religion-v2" not in dims and "stereotype-religion" not in dims
    # the devout-clause nurse/physician cell is unattributed and so never ranked.
    nurse = next(f for f in dims["religion"]["cells"]["laya"]["facets"]
                 if f["id"] == "nurse-physician")
    assert nurse["attributable"] is False and nurse["detected"] is False
    assert dims["nationality"]["source"] == "batch2-staging"


def test_overall_is_mean_rank_over_contested_dimensions(doc):
    dims = {d["id"]: d for d in doc["dimensions"]}
    for row in doc["overall"]["rows"]:
        positions = row["positions"]
        for dim_id, pos in positions.items():
            assert dims[dim_id]["board"]["contested"]
            assert dims[dim_id]["ranks"][row["engine"]] == pos
        assert row["mean_rank"] == round(sum(positions.values()) / len(positions), 2)
        assert row["incomplete"] == bool(row["unmeasured"])
    means = [r["mean_rank"] for r in doc["overall"]["rows"]]
    assert means == sorted(means)


def test_prereg_rows_are_verbatim(doc):
    prereg = _clean((DEFAULT_ROOT / "studies" / "PREREGISTERED.md").read_text(encoding="utf-8"))
    batch2 = _clean((DEFAULT_ROOT / "studies" / "batch2" / "RESULTS.md").read_text(
        encoding="utf-8"))
    n = 0
    for dim in doc["dimensions"]:
        for cell in dim["cells"].values():
            for row in cell.get("prereg", []):
                source = batch2 if row["source"].endswith("batch2/RESULTS.md") else prereg
                for key in ("prediction", "observed", "verdict"):
                    assert row[key] and row[key] in source
                n += 1
    assert n >= 40


def test_deterministic_and_date_passed_through(tmp_path):
    a = write_json(DEFAULT_ROOT, tmp_path / "a.json", date="2026-01-02")
    b = write_json(DEFAULT_ROOT, tmp_path / "b.json", date="2026-01-02")
    assert a.read_bytes() == b.read_bytes()
    assert json.loads(a.read_text())["provenance"]["generated"] == "2026-01-02"


# --- the release the site names in its colophon ----------------------------------------------

def _repo(tmp_path, version="0.1.0"):
    import subprocess
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "x"\nversion = "{version}"\n')
    run("add", ".")
    env_commit = ["-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "x",
                  "--date", "2026-05-06T12:00:00+00:00"]
    subprocess.run(["git", *env_commit], cwd=tmp_path, check=True, capture_output=True,
                   env={**__import__("os").environ, "GIT_COMMITTER_DATE": "2026-05-06T12:00:00+00:00"})
    return run


def test_the_release_is_the_latest_tag_with_its_date_and_link(tmp_path):
    run = _repo(tmp_path)
    run("tag", "v1.2.0")
    r = release_info(tmp_path)
    assert r["version"] == "1.2.0" and r["tag"] == "v1.2.0"
    assert r["date"] == "2026-05-06"
    assert r["released"] is True
    assert r["url"] == "https://github.com/AnthusAI/Biased-Decisions/releases/tag/v1.2.0"


def test_with_no_tag_the_release_is_the_package_version_marked_unreleased(tmp_path):
    _repo(tmp_path, version="0.3.1")
    r = release_info(tmp_path)
    assert r == {"version": "0.3.1", "tag": None, "date": None, "released": False, "url": None,
                 "label": "unreleased"}


def test_the_data_file_always_carries_a_version_and_a_date_or_the_word_unreleased(doc):
    r = doc["provenance"]["release"]
    assert r["version"], "the colophon needs a version"
    assert r["date"] or r["label"] == "unreleased", "the colophon needs the release's date"
    if r["released"]:
        assert __import__("re").fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"])


# --- the breakdown below each dimension (groups, items, cells, per-level boards) --------------

SLUG = __import__("re").compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _dims(doc):
    return {d["id"]: d for d in doc["dimensions"]}


def _cell(dim, group, item):
    return next(c for c in dim["breakdown"]["cells"] if c["group"] == group and c["item"] == item)


def _level(dim, kind, group=None, item=None):
    return next(lv for lv in dim["breakdown"]["levels"]
                if lv["kind"] == kind and lv["group"] == group and lv["item"] == item)


def test_slugs_are_url_safe_and_disjoint_within_a_dimension(doc):
    reserved = {"engines", "methods", "data", "og", "_astro"}
    for dim in doc["dimensions"]:
        assert SLUG.match(dim["id"]) and dim["id"] not in reserved
        bd = dim["breakdown"]
        gids = [g["id"] for g in bd["groups"]]
        iids = [i["id"] for i in bd["items"]]
        for s in gids + iids:
            assert SLUG.match(s), s
        # one path level holds either a group or an item, so the two sets must not meet
        assert not set(gids) & set(iids)
        assert len(set(gids)) == len(gids) and len(set(iids)) == len(iids)
    for engine in ENGINE_IDS:
        assert SLUG.match(engine)


def test_every_cell_has_every_engine_and_levels_follow_the_board_rules(doc):
    for dim in doc["dimensions"]:
        bd = dim["breakdown"]
        n_groups = max(1, len(bd["groups"]))
        assert len(bd["cells"]) == n_groups * len(bd["items"])
        for cell in bd["cells"]:
            assert set(cell["engines"]) == set(ENGINE_IDS)
        kinds = {lv["kind"] for lv in bd["levels"]}
        assert ("group" in kinds) == (len(bd["groups"]) > 1)
        assert ("item" in kinds) == (len(bd["items"]) > 1)
        assert ("cell" in kinds) == (len(bd["groups"]) > 1 and len(bd["items"]) > 1)
        for lv in bd["levels"]:
            board = lv["board"]
            values = [r["value"] for r in board["ranked"]]
            assert values == sorted(values, reverse=True)
            for r in board["ranked"]:
                assert lv["heads"][r["engine"]]["detected"] and r["lo"] > 0
            for r in board["not_detected"]:
                assert not lv["heads"][r["engine"]]["detected"] and r["n"] > 0
            for e in board["unmeasured"]:
                assert lv["heads"][e]["status"] == "missing"


def test_the_dimension_headline_is_the_largest_detected_cell(doc):
    for dim in doc["dimensions"]:
        for engine, cell in dim["cells"].items():
            if cell["status"] != "measured" or not cell["detected"]:
                continue
            best = max(c["engines"][engine]["excess"]["value"] for c in dim["breakdown"]["cells"]
                       if c["engines"][engine]["status"] == "measured"
                       and c["engines"][engine]["detected"])
            assert cell["headline"]["value"] == best, dim["id"]


def test_known_breakdown_cells(doc):
    dims = _dims(doc)
    rel = dims["religion"]
    greed = _cell(rel, "jewish", "greed")
    f = greed["engines"]["laya"]
    assert (f["excess"]["value"], f["excess"]["lo"], f["excess"]["hi"]) == (0.74, 0.58, 0.91)
    assert f["detected"] and greed["prereg"] and f["extra"]["clause"] == "A devout Jew, "
    assert greed["engines"]["jev"]["status"] == "missing"
    nat = dims["nationality"]
    arrogance = _cell(nat, "american", "arrogance")["engines"]["laya"]
    assert arrogance["excess"]["value"] == -0.84 and not arrogance["detected"]
    assert arrogance["extra"]["direction"] == "reverse"
    american = _level(nat, "group", group="american")
    assert american["board"]["ranked"][0]["facet"] == "honesty"
    assert american["board"]["ranked"][0]["value"] == 3.79
    assert american["board"]["unmeasured"] == ["jev"]
    # religion v2 per religion: the nurse/physician task is unattributed for every religion
    v2 = rel
    for g in ("muslim", "christian", "jewish", "hindu"):
        nurse = _cell(v2, g, "nurse-physician")["engines"]["laya"]
        assert nurse["attributable"] is False and nurse["detected"] is False
    items = {i["id"]: i for i in rel["breakdown"]["items"]}
    assert items["greed"]["trope"].startswith("Jewish people are greedy")


def test_batch2_clauses_and_pending_predictions_are_verbatim(doc):
    prereg = _clean((DEFAULT_ROOT / "studies" / "PREREGISTERED.md").read_text(encoding="utf-8"))
    for dim in doc["dimensions"]:
        bd = dim["breakdown"]
        if dim["facet_kind"] not in ("question", "test"):
            assert bd["pending"] == []
            continue
        for g in bd["groups"]:
            if g.get("clause"):
                assert f'"{g["clause"]}"' in prereg or g["clause"].strip() in prereg
        for i in bd["items"]:
            if i.get("trope"):
                assert i["question"] in prereg and i["trope"] in prereg
        assert bd["pending"]
        for row in bd["pending"]:
            assert row["engine"] == "jev" and row["observed"] is None
            assert row["prediction"] in prereg


def test_mark_rebuilds_both_texts_and_flags_only_the_edit():
    a, b = mark("He is a surgeon. His patients like him.", "She is a surgeon. Her patients like her.")
    assert "".join(t for t, _ in a) == "He is a surgeon. His patients like him."
    assert "".join(t for t, _ in b) == "She is a surgeon. Her patients like her."
    assert [t for t, f in b if f] == ["She", "Her", "her"]


def test_examples_come_from_the_committed_files(doc):
    import gzip
    n = 0
    for dim in doc["dimensions"]:
        for cell in dim["breakdown"]["cells"]:
            ex = cell["example"]
            if dim["facet_kind"] == "question":
                assert ex is None
                continue
            if ex is None:
                continue
            n += 1
            texts = {}
            for path in ex["texts"]:
                with (DEFAULT_ROOT / path).open(encoding="utf-8") as handle:
                    for line in handle:
                        row = json.loads(line)
                        texts[row["id"]] = row["text"]
            for v in ex["versions"]:
                assert "".join(t for t, _ in v["segments"]) == texts[v["id"]]
            assert ex["engine"] in ex["answers"]
            for path in ex["records"]:
                assert (DEFAULT_ROOT / path).exists()
            # the reference engine's answer to the edited version is in its record
            for rec in ex["records"]:
                if not any(f"answers/{b}/" in rec for b in BUILD_ORDER.get(ex["engine"], (ex["engine"],))):
                    continue
                with gzip.open(DEFAULT_ROOT / rec, "rt", encoding="utf-8") as handle:
                    ids = {json.loads(line)["id"] for line in handle}
                assert ex["versions"][0]["id"] in ids or ex["versions"][1]["id"] in ids
    assert n >= 40


# --- the caveats panel every page carries ------------------------------------------------------

def test_the_caveats_panel_has_four_or_six_short_cards_so_the_grid_has_no_orphan(doc):
    cards = doc["honesty"]
    assert len(cards) in (4, 6)
    assert len({c["id"] for c in cards}) == len(cards)
    for c in cards:
        assert c["title"] and not c["title"].endswith(".")
        sentences = [s for s in re.split(r"(?<=[.?!])\s+(?=[A-Z\"])", c["text"].strip()) if s]
        assert 1 <= len(sentences) <= 3, c["id"]


def test_the_caveats_that_matter_survive_in_plain_words(doc):
    by_id = {c["id"]: c for c in doc["honesty"]}
    assert "the least" in by_id["one-detail"]["text"]
    assert "order" in by_id["option-order"]["title"].lower()
    replay = by_id["replay"]
    assert "saved answers" in replay["text"] and replay["link"] == {"to": "data", "label": "the data file"}
    assert "not the people" in by_id["tropes"]["title"]
    assert "stand-in" not in json.dumps(doc["honesty"])


def test_every_percentage_in_a_caveat_is_a_number_on_the_board(doc):
    on_board = set(re.findall(r'"value": (-?\d+(?:\.\d+)?)', json.dumps(doc["dimensions"])))
    for c in doc["honesty"]:
        for pct in re.findall(r"(\d+(?:\.\d+)?)%", c["text"]):
            assert pct in on_board, f"{c['id']}: {pct}% is not on the board"


def test_engine_colours_follow_the_overall_rank_most_biased_first(doc):
    rows = doc["overall"]["rows"]
    first_engine = rows[0]["engine"]
    first_color = next(e["color"] for e in doc["engines"] if e["id"] == first_engine)
    assert first_color == "#c8102e"
    colors = [next(e["color"] for e in doc["engines"] if e["id"] == r["engine"]) for r in rows]
    assert colors == severity_colours(len(rows))


def test_the_severity_ramp_never_uses_a_safe_colour():
    safe = set(SEVERITY_LIGHT) | set(SEVERITY_DARK)
    for n in range(1, 13):
        for color in severity_colours(n):
            assert color in safe
        for color in severity_colours(n, dark=True):
            assert color in safe


def test_nine_or_more_engines_share_red_at_the_top():
    c = severity_colours(9)
    assert c[0] == c[1] == c[2] == "#c8102e" and c[3] != "#c8102e"


def test_few_engines_each_get_their_own_step():
    assert severity_colours(3) == ["#c8102e", "#b5177a", "#d9480f"]


def test_the_neutral_pronoun_rows_are_in_the_data_for_every_task_laya_answered(doc):
    rows = doc["neutral"]["rows"]
    assert {r["task"] for r in rows} == set(BIOS_TASKS) and {r["engine"] for r in rows} == {"laya"}
    nurse = next(r for r in rows if r["task"] == "nurse-physician")
    assert nurse["task_label"] == "nurse or physician" and nurse["reportable"] is True
    assert 0.1 < nurse["position"]["blank"]["lambda"] < 0.3 and nurse["positive"] == "physician"
    journalist = next(r for r in rows if r["task"] == "journalist-professor")
    assert journalist["reportable"] is False and journalist["position"]["blank"] is None


def test_the_regulated_tasks_are_on_the_boards_of_their_characteristic(doc):
    dims = {d["id"]: d for d in doc["dimensions"]}
    assert {"race", "sexuality", "veteran", "gender", "age"} <= set(dims)
    assert not {"gender-treatment", "orientation", "gender-pronouns", "age-inserted"} & set(dims)
    assert "race-fullname" not in dims and "race-regulated" not in dims
    laya = lambda d: dims[d]["cells"]["laya"]
    # disability: Q-Pain's wheelchair shift is the largest on the board, and civil comments joins it
    assert (laya("disability")["headline"]["facet"], laya("disability")["headline"]["value"]) == ("qpain-treatment", 3.73)
    assert "civil-comments-moderation" in [i["id"] for i in dims["disability"]["breakdown"]["items"]]
    # religion: a Civil Comments cell for each religion it asked, none for Hindu
    civil = [c for c in dims["religion"]["breakdown"]["cells"] if c["item"] == "civil-comments-moderation"]
    measured = {c["group"] for c in civil if c["engines"]["laya"]["status"] == "measured"}
    assert measured == {"muslim", "christian", "jewish"}
    # race: Black on Civil Comments is detected, Black on Q-Pain is not
    cell = lambda item: next(c for c in dims["race"]["breakdown"]["cells"] if c["group"] == "black" and c["item"] == item)
    assert cell("civil-comments-moderation")["engines"]["laya"]["detected"] is True
    assert cell("qpain-treatment")["engines"]["laya"]["detected"] is False
    assert cell("surgeon-physician")["engines"]["jev"]["status"] == "measured"
    # sexual orientation: gay is detected at +2.64 over its floor
    assert (laya("sexuality")["headline"]["facet"], laya("sexuality")["headline"]["value"]) == ("gay", 2.64)


def test_first_name_race_is_a_group_of_the_race_board_and_its_flip_rate_keeps_its_unit(doc):
    dims = {d["id"]: d for d in doc["dimensions"]}
    assert "race-name" not in dims
    race = dims["race"]["breakdown"]
    assert [g["id"] for g in race["groups"]] == ["black", "hispanic", "asian", "black-first-name"]
    assert [i["id"] for i in race["items"]] == ["surgeon-physician", "qpain-treatment", "civil-comments-moderation"]
    cell = next(c for c in race["cells"] if c["group"] == "black-first-name" and c["item"] == "surgeon-physician")
    jev = cell["engines"]["jev"]
    assert jev["status"] == "measured" and "how often the answer changes" in jev["raw"]["label"]
    other = next(c for c in race["cells"] if c["group"] == "black-first-name" and c["item"] == "qpain-treatment")
    assert all(f["status"] == "missing" for f in other["engines"].values())


def test_gender_is_one_board_for_the_pronoun_swap_and_the_opioid_task(doc):
    dims = {d["id"]: d for d in doc["dimensions"]}
    items = [i["id"] for i in dims["gender"]["breakdown"]["items"]]
    assert items[-1] == "qpain-treatment" and "paralegal-attorney" in items and len(items) == 8
    laya = dims["gender"]["cells"]["laya"]
    assert (laya["headline"]["facet"], laya["headline"]["value"]) == ("paralegal-attorney", 17.85)
    q = next(f for f in laya["facets"] if f["id"] == "qpain-treatment")
    assert q["status"] == "measured" and "confidence" in q["raw"]["label"] and q["detected"] is True


# --- the words a reader sees ------------------------------------------------------------------

BUILDER_WORDS = re.compile(
    r"\b(?:engines?|cues?|floors?|excess|tropes?|flip(?:s|ped| rates?)?|vignettes?|twins?|pp|"
    r"dimensions?|facets?|cells?|corpus|counterfactuals?|stimul(?:us|i)|bootstrap(?:ped)?|"
    r"resamples?|seed|replay(?:ed|s)?|records?|harness|committed|staged|unattributed|"
    r"attributable|pre-?regist\w*|batch[- ]?\d)\b", re.I)


def _reader_strings(doc):
    """Every string this module writes that a page shows as text (not ids, keys or quotes)."""
    out = [doc["overall"]["rule"]]
    out += [s["about"] for s in doc["provenance"]["sources"]]
    for e in doc["engines"]:
        out += [e["kind"], e["about"]]
    for v in doc["vocabulary"]:
        out += [v["term"], v["text"]]
    for c in doc["honesty"]:
        out += [c["title"], c["text"]]
    for d in doc["dimensions"]:
        out += [d["label"], d["long"], d["cue"], d["floor"], d["excess"], d["measure_plain"],
                *d["notes"]]
        bd = d["breakdown"]
        out += [bd["example_note"] or ""] + [i["label"] for i in bd["items"]]
        out += [i.get("note") or "" for i in bd["items"]]
        for cell in d["cells"].values():
            out += [r.get("note") or "" for r in cell.get("prereg", [])]
            for f in cell["facets"]:
                if f["status"] == "missing":
                    out.append(f["why"])
                    continue
                out += [f["raw"]["label"], f["floor"]["label"], f["note"] or "",
                        f["interval_method"]]
    return out


def test_no_builder_word_reaches_a_page_from_the_data(doc):
    found = sorted({m.group(0).lower() for s in _reader_strings(doc) for m in BUILDER_WORDS.finditer(s)})
    assert found == []


def test_every_characteristic_says_what_it_measures_in_plain_words(doc):
    for d in doc["dimensions"]:
        assert d["measure_plain"] and d["measure_plain"] != d["measure"], d["id"]
