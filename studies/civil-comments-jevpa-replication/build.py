"""Freeze a disjoint, sealed Civil Comments corpus for the JEVPA replication."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable


STUDY_DIR = Path(__file__).resolve().parent
VAR_DIR = STUDY_DIR.parent.parent / "var" / "civil-comments-jevpa-replication"
PARQUET_SHA256 = "2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03"
FIRST_STUDY_SEED = 20260925
FIRST_STUDY_SAMPLE_SIZE = 30_000
SEED = 20260926
SAMPLE_SIZE = 30_000
DISCOVERY_SIZE = 500
SELECTION_SIZE = 500
TEST_SIZE = 1_000
SLICE_SELECTION_THRESHOLD = 0.3
SLICE_SELECTION_SIZE = 150
SLICE_THRESHOLD = 0.1


def binary_label(row: dict[str, Any]) -> int:
    return int(float(row["toxicity"]) >= 0.5)


def sample_ids(rows: Iterable[dict[str, Any]], *, size: int, seed: int) -> set[int]:
    source = sorted((dict(row) for row in rows), key=lambda row: int(row["row_index"]))
    random.Random(seed).shuffle(source)
    return {int(row["row_index"]) for row in source[:size]}


def _item(row: dict[str, Any], split: str) -> dict[str, Any]:
    return {"id": f"civil-validation-{int(row['row_index']):06d}", "text": str(row["text"]),
            "metadata": {"split": split}}


def freeze_rows(rows: Iterable[dict[str, Any]], *, original_sample_size: int = FIRST_STUDY_SAMPLE_SIZE,
                sample_size: int = SAMPLE_SIZE, discovery_size: int = DISCOVERY_SIZE,
                selection_size: int = SELECTION_SIZE, test_size: int = TEST_SIZE,
                original_seed: int = FIRST_STUDY_SEED, seed: int = SEED,
                slice_size: int = SLICE_SELECTION_SIZE) -> dict[str, Any]:
    """Make deterministic splits that share no row with the first 30,000-row sample."""
    source = sorted((dict(row) for row in rows), key=lambda row: int(row["row_index"]))
    if len(source) < original_sample_size + sample_size:
        raise ValueError(f"source has {len(source)} rows; need at least {original_sample_size + sample_size}")
    if len({int(row["row_index"]) for row in source}) != len(source):
        raise ValueError("source row_index values must be unique")
    if discovery_size + selection_size + test_size > sample_size:
        raise ValueError("sample_size cannot hold the registered splits")
    if slice_size * 2 > selection_size:
        raise ValueError("selection_size cannot hold the two registered slice allocations")
    original_ids = sample_ids(source, size=original_sample_size, seed=original_seed)
    eligible = [row for row in source if int(row["row_index"]) not in original_ids]
    random.Random(seed).shuffle(eligible)
    sampled = eligible[:sample_size]
    discovery_rows = sampled[:discovery_size]
    remaining = sampled[discovery_size:]
    selected: list[dict[str, Any]] = []
    selected_ids: set[int] = set()
    for field in ("threat", "identity_attack"):
        choices = [row for row in remaining if int(row["row_index"]) not in selected_ids
                   and float(row[field]) >= SLICE_SELECTION_THRESHOLD]
        if len(choices) < slice_size:
            raise ValueError(f"only {len(choices)} rows qualify for the {field} selection allocation")
        selected.extend(choices[:slice_size])
        selected_ids.update(int(row["row_index"]) for row in choices[:slice_size])
    selected.extend(row for row in remaining if int(row["row_index"]) not in selected_ids)
    selection_rows = selected[:selection_size]
    selection_ids = {int(row["row_index"]) for row in selection_rows}
    test_rows = [row for row in remaining if int(row["row_index"]) not in selection_ids][:test_size]
    splits = {"discovery": [_item(row, "discovery") for row in discovery_rows],
              "selection": [_item(row, "selection") for row in selection_rows],
              "test": [_item(row, "test") for row in test_rows]}

    def sealed(source_rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
        return [{"id": f"civil-validation-{int(row['row_index']):06d}",
                 "row_index": int(row["row_index"]), "reference_label": binary_label(row),
                 "score": float(row[field])}
                for row in source_rows if float(row[field]) >= SLICE_THRESHOLD]

    analyst_items = [{**item, "metadata": {**item["metadata"], "reference_label": binary_label(row)}}
                     for item, row in zip(splits["discovery"], discovery_rows)]
    sealed_evaluation = [
        {"id": f"civil-validation-{int(row['row_index']):06d}", "row_index": int(row["row_index"]),
         "split": "selection" if index < selection_size else "test", "reference_label": binary_label(row),
         "threat": float(row["threat"]), "identity_attack": float(row["identity_attack"])}
        for index, row in enumerate(selection_rows + test_rows)]
    return {"splits": splits, "analyst_items": analyst_items,
            "sealed_selection_slices": {"threat": sealed(selection_rows, "threat"),
                                        "identity_attack": sealed(selection_rows, "identity_attack")},
            "sealed_evaluation": sealed_evaluation,
            "first_study_sample_ids": sorted(original_ids)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(path: Path) -> list[dict[str, Any]]:
    import pandas as pd
    frame = pd.read_parquet(path, columns=["text", "toxicity", "threat", "identity_attack"])
    return [{"row_index": int(index), **row} for index, row in frame.to_dict("index").items()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def freeze(source_path: Path, out_dir: Path) -> dict[str, Any]:
    actual_sha = sha256(source_path)
    if actual_sha != PARQUET_SHA256:
        raise ValueError(f"source checksum mismatch: expected {PARQUET_SHA256}, got {actual_sha}")
    result = freeze_rows(load_source(source_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "corpus.jsonl", [item for split in ("discovery", "selection", "test")
                                               for item in result["splits"][split]])
    write_jsonl(out_dir / "analyst_discovery.jsonl", result["analyst_items"])
    (out_dir / "sealed_evaluation.json").write_text(json.dumps({
        "slice_threshold": SLICE_THRESHOLD, "selection_slices": result["sealed_selection_slices"],
        "rows": result["sealed_evaluation"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {"experiment": "Civil Comments JEVPA replication", "source_sha256": actual_sha,
                "first_study_seed": FIRST_STUDY_SEED, "first_study_sample_size": FIRST_STUDY_SAMPLE_SIZE,
                "seed": SEED, "sample_size": SAMPLE_SIZE,
                "selection_slice_threshold": SLICE_SELECTION_THRESHOLD,
                "selection_slice_size": SLICE_SELECTION_SIZE,
                "split_ids": {name: [row["id"] for row in split] for name, split in result["splits"].items()},
                "analyst_visible": "analyst_discovery.jsonl only",
                "sealed_fields": ["reference_label outside discovery", "threat", "identity_attack"]}
    manifest["sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (out_dir / "split_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=VAR_DIR)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
