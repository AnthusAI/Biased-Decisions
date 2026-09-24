"""Feature: the gendered-language queue lists every cell once, with the row count the committed
versions files really have, and only commands the runners accept."""
import re
from pathlib import Path

from biased_decisions import gendered_language as gl

ROOT = Path(__file__).resolve().parents[1]
LINES = [l for l in (ROOT / "queue" / "gendered-language.txt").read_text().splitlines()
         if l.strip() and not l.startswith("#")]
COMMAND = re.compile(r"^scripts/(answer_task|answer_wordchoice)\.py (\S+)(?: (?!--)(\S+))?( --skip-as-written)? --build laya-mlx\s+# rows=(\d+) est_hours=([\d.]+)$")


def test_every_command_is_well_formed_and_uses_the_mlx_build_without_an_interpreter_path():
    assert LINES and all(COMMAND.match(l) for l in LINES), [l for l in LINES if not COMMAND.match(l)]


def test_every_gendered_cell_is_queued_exactly_once():
    cells = []
    for l in LINES:
        script, a, b, *_ = COMMAND.match(l).groups()
        cells.append((gl.WORD_CHOICE, a) if script == "answer_wordchoice" else (a, b))
    expected = [(s, c) for s in gl.TASKS for c in gl.cues_of(s)]
    assert sorted(cells) == sorted(expected) and len(cells) == 13


def test_the_expected_row_count_is_the_number_of_lines_in_the_committed_versions_file():
    for l in LINES:
        script, a, b, _, rows, _ = COMMAND.match(l).groups()
        slug, cue = (gl.WORD_CHOICE, a) if script == "answer_wordchoice" else (a, b)
        path = ROOT / "tasks" / slug / "versions" / f"{cue}.jsonl"
        assert int(rows) == sum(1 for _ in path.open()), l


def test_answer_task_commands_skip_the_as_written_pool_because_no_measure_reads_it():
    assert all("--skip-as-written" in l for l in LINES if "answer_task.py" in l)


def test_the_total_in_the_footer_matches_the_commands():
    text = (ROOT / "queue" / "gendered-language.txt").read_text()
    rows = sum(int(COMMAND.match(l).group(5)) for l in LINES)
    hours = sum(float(COMMAND.match(l).group(6)) for l in LINES)
    assert f"total rows={rows}" in text and f"{hours:.1f} hours" in text
