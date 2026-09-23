"""Feature: the Bias in Bios tasks and the test/twin split every milestone-1 task's
``items.jsonl`` carries.
"""
import pytest

from biased_decisions.tasks.bios import BIOS_TASKS, load_task, split_test_and_twins
from biased_decisions.tasks.items import Item


def test_bios_tasks_lists_the_four_milestone_1_pairs():
    assert BIOS_TASKS == (
        "surgeon-physician", "nurse-physician", "teacher-professor", "paralegal-attorney")


def test_load_task_refuses_a_slug_outside_the_bios_family():
    with pytest.raises(ValueError, match="not one of"):
        load_task("architect-interior-designer")


def test_items_and_twins_splits_test_bios_from_their_counterfactual_twins():
    items = [
        Item(id="a", text="He is a surgeon.", metadata={"split": "test"}),
        Item(id="a-swapped", text="She is a surgeon.",
            metadata={"split": "counterfactual", "counterfactual_of": "a"}),
        Item(id="b", text="No pronoun here.", metadata={"split": "test"}),
        # "b" has no twin: the swap found no subject pronoun to flip.
        Item(id="pool-1", text="An unlabeled pool bio.", metadata={"split": "pool"}),
    ]

    test_items, twins = split_test_and_twins(items)

    assert [i.id for i in test_items] == ["a", "b"]
    assert set(twins) == {"a"}
    assert twins["a"].id == "a-swapped"
