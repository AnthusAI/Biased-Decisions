"""The engine protocol every adapter (``jev``, ``laya``, ``laya-mlx``) implements.

An engine answers one typed question about one text and returns a probability per option, in
the record's own row shape (see ``biased_decisions.record``): a dict of question name to
``{"type": ..., "choice": ..., "probabilities": {...}, ...}``. Milestone 1 asks exactly one
question per item ("Occupation"), so ``answer`` takes a single ``questions`` mapping (name ->
question body, matching Jev's own wire shape) and returns the matching ``answers`` mapping --
never a bare probability, so the row keeps every field a record needs (``choice``,
``confidence``, whatever else the engine reports).

This module declares the shape; it imports nothing so that importing it never requires an
engine's own SDK.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Protocol, runtime_checkable


@runtime_checkable
class Engine(Protocol):
    """What ``biased_decisions.tasks`` and ``biased_decisions.record`` need from an engine."""

    name: str

    async def answer(self, text: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, dict]:
        """Answer every question in ``questions`` about ``text``.

        Returns a mapping of question name to that question's answer body, in the shape
        ``biased_decisions.record`` writes to the ``answers`` field of a record row.
        """
        ...
