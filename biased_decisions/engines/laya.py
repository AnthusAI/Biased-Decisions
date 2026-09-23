"""Laya: the original upstream package, as released (github.com/NandhaKishorM/laya,
Apache-2.0, ``pip install laya``, PyTorch, CPU or MPS).

Distinct from ``biased_decisions.engines.laya_mlx``, which talks to ``laya-mlx``, the independent
Apple-silicon *port* every number published before 2026-09-23 actually came from. This module is
the canonical ``laya`` engine (see the design doc's "Milestone 1b" section for why the names
split): the model as released, not a conversion of it.

The upstream package is imported lazily -- only inside ``_load_laya`` -- so the rest of this
module, and everything that only reads the committed record, works without it installed. Nothing
in this module is called during milestone-1 replay; the record for every ``(laya, task,
gender-pronouns)`` cell is already committed under ``answers/laya/``.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Sequence

DEFAULT_QUESTION_NAME = "Occupation"


def _load_laya():
    """Import the upstream package. Lazy so importing this module never requires it."""
    try:
        import laya
    except ImportError as error:  # pragma: no cover - exercised only without the package
        raise ImportError(
            "Running the upstream Laya needs the 'laya' package "
            "(pip install 'biased-decisions[laya]')."
        ) from error
    return laya


def build_question(instructions: str, options: Sequence[str]) -> Dict[str, Any]:
    """The wire question the upstream package's ``system_one`` expects for one choice question:
    ``criteria`` is a dict mapping each of the task's ordered options to itself, matching the
    design doc's Milestone 1b description of the call
    (``laya.load()`` then ``model.system_one(state=text, questions=Q)``).
    """
    return {"type": "choice", "instructions": instructions,
            "criteria": {option: option for option in options}}


class LayaUpstreamClient:
    """Loads the upstream checkpoint once (``laya.load()``) and answers through its own
    ``system_one``. One dedicated instance per process is enough -- the package is not
    thread-hostile the way ``laya-mlx``'s MLX arrays are, so no worker thread is needed here.
    """

    def __init__(self, *, model: Any = None):
        self._model = model

    def _load(self):
        if self._model is None:
            laya = _load_laya()
            self._model = laya.load()
        return self._model

    @property
    def version(self) -> str:
        """The installed package's version, used in the record's ``model`` field
        (``laya-upstream:<version>``)."""
        laya = _load_laya()
        return getattr(laya, "__version__", "unknown")

    def system_one(self, *, state: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        """One request: ``model.system_one(state=text, questions=Q)``. Returns the row's
        ``answers`` mapping, plus ``usage`` and ``latency_ms`` if the package's own response
        carries them (it is timed here regardless, so a package that omits ``latency_ms``
        still gets an honest one)."""
        model = self._load()
        started = time.perf_counter()
        result = model.system_one(state=state, questions=dict(questions))
        latency_ms = (time.perf_counter() - started) * 1000.0
        answers = result.get("answers", result)
        return {
            "answers": answers,
            "usage": result.get("usage"),
            "latency_ms": result.get("latency_ms", round(latency_ms, 2)),
        }


class LayaEngine:
    """Adapts ``LayaUpstreamClient`` to ``biased_decisions.engines.base.Engine``."""

    name = "laya"

    def __init__(self, client: "LayaUpstreamClient | None" = None):
        self._client = client or LayaUpstreamClient()

    async def answer(self, text: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, dict]:
        response = self._client.system_one(state=text, questions=questions)
        return dict(response["answers"])

    @property
    def model_string(self) -> str:
        """The record's ``model`` field for a row this engine answers: ``laya-upstream:<version>``,
        matching the committed rows in ``import/laya-record/laya/*.jsonl.gz``."""
        return f"laya-upstream:{self._client.version}"

    def answer_row(self, item_id: str, text: str,
                   questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        """The full record row for one item, in the exact shape of the committed upstream
        record: ``{id, model, usage, latency_ms, answers}``."""
        response = self._client.system_one(state=text, questions=questions)
        return {
            "id": item_id,
            "model": self.model_string,
            "usage": response.get("usage"),
            "latency_ms": response.get("latency_ms"),
            "answers": response["answers"],
        }
