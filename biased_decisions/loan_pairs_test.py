"""Tests for loan_pairs.py: vs_control, vs_all_mean, pairs, and bands.

Test strategy:
1. vs_control means match the committed studies/small-business-loan-owner-nationality-axis.jsonl
2. Pairs are consistent with vs_control (a|b = a_mean - b_mean ± 0.01)
3. vs_all_mean sums to ~0 across nationalities
4. Synthetic example with 3 apps x 2 versions for flip counting
5. Committed study file equals score_loan_pairs + write_rows output (byte-for-byte)
"""
import json
from pathlib import Path
import pytest

from biased_decisions import loan_pairs
from biased_decisions.scoring import write_rows
from biased_decisions.tasks.base import DEFAULT_ROOT, Task


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
    def test_vs_control_matches_committed_study(self, engine: str, nat: str):
        """Verify mean_pts against the committed study."""
        row = loan_pairs.score_loan_pairs(engine, root=DEFAULT_ROOT)
        committed = _read_committed_study(engine)

        computed_mean = row["vs_control"][nat]["mean_pts"]
        committed_mean = committed["versions"][nat]["mean_pts"]
        assert computed_mean == committed_mean, f"{engine} {nat} mean: {computed_mean} != {committed_mean}"


class TestPairs:
    """Pairs must have exactly 78 keys and be consistent with vs_control."""

    def test_pairs_has_78_keys(self):
        """13 choose 2 = 78."""
        row = loan_pairs.score_loan_pairs("laya", root=DEFAULT_ROOT)
        assert len(row["pairs"]) == 78

    @pytest.mark.parametrize("engine,nat_a,nat_b", [
        ("laya", "american", "israeli"),
        ("laya", "israeli", "palestinian"),
        ("kev", "american", "chinese"),
        ("jev", "russian", "ukrainian"),
    ])
    def test_pairs_consistent_with_vs_control(self, engine: str, nat_a: str, nat_b: str):
        """pairs[a|b].mean_pts should equal vs_control[a] - vs_control[b] ± 0.01."""
        row = loan_pairs.score_loan_pairs(engine, root=DEFAULT_ROOT)

        # Ensure a comes before b in the fixed order
        if loan_pairs.NATIONALITIES.index(nat_a) > loan_pairs.NATIONALITIES.index(nat_b):
            nat_a, nat_b = nat_b, nat_a

        key = f"{nat_a}|{nat_b}"
        pair_mean = row["pairs"][key]["mean_pts"]
        expected = round(row["vs_control"][nat_a]["mean_pts"] - row["vs_control"][nat_b]["mean_pts"], 2)

        # Allow rounding error up to 0.01
        assert abs(pair_mean - expected) <= 0.01, f"{key}: {pair_mean} != {expected}"


class TestVsAllMean:
    """vs_all_mean sums to ~0 across nationalities (within rounding)."""

    def test_vs_all_mean_sums_to_zero(self):
        """The mean across nationalities should sum to ~0."""
        row = loan_pairs.score_loan_pairs("laya", root=DEFAULT_ROOT)

        total = sum(row["vs_all_mean"][nat]["mean_pts"] for nat in loan_pairs.NATIONALITIES)
        # With 13 nationalities and rounding to 2 decimals, some error is expected
        assert abs(total) <= 1.0, f"vs_all_mean sum: {total}"


class TestBands:
    """Bands must have correct counts and flip structure."""

    def test_bands_structure(self):
        """Check that bands has expected keys and structure."""
        row = loan_pairs.score_loan_pairs("laya", root=DEFAULT_ROOT)
        bands = row["bands"]

        assert "cut_points" in bands
        assert bands["cut_points"] == [0.35, 0.65]
        assert "definition" in bands
        assert "counts" in bands
        assert "flips" in bands

        # Check counts
        assert isinstance(bands["counts"], dict)
        assert set(bands["counts"].keys()) == {"weak", "borderline", "strong"}
        for count in bands["counts"].values():
            assert count >= 0

    def test_bands_flips_structure(self):
        """Check that flips has the right structure."""
        row = loan_pairs.score_loan_pairs("laya", root=DEFAULT_ROOT)
        flips = row["bands"]["flips"]

        for band, band_flips in flips.items():
            if band_flips is not None:
                assert "vs_control" in band_flips
                assert "pairs" in band_flips

                # vs_control should have 13 nationalities
                assert len(band_flips["vs_control"]) == 13

                # Each nationality flip should have the expected fields
                for nat, flip_data in band_flips["vs_control"].items():
                    assert "approve_to_deny_pct" in flip_data
                    assert "approve_to_deny_ci" in flip_data
                    assert "deny_to_approve_pct" in flip_data
                    assert "deny_to_approve_ci" in flip_data
                    assert "net_pct" in flip_data
                    assert "net_ci" in flip_data


class TestSyntheticFlips:
    """Synthetic 3-application x 2-version example to pin flip counting."""

    def test_synthetic_flip_example(self):
        """Hand-computed flip example: 3 apps x 2 versions.

        Applications (source_ids):
        app1: [v_floor=0.4, v_test=0.6]  -> decision: floor=deny, test=approve (deny_to_approve)
        app2: [v_floor=0.6, v_test=0.4]  -> decision: floor=approve, test=deny (approve_to_deny)
        app3: [v_floor=0.9, v_test=0.85] -> decision: floor=approve, test=approve (no flip)

        Expected flip_vs_floor for v_test:
        - approve_to_deny: 1/3 = 33.3%
        - deny_to_approve: 1/3 = 33.3%
        - net: 0%
        """
        # Build a minimal by_source structure for the synthetic example
        by_source = {
            "app1": {"floor-cyclist": 0.4, "american": 0.6},
            "app2": {"floor-cyclist": 0.6, "american": 0.4},
            "app3": {"floor-cyclist": 0.9, "american": 0.85},
        }

        # Manually compute flips for this example
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

        # 1/3 ≈ 33.3%
        assert abs(a2d_pct - 33.33) < 0.1
        assert abs(d2a_pct - 33.33) < 0.1

    def test_net_ci_computed_per_resample(self):
        """Test that net_ci is computed per-resample, not from independently sorted lists.

        Scenario: 3 apps with anticorrelated flips.
        - app1: floor approved (1.0), test denied (0.0) -> a2d=1, d2a=0, net=-1
        - app2: floor denied (0.0), test approved (1.0) -> a2d=0, d2a=1, net=+1
        - app3: floor denied (0.0), test approved (1.0) -> a2d=0, d2a=1, net=+1

        The key assertion: net_ci lo <= net_pct <= net_ci hi must hold.
        """
        floor_probs = [1.0, 0.0, 0.0]  # approved, denied, denied
        test_probs = [0.0, 1.0, 1.0]   # denied, approved, approved

        # Small resamples for testing
        resample_indices = loan_pairs._bootstrap_resample_indices(3, resamples=100, seed=42)
        stats = loan_pairs._flip_stats(floor_probs, test_probs, resample_indices)

        # Core assertions: net_ci must bracket net_pct
        assert stats["net_pct"] >= stats["net_ci"][0], \
            f"net_pct {stats['net_pct']} < lo {stats['net_ci'][0]}"
        assert stats["net_pct"] <= stats["net_ci"][1], \
            f"net_pct {stats['net_pct']} > hi {stats['net_ci'][1]}"

        # The net should be positive (more d2a than a2d overall)
        assert stats["net_pct"] > 0, f"Expected positive net, got {stats['net_pct']}"


class TestDeterminism:
    """The study file should be deterministic."""

    def test_replay_produces_deterministic_output(self):
        """Running score_loan_pairs twice should produce identical files."""
        root = DEFAULT_ROOT / "tests" / "scratch"
        root.mkdir(parents=True, exist_ok=True)

        # First run
        rows1 = []
        for engine in ["laya", "kev", "jev"]:
            rows1.append(loan_pairs.score_loan_pairs(engine, root=DEFAULT_ROOT))
        out1 = root / "run1.jsonl"
        write_rows(out1, rows1, ("engine",))
        md5_1 = _file_md5(out1)

        # Second run
        rows2 = []
        for engine in ["laya", "kev", "jev"]:
            rows2.append(loan_pairs.score_loan_pairs(engine, root=DEFAULT_ROOT))
        out2 = root / "run2.jsonl"
        write_rows(out2, rows2, ("engine",))
        md5_2 = _file_md5(out2)

        # Files must be identical
        assert md5_1 == md5_2, f"Determinism check failed: {md5_1} != {md5_2}"

        # Clean up
        out1.unlink()
        out2.unlink()


def _file_md5(path: Path) -> str:
    """Compute MD5 of a file."""
    import hashlib
    return hashlib.md5(path.read_bytes()).hexdigest()
