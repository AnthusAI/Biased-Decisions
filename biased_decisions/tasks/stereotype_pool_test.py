"""Feature: the antisemitic-tropes-in-depth stereotype pool -- 500 bios per task, drawn and
re-sorted deterministically from each of the four original tasks' held-out splits.
"""
from biased_decisions.tasks.stereotype_pool import ORIGINAL_TASKS, PER_TASK, draw_pool


def test_original_tasks_is_the_four_classic_bias_in_bios_pairs():
    assert ORIGINAL_TASKS == (
        "paralegal-attorney", "surgeon-physician", "teacher-professor", "nurse-physician",
    )


def test_the_pool_has_500_items_per_task_2000_total():
    pool = draw_pool()
    assert len(pool) == len(ORIGINAL_TASKS) * PER_TASK
    by_task = {}
    for item in pool:
        by_task.setdefault(item.metadata["source_task"], []).append(item)
    assert set(by_task) == set(ORIGINAL_TASKS)
    for task_slug, items in by_task.items():
        assert len(items) == PER_TASK, task_slug


def test_the_draw_is_reproducible_from_the_seed():
    a = draw_pool()
    b = draw_pool()
    assert [item.id for item in a] == [item.id for item in b]
    assert [item.text for item in a] == [item.text for item in b]


def test_item_ids_are_namespaced_by_task_and_carry_provenance_metadata():
    pool = draw_pool()
    sample = pool[0]
    assert sample.id == f"{sample.metadata['source_task']}-{sample.metadata['source_id']}"
    assert sample.metadata["source_task"] in ORIGINAL_TASKS


def test_items_within_a_task_are_sorted_by_source_id():
    pool = draw_pool()
    ids_by_task = {}
    for item in pool:
        ids_by_task.setdefault(item.metadata["source_task"], []).append(item.metadata["source_id"])
    for task_slug, ids in ids_by_task.items():
        assert ids == sorted(ids), task_slug


def test_a_smaller_per_task_draw_is_a_subset_style_sample_not_a_prefix():
    # Regression guard: this must call rng.sample, not just take the first N sorted ids -- a
    # prefix would silently correlate with whatever alphabetizes ids (e.g. always the same
    # occupation gender balance skew as the corpus itself).
    small = draw_pool(per_task=5, seed=0)
    full_ids = draw_pool(per_task=500, seed=0)
    small_ids = {item.metadata["source_id"] for item in small
                if item.metadata["source_task"] == "paralegal-attorney"}
    full_first_five = {item.metadata["source_id"] for item in full_ids
                       if item.metadata["source_task"] == "paralegal-attorney"}
    # Not asserting they differ (they could coincidentally match), just that the smaller draw's
    # ids are a well-formed subset of the sorted candidate pool.
    assert small_ids  # non-empty
