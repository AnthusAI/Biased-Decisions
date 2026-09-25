"""Freeze a raw-label Civil Comments corpus for the JEVPA study.

The public parquet is checksum-pinned.  This builder never puts threat or
identity-attack annotations beside text made available to the analyst.  It
writes those annotations only to a sealed local evaluation file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import urllib.request
from pathlib import Path
from typing import Any, Iterable


STUDY_DIR = Path(__file__).resolve().parent
VAR_DIR = STUDY_DIR.parent.parent / "var" / "civil-comments-jevpa"
PARQUET_URL = (
    "https://huggingface.co/datasets/google/civil_comments/resolve/main/"
    "data/validation-00000-of-00001.parquet"
)
PARQUET_SHA256 = "2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03"
SOURCE_NAME = "google/civil_comments validation-00000-of-00001.parquet"
SEED = 20260925
SAMPLE_SIZE = 30_000
DISCOVERY_SIZE = 140
SELECTION_SIZE = 300
TEST_SIZE = 500
SLICE_THRESHOLD = 0.1
SLICE_SELECTION_THRESHOLD = 0.3
SLICE_SELECTION_SIZE = 100


def binary_label(row: dict[str, Any]) -> int:
    return int(float(row["toxicity"]) >= 0.5)


def _item(row: dict[str, Any], split: str) -> dict[str, Any]:
    return {
        "id": f"civil-validation-{int(row['row_index']):06d}",
        "text": str(row["text"]),
        "metadata": {"split": split},
    }


def freeze_rows(rows: Iterable[dict[str, Any]], *, sample_size: int = SAMPLE_SIZE,
                discovery_size: int = DISCOVERY_SIZE,
                selection_size: int = SELECTION_SIZE,
                test_size: int = TEST_SIZE, seed: int = SEED,
                slice_size: int = SLICE_SELECTION_SIZE) -> dict[str, Any]:
    """Return deterministic, non-overlapping splits and sealed subtype slices."""
    required = discovery_size + selection_size + test_size
    if sample_size < required:
        raise ValueError(f"sample_size {sample_size} cannot hold {required} registered rows")
    source = sorted((dict(row) for row in rows), key=lambda row: int(row["row_index"]))
    if len(source) < sample_size:
        raise ValueError(f"source has {len(source)} rows; need {sample_size}")
    if len({int(row["row_index"]) for row in source}) != len(source):
        raise ValueError("source row_index values must be unique")
    random.Random(seed).shuffle(source)
    if slice_size * 2 > selection_size:
        raise ValueError("selection_size cannot hold the two registered slice allocations")
    sampled = source[:sample_size]
    discovery_rows = sampled[:discovery_size]
    remaining = sampled[discovery_size:]
    selected: list[dict[str, Any]] = []
    selected_indexes: set[int] = set()
    for field in ("threat", "identity_attack"):
        eligible = [row for row in remaining if int(row["row_index"]) not in selected_indexes
                    and float(row[field]) >= SLICE_SELECTION_THRESHOLD]
        if len(eligible) < slice_size:
            raise ValueError(f"only {len(eligible)} rows qualify for the {field} selection allocation")
        selected.extend(eligible[:slice_size])
        selected_indexes.update(int(row["row_index"]) for row in eligible[:slice_size])
    selected.extend(row for row in remaining if int(row["row_index"]) not in selected_indexes)
    selection_rows = selected[:selection_size]
    selection_indexes = {int(row["row_index"]) for row in selection_rows}
    test_rows = [row for row in remaining if int(row["row_index"]) not in selection_indexes][:test_size]
    splits = {
        "discovery": [_item(row, "discovery") for row in discovery_rows],
        "selection": [_item(row, "selection") for row in selection_rows],
        "test": [_item(row, "test") for row in test_rows],
    }
    analyst_items = [
        {**item, "metadata": {**item["metadata"], "reference_label": binary_label(row)}}
        for item, row in zip(splits["discovery"], discovery_rows)
    ]
    sealed_selection = selection_rows
    sealed_evaluation = selection_rows + test_rows

    def sealed_rows(source_rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
        return [
            {"id": f"civil-validation-{int(row['row_index']):06d}",
             "row_index": int(row["row_index"]), "reference_label": binary_label(row),
             "score": float(row[field])}
            for row in source_rows if float(row[field]) >= SLICE_THRESHOLD
        ]

    return {
        "splits": splits,
        "analyst_items": analyst_items,
        "sealed_selection_slices": {
            "threat": sealed_rows(sealed_selection, "threat"),
            "identity_attack": sealed_rows(sealed_selection, "identity_attack"),
        },
        "sealed_evaluation": [
            {"id": f"civil-validation-{int(row['row_index']):06d}",
             "row_index": int(row["row_index"]), "split": "selection" if index < selection_size else "test",
             "reference_label": binary_label(row), "threat": float(row["threat"]),
             "identity_attack": float(row["identity_attack"])}
            for index, row in enumerate(sealed_evaluation)
        ],
    }


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


def freeze(source_path: Path, out_dir: Path, *, seed: int = SEED) -> dict[str, Any]:
    actual_sha = sha256(source_path)
    if actual_sha != PARQUET_SHA256:
        raise ValueError(f"source checksum mismatch: expected {PARQUET_SHA256}, got {actual_sha}")
    result = freeze_rows(load_source(source_path), seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = [item for split in ("discovery", "selection", "test") for item in result["splits"][split]]
    write_jsonl(out_dir / "corpus.jsonl", corpus)
    write_jsonl(out_dir / "analyst_discovery.jsonl", result["analyst_items"])
    (out_dir / "sealed_evaluation.json").write_text(
        json.dumps({"slice_threshold": SLICE_THRESHOLD,
                    "selection_slices": result["sealed_selection_slices"],
                    "rows": result["sealed_evaluation"]}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    manifest = {
        "experiment": "Civil Comments JEVPA",
        "source": SOURCE_NAME,
        "source_sha256": actual_sha,
        "seed": seed,
        "sample_size": SAMPLE_SIZE,
        "selection_slice_threshold": SLICE_SELECTION_THRESHOLD,
        "selection_slice_size": SLICE_SELECTION_SIZE,
        "split_ids": {name: [row["id"] for row in rows]
                      for name, rows in result["splits"].items()},
        "analyst_visible": "analyst_discovery.jsonl only",
        "sealed_fields": ["reference_label outside discovery", "threat", "identity_attack"],
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["sha256"] = hashlib.sha256(canonical).hexdigest()
    (out_dir / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def fetch(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(PARQUET_URL, destination)
    if sha256(destination) != PARQUET_SHA256:
        raise ValueError("downloaded parquet checksum does not match the preregistered source")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=VAR_DIR / "validation.parquet")
    parser.add_argument("--out", type=Path, default=VAR_DIR)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch(args.source)
    print(json.dumps(freeze(args.source, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
