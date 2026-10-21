"""Read the built site's pages as prose and check them with Humanus against writing/style-profile.yml.

    make copy-check            # builds the site, then scans every page in writing/pages.txt
    python scripts/scan_copy.py --pages / /methods/

Each page's readable text (headings and paragraphs; no tables of numbers, charts or code) is written
to var/copy/<page>.md and checked; the findings (Humanus check-result-v1) go beside it as
var/copy/<page>.json, and the policy pack made from the style profile as var/copy/pack.json. Humanus
reports findings; it never rewrites anything. A finding is a question for a person: skip it, rewrite
it, delete it or keep it (see writing/README.md).

Needs the `copy` extra: pip install -e '.[copy]' (humanus from PyPI; `make install` includes it).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "site" / "dist"
OUT = ROOT / "var" / "copy"
PROFILE = ROOT / "writing" / "style-profile.yml"
PAGES = ROOT / "writing" / "pages.txt"
# Pin the pack version so var/copy/pack.json and the finding ids do not change with the date.
PACK_VERSION = "style-profile"

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


def load_pack() -> dict:
    """The policy pack Humanus checks against, converted from writing/style-profile.yml."""
    try:
        import humanus
    except ImportError:
        raise SystemExit("humanus is not installed; run `pip install -e '.[copy]'` (or `make install`)")
    try:
        pack = humanus.policy_pack_from_style_profile(PROFILE, version=PACK_VERSION)
    except ValueError as exc:
        raise SystemExit(f"{PROFILE}: {exc}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return pack


def scan(path: str, pack: dict) -> dict:
    import humanus

    OUT.mkdir(parents=True, exist_ok=True)
    draft = OUT / f"{slug(path)}.md"
    text = page_prose(path)
    draft.write_text(text, encoding="utf-8")
    try:
        report = humanus.check({"schemaVersion": 1, "content": {"format": "markdown", "text": text}, "pack": pack})
    except Exception as exc:  # report which page broke, as the old CLI failure did
        raise SystemExit(f"{path}: humanus check failed\n{type(exc).__name__}: {exc}")
    (OUT / f"{slug(path)}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def kind(finding: dict) -> str:
    """The summary label: the policy, or the check itself for the style profile's built-in checks."""
    return finding["detectorId"] if finding["policyId"] == "house-checks" else finding["policyId"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", nargs="*", help="page paths (default: writing/pages.txt)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any finding remains")
    args = ap.parse_args()
    pages = args.pages or [l.strip() for l in PAGES.read_text().splitlines() if l.strip() and not l.startswith("#")]
    pack = load_pack()
    total = Counter()
    for path in pages:
        findings = scan(path, pack).get("findings", [])
        kinds = Counter(kind(f) for f in findings)
        total.update(kinds)
        print(f"{path:42s} {len(findings):3d}  " + ", ".join(f"{k} {n}" for k, n in kinds.most_common()))
    print(f"\n{sum(total.values())} findings on {len(pages)} pages: " + ", ".join(f"{k} {n}" for k, n in total.most_common()))
    return 1 if args.strict and total else 0


if __name__ == "__main__":
    sys.exit(main())
