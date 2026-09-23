"""A task: a corpus, one choice question, a positive class, and the group attribute used for
recall gaps.

``question.yaml`` (see the design doc) carries the question text and its **ordered** options --
option order is part of a task, because Jev's own probabilities are keyed by option label but a
shortlist or a four-fifths ratio can depend on how ties break, so the order a record was built
under has to be reproducible from the committed file, not just implied by dict iteration.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from biased_decisions.tasks.items import Item, load_items

# repo root: biased_decisions/tasks/base.py -> tasks -> biased_decisions -> repo root.
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Task:
    """A task's fixed definition, loaded from ``tasks/<slug>/question.yaml``.

    ``options`` is ordered exactly as the file lists it; a caller that needs Jev's/Laya's wire
    ``criteria`` should build it from ``options`` (not from ``set(options)`` or a dict), so the
    option order a record was answered under is always reproducible from this file.
    """

    slug: str
    question: str
    options: Tuple[str, ...]
    positive: str
    group_attribute: str
    root: Path = DEFAULT_ROOT

    @classmethod
    def load(cls, slug: str, *, root: Optional[Path] = None) -> "Task":
        root = Path(root) if root is not None else DEFAULT_ROOT
        path = root / "tasks" / slug / "question.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        options = tuple(data["options"])
        if data["positive"] not in options:
            raise ValueError(
                f"{path}: positive class {data['positive']!r} is not one of {options!r}")
        return cls(slug=slug, question=data["question"], options=options,
                   positive=data["positive"], group_attribute=data["group_attribute"], root=root)

    @property
    def dir(self) -> Path:
        return self.root / "tasks" / self.slug

    @property
    def items_path(self) -> Path:
        return self.dir / "items.jsonl"

    def load_items(self) -> List[Item]:
        """Every item this task's corpus carries: the held-out test bios, their pooled
        (unlabeled) siblings if any, and any counterfactual twins committed alongside them in
        ``items.jsonl`` (see ``versions_path`` for a cue whose versions live in a separate
        file instead)."""
        return load_items(self.items_path)

    def versions_dir(self) -> Path:
        return self.dir / "versions"

    def versions_path(self, cue: str) -> Path:
        """Where a cue's *separately built* versions file lives, e.g. ``race-name.jsonl``.

        Not every cue needs one: the ``gender-pronouns`` twins for every milestone-1 task are
        committed inside ``items.jsonl`` itself (id suffix ``-swapped``, ``metadata.split ==
        "counterfactual"``, ``metadata.counterfactual_of`` pointing back at the original id) --
        see ``data/MANIFEST.md`` for why that choice was made instead of a redundant copy.
        """
        return self.versions_dir() / f"{cue}.jsonl"

    def load_versions(self, cue: str) -> List[Item]:
        """The versions file for a cue that has one; ``[]`` if the cue's versions live inside
        ``items.jsonl`` instead (see ``versions_path``)."""
        path = self.versions_path(cue)
        if not path.exists():
            return []
        return load_items(path)

    def criteria(self) -> dict:
        """The wire ``criteria`` an engine's choice question expects: each option mapped to
        itself, in the task's own order."""
        return {option: option for option in self.options}
