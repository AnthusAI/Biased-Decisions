"""Deterministic, resumable collection for registered task/cue definitions."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
import gzip
import hashlib
import json
import os
import time
import yaml
from pathlib import Path
from typing import Any, Mapping

from biased_decisions.engines.laya import build_question
from biased_decisions.record import read_record, record_path
from biased_decisions.tasks.base import DEFAULT_ROOT, Task
from biased_decisions.tasks.bios import BIOS_TASKS
from biased_decisions.tasks.items import Item


class CollectionError(RuntimeError):
    pass


class CollectorDefinition:
    """One registered task's single-choice or explicitly supported multi-noul contract."""

    def __init__(self, slug: str, root: Path, *, task: Task | None = None,
                 questions: Mapping[str, Mapping] | None = None):
        self.slug, self.root, self._task = slug, root, task
        self.questions = dict(questions) if questions is not None else None
        if task is not None:
            self.question, self.options = task.question, task.options
        else:
            self.question, self.options = "", ()

    def versions_dir(self):
        return self.root / "tasks" / self.slug / "versions"

    def versions_path(self, cue):
        return self.versions_dir() / f"{cue}.jsonl"

    def load_items(self):
        from biased_decisions.tasks.items import load_items
        return load_items(self.root / "tasks" / self.slug / "items.jsonl")

    def load_versions(self, cue):
        from biased_decisions.tasks.items import load_items
        path = self.versions_path(cue)
        return load_items(path) if path.exists() else []


def load_definition(root: Path, slug: str) -> CollectorDefinition:
    path = Path(root) / "tasks" / slug / "question.yaml"
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CollectionError(f"task definition does not exist: {path}") from error
    # Explicit multi-question schema used by the registered stereotype task. Do not guess at
    # arbitrary alternative task formats: unsupported schemas fail with a direct message.
    if isinstance(raw, Mapping) and "questions" in raw and "options" not in raw:
        definitions = raw["questions"]
        if not isinstance(definitions, Mapping) or not definitions:
            raise CollectionError(f"{path}: questions must be a non-empty mapping")
        questions = {}
        for name, spec in definitions.items():
            if not isinstance(spec, Mapping) or not isinstance(spec.get("question"), str):
                raise CollectionError(f"{path}: question {name!r} needs a question string")
            if "trope_consistent_answer" not in spec or "trope" not in spec:
                raise CollectionError(f"{path}: unsupported multi-question definition {name!r}")
            questions[name] = {"type": "noul", "instructions": spec["question"]}
        return CollectorDefinition(slug, Path(root), questions=questions)
    if not isinstance(raw, Mapping) or not {"question", "options", "positive"} <= set(raw):
        raise CollectionError(f"{path}: unsupported task definition schema")
    return CollectorDefinition(slug, Path(root), task=Task.load(slug, root=root))


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _items(task: Task, cue: str) -> list[Item]:
    if cue == "as-written":
        if task.questions is not None:
            return task.load_items()
        return [i for i in task.load_items() if i.metadata.get("split") == "test"]
    if cue == "gender-pronouns":
        return [i for i in task.load_items() if i.metadata.get("split") in ("test", "counterfactual")]
    if cue in ("option-order-reversed", "option-order-reversed-twins"):
        test_ids = {i.id for i in task.load_items() if i.metadata.get("split") == "test"}
        if cue == "option-order-reversed-twins":
            return [i for i in task.load_items()
                    if i.metadata.get("split") == "counterfactual" and
                    i.metadata.get("counterfactual_of") in test_ids]
        return [i for i in task.load_items()
                if i.metadata.get("split") == "test"]
    if cue == "ask-twice":
        selection = task.versions_dir() / "ask-twice.txt"
        if not selection.exists():
            raise CollectionError("ask-twice requires the committed versions/ask-twice.txt selection")
        selected = [line.strip() for line in selection.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
        if len(selected) != len(set(selected)):
            raise CollectionError("ask-twice selection contains duplicate item ids")
        by_id = {i.id: i for i in task.load_items()}
        missing = [item_id for item_id in selected if item_id not in by_id]
        if missing:
            raise CollectionError(f"ask-twice selection references missing ids: {missing[:3]}")
        return [by_id[item_id] for item_id in selected]
    # Any task's registered version files are authoritative inputs, including newly added
    # decision tasks and regulated-study arms. This avoids maintaining a second cue inventory.
    version_path = task.versions_path(cue)
    if version_path.exists():
        return task.load_versions(cue)
    raise CollectionError(f"unsupported or uncommitted cue/experiment {cue!r}; commit its task versions first")


def _questions(task: Task, cue: str, question_name: str) -> dict:
    if task.questions is not None:
        if cue.startswith("option-order-reversed"):
            raise CollectionError("option-order reversal is not supported for multi-noul tasks")
        return dict(task.questions)
    options = tuple(reversed(task.options)) if cue in (
        "option-order-reversed", "option-order-reversed-twins") else task.options
    return {question_name: build_question(task.question, options)}


def collect(root: Path = DEFAULT_ROOT, engine_name: str = "kev", task_slug: str = "",
            cue: str = "", *, engine: Any = None, model: str | None = None,
            provenance: Mapping | None = None, question_name: str | None = None,
            dry_run: bool = False, max_new_items: int | None = None,
            progress: bool = True) -> dict:
    """Collect one cell. ``dry_run`` only reads definitions and existing files."""
    if max_new_items is not None and max_new_items < 1:
        raise ValueError("max_new_items must be positive")
    root = Path(root)
    task = load_definition(root, task_slug)
    items = _items(task, cue)
    qname = question_name or ("Occupation" if task_slug in BIOS_TASKS else "Decision")
    questions = _questions(task, cue, qname)
    path = record_path(engine_name, task_slug, cue, root=root)
    partial = path.with_name(path.name + ".partial.jsonl")
    manifest_path = path.with_name(path.name + ".metadata.json")
    planned_ids = [i.id for i in items]
    if len(planned_ids) != len(set(planned_ids)):
        raise CollectionError("planned inputs contain duplicate item ids")
    definition_path = root / "tasks" / task_slug / "question.yaml"
    raw_definition = yaml.safe_load(definition_path.read_text(encoding="utf-8"))
    input_hash = _fingerprint({"task": task_slug, "cue": cue,
                               "definition": raw_definition,
                               "items": [asdict(i) for i in items],
                               "questions": questions, "ordered_options": list(
                                   reversed(task.options) if cue.startswith("option-order-reversed")
                                   else task.options),
                               "ordered_question_names": list(questions)})
    provenance = dict(provenance if provenance is not None else
                      (getattr(engine, "provenance_data", None) or {}))
    saved_manifest = None
    if manifest_path.exists():
        saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if dry_run and engine is None and saved_manifest:
        if model is None:
            model = saved_manifest.get("model")
        if provenance is None or not provenance:
            provenance = saved_manifest.get("provenance", {})
    current_model = model or getattr(engine, "model_name", None) or getattr(engine, "name", engine_name)
    manifest = {"engine": engine_name, "model": current_model,
                "input_fingerprint": input_hash, "provenance": provenance}
    if path.exists():
        rows = read_record(path)
        if not manifest_path.exists():
            raise CollectionError("completed record has no metadata manifest; refusing unsafe reuse")
        saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if saved_manifest.get("input_fingerprint") != input_hash:
            raise CollectionError("completed record inputs do not match current task/cue")
        if not dry_run and saved_manifest != manifest:
            raise CollectionError("completed record model or provenance does not match request")
        allowed_models = {saved_manifest.get("model")}
        allowed_models.update(saved_manifest.get("provenance", {}).get(key)
                              for key in ("model", "checkpoint"))
        if any(row.get("model") not in allowed_models for row in rows):
            raise CollectionError("completed record rows do not match its model provenance")
        if len(rows) != len(items) or [r["id"] for r in rows] != [i.id for i in items]:
            raise CollectionError("completed record does not exactly cover the current ordered inputs")
        return {"path": path, "total": len(items), "pending": 0, "complete": True}

    existing: dict[str, dict] = {}
    if partial.exists():
        try:
            with partial.open(encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)
                    if row["id"] in existing:
                        raise CollectionError(f"duplicate partial record id {row['id']!r}")
                    existing[row["id"]] = row
        except CollectionError:
            raise
        except Exception as e:
            raise CollectionError("partial record is corrupt; refusing to discard it") from e
    expected_ids = planned_ids
    expected_id_set = set(expected_ids)
    if any(item_id not in expected_id_set for item_id in existing):
        raise CollectionError("partial record contains ids outside the current inputs")
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior.get("input_fingerprint") != input_hash:
            raise CollectionError("partial collection inputs changed")
        if not dry_run and prior != manifest:
            raise CollectionError("partial collection inputs, model, or provenance changed")
    elif existing:
        raise CollectionError("partial rows have no metadata manifest; refusing unsafe resume")
    accepted_row_models = {current_model}
    if provenance.get("model"):
        accepted_row_models.add(provenance["model"])
    if provenance.get("checkpoint"):
        accepted_row_models.add(provenance["checkpoint"])
    if any(row.get("model") not in accepted_row_models for row in existing.values()):
        raise CollectionError("partial record rows do not match the current model identity")
    if dry_run:
        return {"path": path, "total": len(items), "pending": sum(i.id not in existing for i in items),
                "complete": False}
    if engine is None:
        raise CollectionError("an engine instance is required to collect")
    if engine_name == "kev":
        from biased_decisions.engines.kev import KevEngine
        if isinstance(engine, KevEngine):
            required_provenance = ("checkpoint", "base_revision", "server_revision", "backend",
                                   "dtype", "calibration")
            missing = [key for key in required_provenance if not provenance.get(key)]
            if missing:
                raise CollectionError(f"Kev collection requires pinned provenance fields: {missing}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temp_manifest.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_manifest, manifest_path)
    partial.parent.mkdir(parents=True, exist_ok=True)
    run_started = time.perf_counter()
    new_count = 0
    with partial.open("a", encoding="utf-8") as output:
        for item in items:
            if item.id in existing:
                continue
            if max_new_items is not None and new_count >= max_new_items:
                break
            started = time.perf_counter()
            answers = asyncio.run(engine.answer(item.text, questions))
            row = {"id": item.id,
                   "model": getattr(engine, "model", None) or current_model,
                   "usage": getattr(engine, "usage", None),
                   "latency_ms": getattr(engine, "latency_ms", None) or
                       round((time.perf_counter() - started) * 1000.0, 2),
                   "answers": answers}
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            os.fsync(output.fileno())
            existing[item.id] = row
            new_count += 1
            if progress and new_count % 100 == 0:
                elapsed = time.perf_counter() - run_started
                print(f"{new_count} new items answered; {sum(i.id not in existing for i in items)} pending; "
                      f"{elapsed:.1f}s elapsed")
    pending = sum(i.id not in existing for i in items)
    if pending:
        return {"path": path, "total": len(items), "pending": pending,
                "complete": False, "new_items": new_count}
    ordered_rows = [existing[item_id] for item_id in expected_ids]
    temp_path = path.with_name(path.name + ".tmp")
    with gzip.open(temp_path, "wt", encoding="utf-8") as output:
        for row in ordered_rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temp_path, path)
    partial.unlink(missing_ok=True)
    return {"path": path, "total": len(items), "pending": 0, "complete": True}
