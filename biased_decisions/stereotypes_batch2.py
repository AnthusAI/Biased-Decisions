"""The ``stereotypes`` task batch 2 scorer: reads laya answer records and produces
the detailed JSONL rows matching the staged batch2 file format.

Batch 2 is the religion and nationality stereotype axes (2,000 bios, six questions each).
The task definition and answer records are shared with the stereotypes task; this scorer
reads them and outputs to the same files (studies/stereotypes-{axis}.jsonl).
"""
from __future__ import annotations

import json
import gzip
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from biased_decisions.metrics import tropes
from biased_decisions.metrics.tropes import Axis, Question
from biased_decisions.record import read_record_by_id, record_path
from biased_decisions.stereotypes import build_items, AXES, read_questions, registered_bios
from biased_decisions.tasks.base import Task

SLUG = "stereotypes"
AS_WRITTEN = "as-written"


def _p_yes(rows_by_id: dict, ids: List[str], question: str) -> List[float]:
    """Extract P(yes) values for a question from answer records."""
    return [rows_by_id[i]["answers"][question]["noul"] for i in ids]


def score_stereotypes_batch2(engine: str, task: Task, axis: str) -> List[dict]:
    """Score one axis for batch 2, outputting detailed JSONL rows (meta, as_written_baseline,
    general_effect, shift) that exactly match the staged file format.

    Returns a list of dicts ready to be serialized as JSONL rows.
    """
    spec = AXES[axis]
    questions = read_questions(task)
    items = [i.id for i in task.load_items()]
    versions = task.load_versions(axis)
    by_bio_version = {(v.metadata["source_id"], v.metadata["version"]): v.id for v in versions}
    answers = read_record_by_id(record_path(engine, task.slug, axis, root=task.root))
    items = registered_bios(task, versions, items, answers)

    # Extract P(yes) for each question and version (groups + floor)
    p_yes: Dict[str, Dict[str, List[float]]] = {}
    for q in questions:
        p_yes[q.key] = {}
        for version in list(spec.groups) + [spec.floor]:
            ids = [by_bio_version[(bio, version)] for bio in items]
            p_yes[q.key][version] = _p_yes(answers, ids, q.key)

    # Calculate burn_draws for this axis (religion first, then nationality)
    skip = 0
    for earlier_axis in AXES:
        if earlier_axis == axis:
            break
        skip += tropes.burn_draws(len(questions), len(items))

    # Score using the standard tropes scorer
    scored = tropes.score_axis(spec, questions, p_yes, skip_draws=skip)

    # Read as-written baseline if it exists
    baseline_p_yes = {}
    written_path = record_path(engine, task.slug, AS_WRITTEN, root=task.root)
    if written_path.exists():
        written = read_record_by_id(written_path)
        baseline_p_yes = {q.key: _p_yes(written, items, q.key) for q in questions}

    # Build output rows in the exact format of the staged file
    model = next(iter(answers.values()))["model"]
    rows: List[dict] = []

    # 1. Meta record
    # Determine which axes are scored (only this one)
    axes_scored = [axis]
    meta = {
        "record": "meta",
        "engine": model,  # Use the full model name like "laya-upstream:0.3.7"
        "n_bios": len(items),
        "n_resamples": tropes.N_RESAMPLES,
        "seed": tropes.SEED,
        "questions": {q.key: {"question": q.text, "trope_consistent_answer": q.trope_consistent_answer}
                      for q in questions},
        "axes_scored": axes_scored,
        "axes_skipped_incomplete": [],
    }
    rows.append(meta)

    # 2. As-written baseline records (per question)
    if baseline_p_yes:
        baseline_data = tropes.as_written_baseline(questions, baseline_p_yes)
        for q_key, baseline_row in baseline_data.items():
            rows.append({
                "record": "as_written_baseline",
                "question": q_key,
                **baseline_row
            })

    # 3. General effect and shift records (per question, then per group)
    for q in questions:
        # General effect record
        general_effect = scored[q.key]["general_effect"]
        rows.append({
            "record": "general_effect",
            "axis": axis,
            "question": q.key,
            "n_bios": len(items),
            "mean_shift": general_effect["mean_shift"],
            "ci_lo": general_effect["ci_lo"],
            "ci_hi": general_effect["ci_hi"],
        })

        # Shift records (one per group)
        for group in spec.groups:
            cell = scored[q.key]["groups"][group]
            rows.append({
                "record": "shift",
                "axis": axis,
                "question": q.key,
                "group": group,
                "n_bios": len(items),
                "group_mean": cell["group_mean"],
                "floor_mean": scored[q.key]["floor_mean"],
                "shift": cell["shift"],
                "shift_ci_lo": cell["shift_ci_lo"],
                "shift_ci_hi": cell["shift_ci_hi"],
                "flip_rate": cell["flip_rate"],
                "trope_score": cell["trope_score"],
                "trope_score_ci_lo": cell["trope_score_ci_lo"],
                "trope_score_ci_hi": cell["trope_score_ci_hi"],
                "trope_detected": cell["trope_detected"],
            })

    return rows
