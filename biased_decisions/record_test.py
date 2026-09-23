"""Feature: the answer record -- read/write of ``answers/<engine>/<task>/<cue>.jsonl.gz``."""
import pytest

from biased_decisions.record import (
    new_path_for_old, read_record, read_record_by_id, record_path, write_record)


def test_record_path_follows_the_design_scheme(tmp_path):
    path = record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)
    assert path == tmp_path / "answers" / "jev" / "surgeon-physician" / "gender-pronouns.jsonl.gz"


def test_read_record_of_a_missing_file_is_empty(tmp_path):
    path = record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)
    assert read_record(path) == []


def test_write_then_read_round_trips_rows(tmp_path):
    path = record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)
    rows = [
        {"id": "a", "model": "jev-1.13.0", "usage": {"input_tokens": 10}, "latency_ms": 1.0,
         "answers": {"Occupation": {"choice": "surgeon"}}},
        {"id": "b", "model": "jev-1.13.0", "usage": {"input_tokens": 12}, "latency_ms": 2.0,
         "answers": {"Occupation": {"choice": "physician"}}},
    ]

    write_record(path, rows)

    assert [row["id"] for row in read_record(path)] == ["a", "b"]
    by_id = read_record_by_id(path)
    assert by_id["a"]["answers"]["Occupation"]["choice"] == "surgeon"


def test_write_record_refuses_a_row_missing_a_required_field(tmp_path):
    path = record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)
    with pytest.raises(ValueError, match="missing"):
        write_record(path, [{"id": "a", "model": "jev"}])


def test_append_adds_rows_without_discarding_what_was_there(tmp_path):
    path = record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)
    write_record(path, [{"id": "a", "model": "m", "usage": None, "latency_ms": 1.0,
                         "answers": {}}])
    write_record(path, [{"id": "b", "model": "m", "usage": None, "latency_ms": 1.0,
                         "answers": {}}], append=True)

    assert [row["id"] for row in read_record(path)] == ["a", "b"]


def test_new_path_for_old_maps_a_known_jev_flywheel_file(tmp_path):
    path = new_path_for_old("fixtures/bios/answers.jsonl.gz", root=tmp_path)
    assert path == record_path("jev", "surgeon-physician", "gender-pronouns", root=tmp_path)


def test_new_path_for_old_maps_the_upstream_laya_record():
    path = new_path_for_old("laya-record/laya/surgeon-physician--gender-pronouns.jsonl.gz")
    assert path.parts[-3:] == ("laya", "surgeon-physician", "gender-pronouns.jsonl.gz")


def test_new_path_for_old_refuses_an_unmapped_path():
    with pytest.raises(KeyError):
        new_path_for_old("fixtures/bios/answers-nonsense.jsonl.gz")
