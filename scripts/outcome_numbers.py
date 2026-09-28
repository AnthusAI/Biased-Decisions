#!/usr/bin/env python3
"""
Extract outcome numbers from study files.
Usage: python3 scripts/outcome_numbers.py <file>

Prints one line per (engine, version):
  <study> <engine> n=<n> <version> mean_pts=<mean_pts> ci=[<lo>, <hi>] flip_vs_floor_pct=<x>

For rows without `versions`, prints every top-level numeric field with its name.
"""

import sys
import json
from pathlib import Path

def extract_engine_from_filename(filename: str) -> str:
    """Extract engine name (e.g., 'jev', 'laya', 'kev') from study filename."""
    # Filename is like cfpb-escalate-family-family-status.jsonl
    # We need to read the file to get the engine
    return None  # Will be read from file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/outcome_numbers.py <file>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]
    filepath = Path("studies") / f"{filename}.jsonl"

    if not filepath.exists():
        # Try without .jsonl extension
        filepath = Path("studies") / filename

    if not filepath.exists():
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    study_name = filepath.stem  # Remove .jsonl extension

    # Read and process lines
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}", file=sys.stderr)
                continue

            engine = row.get("engine")
            n = row.get("n")

            if "versions" in row:
                # Rows with versions: print one line per version
                versions = row["versions"]
                for version, data in versions.items():
                    mean_pts = data.get("mean_pts")
                    ci_pts = data.get("ci_pts", [])
                    flip_vs_floor_pct = data.get("flip_vs_floor_pct")

                    if ci_pts:
                        ci_str = f"[{ci_pts[0]}, {ci_pts[1]}]"
                    else:
                        ci_str = "[]"

                    print(f"{study_name} {engine} n={n} {version} mean_pts={mean_pts} ci={ci_str} flip_vs_floor_pct={flip_vs_floor_pct}")
            else:
                # Rows without versions: print all top-level numeric fields
                for key, value in row.items():
                    if isinstance(value, (int, float)):
                        print(f"{study_name} {engine} {key}={value}")

if __name__ == "__main__":
    main()
