.PHONY: install test replay report leaderboard site dev serve ci check copy-check

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

# The static site (site/, Astro): every page generated from site/data/leaderboard.json.
# `make site` builds it into site/dist/ and runs the build specs; `make dev` serves the source
# with live reload on PORT; `make serve` serves the built output on PREVIEW_PORT with the same
# redirects, 404s and headers as AWS Amplify (deploy/amplify-rules.json, customHttp.yml).
PORT ?= 4321
PREVIEW_PORT ?= 4323
site/node_modules: site/package-lock.json
	cd site && npm ci --no-fund --no-audit
	touch site/node_modules

site: site/node_modules
	cd site && npm run build && npm test

copy-check: site/node_modules
	cd site && npm run build
	$(PY) scripts/scan_copy.py

dev: site/node_modules
	cd site && npx astro dev --port $(PORT)

serve:
	node site/scripts/serve.mjs $(PREVIEW_PORT)

# Everything the Amplify build runs (amplify.yml): unit specs, the replay check, the data file,
# the site and its build specs. Stops at the first failure.
ci: site/node_modules
	PYTHON=$(PY) bash scripts/site-build.sh

# The full offline check: replay every cell, regenerate RESULTS.md, then the regression test
# that every replayed number still matches Jev-Flywheel's published studies.
check: replay report
	$(PY) -m pytest tests/replay_test.py -v
