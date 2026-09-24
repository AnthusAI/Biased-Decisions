"""Rebuild this task: `python tasks/cfpb-escalate-family/build.py --source <complaints_20200217.csv.zip>`.

All the logic (sampling rule, clauses, checksum) lives in `biased_decisions/cfpb.py`, with its specs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from biased_decisions import cfpb  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(cfpb.main(["family"] + sys.argv[1:]))
