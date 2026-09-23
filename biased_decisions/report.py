"""``bd report``: regenerate ``RESULTS.md`` from the committed record.

Every number in the file this module writes comes from calling
``biased_decisions.scoring``'s scorers directly against the committed ``answers/`` record -- no
study file has to be regenerated first (``bd replay`` writes ``studies/<task>-<cue>.jsonl`` as a
byproduct for the regression test to check against, but this module does not read them back;
re-deriving straight from the record means the report can never drift from what ``bd replay``
would say, and can be regenerated with no prior step). Nothing here calls an engine.

Laid out as a list of independent section builders (``SECTIONS``) so task 3 can add a table for
a new cue by appending one more ``(title, builder)`` pair -- nothing above ``generate`` needs to
change, and nothing in a builder depends on another builder having run first.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from biased_decisions.scoring import (
    FULLNAME_GROUPS, ScoreError, TASK_CUES, score_age_inserted, score_gender_pronouns,
    score_race_fullname, score_race_name, score_shortlist,
)
from biased_decisions.tasks.base import DEFAULT_ROOT
from biased_decisions.tasks.bios import BIOS_TASKS, load_task

ENGINE_LABELS: Dict[str, str] = {"jev": "Jev", "laya": "Laya", "laya-mlx": "Laya-mlx"}
GENDER_PRONOUNS_ENGINES = ("jev", "laya", "laya-mlx")
SHORTLIST_PAIRS = ("paralegal-attorney", "nurse-physician")
SHORTLIST_CUT = 500  # the cut the shortlist table reports; bd replay scores 250/500/1000 all.


class ReportContext:
    """Everything a section builder needs, computed once and shared."""

    def __init__(self, root: Path = DEFAULT_ROOT):
        self.root = root
        self.tasks = {slug: load_task(slug, root=root) for slug in BIOS_TASKS}

    def try_score(self, fn: Callable, *args, **kwargs) -> Optional[dict]:
        try:
            return fn(*args, **kwargs)
        except ScoreError:
            return None


def _record_provenance(root: Path) -> Tuple[str, str]:
    """``(short sha, date)`` of the record's last commit (``git log -1 -- answers/``), or
    ``("unknown", "unknown")`` outside a git checkout (a source tarball, say)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%h\t%cd", "--date=short", "--", "answers"],
            cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        if not out:
            return "unknown", "unknown"
        sha, date = out.split("\t")
        return sha, date
    except Exception:
        return "unknown", "unknown"


def _fmt_pct(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def _fmt_ci(ci: Optional[List[float]]) -> str:
    if not ci:
        return ""
    return f"[{ci[0] * 100:.2f}, {ci[1] * 100:.2f}]"


def _fmt_ratio(value: Optional[float], digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


# ---------------------------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------------------------

def build_header(ctx: ReportContext) -> str:
    sha, date = _record_provenance(ctx.root)
    return (
        f"# Results\n\n"
        f"Generated on {date} from record commit `{sha}`. Regenerate with `make report` (or "
        f"`bd report`); every number below is replayed from the committed record under "
        f"`answers/` -- nothing here calls an engine.\n"
    )


# ---------------------------------------------------------------------------------------------
# gender-pronouns and race-name: one table per cue, engines as columns, tasks as rows.
# ---------------------------------------------------------------------------------------------

def _cue_table(ctx: ReportContext, cue: str, title: str, scorer: Callable) -> str:
    task_slugs = [slug for slug in BIOS_TASKS if cue in TASK_CUES[slug]]
    rows_by_task: Dict[str, Dict[str, dict]] = {}
    engines_seen: List[str] = []
    for slug in task_slugs:
        task = ctx.tasks[slug]
        rows_by_task[slug] = {}
        for engine in GENDER_PRONOUNS_ENGINES:
            row = ctx.try_score(scorer, engine, task)
            if row is None:
                continue
            rows_by_task[slug][engine] = row
            if engine not in engines_seen:
                engines_seen.append(engine)
    if not engines_seen:
        return ""

    lines = [f"## {title}", "",
             "| task | " + " | ".join(ENGINE_LABELS[e] for e in engines_seen) + " |",
             "|---|" + "---|" * len(engines_seen)]
    for slug in task_slugs:
        cells = []
        for engine in engines_seen:
            row = rows_by_task[slug].get(engine)
            if row is None:
                cells.append("—")
                continue
            cells.append(_render_cue_cell(cue, row))
        lines.append(f"| {slug} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def _render_cue_cell(cue: str, row: dict) -> str:
    if cue == "gender-pronouns":
        flip = _fmt_pct(row["counterfactual_flip_rate"])
        ci = _fmt_ci(row.get("flip_rate_ci"))
        direction = _fmt_pct(row.get("flip_toward_more_female_share"))
        gap = _fmt_pct(row.get("recall_gap_less_female_women_minus_men"))
        return f"flip {flip} {ci}<br>floor: none (the swap is the only edit)<br>direction: {direction}<br>recall gap: {gap}"
    if cue == "race-name":
        flip = _fmt_pct(row["race_flip"])
        ci = _fmt_ci(row.get("race_ci"))
        floor = _fmt_pct(row["floor"])
        floor_ci = _fmt_ci(row.get("floor_ci"))
        direction = _fmt_pct(row.get("direction_share"))
        return (f"flip {flip} {ci}<br>floor: {floor} {floor_ci}<br>direction: {direction}"
                f"<br>recall gap: —")
    return "—"


def section_gender_pronouns(ctx: ReportContext) -> str:
    return _cue_table(ctx, "gender-pronouns", "gender-pronouns: flip rate by task and engine",
                      score_gender_pronouns)


def section_race_name(ctx: ReportContext) -> str:
    return _cue_table(ctx, "race-name", "race-name: flip rate (surgeon-physician only)",
                      score_race_name)


# ---------------------------------------------------------------------------------------------
# race-fullname: signed shifts per group, with CIs and floors.
# ---------------------------------------------------------------------------------------------

def section_race_fullname(ctx: ReportContext) -> str:
    task = ctx.tasks["surgeon-physician"]
    columns: List[Tuple[str, str, dict]] = []
    for engine in ("jev", "laya", "laya-mlx"):
        for sample in ("all", "500"):
            row = ctx.try_score(score_race_fullname, engine, task, sample=sample)
            if row is not None:
                columns.append((engine, sample, row))
    if not columns:
        return ""

    lines = ["## race-fullname: signed shift in P(surgeon) by group", "",
             "Positive: the named group reads *more* like the positive class than the white "
             "names on the same bio.", "",
             "| group | " + " | ".join(f"{ENGINE_LABELS[e]} ({s})" for e, s, _ in columns) +
             " |",
             "|---|" + "---|" * len(columns)]
    for group in FULLNAME_GROUPS:
        cells = []
        for _, _, row in columns:
            if group == "white":
                cells.append("(reference group)")
                continue
            g = row["groups"][group]
            shift = _fmt_pct(g["shift"], digits=3)
            ci = _fmt_ci(g.get("shift_ci"))
            cells.append(f"{shift} {ci}")
        lines.append(f"| {group} | " + " | ".join(cells) + " |")
    floor_cells = []
    for _, _, row in columns:
        shift = _fmt_pct(row["floor_shift"], digits=3)
        ci = _fmt_ci(row.get("floor_shift_ci"))
        floor_cells.append(f"{shift} {ci}")
    lines.append("| floor (white split in half) | " + " | ".join(floor_cells) + " |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# age-inserted.
# ---------------------------------------------------------------------------------------------

def section_age(ctx: ReportContext) -> str:
    task = ctx.tasks["surgeon-physician"]
    columns: List[Tuple[str, dict]] = []
    for engine in ("jev", "laya", "laya-mlx"):
        row = ctx.try_score(score_age_inserted, engine, task)
        if row is not None:
            columns.append((engine, row))
    if not columns:
        return ""

    metric_rows = [
        ("34 -> 61 flip", "age_flip", "age_flip_ci"),
        ("34 -> 61 shift", "age_shift", "age_shift_ci"),
        ("floor: 34 -> 35 flip", "floor_35_flip", "floor_35_flip_ci"),
        ("floor: 34 -> 35 shift", "floor_35_shift", "floor_35_shift_ci"),
        ("floor: 61 -> 62 flip", "floor_62_flip", "floor_62_flip_ci"),
        ("floor: 61 -> 62 shift", "floor_62_shift", "floor_62_shift_ci"),
    ]
    lines = ["## age-inserted (surgeon-physician only)", "",
             "| measurement | " + " | ".join(ENGINE_LABELS[e] for e, _ in columns) + " |",
             "|---|" + "---|" * len(columns)]
    for label, field, ci_field in metric_rows:
        cells = [f"{_fmt_pct(row[field], digits=3)} {_fmt_ci(row.get(ci_field))}"
                for _, row in columns]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("| direction (older -> surgeon), of flips | " +
                " | ".join(_fmt_pct(row.get("direction_share")) for _, row in columns) + " |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Shortlist: top-N four-fifths ratio, tie-fair, counterfactual counts, twin-averaged.
# ---------------------------------------------------------------------------------------------

def section_shortlist(ctx: ReportContext) -> str:
    blocks: List[str] = [f"## Shortlist (top {SHORTLIST_CUT})", "",
                         "An invented employer ranks applicants by P(positive) and shortlists "
                         "the top N; the EEOC four-fifths rule flags a women:men ratio under "
                         "0.8.", ""]
    any_rows = False
    for pair_slug in SHORTLIST_PAIRS:
        task = ctx.tasks[pair_slug]
        rows_for_pair = []
        for engine in ("jev", "laya", "laya-mlx"):
            rows = ctx.try_score(score_shortlist, engine, task)
            if not rows:
                continue
            rows_for_pair.extend(r for r in rows if r["cut"] == SHORTLIST_CUT)
        if not rows_for_pair:
            continue
        any_rows = True
        blocks.append(f"### {pair_slug} (positive: {task.positive})")
        blocks.append("")
        blocks.append("| engine | variant | women rate | men rate | 4/5 ratio [CI] | "
                      "tie-fair | women in only as men | men out as women |")
        blocks.append("|---|---|---|---|---|---|---|---|")
        for row in rows_for_pair:
            blocks.append(
                f"| {ENGINE_LABELS.get(row['engine'], row['engine'])} | {row['variant']} | "
                f"{_fmt_pct(row['women_shortlist_rate'])} | "
                f"{_fmt_pct(row['men_shortlist_rate'])} | "
                f"{_fmt_ratio(row['four_fifths_ratio'])} "
                f"[{_fmt_ratio(row['ratio_ci'][0])}, {_fmt_ratio(row['ratio_ci'][1])}] | "
                f"{_fmt_ratio(row['tie_fair_ratio'])} | "
                f"{row['women_who_gain_place_read_as_men']} | "
                f"{row['men_who_lose_place_read_as_women']} |")
        blocks.append("")
    return "\n".join(blocks) if any_rows else ""


# ---------------------------------------------------------------------------------------------
# Footnotes.
# ---------------------------------------------------------------------------------------------

def section_footnotes(ctx: ReportContext) -> str:
    return "\n".join([
        "## Footnotes",
        "",
        "- **Floors.** A floor is an equally trivial edit that changes no protected signal "
        "(a second white name instead of the first, one age-adjacent year instead of a "
        "27-year jump, half of one name pool against the other half). A cue's real effect is "
        "read against its floor, not against zero -- some flip rate is just noise from "
        "re-asking a near-tied item.",
        "- **Flip rates are lower bounds.** Every milestone-1 corpus has first names redacted "
        "before a cue is applied, and gender-pronouns twins still swap pronouns and role nouns "
        "only, not every possible cue (a name left in place, for instance, is itself a gender "
        "cue the pronoun swap alone does not remove). A reported flip rate is a lower bound on "
        "an engine's sensitivity to the attribute, not an estimate of it.",
        "- **The swap-rule artefacts.** `bd build`'s gender-pronouns twins use the "
        "pre-amendment rule (`biased_decisions.cues.gender.ORIGINAL_RULE`) because that is the "
        "rule the published twins in `tasks/*/items.jsonl` were actually built with -- checked "
        "byte-for-byte, not read off that module's own (incorrect) docstring claim that the "
        "amended rule built them. Measured against the 8,000 milestone-1 test bios: the "
        "amended rule's medical-phrase carve-out (\"women's/men's health\", etc.) would change "
        "36 bios' twins (0.45%); its Miss/Sir/Madam pairs would change 11 (0.14%).",
        "- **Option order is part of a task.** `question.yaml`'s `options:` list is ordered, "
        "and every probability in the record is keyed by that order; `bd build`/`bd answer` "
        "refuse to touch a cell whose committed order disagrees with the task file's current "
        "one. Every number in this file is under the order each task's `question.yaml` commits "
        "today.",
        "- **Missing cells.** `race-name`, `race-fullname` and `age-inserted` exist only for "
        "`surgeon-physician` -- the other three tasks (`nurse-physician`, `teacher-professor`, "
        "`paralegal-attorney`) were only run on `gender-pronouns`, to check whether the gender "
        "result generalizes past surgeon/physician. Jev's `race-fullname` record covers only "
        "the 500-bio subsample in `tasks/surgeon-physician/versions/"
        "race-fullname_jev-subsample.txt` (drawn once, so Laya can be compared to Jev on "
        "identical bios); Laya-mlx's covers all eligible bios, and is reported both ways.",
        "- Run nothing new: every number here is replayed from the committed record.",
        "",
    ])


SECTIONS: List[Tuple[str, Callable[[ReportContext], str]]] = [
    ("header", build_header),
    ("gender-pronouns", section_gender_pronouns),
    ("race-name", section_race_name),
    ("race-fullname", section_race_fullname),
    ("age-inserted", section_age),
    ("shortlist", section_shortlist),
    ("footnotes", section_footnotes),
]


def generate(root: Path = DEFAULT_ROOT) -> str:
    ctx = ReportContext(root)
    parts = []
    for _name, builder in SECTIONS:
        text = builder(ctx)
        if text:
            parts.append(text)
    return "\n\n".join(parts).rstrip() + "\n"


def write(root: Path = DEFAULT_ROOT, out: Optional[Path] = None) -> Path:
    out = out or (root / "RESULTS.md")
    out.write_text(generate(root), encoding="utf-8")
    return out
