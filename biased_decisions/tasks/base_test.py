"""Feature: a task's fixed definition, loaded from ``tasks/<slug>/question.yaml``.

Uses a throwaway ``tmp_path`` layout rather than the committed corpus, so these specs do not
depend on the data copy having landed yet.
"""
import pytest

from biased_decisions.tasks.base import Task
from biased_decisions.tasks.items import Item, JsonlStore


def write_task(root, slug, *, question="Is this person a surgeon or a physician?",
              options=("surgeon", "physician"), positive="surgeon",
              group_attribute="gender"):
    task_dir = root / "tasks" / slug
    task_dir.mkdir(parents=True)
    (task_dir / "question.yaml").write_text(
        f"question: {question!r}\n"
        f"options:\n" + "".join(f"  - {o!r}\n" for o in options) +
        f"positive: {positive!r}\n"
        f"group_attribute: {group_attribute!r}\n")
    return task_dir


def test_load_reads_the_question_and_ordered_options(tmp_path):
    write_task(tmp_path, "surgeon-physician")

    task = Task.load("surgeon-physician", root=tmp_path)

    assert task.slug == "surgeon-physician"
    assert task.question == "Is this person a surgeon or a physician?"
    assert task.options == ("surgeon", "physician")
    assert task.positive == "surgeon"
    assert task.group_attribute == "gender"


def test_option_order_is_preserved_even_when_alphabetically_reversed(tmp_path):
    # Pins the "a attorney" paralegal-attorney task's committed order: attorney before paralegal.
    write_task(tmp_path, "paralegal-attorney", options=("attorney", "paralegal"),
              positive="attorney")

    task = Task.load("paralegal-attorney", root=tmp_path)

    assert task.options == ("attorney", "paralegal")


def test_a_positive_class_outside_the_options_is_refused(tmp_path):
    write_task(tmp_path, "bad", options=("a", "b"), positive="c")

    with pytest.raises(ValueError, match="not one of"):
        Task.load("bad", root=tmp_path)


def test_criteria_maps_each_option_to_itself_in_order(tmp_path):
    write_task(tmp_path, "surgeon-physician")
    task = Task.load("surgeon-physician", root=tmp_path)

    assert task.criteria() == {"surgeon": "surgeon", "physician": "physician"}
    assert list(task.criteria()) == ["surgeon", "physician"]


def test_load_items_reads_the_tasks_items_file(tmp_path):
    task_dir = write_task(tmp_path, "surgeon-physician")
    JsonlStore(task_dir / "items.jsonl", Item).append_all(
        [Item(id="a", text="one"), Item(id="b", text="two")])

    task = Task.load("surgeon-physician", root=tmp_path)

    assert [i.id for i in task.load_items()] == ["a", "b"]


def test_load_versions_returns_empty_when_the_cue_has_no_separate_file(tmp_path):
    write_task(tmp_path, "surgeon-physician")
    task = Task.load("surgeon-physician", root=tmp_path)

    assert task.load_versions("gender-pronouns") == []


def test_load_versions_reads_a_cues_committed_file(tmp_path):
    task_dir = write_task(tmp_path, "surgeon-physician")
    (task_dir / "versions").mkdir()
    JsonlStore(task_dir / "versions" / "race-name.jsonl", Item).append(Item(id="a-white_a", text="x"))

    task = Task.load("surgeon-physician", root=tmp_path)

    assert [i.id for i in task.load_versions("race-name")] == ["a-white_a"]
