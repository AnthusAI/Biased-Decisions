from biased_decisions.subsample import SEED, family_id, subsample
from biased_decisions.tasks.base import Item


def item(item_id, **metadata):
    return Item(id=item_id, text=item_id, metadata=metadata)


def bios(n):
    """n originals, each with a twin and an edited version, the way the gender and religion cells carry them."""
    out = []
    for i in range(n):
        out.append(item(f"bios-{i:06d}", split="test"))
        out.append(item(f"bios-{i:06d}-swapped", split="counterfactual", counterfactual_of=f"bios-{i:06d}"))
        out.append(item(f"bios-{i:06d}-religion-jewish", source_id=f"bios-{i:06d}"))
    return out


def test_an_item_and_its_twin_and_edits_are_one_family():
    assert family_id(item("bios-000007"), "surgeon-physician") == "bios-000007"
    assert family_id(item("bios-000007-swapped", counterfactual_of="bios-000007"), "surgeon-physician") == "bios-000007"
    assert family_id(item("bios-000007-religion-jewish", source_id="bios-000007"), "surgeon-physician") == "bios-000007"


def test_a_task_prefixed_source_id_is_the_same_family_as_the_bare_one():
    prefixed = item("x", source_id="surgeon-physician-bios-000381", source_task="surgeon-physician")
    assert family_id(prefixed, "surgeon-physician") == "bios-000381"
    assert family_id(prefixed, "surgeon-physician") == family_id(item("y", source_id="bios-000381"), "surgeon-physician")


def test_no_cap_keeps_everything_and_a_large_cap_keeps_everything():
    items = bios(5)
    assert subsample(items, "surgeon-physician", None) == items
    assert subsample(items, "surgeon-physician", 5) == items
    assert subsample(items, "surgeon-physician", 500) == items


def test_a_cap_keeps_whole_families_in_the_original_order():
    items = bios(20)
    kept = subsample(items, "surgeon-physician", 4)
    assert len(kept) == 12
    assert [i for i in items if i in kept] == kept
    families = {family_id(i, "surgeon-physician") for i in kept}
    assert len(families) == 4
    assert all(family_id(i, "surgeon-physician") in families for i in kept)
    assert sum(1 for i in items if family_id(i, "surgeon-physician") in families) == len(kept)


def test_the_sample_is_nested_so_growing_the_cap_only_adds_families():
    items = bios(50)
    small = {family_id(i, "nurse-physician") for i in subsample(items, "nurse-physician", 10)}
    large = {family_id(i, "nurse-physician") for i in subsample(items, "nurse-physician", 25)}
    assert small < large


def test_every_cue_of_a_task_draws_the_same_families():
    edit_cell = bios(50)
    control_cell = [i for i in bios(50) if i.metadata.get("split") == "test"][::-1]
    a = {family_id(i, "nurse-physician") for i in subsample(edit_cell, "nurse-physician", 10)}
    b = {family_id(i, "nurse-physician") for i in subsample(control_cell, "nurse-physician", 10)}
    assert a == b


def test_the_choice_does_not_depend_on_any_answer_or_item_text_and_depends_on_the_task():
    items = bios(50)
    reworded = [Item(id=i.id, text="something else", metadata=i.metadata) for i in items]
    assert [i.id for i in subsample(items, "nurse-physician", 10)] == \
           [i.id for i in subsample(reworded, "nurse-physician", 10)]
    assert {i.id for i in subsample(items, "nurse-physician", 10)} != \
           {i.id for i in subsample(items, "teacher-professor", 10)}


def test_the_registered_seed_is_the_one_in_the_preregistration():
    assert SEED == "biased-decisions-subsample-1"
    text = open("docs/subsample-preregistration.md", encoding="utf-8").read()
    assert SEED in text


def test_a_cap_below_one_is_refused():
    import pytest
    with pytest.raises(ValueError):
        subsample(bios(3), "nurse-physician", 0)
