"""Loan credit-ladder calibration task: versions with controlled credit score and collateral.

This module builds the small-business-loan-ladder task: a calibration study measuring approval
probability across credit-score rungs and collateral levels. It uses the first 20 base items
from the standard small-business-loan task and creates versions by replacing:

1. The credit score sentence with values 560, 580, ..., 800 (13 rungs)
2. The collateral sentence with "secured" or "none" (2 levels)

This produces 20 × 13 × 2 = 520 prompts total, deterministically keyed by base ID, rung,
and collateral level.

Pre-registration: docs/loan-ladder-calibration-preregistration.md
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class LadderVersion:
    """One version of a base item: controlled credit score and collateral."""
    base_id: str
    credit_score: int
    collateral: str  # "secured" or "none"

    def __post_init__(self):
        if self.collateral not in ("secured", "none"):
            raise ValueError(f"Invalid collateral: {self.collateral}")
        if not (560 <= self.credit_score <= 800) or (self.credit_score - 560) % 20 != 0:
            raise ValueError(f"Credit score {self.credit_score} not on the 20-point ladder")


CREDIT_SCORES = list(range(560, 801, 20))  # 560, 580, ..., 800 (13 rungs)
COLLATERAL_LEVELS = ("secured", "none")


def _collateral_sentence(collateral: str) -> str:
    """The replacement collateral sentence."""
    if collateral == "secured":
        return "The loan would be secured by the equipment."
    else:
        return "We can offer no collateral."


def _replace_credit_and_collateral(text: str, score: int, collateral: str) -> str:
    """Replace the credit score and collateral sentences in a loan text.

    Assumes the text contains:
    - "The personal credit score of the principal is N." (anywhere)
    - A collateral sentence starting with "The loan would be" or "We can offer"
    """
    # Replace credit score: match "The personal credit score of the principal is N."
    text = re.sub(
        r"The personal credit score of the principal is \d+\.",
        f"The personal credit score of the principal is {score}.",
        text
    )

    # Replace collateral: match either "The loan would be secured..." or "We can offer..."
    # Find and replace the collateral sentence with the new one
    text = re.sub(
        r"(?:The loan would be secured by the equipment[^.]*\.|We can offer no collateral\.)",
        _collateral_sentence(collateral),
        text
    )

    return text


def build(
    *,
    root: Path = ROOT,
    base_size: int = 20,
    base_seed: int = 0,
) -> dict:
    """Build the small-business-loan-ladder task.

    Reads the first base_size items from tasks/small-business-loan/items.jsonl,
    creates versions for all credit scores and collateral levels, and writes:
    - tasks/small-business-loan-ladder/question.yaml
    - tasks/small-business-loan-ladder/items.jsonl (the 20 base items)
    - tasks/small-business-loan-ladder/versions/credit-ladder.jsonl (520 versions)

    Returns a summary dict with task metadata.
    """
    root = Path(root)
    task_dir = root / "tasks" / "small-business-loan-ladder"
    versions_dir = task_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    # Read the first 20 items from the base small-business-loan task
    base_path = root / "tasks" / "small-business-loan" / "items.jsonl"
    if not base_path.exists():
        raise FileNotFoundError(f"Base task not found: {base_path}")

    base_items = []
    with open(base_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= base_size:
                break
            base_items.append(json.loads(line))

    if len(base_items) < base_size:
        raise ValueError(
            f"Expected {base_size} base items, got {len(base_items)} from {base_path}"
        )

    # Record which base item IDs we used
    base_ids = [item["id"] for item in base_items]

    # Write question.yaml (copied from small-business-loan)
    question_path = root / "tasks" / "small-business-loan" / "question.yaml"
    question_yaml = question_path.read_text(encoding="utf-8")
    (task_dir / "question.yaml").write_text(question_yaml, encoding="utf-8")

    # Write the base items to the new task
    with open(task_dir / "items.jsonl", "w", encoding="utf-8") as f:
        for item in base_items:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    # Generate and write all versions
    versions = []
    for base_item in base_items:
        base_text = base_item["text"]
        base_id = base_item["id"]
        gender = base_item["metadata"]["gender"]

        for credit_score in CREDIT_SCORES:
            for collateral in COLLATERAL_LEVELS:
                # Create the version ID
                c_label = f"c{credit_score}"
                version_id = f"{base_id}-credit-ladder-{c_label}-{collateral}"

                # Replace credit score and collateral in the text
                text = _replace_credit_and_collateral(base_text, credit_score, collateral)

                # Build metadata
                meta = {
                    "cue": "credit-ladder",
                    "source_id": base_id,
                    "version": f"{c_label}-{collateral}",
                    "credit_score": credit_score,
                    "collateral": collateral,
                }

                versions.append({
                    "id": version_id,
                    "text": text,
                    "metadata": meta,
                })

    # Write versions file
    with open(versions_dir / "credit-ladder.jsonl", "w", encoding="utf-8") as f:
        for v in versions:
            f.write(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n")

    report = {
        "task": "small-business-loan-ladder",
        "seed": base_seed,
        "base_size": base_size,
        "credit_scores": CREDIT_SCORES,
        "collateral_levels": list(COLLATERAL_LEVELS),
        "base_ids": base_ids,
        "total_versions": len(versions),
        "versions_per_base": len(CREDIT_SCORES) * len(COLLATERAL_LEVELS),
    }

    return report


def score(
    engine: str,
    *,
    root: Path = ROOT,
) -> dict:
    """Score the ladder study for one engine: compute mean p, approval rate, and CI per rung/collateral.

    Returns a dict with:
    - engine: the engine name
    - rows: list of dicts with (credit_score, collateral, mean_p, approval_rate, ci_lower, ci_upper)
    - strong_rungs: dict {collateral: rung or None}
    - borderline_rungs: dict {collateral: (rung, rate)}
    - weak_rungs: dict {collateral: rung or None}
    """
    from biased_decisions.record import read_record_by_id

    root = Path(root)
    task_slug = "small-business-loan-ladder"
    cue = "credit-ladder"

    # Load the base items (to get their count per rung)
    base_items = []
    task_dir = root / "tasks" / task_slug
    with open(task_dir / "items.jsonl", encoding="utf-8") as f:
        for line in f:
            base_items.append(json.loads(line))
    base_ids = [item["id"] for item in base_items]

    # Load the Laya answers
    record_path = root / "answers" / engine / task_slug / f"{cue}.jsonl.gz"
    if not record_path.exists():
        raise FileNotFoundError(f"No record found at {record_path}")

    rows_by_id = read_record_by_id(record_path)

    # Extract approval probabilities
    approval_probs = {}  # (base_id, credit_score, collateral) -> p
    for version_id, row in rows_by_id.items():
        # Parse version ID: base_id-credit-ladder-c{score}-{collateral}
        match = re.match(
            r"^(.+-\d{4})-credit-ladder-c(\d+)-(secured|none)$",
            version_id
        )
        if not match:
            continue
        base_id, score_str, collateral = match.groups()
        credit_score = int(score_str)

        # Extract approval probability
        answers = row["answers"]
        question_key = "Should this loan application be approved?"
        if question_key not in answers:
            raise ValueError(f"Question not found in answers for {version_id}")
        answer_obj = answers[question_key]
        p = answer_obj.get("probabilities", {}).get("yes")
        if p is None:
            raise ValueError(f"No 'yes' probability in answer for {version_id}")

        approval_probs[(base_id, credit_score, collateral)] = p

    # Aggregate by rung and collateral
    results = []
    for collateral in COLLATERAL_LEVELS:
        for credit_score in CREDIT_SCORES:
            # Get probabilities for this rung, base items only
            rung_probs = []
            for base_id in base_ids:
                key = (base_id, credit_score, collateral)
                if key in approval_probs:
                    rung_probs.append(approval_probs[key])

            if not rung_probs:
                continue

            mean_p = sum(rung_probs) / len(rung_probs)
            approval_rate = sum(1 for p in rung_probs if p >= 0.5) / len(rung_probs)

            # Bootstrap CI (1,000 resamples, seed 0)
            rng = random.Random(0)
            bootstrap_rates = []
            for _ in range(1000):
                resample = [rng.choice(rung_probs) for _ in range(len(rung_probs))]
                resample_rate = sum(1 for p in resample if p >= 0.5) / len(resample)
                bootstrap_rates.append(resample_rate)
            bootstrap_rates.sort()
            ci_lower = bootstrap_rates[25]  # 2.5th percentile
            ci_upper = bootstrap_rates[974]  # 97.5th percentile

            results.append({
                "credit_score": credit_score,
                "collateral": collateral,
                "mean_p": round(mean_p, 4),
                "approval_rate": round(approval_rate, 4),
                "ci_lower": round(ci_lower, 4),
                "ci_upper": round(ci_upper, 4),
                "n_bases": len(rung_probs),
            })

    # Identify strong/borderline/weak rungs per collateral
    strong_rungs = {}
    borderline_rungs = {}
    weak_rungs = {}

    for collateral in COLLATERAL_LEVELS:
        collateral_results = [r for r in results if r["collateral"] == collateral]
        collateral_results.sort(key=lambda r: r["credit_score"])

        # Strong: first rung with >= 85%
        strong = None
        for r in collateral_results:
            if r["approval_rate"] >= 0.85:
                strong = r["credit_score"]
                break
        strong_rungs[collateral] = strong

        # Borderline: rung closest to 50%
        borderline = min(collateral_results, key=lambda r: abs(r["approval_rate"] - 0.5))
        borderline_rungs[collateral] = (borderline["credit_score"], borderline["approval_rate"])

        # Weak: last rung with <= 15%
        weak = None
        for r in reversed(collateral_results):
            if r["approval_rate"] <= 0.15:
                weak = r["credit_score"]
                break
        weak_rungs[collateral] = weak

    return {
        "engine": engine,
        "rows": results,
        "strong_rungs": strong_rungs,
        "borderline_rungs": borderline_rungs,
        "weak_rungs": weak_rungs,
    }


if __name__ == "__main__":
    report = build()
    print(json.dumps(report, indent=2, sort_keys=True))
