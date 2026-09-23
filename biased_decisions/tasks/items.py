"""Items: one thing to be scored, and the append-only JSONL store that holds them.

Ported from Jev-Flywheel's ``jev_flywheel/items.py``, trimmed to what a replay needs: ``Item``,
``load_items``, and the ``JsonlStore`` that backs it (the inventory notes only these are used by
the bias studies; ``FeedbackItem`` and the label-normalization helpers exist to connect a study
back into Plexus and are out of scope here).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


@dataclass
class Item:
    """One thing to be scored.

    ``identifiers`` is a list of {name, value, url} objects, kept for shape-compatibility with
    Plexus's own vocabulary even though this package never reads it.
    """

    id: str
    text: str
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    identifiers: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def split(self) -> Optional[str]:
        """Which corpus split this item belongs to, if the corpus has splits."""
        value = self.metadata.get("split")
        return str(value) if value is not None else None

    @property
    def reference_label(self) -> Optional[str]:
        """The corpus's own ground-truth label, when there is one."""
        value = self.metadata.get("reference_label")
        return str(value) if value is not None else None


def _from_row(cls, row: Dict[str, Any]):
    """Build a dataclass from a stored row, ignoring fields it does not declare.

    Tolerating unknown keys means an older fixture file still loads after a field is added,
    which matters because fixtures are committed.
    """
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in row.items() if k in known})


def load_items(path: Path) -> List[Item]:
    """Read the item corpus. Items are immutable input, so this is a plain read."""
    return JsonlStore(path, Item).all()


class JsonlStore:
    """An append-only JSONL file of dataclass records."""

    def __init__(self, path: Path, record_type: type):
        self.path = Path(path)
        self.record_type = record_type

    def append(self, record) -> None:
        self.append_all([record])

    def append_all(self, records: Iterable[Any]) -> None:
        rows = [json.dumps(asdict(r), ensure_ascii=False) for r in records]
        if not rows:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(row + "\n")
            handle.flush()

    def __iter__(self) -> Iterator[Any]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    yield _from_row(self.record_type, json.loads(line))

    def all(self) -> List[Any]:
        return list(self)

    def latest_by(self, key: str) -> Dict[Any, Any]:
        """The last record for each distinct value of ``key``."""
        out: Dict[Any, Any] = {}
        for record in self:
            out[getattr(record, key)] = record
        return out
