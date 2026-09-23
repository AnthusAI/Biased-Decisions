"""The ``bd`` command line: ``list | build | answer | score | replay | report``.

Stub for milestone 1: the package, the data and the ported metrics are in place, but the
command itself -- reading a task's record, scoring it, regenerating ``RESULTS.md`` -- is filled
in next. See the design doc's "Commands" section for what each subcommand will do.
"""
from __future__ import annotations

import sys


def main(argv=None) -> int:
    print(
        "bd: not yet implemented in this milestone. See the design doc's 'Commands' section "
        "(list | build | answer | score | replay | report).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
