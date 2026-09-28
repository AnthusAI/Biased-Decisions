from biased_decisions.collector import _items
from biased_decisions.tasks.items import Item


class Task:
    questions = None

    def __init__(self, items):
        self.items = items

    def load_items(self):
        return self.items


def test_as_written_uses_all_registered_items_when_no_split_is_defined():
    items = [
        Item(id="one", text="First", metadata={"status": "No name"}),
        Item(id="two", text="Second", metadata={"status": "Decision requested for: Tova"}),
    ]

    assert _items(Task(items), "as-written") == items


def test_as_written_keeps_the_test_partition_for_split_tasks():
    train = Item(id="train", text="Train", metadata={"split": "train"})
    test = Item(id="test", text="Test", metadata={"split": "test"})

    assert _items(Task([train, test]), "as-written") == [test]
