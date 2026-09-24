"""Read the built site's pages as prose and check them with Limatus against writing/style-profile.yml.

    make copy-check            # builds the site, then scans every page in writing/pages.txt
    python scripts/scan_copy.py --pages / /methods/

Each page's readable text (headings and paragraphs; no tables of numbers, charts or code) is written
to var/copy/<page>.md and scanned. Limatus reports findings; it never rewrites anything. A finding
is a question for a person: skip it, rewrite it, delete it or keep it (see writing/README.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "site" / "dist"
OUT = ROOT / "var" / "copy"
PROFILE = ROOT / "writing" / "style-profile.yml"
PAGES = ROOT / "writing" / "pages.txt"
FINDING_LISTS = ("generic_passages", "unsupported_claims", "repetition_groups", "voice_observations")
# Limatus is developed in ../Limatus; the profile uses keys newer than some installed releases, so
# prefer that checkout (override with LIMATUS_SRC) and fall back to whatever `limatus` is installed.
LIMATUS_SRC = Path(os.environ.get("LIMATUS_SRC", ROOT.parent / "Limatus" / "src"))

SKIP = {"script", "style", "svg", "code", "pre", "table", "nav", "footer", "head", "header", "noscript", "button"}
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "dd", "dt", "figcaption", "blockquote", "summary"}
HEADING = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### "}


class Prose(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth_skip = 0
        self.stack: list[tuple[str, bool]] = []
        self.buf: list[str] = []
        self.lines: list[str] = []

    def handle_starttag(self, tag, attrs):
        skip = tag in SKIP or (tag == "a" and "skip" in (dict(attrs).get("class") or ""))
        if skip:
            self.depth_skip += 1
        self.stack.append((tag, skip))
        self.buf.append(" ")

    def handle_endtag(self, tag):
        while self.stack and self.stack[-1][0] != tag:
            _, skipped = self.stack.pop()
            self.depth_skip -= 1 if skipped else 0
        if self.stack:
            _, skipped = self.stack.pop()
            self.depth_skip -= 1 if skipped else 0
        self.buf.append(" ")
        if tag in BLOCK:
            self.flush(tag)

    def handle_data(self, data):
        if not self.depth_skip:
            self.buf.append(data)

    def flush(self, tag: str) -> None:
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text:
            self.lines.append(HEADING.get(tag, "") + text)


def page_prose(path: str) -> str:
    file = DIST / path.strip("/") / "index.html"
    if not file.exists():
        raise SystemExit(f"{path}: not built ({file}); run `make site` first")
    parser = Prose()
    parser.feed(file.read_text(encoding="utf-8"))
    parser.flush("p")
    return "\n\n".join(parser.lines) + "\n"


def slug(path: str) -> str:
    return path.strip("/").replace("/", "__") or "home"


def scan(path: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    draft = OUT / f"{slug(path)}.md"
    draft.write_text(page_prose(path), encoding="utf-8")
    result = OUT / f"{slug(path)}.json"
    env = dict(os.environ)
    if LIMATUS_SRC.is_dir():
        env["PYTHONPATH"] = str(LIMATUS_SRC) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "limatus"]
    else:
        cmd = ["limatus"]
    proc = subprocess.run(cmd + ["scan", "--draft", str(draft), "--profile", str(PROFILE), "--output", str(result)],
                          capture_output=True, text=True, env=env)
    if proc.returncode not in (0, 1) or not result.exists():
        raise SystemExit(f"{path}: limatus failed\n{proc.stderr or proc.stdout}")
    return json.loads(result.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", nargs="*", help="page paths (default: writing/pages.txt)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any finding remains")
    args = ap.parse_args()
    pages = args.pages or [l.strip() for l in PAGES.read_text().splitlines() if l.strip() and not l.startswith("#")]
    total = Counter()
    for path in pages:
        report = scan(path)
        findings = [f for key in FINDING_LISTS for f in report.get(key, [])]
        kinds = Counter(f.get("kind", key) for key in FINDING_LISTS for f in report.get(key, []))
        total.update(kinds)
        print(f"{path:42s} {len(findings):3d}  " + ", ".join(f"{k} {n}" for k, n in kinds.most_common()))
    print(f"\n{sum(total.values())} findings on {len(pages)} pages: " + ", ".join(f"{k} {n}" for k, n in total.most_common()))
    return 1 if args.strict and total else 0


if __name__ == "__main__":
    sys.exit(main())
