.PHONY: install test replay report leaderboard serve check

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Create the venv and install the package (dev + build extras) into it. Re-run safely --
# pip install is idempotent.
install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e '.[dev]'

test:
	$(PY) -m pytest

# Score every (engine, task, cue) cell that has a committed record, including the shortlist
# block, into studies/<task>-<cue>.jsonl / studies/<task>-shortlist.jsonl. Calls no engine --
# every number comes from the committed answers/ record.
replay:
	$(PY) -m biased_decisions.cli replay

report:
	$(PY) -m biased_decisions.cli report

# The leaderboard's data file, site/data/leaderboard.json. DATE defaults to the last commit's
# date so the file is deterministic for a given commit.
DATE ?= $(shell git log -1 --format=%cs)
leaderboard:
	$(PY) -m biased_decisions.cli report --json --date $(DATE)

# Serve the static site locally (any static server works; it must be HTTP, not file://).
PORT ?= 8000
serve:
	cd site && python3 -m http.server $(PORT)

# The full offline check: replay every cell, regenerate RESULTS.md, then the regression test
# that every replayed number still matches Jev-Flywheel's published studies.
check: replay report
	$(PY) -m pytest tests/replay_test.py -v
