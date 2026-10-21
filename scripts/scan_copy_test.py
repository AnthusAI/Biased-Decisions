"""The copy scan converts writing/style-profile.yml to a Humanus policy pack and checks built pages with it."""
import json

import pytest

pytest.importorskip("humanus")

from scripts import scan_copy  # noqa: E402


@pytest.fixture
def site(tmp_path, monkeypatch):
    dist, out = tmp_path / "dist", tmp_path / "copy"
    page = dist / "gender" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text(
        "<html><head><title>x</title></head><body><nav>Home</nav><main>"
        "<h1>Gender</h1><p>The engine changed its answer on 17 of every 100 bios.</p>"
        "<table><tr><td>engine</td></tr></table></main></body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(scan_copy, "DIST", dist)
    monkeypatch.setattr(scan_copy, "OUT", out)
    return out


def test_scan_writes_prose_findings_and_pack(site):
    pack = scan_copy.load_pack()
    report = scan_copy.scan("/gender/", pack)

    prose = (site / "gender.md").read_text(encoding="utf-8")
    assert prose.startswith("# Gender\n\nThe engine changed")
    assert "Home" not in prose and prose.count("engine") == 1
    assert json.loads((site / "gender.json").read_text(encoding="utf-8")) == report
    assert json.loads((site / "pack.json").read_text(encoding="utf-8"))["version"] == scan_copy.PACK_VERSION
    flagged = {(scan_copy.kind(f), f["excerpt"].lower()) for f in report["findings"]}
    assert ("banned-patterns", "engine") in flagged


def test_kind_names_the_check_for_house_checks():
    assert scan_copy.kind({"policyId": "house-checks", "detectorId": "redundancy"}) == "redundancy"
    assert scan_copy.kind({"policyId": "avoid-lexicon", "detectorId": "avoid-lexicon"}) == "avoid-lexicon"


def test_unbuilt_page_says_to_build(site):
    with pytest.raises(SystemExit, match="run `make site` first"):
        scan_copy.scan("/missing/", scan_copy.load_pack())
