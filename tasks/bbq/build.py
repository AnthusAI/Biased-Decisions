"""Reproducible build for the ``bbq`` task.

Source: BBQ, the Bias Benchmark for QA (Parrish et al. 2022), CC BY 4.0, from the authors' GitHub
repository at a pinned commit: the eleven category files under ``data/`` and
``analysis_scripts/additional_metadata.csv``, whose ``target_loc`` column says which of the three
answers is consistent with the stereotype (the benchmark's own bias-score script uses it that way).
``--fetch`` downloads everything to ``var/bbq/`` and verifies each sha256; the build verifies again,
draws a seeded, group-blind sample (see README.md) and writes ``items.jsonl``,
``versions/<category>-<ambig|disambig>.jsonl`` and ``sampling.json``.

    python3 tasks/bbq/build.py --fetch    # download and verify
    python3 tasks/bbq/build.py            # rebuild the committed files
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from biased_decisions import discrim_bbq  # noqa: E402

TASK_DIR = Path(__file__).resolve().parent
VAR_DIR = REPO / "var" / "bbq"
COMMIT = "bea11bd97d79217245b5871acd247b9d6eb24598"
BASE_URL = f"https://raw.githubusercontent.com/nyu-mll/BBQ/{COMMIT}/"
# local file name -> path in the repository
REMOTE = {**{f"{c}.jsonl": f"data/{c}.jsonl" for c in discrim_bbq.BBQ_CATEGORIES},
          "additional_metadata.csv": "analysis_scripts/additional_metadata.csv",
          "LICENSE": "LICENSE",
          "BBQ_calculate_bias_score.R": "analysis_scripts/BBQ_calculate_bias_score.R",
          "BBQ_README.md": "README.md"}
SHA256 = {
    "Age.jsonl": "46e805b3fc2d8cbd26eeb8e8430d98cf7b2dc9c83574ff3674e8ce4f0fca2a60",
    "Disability_status.jsonl": "375d40d9b71f056150264445ec189b13934998f3f49a1e311aa7578eb3b45e5f",
    "Gender_identity.jsonl": "8b5adbb368510a97d5775dc43e1c719e0249fe2da33f13c83e3e29edafec7a00",
    "Nationality.jsonl": "a583e74666aec0341ded8aa3983e7cad694eb24de72c254d28b2df3035720090",
    "Physical_appearance.jsonl": "e48d7e13508565f4801574e611043470c25c95a0a62af3699cb5ee7cb02608fb",
    "Race_ethnicity.jsonl": "4a9f1214cfaa115ce7f0bdb40609122e431f5152c71b8ca64d665e483b946ae6",
    "Race_x_SES.jsonl": "af8e2ae3d0e5be9ebcbfe7149e591d47ff649e263307f4548f7fb12f6a6d83e8",
    "Race_x_gender.jsonl": "e5dbba782f8c4e25b99dd5470b5136e2db73dbf401cf6d4a5a3ed31b02f95696",
    "Religion.jsonl": "cb9555f9f3454a52cd2df85956b59bd7fcca5aa922c8527693b1164d08417616",
    "SES.jsonl": "9f92754bb037b0982604b9112705fb81d60a19d9e759c67e4a85e484a070f528",
    "Sexual_orientation.jsonl": "2c71036b9e7584fe589c42aef32c1a42bc01b9a5e9b1b8704342630cdb08cefd",
    "additional_metadata.csv": "f36708416b0e7adb81b47ad1926f9c39c2beb611702b73b01e06c9b6c9ffbd3d",
    "LICENSE": "95df2e9564862e51d69683a899b6dcc8218d577057bdf67322880769ff85f29e",
    "BBQ_calculate_bias_score.R": "683294c728e5077209fa83907e3c0d21a178d6cfdb7c5135153070627d685f44",
    "BBQ_README.md": "9b98910f37b3c1b0dc12170ece772847e37bbb514e3158f5cfce18aa8cc703b8",
}
TOKENIZER_GLOB = str(Path.home() / ".cache/huggingface/hub/models--aac6fef--laya-mlx/snapshots/*/tokenizer/tokenizer.json")


def fetch() -> None:
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    for name, remote in REMOTE.items():
        urllib.request.urlretrieve(BASE_URL + remote, VAR_DIR / name)
    verify(VAR_DIR)


def verify(var_dir: Path = VAR_DIR) -> None:
    for name, expected in SHA256.items():
        path = Path(var_dir) / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
        if actual != expected:
            raise SystemExit(f"checksum mismatch for {name}: expected {expected}, got {actual}; "
                             "stopping rather than building from different data.")


def _write(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _tokens():
    found = sorted(glob.glob(TOKENIZER_GLOB))
    if not found:
        return None
    from tokenizers import Tokenizer
    tk = Tokenizer.from_file(found[0])

    class Tokens:
        def count(self, text: str) -> int:
            return len(tk.encode(text, add_special_tokens=False).ids)
    return Tokens()


def target_locs(var_dir: Path) -> dict:
    """(category, example_id, question_index) -> the source's target_loc, or None where it is NA."""
    out = {}
    with open(Path(var_dir) / "additional_metadata.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["category"], row["example_id"], row["question_index"])
            value = None if row["target_loc"] in ("NA", "") else int(row["target_loc"])
            if key in out and out[key] != value:
                raise SystemExit(f"additional_metadata.csv gives two target_loc values for {key}")
            out[key] = value
    return out


def build(out_dir: Path = TASK_DIR, var_dir: Path = VAR_DIR) -> dict:
    verify(var_dir)
    targets = target_locs(var_dir)
    out_dir = Path(out_dir)
    per_category = {}
    picked = []
    for category in discrim_bbq.BBQ_CATEGORIES:
        rows = [json.loads(l) for l in (Path(var_dir) / f"{category}.jsonl").read_text(encoding="utf-8").splitlines()]
        for row in rows:
            row["_target_loc"] = targets.get((category, str(row["example_id"]), str(row["question_index"])))
        pool = discrim_bbq.bbq_pool(rows)
        sample = discrim_bbq.bbq_sample(pool, per_stratum=discrim_bbq.BBQ_PER_STRATUM)
        picked += sample
        per_category[category] = {
            "source_rows": len(rows), "left_out_no_target_loc": pool.skipped, "pool": len(pool),
            "pool_by_condition": dict(sorted(Counter(p["context_condition"] for p in pool).items())),
            "sampled": len(sample)}
    items = [discrim_bbq.bbq_item(p) for p in picked]
    _write(out_dir / "items.jsonl", items)
    texts = [i["text"] for i in items]
    written = {}
    for cue in discrim_bbq.bbq_cues():
        rows = [v for p in picked if discrim_bbq.bbq_cue(p["category"], p["context_condition"]) == cue
                for v in discrim_bbq.bbq_versions(p)]
        _write(out_dir / "versions" / f"{cue}.jsonl", rows)
        written[cue] = len(rows)
        texts += [r["text"] for r in rows]
    tokens = _tokens()
    if tokens is not None:
        discrim_bbq.check_fits(texts, tokens, discrim_bbq.BBQ_QUESTION)
    report = {"source_commit": COMMIT, "source_sha256": {k: SHA256[k] for k in SHA256},
              "seed": discrim_bbq.SEED, "per_stratum": discrim_bbq.BBQ_PER_STRATUM,
              "strata": "ambig: question polarity; disambig: which answer is correct",
              "items": len(items), "texts_written": written, "categories": per_category}
    (out_dir / "sampling.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "source_sha256"}, sort_keys=True))
    return report


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    build()
