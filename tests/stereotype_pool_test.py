"""The trope tasks that share the 2,000-biography pool carry a byte-identical copy of it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks"


def test_every_trope_task_uses_the_same_biography_pool():
    pool = (ROOT / "stereotypes" / "items.jsonl").read_bytes()
    for name in ("stereotypes-veteran", "stereotypes-sexuality", "stereotypes-batch3"):
        assert (ROOT / name / "items.jsonl").read_bytes() == pool, name
