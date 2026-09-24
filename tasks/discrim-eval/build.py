"""Reproducible build for the ``discrim-eval`` task.

Source: Anthropic's discrim-eval (Tamkin et al. 2023), CC BY 4.0, ``explicit.jsonl`` at a pinned
Hugging Face revision. ``--fetch`` downloads it to ``var/discrim-eval/`` and verifies its sha256; the
build verifies it again, then writes ``items.jsonl``, ``versions/{race,gender,age}.jsonl`` and
``sampling.json`` using ``biased_decisions.discrim_bbq``. Every text is the dataset's own filled text,
unchanged. See README.md for the rule and the counts.

    python3 tasks/discrim-eval/build.py --fetch    # download and verify
    python3 tasks/discrim-eval/build.py            # rebuild the committed files
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from biased_decisions import discrim_bbq  # noqa: E402

TASK_DIR = Path(__file__).resolve().parent
VAR_DIR = REPO / "var" / "discrim-eval"
REVISION = "6986d6ea802e019d01e94dd59597e94fbd8f8c4a"
BASE_URL = f"https://huggingface.co/datasets/Anthropic/discrim-eval/resolve/{REVISION}/"
SHA256 = {
    "explicit.jsonl": "348f64457832056fa2601044c5107f42b50e8ff16c0428844c4b2d18ddd2d42a",
    "README.md": "8408a0da2dc406d794aa29f16aa8f471fc938a6cda8592581a5c70d4949de1af",
}
TOKENIZER_GLOB = str(Path.home() / ".cache/huggingface/hub/models--aac6fef--laya-mlx/snapshots/*/tokenizer/tokenizer.json")


def fetch() -> None:
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    for name in SHA256:
        urllib.request.urlretrieve(BASE_URL + name, VAR_DIR / name)
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


def build(out_dir: Path = TASK_DIR, var_dir: Path = VAR_DIR) -> dict:
    verify(var_dir)
    source = [json.loads(line) for line in (Path(var_dir) / "explicit.jsonl").read_text(encoding="utf-8").splitlines()]
    grid = discrim_bbq.discrim_grid(source)
    items = discrim_bbq.discrim_items(grid)
    out_dir = Path(out_dir)
    _write(out_dir / "items.jsonl", items)
    counts = {"items": len(items)}
    texts = [i["text"] for i in items]
    for axis in discrim_bbq.DISCRIM_AXES:
        versions = discrim_bbq.discrim_versions(grid, axis)
        _write(out_dir / "versions" / f"{axis}.jsonl", versions)
        counts[axis] = len(versions)
        texts += [v["text"] for v in versions]
    tokens = _tokens()
    if tokens is not None:
        discrim_bbq.check_fits(texts, tokens, discrim_bbq.DISCRIM_QUESTION)
    report = {"source": "explicit.jsonl", "source_sha256": SHA256["explicit.jsonl"],
              "source_revision": REVISION, "source_rows": len(source),
              "scenarios": len({k[0] for k in grid}), "seed": discrim_bbq.SEED,
              "backgrounds_per_scenario_and_cue": discrim_bbq.DISCRIM_BACKGROUNDS,
              "reference": discrim_bbq.REFERENCE, "texts_written": counts}
    (out_dir / "sampling.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    build()
