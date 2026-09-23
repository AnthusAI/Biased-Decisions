"""``bd answer``: fill a record cell by actually asking an engine.

Every milestone-1 number replays from a committed record; nothing in ``bd list``, ``bd build``,
``bd score``, ``bd replay`` or ``bd report`` calls this module. It exists so a later cell (a new
engine, a new task, a new cue) can be answered the same way the committed ones were, once a key
or a GPU is available -- and so it can refuse loudly, before spending anything, when it should
not run.

Two refusals, both checked before any request is sent:

1. **the engine's own package is not installed** -- each adapter's own lazy import already
   raises a clear ``ImportError``; this module checks for it up front instead of failing
   mid-batch.
2. **the record's own option order disagrees with the task's** -- an engine's ``probabilities``
   dict is keyed in the order its ``criteria`` were sent (see the design doc, "Option order is
   part of a task"), so a task file edited after a record was built would silently answer under
   a different order than the rows already there. This module reads the order back out of the
   record's own first row and compares it to ``task.options``, needing no separate metadata file.
"""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import List, Mapping, Sequence

from biased_decisions.record import read_record, record_path
from biased_decisions.tasks.base import Task
from biased_decisions.tasks.items import Item

QUESTION_NAME = "Occupation"


class AnswerRefused(RuntimeError):
    """``bd answer`` will not proceed: a missing dependency, or an option-order mismatch."""


# engine -> (the package its adapter needs, the extra that installs it).
_ENGINE_PACKAGE = {
    "jev": ("typesafe_sdk", "jev"),
    "laya": ("laya", "laya"),
    "laya-mlx": ("laya_mlx", "laya-mlx"),
}


def _check_engine_installed(engine: str) -> None:
    """Check the engine's underlying package can be found, without importing it (a bare
    ``find_spec`` -- no module-level side effects, and nothing left unused for a linter to
    flag)."""
    try:
        package, extra = _ENGINE_PACKAGE[engine]
    except KeyError:
        raise AnswerRefused(f"unknown engine {engine!r}; one of {tuple(_ENGINE_PACKAGE)}")
    if importlib.util.find_spec(package) is None:
        raise AnswerRefused(
            f"{engine} needs the {package!r} package: pip install 'biased-decisions[{extra}]'")


def _check_option_order(task: Task, path: Path) -> None:
    """Refuse if an existing record's rows were answered under an option order that no longer
    matches ``task.options`` -- see this module's docstring."""
    rows = read_record(path)
    if not rows:
        return
    answer = rows[0]["answers"].get(QUESTION_NAME)
    if not answer or "probabilities" not in answer:
        return
    recorded_order = tuple(answer["probabilities"].keys())
    if recorded_order != task.options:
        raise AnswerRefused(
            f"{path} was answered under option order {recorded_order!r}, but "
            f"{task.slug}/question.yaml now lists {task.options!r} -- rebuild the record (or "
            f"revert the task file) before answering more of this cell")


def _engine_factory(engine: str):
    if engine == "jev":
        from biased_decisions.engines.jev import JevEngine
        return JevEngine()
    if engine == "laya":
        from biased_decisions.engines.laya import LayaEngine
        return LayaEngine()
    if engine == "laya-mlx":
        from biased_decisions.engines.laya_mlx import LayaMlxEngine
        return LayaMlxEngine()
    raise AnswerRefused(f"unknown engine {engine!r}; one of jev, laya, laya-mlx")


def preflight(engine: str, task: Task, cue: str, *, root: Path) -> Path:
    """Both refusal checks, run before anything else. Returns the record path they were run
    against; raises ``AnswerRefused`` if either fails."""
    _check_engine_installed(engine)
    path = record_path(engine, task.slug, cue, root=root)
    _check_option_order(task, path)
    return path


def price_estimate(engine: str, task: Task, cue: str, items: Sequence[Item], *,
                    root: Path) -> str:
    """A rough cost estimate for answering ``items``, calibrated from any existing record for
    the same engine (any cue, any task) rather than a hardcoded price table -- there is no
    pricing data bundled with this package, only what a committed record already paid.
    """
    sample_rows: List[dict] = []
    for other_task_dir in (root / "answers" / engine).glob("*"):
        for other_cue_path in other_task_dir.glob("*.jsonl.gz"):
            sample_rows.extend(read_record(other_cue_path)[:50])
            if len(sample_rows) >= 50:
                break
        if len(sample_rows) >= 50:
            break
    if not sample_rows:
        return (f"no existing {engine!r} record to calibrate a price estimate from; "
                f"{len(items)} items would need answering")
    usages = [row["usage"] for row in sample_rows if row.get("usage")]
    if not usages:
        return f"{len(items)} items; existing {engine!r} rows carry no usage to estimate from"
    avg_input = sum(u.get("input_tokens") or 0 for u in usages) / len(usages)
    avg_output = sum(u.get("output_tokens") or 0 for u in usages) / len(usages)
    return (f"{len(items)} items x ~{avg_input:.0f} input / ~{avg_output:.0f} output tokens "
            f"each (averaged over {len(usages)} existing {engine!r} rows) -- no price-per-token "
            f"table is bundled with this package; multiply by your own rate before spending")


async def answer_all(engine: str, task: Task, cue: str, items: Sequence[Item],
                     questions: Mapping[str, Mapping]) -> List[dict]:
    """Answer every item in ``items`` with ``engine``, returning record rows ready for
    ``biased_decisions.record.write_record``. Never called by ``bd list``/``build``/``score``/
    ``replay``/``report`` -- this is what a future ``bd answer`` run (with a key or a GPU
    available) would call after ``preflight`` passes.
    """
    adapter = _engine_factory(engine)
    rows: List[dict] = []
    for item in items:
        started = time.perf_counter()
        answers = await adapter.answer(item.text, questions)
        rows.append({
            "id": item.id,
            "model": getattr(adapter, "name", engine),
            "usage": None,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
            "answers": answers,
        })
    return rows
