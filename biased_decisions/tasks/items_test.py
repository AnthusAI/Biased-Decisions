"""Feature: items and the append-only store that holds them.

Ported from the relevant parts of Jev-Flywheel's ``jev_flywheel/items_test.py`` (the part that
exercises ``FeedbackItem`` and label normalization is out of scope here -- see ``items.py``'s
docstring).
"""
from biased_decisions.tasks.items import Item, JsonlStore, load_items


def test_an_item_exposes_its_split_and_reference_label_from_metadata():
    item = Item(id="a", text="x", metadata={"split": "test", "reference_label": "positive"})
    assert item.split == "test"
    assert item.reference_label == "positive"


def test_an_item_without_corpus_metadata_has_neither():
    item = Item(id="a", text="x")
    assert item.split is None
    assert item.reference_label is None


def test_the_store_round_trips_records(tmp_path):
    store = JsonlStore(tmp_path / "items.jsonl", Item)
    store.append(Item(id="a", text="hello"))
    store.append(Item(id="b", text="world"))

    loaded = store.all()

    assert [i.id for i in loaded] == ["a", "b"]
    assert loaded[0].text == "hello"


def test_a_store_that_does_not_exist_yet_reads_as_empty(tmp_path):
    assert JsonlStore(tmp_path / "missing.jsonl", Item).all() == []


def test_a_later_record_supersedes_an_earlier_one_for_the_same_key(tmp_path):
    store = JsonlStore(tmp_path / "items.jsonl", Item)
    store.append(Item(id="a", text="first"))
    store.append(Item(id="a", text="second"))

    latest = store.latest_by("id")

    assert len(latest) == 1
    assert latest["a"].text == "second"


def test_stored_rows_with_unknown_fields_still_load(tmp_path):
    # Fixtures are committed, so an older file has to survive a new field.
    path = tmp_path / "items.jsonl"
    path.write_text('{"id": "a", "text": "hi", "from_the_future": 1}\n')

    loaded = JsonlStore(path, Item).all()

    assert loaded[0].id == "a"


def test_load_items_reads_a_jsonl_file(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_text('{"id": "a", "text": "one"}\n{"id": "b", "text": "two"}\n')

    items = load_items(path)

    assert [i.id for i in items] == ["a", "b"]
