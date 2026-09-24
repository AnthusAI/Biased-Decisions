"""The two Laya builds an answer runner can use, and what each writes into a record.

``laya``     the original PyTorch package (``laya`` on PyPI); records go to ``answers/laya/``.
``laya-mlx`` the Apple-silicon MLX port (``laya-mlx``); records go to ``answers/laya-mlx/``.

Both answer the same questions and give the same headline results (on a single text their
probabilities can differ by up to about 0.02: docs/mlx-runner.md), so a runner picks a build with ``--build`` and everything else (question shapes, row shape, resume
files) is identical. The ``model`` string in every row names the build and its installed
version, so a record says which software produced it.
"""
from __future__ import annotations

from importlib import metadata
from typing import Any, Dict, Mapping

BUILDS = ("laya", "laya-mlx")
DEFAULT_BUILD = "laya"
# What each build writes in a record row's ``model`` field, before ``:<version>``.
_MODEL_PREFIX = {"laya": "laya-upstream", "laya-mlx": "laya-mlx"}
_DISTRIBUTION = {"laya": "laya", "laya-mlx": "laya-mlx"}
_PINNED = {"laya": "0.3.7", "laya-mlx": "0.1.0"}


def check_build(build: str) -> str:
    if build not in BUILDS:
        raise ValueError(f"unknown build {build!r}; choose one of {', '.join(BUILDS)}")
    return build


def build_version(build: str) -> str:
    """The installed version of the build's package; the pinned one if it is not installed."""
    try:
        return metadata.version(_DISTRIBUTION[check_build(build)])
    except metadata.PackageNotFoundError:
        return _PINNED[build]


def model_tag(build: str, version: str | None = None) -> str:
    """The record's ``model`` field: ``laya-upstream:0.3.7`` or ``laya-mlx:0.1.0``."""
    check_build(build)
    return f"{_MODEL_PREFIX[build]}:{version or build_version(build)}"


class MlxModel:
    """A laya-mlx agent behind the same synchronous ``system_one(state, questions)`` the
    upstream model has, so the many-question runner treats both builds alike.

    Applies the harness's own guards from ``laya_mlx.py``: unwraps a ``{"text": ...}`` state,
    converts questions, and refuses anything the 512-token window would silently truncate.
    """

    def __init__(self, agent: Any = None, *, check=None):
        self._agent = agent
        self._check = check

    def _load(self):
        if self._agent is None:
            import laya_mlx
            from biased_decisions.engines.laya_mlx import DEFAULT_CHECKPOINT
            self._agent = laya_mlx.load(DEFAULT_CHECKPOINT)
        return self._agent

    def system_one(self, state: Any, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        from biased_decisions.engines import laya_mlx as mlx
        agent = self._load()
        state = mlx.to_laya_state(state)
        wire = {name: mlx.to_laya_question(q) for name, q in questions.items()}
        (self._check or mlx.check_budget)(agent, state, wire)
        return agent.system_one(state, wire)


def load_model(build: str):
    """A model with ``system_one(state, questions)`` for the build (heavy imports happen here)."""
    if check_build(build) == "laya-mlx":
        return MlxModel()
    import laya
    return laya.load()


def load_engine(build: str):
    """An async ``Engine`` for the single-question runner."""
    if check_build(build) == "laya-mlx":
        from biased_decisions.engines.laya_mlx import LayaMlxEngine
        return LayaMlxEngine()
    from biased_decisions.engines.laya import LayaEngine
    return LayaEngine()
