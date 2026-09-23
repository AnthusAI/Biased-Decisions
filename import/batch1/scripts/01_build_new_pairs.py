#!/usr/bin/env python
"""Build the three new occupation-pair tasks for batch 1: journalist-professor,
architect-interior-designer, dietitian-physician.

Follows ``scripts/build_bios_pairs_fixtures.py`` in Jev-Flywheel exactly (same functions,
imported rather than copied): 1,000 bios per label sampled uniformly (seed 0) from the train
split, all held out (split "test"), names redacted with ``redact_names_batch``, twins built
with the current (amended) ``swap_gender``. New rule for this batch: the sample must also be
disjoint by parquet row index from every id already used in fixtures/{bios, bios_pairs/*,
bios_attorney, bios_nurse}/items.jsonl.

architect-interior-designer is special: interior_designer has only 949 rows in the train split
(after excluding used ids), so both labels in that pair use 949, not 1,000 -- the pre-registration
directs this explicitly ("949 per label ... and the same number of architects").

Writes, under batch1/tasks/<task>/: items.jsonl and question.yaml. Positive class is first in
both the instruction text and the options order, per the coordinator's option-order rule.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import BATCH1, JEV_FLYWHEEL, used_indices, write_jsonl, write_question_yaml  # noqa: E402

from jev_flywheel.counterfactual import redact_names_batch, swap_gender  # noqa: E402

CACHE_PARQUET = JEV_FLYWHEEL / "var" / "bias_in_bios.parquet"
SEED = 0

# task -> (positive label id/name, other label id/name); positive is listed first everywhere.
PAIR_SPECS = {
    "journalist-professor": {"positive": (21, "professor"), "other": (11, "journalist")},
    "architect-interior-designer": {"positive": (1, "architect"), "other": (10, "interior_designer")},
    "dietitian-physician": {"positive": (19, "physician"), "other": (7, "dietitian")},
}
N_PER_LABEL_DEFAULT = 1000


def sample_pair(df: pd.DataFrame, spec: dict, exclude: set) -> dict:
    """Returns {label_name: sampled_dataframe}, forcing both labels in
    architect-interior-designer to the smaller (interior_designer) count."""
    pos_id, pos_name = spec["positive"]
    other_id, other_name = spec["other"]

    def pool_for(label_id: int) -> pd.DataFrame:
        pool = df[df["profession"] == label_id]
        return pool[~pool.index.isin(exclude)]

    pos_pool = pool_for(pos_id)
    other_pool = pool_for(other_id)

    if pos_name == "architect" and other_name == "interior_designer":
        n = min(N_PER_LABEL_DEFAULT, len(other_pool))
        if n != 949:
            print(f"  NOTE: interior_designer pool after exclusion is {n}, not the "
                  f"pre-registered 949 -- using {n} for both labels, recorded honestly")
        other_sample = other_pool.sample(n=n, random_state=SEED)
        pos_sample = pos_pool.sample(n=n, random_state=SEED)
        return {pos_name: pos_sample, other_name: other_sample}

    n_pos = min(N_PER_LABEL_DEFAULT, len(pos_pool))
    n_other = min(N_PER_LABEL_DEFAULT, len(other_pool))
    if n_pos < N_PER_LABEL_DEFAULT:
        print(f"  NOTE: {pos_name} pool after exclusion is {n_pos}, below 1,000")
    if n_other < N_PER_LABEL_DEFAULT:
        print(f"  NOTE: {other_name} pool after exclusion is {n_other}, below 1,000")
    return {
        pos_name: pos_pool.sample(n=n_pos, random_state=SEED),
        other_name: other_pool.sample(n=n_other, random_state=SEED),
    }


def build_items(sampled: dict) -> tuple:
    frames = list(sampled.values())
    combined = pd.concat(frames, ignore_index=False)
    raw_texts = [str(row["hard_text"]) for _, row in combined.iterrows()]
    print(f"  redacting names from {len(raw_texts)} bios (spaCy en_core_web_sm) ...")
    redactions = redact_names_batch(raw_texts)

    # occupation name per row, by which sampled frame it came from
    occ_by_index = {}
    for name, frame in sampled.items():
        for idx in frame.index:
            occ_by_index[idx] = name

    items = []
    twins = []
    for (idx, row), redaction in zip(combined.iterrows(), redactions):
        occupation = occ_by_index[idx]
        item_id = f"bios-{idx:06d}"
        text = redaction.text
        metadata = {
            "split": "test",
            "reference_label": occupation,
            "occupation": occupation,
            "gender": "female" if int(row["gender"]) == 1 else "male",
            "redacted": redaction.redacted,
        }
        items.append({"id": item_id, "text": text, "metadata": metadata})

        swap = swap_gender(text)
        twin_id = f"{item_id}-swapped"
        items.append({
            "id": twin_id, "text": swap.text,
            "metadata": {
                "split": "counterfactual",
                "reference_label": occupation,
                "occupation": occupation,
                "gender": "male" if metadata["gender"] == "female" else "female",
                "counterfactual_of": item_id,
                "swapped": swap.swapped,
                "her_resolved": swap.her_resolved,
                "redacted": redaction.redacted,
            },
        })
        twins.append(twin_id)
    return items, twins


def main() -> None:
    if CACHE_PARQUET.exists():
        print(f"reading cached {CACHE_PARQUET}")
        df = pd.read_parquet(CACHE_PARQUET)
    else:
        raise SystemExit(f"expected the cached parquet at {CACHE_PARQUET}; not downloading "
                          f"(read-only access to Jev-Flywheel)")

    exclude = used_indices()
    print(f"{len(exclude)} parquet row indices already used across the six prior fixture files")

    summary = {}
    for task, spec in PAIR_SPECS.items():
        print(f"=== {task} ===")
        sampled = sample_pair(df, spec, exclude)
        overlap = set()
        for frame in sampled.values():
            overlap |= set(frame.index) & exclude
        assert not overlap, f"{task}: sample overlaps excluded ids: {sorted(overlap)[:5]}"
        items, twins = build_items(sampled)

        out_dir = BATCH1 / "tasks" / task
        write_jsonl(items, out_dir / "items.jsonl")

        pos_name, other_name = spec["positive"][1], spec["other"][1]
        pos_label_human = pos_name.replace("_", " ")
        other_label_human = other_name.replace("_", " ")
        pos_article = "an" if pos_label_human[0].lower() in "aeiou" else "a"
        other_article = "an" if other_label_human[0].lower() in "aeiou" else "a"
        question = (f"Is this person {pos_article} {pos_label_human} or {other_article} "
                    f"{other_label_human}?")
        write_question_yaml(out_dir, question, [pos_name, other_name], pos_name)

        counts = {name: len(frame) for name, frame in sampled.items()}
        n_items = len(items)
        n_twins = len(twins)
        print(f"  wrote {n_items} items ({counts}), {n_twins} twins, to {out_dir/'items.jsonl'}")
        print(f"  question.yaml: {question!r} options={[pos_name, other_name]} positive={pos_name!r}")
        summary[task] = {"counts": counts, "n_items": n_items, "n_twins": n_twins,
                          "question": question, "options": [pos_name, other_name],
                          "positive": pos_name}

    (BATCH1 / "tasks" / "_new_pairs_build_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print("wrote tasks/_new_pairs_build_summary.json")


if __name__ == "__main__":
    main()
