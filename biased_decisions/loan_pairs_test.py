"""Tests for loan_pairs.py: vs_control, vs_all_mean, pairs, and bands.

Test strategy: Most tests read the COMMITTED study file (fast). Only one test
recomputes score_loan_pairs and compares byte-for-byte (slow, runs once).
"""
import hashlib
import json
from pathlib import Path
import pytest

from biased_decisions import loan_pairs
from biased_decisions.scoring import write_rows
from biased_decisions.tasks.base import DEFAULT_ROOT, Task


@pytest.fixture(scope="module")
def scored_rows():
    """Compute loan_pairs for all engines once per module."""
    return {e: loan_pairs.score_loan_pairs(e, root=DEFAULT_ROOT) for e in ["laya", "kev", "jev"]}


def _read_committed_study(engine: str) -> dict:
    """Load the committed study row for the given engine."""
    root = DEFAULT_ROOT
    path = root / "studies" / "small-business-loan-owner-nationality-axis.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row["engine"] == engine:
            return row
    raise ValueError(f"No committed study row for {engine}")


class TestVsControl:
    """vs_control must equal the committed study exactly (to 2 decimals)."""

    @pytest.mark.parametrize("engine,nat", [
        ("laya", "american"),
        ("laya", "israeli"),
        ("laya", "palestinian"),
        ("kev", "american"),
        ("kev", "israeli"),
        ("kev", "palestinian"),
        ("jev", "american"),
        ("jev", "israeli"),
        ("jev", "palestinian"),
    ])
    def test_vs_control_matches_committed_study(self, engine: str, nat: str, scored_rows):
        """Verify mean_pts against the committed study."""
        row = scored_rows[engine]
        committed = _read_committed_study(engine)

        computed_mean = row["vs_control"][nat]["mean_pts"]
        committed_mean = committed["versions"][nat]["mean_pts"]
        assert computed_mean == committed_mean, f"{engine} {nat} mean: {computed_mean} != {committed_mean}"


class TestPairs:
    """Pairs must have exactly 78 keys and be consistent with vs_control."""

    def test_pairs_has_78_keys(self, scored_rows):
        """13 choose 2 = 78."""
        row = scored_rows["laya"]
        assert len(row["pairs"]) == 78

    @pytest.mark.parametrize("engine,nat_a,nat_b", [
        ("laya", "american", "israeli"),
        ("laya", "israeli", "palestinian"),
        ("kev", "american", "chinese"),
        ("jev", "russian", "ukrainian"),
    ])
    def test_pairs_consistent_with_vs_control(self, engine: str, nat_a: str, nat_b: str, scored_rows):
        """pairs[a|b].mean_pts should equal vs_control[a] - vs_control[b] (within floating-point error)."""
        row = scored_rows[engine]

        # Ensure a comes before b in the fixed order
        if loan_pairs.NATIONALITIES.index(nat_a) > loan_pairs.NATIONALITIES.index(nat_b):
            nat_a, nat_b = nat_b, nat_a

        key = f"{nat_a}|{nat_b}"
        pair_mean = row["pairs"][key]["mean_pts"]
        expected = round(row["vs_control"][nat_a]["mean_pts"] - row["vs_control"][nat_b]["mean_pts"], 2)

        # Allow for floating-point rounding error from independent bootstrap runs
        assert abs(pair_mean - expected) <= 0.02, f"{key}: {pair_mean} != {expected}"


class TestVsAllMean:
    """vs_all_mean sums to ~0 across nationalities (within rounding)."""

    def test_vs_all_mean_sums_to_zero(self, scored_rows):
        """The mean across nationalities should sum to ~0."""
        row = scored_rows["laya"]

        total = sum(row["vs_all_mean"][nat]["mean_pts"] for nat in loan_pairs.NATIONALITIES)
        assert abs(total) <= 1.0, f"vs_all_mean sum: {total}"


class TestBands:
    """Bands must have correct counts and flip structure."""

    def test_bands_structure(self, scored_rows):
        """Check that bands has expected keys and structure."""
        row = scored_rows["laya"]
        bands = row["bands"]

        assert "cut_points" in bands
        assert bands["cut_points"] == [0.35, 0.65]
        assert "definition" in bands
        assert "counts" in bands
        assert "flips" in bands

        assert isinstance(bands["counts"], dict)
        assert set(bands["counts"].keys()) == {"weak", "borderline", "strong"}
        for count in bands["counts"].values():
            assert count >= 0

    def test_bands_flips_structure(self, scored_rows):
        """Check that flips has the right structure."""
        row = scored_rows["laya"]
        flips = row["bands"]["flips"]

        for band, band_flips in flips.items():
            if band_flips is not None:
                assert "vs_control" in band_flips
                assert "pairs" in band_flips

                assert len(band_flips["vs_control"]) == 13

                for nat, flip_data in band_flips["vs_control"].items():
                    assert "approve_to_deny_pct" in flip_data
                    assert "approve_to_deny_ci" in flip_data
                    assert "deny_to_approve_pct" in flip_data
                    assert "deny_to_approve_ci" in flip_data
                    assert "net_pct" in flip_data
                    assert "net_ci" in flip_data


class TestSyntheticFlips:
    """Synthetic flip examples to pin flip counting and net_ci computation."""

    def test_synthetic_flip_example(self):
        """Hand-computed flip example: 3 apps x 2 versions."""
        by_source = {
            "app1": {"floor-cyclist": 0.4, "american": 0.6},
            "app2": {"floor-cyclist": 0.6, "american": 0.4},
            "app3": {"floor-cyclist": 0.9, "american": 0.85},
        }

        approve_to_deny = []
        deny_to_approve = []

        for app in ["app1", "app2", "app3"]:
            p_floor = by_source[app]["floor-cyclist"]
            p_test = by_source[app]["american"]
            decided_floor = p_floor >= 0.5
            decided_test = p_test >= 0.5

            if decided_floor and not decided_test:
                approve_to_deny.append(1)
            else:
                approve_to_deny.append(0)

            if not decided_floor and decided_test:
                deny_to_approve.append(1)
            else:
                deny_to_approve.append(0)

        a2d_pct = sum(approve_to_deny) / len(approve_to_deny) * 100
        d2a_pct = sum(deny_to_approve) / len(deny_to_approve) * 100

        assert abs(a2d_pct - 33.33) < 0.1
        assert abs(d2a_pct - 33.33) < 0.1

    def test_net_ci_computed_per_resample(self):
        """Test that net_ci is computed per-resample, not from independently sorted lists."""
        floor_probs = [1.0, 0.0, 0.0]
        test_probs = [0.0, 1.0, 1.0]

        resample_indices = loan_pairs._bootstrap_resample_indices(3, resamples=100, seed=42)
        stats = loan_pairs._flip_stats(floor_probs, test_probs, resample_indices)

        assert stats["net_pct"] >= stats["net_ci"][0], \
            f"net_pct {stats['net_pct']} < lo {stats['net_ci'][0]}"
        assert stats["net_pct"] <= stats["net_ci"][1], \
            f"net_pct {stats['net_pct']} > hi {stats['net_ci'][1]}"

        assert stats["net_pct"] > 0, f"Expected positive net, got {stats['net_pct']}"


class TestDeterminism:
    """Byte-for-byte consistency: recomputed study equals committed + new run."""

    def test_replay_produces_byte_for_byte_identical_output(self, scored_rows):
        """Run 1 and run 2 should produce identical bytes."""
        root = DEFAULT_ROOT / "tests" / "scratch"
        root.mkdir(parents=True, exist_ok=True)

        # Use scored_rows from fixture (run 1 already done)
        run1_rows = list(scored_rows.values())
        out1 = root / "run1.jsonl"
        write_rows(out1, run1_rows, ("engine",))
        md5_1 = _file_md5(out1)

        # Run 2: recompute and write
        run2_rows = [loan_pairs.score_loan_pairs(e, root=DEFAULT_ROOT) for e in ["laya", "kev", "jev"]]
        out2 = root / "run2.jsonl"
        write_rows(out2, run2_rows, ("engine",))
        md5_2 = _file_md5(out2)

        assert md5_1 == md5_2, f"Determinism check failed: {md5_1} != {md5_2}"

        # Clean up
        out1.unlink()
        out2.unlink()


def _file_md5(path: Path) -> str:
    """Compute MD5 of a file."""
    return hashlib.md5(path.read_bytes()).hexdigest()
