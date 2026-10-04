"""Feature: the Laya queue lists every brand cue once, with the row count each command will write."""
import re
from pathlib import Path

from biased_decisions import brand_bias as bb

ROOT = Path(__file__).resolve().parent.parent


def _commands():
    out = []
    for line in (ROOT / "queue" / "brand-bias.txt").read_text().splitlines():
        if line.startswith("python3 "):
            words, _, comment = line.partition("#")
            task, cue = words.split()[2:4]
            out.append((task, cue, "--skip-as-written" in words, int(re.search(r"rows=(\d+)", comment).group(1)), words))
    return out


def test_every_brand_cue_is_queued_exactly_once_and_on_the_original_laya_build():
    cells = [(t, c) for t, c, _, _, _ in _commands()]
    assert sorted(cells) == sorted((t, c) for t in bb.TASKS for c in bb.shape_of(t))
    assert all("--build laya " in words + " " and "laya-mlx" not in words for *_, words in _commands())


def test_each_expected_row_count_is_the_versions_file_plus_the_as_written_texts_when_they_are_kept():
    for task, cue, skip, rows, _ in _commands():
        versions = sum(1 for _ in open(ROOT / "tasks" / task / "versions" / f"{cue}.jsonl"))
        items = sum(1 for _ in open(ROOT / "tasks" / task / "items.jsonl"))
        assert rows == versions + (0 if skip else items), (task, cue)


def test_the_stated_total_is_the_sum_of_the_commands():
    text = (ROOT / "queue" / "brand-bias.txt").read_text()
    assert int(re.search(r"# total rows=(\d+)", text).group(1)) == sum(r for _, _, _, r, _ in _commands())
