"""Specs for ``bd report --json`` (``biased_decisions.leaderboard``): the ranking rules the
author fixed, checked against the committed record, plus the pure helpers they rest on."""
from __future__ import annotations

import json

import pytest

from biased_decisions.leaderboard import (
    ENGINE_IDS, _clean, _fractional_ranks, _magnitude, _wilson, generate_json, write_json,
)
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
    assert doc["schema"] == "biased-decisions/leaderboard@1"
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
    gender = dims["gender-pronouns"]["cells"]["laya"]["headline"]
    assert (gender["facet"], gender["value"]) == ("paralegal-attorney", 17.85)
    # Jev's race-name interval [0.51, 1.40] includes its 0.57% floor: listed, not ranked.
    assert [r["engine"] for r in dims["race-name"]["board"]["not_detected"]] == ["jev",
                                                                                "laya-mlx"]
    assert dims["race-name"]["board"]["ranked"] == []
    # religion v1 is a contrast (Jewish minus Muslim on paralegal/attorney), never a shared shift.
    rel = dims["religion"]["cells"]["laya"]["headline"]
    assert (rel["facet"], rel["value"]) == ("paralegal-attorney", 5.34)
    # religion v2's nurse/physician cell is unattributed and so never ranked.
    nurse = next(f for f in dims["religion-v2"]["cells"]["laya"]["facets"]
                 if f["id"] == "nurse-physician")
    assert nurse["attributable"] is False and nurse["detected"] is False
    assert dims["stereotype-religion"]["source"] == "batch2-staging"


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
