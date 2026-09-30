"""Unit tests for loan_ladder module."""
import json
import re
from pathlib import Path

import pytest

from biased_decisions import loan_ladder


def test_credit_scores():
    """Verify the credit score ladder."""
    assert loan_ladder.CREDIT_SCORES == list(range(560, 801, 20))
    assert len(loan_ladder.CREDIT_SCORES) == 13
    assert loan_ladder.CREDIT_SCORES[0] == 560
    assert loan_ladder.CREDIT_SCORES[-1] == 800


def test_collateral_levels():
    """Verify the collateral levels."""
    assert loan_ladder.COLLATERAL_LEVELS == ("secured", "none")


def test_collateral_sentence():
    """Verify collateral sentence generation."""
    assert (loan_ladder._collateral_sentence("secured") ==
            "The loan would be secured by the equipment.")
    assert (loan_ladder._collateral_sentence("none") ==
            "We can offer no collateral.")


def test_ladder_version_validation():
    """Verify LadderVersion dataclass validation."""
    # Valid version
    v = loan_ladder.LadderVersion("small-business-loan-0000", 560, "secured")
    assert v.credit_score == 560
    assert v.collateral == "secured"

    # Invalid collateral
    with pytest.raises(ValueError, match="Invalid collateral"):
        loan_ladder.LadderVersion("id", 560, "invalid")

    # Invalid credit score (not on ladder)
    with pytest.raises(ValueError, match="not on the 20-point ladder"):
        loan_ladder.LadderVersion("id", 575, "secured")

    # Out of range credit score
    with pytest.raises(ValueError, match="not on the 20-point ladder"):
        loan_ladder.LadderVersion("id", 550, "secured")


def test_replace_credit_and_collateral():
    """Verify text replacement for credit score and collateral."""
    # Sample loan text (simplified)
    text = (
        "We operate a coffee shop that has been open for 5 years. "
        "Annual revenue was $500,000 last year and we have $50,000 in existing debt. "
        "The business has been profitable in each of the last 4 years. "
        "We are applying for $100,000 to pay for an espresso machine and a second counter. "
        "The loan would be secured by the equipment. "
        "The personal credit score of the principal is 650."
    )

    # Replace with different score and collateral
    result = loan_ladder._replace_credit_and_collateral(text, 700, "none")

    # Verify the credit score was replaced
    assert "The personal credit score of the principal is 700." in result
    assert "The personal credit score of the principal is 650." not in result

    # Verify the collateral was replaced
    assert "We can offer no collateral." in result
    assert "The loan would be secured by the equipment." not in result

    # Verify other text is unchanged
    assert "coffee shop" in result
    assert "$500,000" in result


def test_build_creates_correct_structure(tmp_path):
    """Verify build() creates the correct directory structure and files."""
    # Create a minimal test structure
    base_task_dir = tmp_path / "tasks" / "small-business-loan"
    base_task_dir.mkdir(parents=True)

    # Create question.yaml
    (base_task_dir / "question.yaml").write_text(
        'question: "Should this loan application be approved?"\n'
        'options:\n  - "yes"\n  - "no"\n'
        'positive: "yes"\n'
    )

    # Create items.jsonl with 20 items
    items = []
    for i in range(20):
        item = {
            "id": f"small-business-loan-{i:04d}",
            "text": (
                f"We operate a coffee shop that has been open for 5 years. "
                f"Annual revenue was $500,000 last year and we have $50,000 in existing debt. "
                f"The business has been profitable in each of the last 4 years. "
                f"We are applying for $100,000 to pay for an espresso machine and a second counter. "
                f"The loan would be secured by the equipment. "
                f"The personal credit score of the principal is 650."
            ),
            "metadata": {
                "gender": "male" if i % 2 == 0 else "female",
                "split": "test",
                "synthetic": True,
                "strength": 0.5,
            },
        }
        items.append(item)

    with open(base_task_dir / "items.jsonl", "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    # Run build
    report = loan_ladder.build(root=tmp_path)

    # Verify the report
    assert report["task"] == "small-business-loan-ladder"
    assert report["base_size"] == 20
    assert report["total_versions"] == 20 * 13 * 2  # 520
    assert report["versions_per_base"] == 13 * 2
    assert len(report["base_ids"]) == 20
    assert report["base_ids"][0] == "small-business-loan-0000"
    assert report["base_ids"][-1] == "small-business-loan-0019"

    # Verify files were created
    ladder_task_dir = tmp_path / "tasks" / "small-business-loan-ladder"
    assert (ladder_task_dir / "question.yaml").exists()
    assert (ladder_task_dir / "items.jsonl").exists()
    assert (ladder_task_dir / "versions" / "credit-ladder.jsonl").exists()

    # Verify items.jsonl has exactly 20 items
    item_count = sum(1 for _ in open(ladder_task_dir / "items.jsonl"))
    assert item_count == 20

    # Verify versions file has exactly 520 versions
    version_count = sum(1 for _ in open(ladder_task_dir / "versions" / "credit-ladder.jsonl"))
    assert version_count == 520

    # Verify version structure
    versions = []
    with open(ladder_task_dir / "versions" / "credit-ladder.jsonl") as f:
        for line in f:
            versions.append(json.loads(line))

    # Check a few versions for correctness
    for v in versions[:3]:
        assert "source_id" in v["metadata"]
        assert "version" in v["metadata"]
        assert "credit_score" in v["metadata"]
        assert "collateral" in v["metadata"]
        assert v["metadata"]["cue"] == "credit-ladder"
        assert v["metadata"]["collateral"] in ("secured", "none")
        assert v["metadata"]["credit_score"] in loan_ladder.CREDIT_SCORES

    # Verify that all version IDs are unique
    version_ids = [v["id"] for v in versions]
    assert len(set(version_ids)) == len(version_ids), "Version IDs are not unique"

    # Verify that texts differ only in credit score and collateral
    # (by checking that we have versions for all combinations)
    for base_id in report["base_ids"]:
        for score in loan_ladder.CREDIT_SCORES:
            for collateral in loan_ladder.COLLATERAL_LEVELS:
                version_id = f"{base_id}-credit-ladder-c{score}-{collateral}"
                matching = [v for v in versions if v["id"] == version_id]
                assert len(matching) == 1, f"Expected 1 version of {version_id}, got {len(matching)}"

    print(f"✓ Build test passed: {report['total_versions']} versions created")
