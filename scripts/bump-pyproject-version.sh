#!/usr/bin/env bash
# Used by @semantic-release/exec (prepare step) to write the new version
# into pyproject.toml so the Python package version tracks the release.
set -euo pipefail

NEW_VERSION="${1:?Usage: bump-pyproject-version.sh <version>}"

python3 - "$NEW_VERSION" <<'PY'
import re
import sys
from pathlib import Path

new_version = sys.argv[1]
path = Path("pyproject.toml")
text = path.read_text()

updated, count = re.subn(
    r'(?m)^version = "[^"]*"',
    f'version = "{new_version}"',
    text,
    count=1,
)

if count != 1:
    raise SystemExit("Could not find a `version = \"...\"` line in pyproject.toml")

path.write_text(updated)
print(f"pyproject.toml version set to {new_version}")
PY
