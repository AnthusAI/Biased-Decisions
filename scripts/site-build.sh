#!/usr/bin/env bash
# The leaderboard's whole build, as AWS Amplify runs it (amplify.yml calls this script) and as
# `make ci` runs it locally. Any failing step stops the build, so nothing is published:
#
#   1. the unit specs (biased_decisions/*_test.py)
#   2. bd replay, which must reproduce the committed studies/ byte for byte (skipped when
#      SITE_SKIP_REPLAY=1: the Amplify deploy skips it; .github/workflows/replay.yml runs it)
#   3. bd report --json: the data file, with the release version and date from the latest tag
#   4. the Astro build into site/dist/, then the build specs (site/test/)
#
# PYTHON names the interpreter with the harness installed (default: .venv/bin/python).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
step() { printf '\n==> %s\n' "$*"; }

step "unit specs"
"$PY" -m pytest -q biased_decisions

if [ "${SITE_SKIP_REPLAY:-0}" != 1 ]; then
  step "replay every cell from the committed record"
  "$PY" -m biased_decisions.cli replay
  git diff --exit-code --stat -- studies/ || { echo "bd replay did not reproduce studies/" >&2; git --no-pager diff --word-diff=plain -U0 -- studies/ | tr ',' '\n' | grep -E '\[-|\{\+' | head -40 >&2; "$PY" -m pip freeze | grep -iE 'numpy|scipy' >&2; exit 1; }
fi

step "leaderboard data"
"$PY" -m biased_decisions.cli report --json --date "$(git log -1 --format=%cs HEAD)"
git diff --stat -- site/data/leaderboard.json || true

step "site"
npm run build --prefix site
npm test --prefix site
