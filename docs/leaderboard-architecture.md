# Leaderboard architecture

Written 2026-09-23 with the first build of `site/`. The author's decisions are in the design
brief (ranking by measured bias, the not-detected list, mean rank, outward-growing spiders, the
drill-down, the honesty panel, the palette); this file records how they were implemented, the
judgement calls the brief left open, and the data contract between `bd report --json` and the
site.

## Pipeline

```
answers/<engine>/<task>/<cue>.jsonl.gz   the record (committed)
        | bd replay
studies/<task>-<cue>.jsonl               scored cells, with 95% paired-bootstrap intervals
studies/batch2/stereotypes-laya.jsonl    batch 2, staged (second source, see below)
studies/PREREGISTERED.md                 predictions and outcomes, quoted verbatim
        | bd report --json --date YYYY-MM-DD      (biased_decisions/leaderboard.py)
site/data/leaderboard.json               the data contract
        | fetch, relative URL
site/*.html + site/js/*.js               static pages, hand-drawn SVG, no build step
```

`bd report --json` reads the scored cells rather than rescoring the record: it runs in a tenth
of a second, and every number it emits is one a committed file already carries, so any value on
the site can be found by hand in `studies/`. It computes no new bootstrap. The Pages workflow
closes the loop by running `bd replay` first and failing if the replay does not reproduce
`studies/` byte for byte, so the published data is always the record's.

The generated date is an argument, not the clock, so a given commit always produces the same
file (the unit test checks byte-for-byte determinism). `provenance.record_commit` is the last
commit touching `answers/` or `studies/`, so later site-only commits do not change it.

## The second source

Batch 2's stereotype axes were answered and scored outside the harness. Their results file and
RESULTS.md are copied verbatim into `studies/batch2/` with a provenance note. Every facet built
from them carries `"source": "batch2-staging"`, `records: []` (the answer record is not in this
repository), and a note; both dimensions carry `"source": "batch2-staging"`, and the methods page
and each dimension page say that `bd replay` cannot regenerate them. When batch 2 is ported into
the harness, `_batch2_facets` should read the harness's own rows and the second source goes away.

## Measures, floors and detection

Every quantity is in percentage points. Each (engine, dimension) cell is a list of **facets**
(a task, a name group, or a trope question), and each measured facet carries `raw` (the
measurement with its interval), `floor` (the value it is read against, with the floor's own
interval where the record has one), and `excess = raw - floor.value`, whose interval is the raw
interval less the floor's point estimate. A facet is **detected** when that excess interval's
lower end is above zero, i.e. the measurement's interval does not include the floor; an interval
that touches the floor counts as including it (Laya-mlx's race-name interval starts at exactly
its 2.36% floor, and it is not ranked).

| dimension | raw measurement | floor | facets |
|---|---|---|---|
| gender-pronouns | flip rate under the swap | ask-twice flip rate for that engine and task | 7 tasks |
| race-name | flip rate, white vs Black first name | white A vs white B flip rate (paired) | surgeon-physician |
| race-fullname | size of shift in P(surgeon) vs white names, 500-bio subsample | size of the white-half vs white-half shift | Black, Hispanic, Asian |
| age-inserted | 34-vs-61 flip rate | 34-vs-35 flip rate | surgeon-physician |
| disability | size of shift vs "A cyclist," (already paired) | 0 | 7 tasks |
| religion (v1) | largest minus smallest religion shift | 0 (all religions alike) | 7 tasks |
| religion-v2 | size of the largest religion shift vs "A devoted gardener," | 0 (already paired) | 7 tasks |
| stereotype-religion, -nationality | largest trope score over the axis's groups, per question | 0 (the score cancels the floor) | 6 questions |
| option-order | order flip rate | ask-twice flip rate | 4 tasks |

A dimension cell's **headline** is its largest excess among detected facets ("where the harm is
largest"); if none is detected the cell is "not detected" and the headline is the largest excess
among attributable facets, shown for information only.

Judgement calls, each visible on the site:

- **Ask-twice as the flip-rate floor.** Batch 1 section C calls it "the floor every other flip
  rate is read against". Where an engine has no ask-twice record on a task (Jev and Laya on the
  three batch-1 pairs) the engine's largest ask-twice rate on any task is borrowed, the more
  conservative choice, and labelled "borrowed". Laya-mlx has no ask-twice record at all, so its
  flip rates are read against zero, as RESULTS.md does, and labelled so. Missing floors are
  never silently zero.
- **Which age floor.** 34-vs-35, the one-year edit from the same starting version as the
  34-vs-61 edit. The 61-vs-62 floor and the probability shift are in the drill-down.
- **Race full name on the 500-bio subsample**, the bios both engines answered; Laya-mlx's
  all-bio numbers are in the drill-down. Magnitudes (|shift| minus |floor shift|) because the
  brief ranks on size of bias regardless of sign.
- **Religion v1 is contrasts only.** The raw measurement is the spread between the highest and
  lowest religion. Its interval is conservative (upper religion's upper bound minus lower
  religion's lower bound, and so on), and it is detected only when the two religions' own
  intervals do not overlap -- the test the pre-registration's outcome used. A proper paired
  bootstrap of the spread would need a rescoring pass (see open issues).
- **Religion v2's unattributed task.** Section E's pre-registered change-belief rule (a
  shared-clause effect over 3 pts) fired on nurse-physician, and its outcome says those cells
  are "reported as unattributed". That facet is shown with `"attributable": false` and is never
  ranked or detected.
- **Trope axes use every (question, group) cell**, per the brief's "largest trope score among
  that axis's questions", not only the groups the pre-registration named. For religion that
  headline is `honesty`, Christian, +10.92 pts: Christians read as more honest than the other
  religions. The named-trope predictions sit beside their questions in the drill-down.
- **Option order has no bootstrap interval in the record**, so its interval is a Wilson score
  interval from the rate and n, labelled as such.

## Ranking

- **A dimension's board** lists detected engines by headline excess, descending. Places are
  shown competition-style ("1=" for a tie: Laya and Laya-mlx agree to two decimals on gender).
  Not-detected engines are listed below the board with `n`; unmeasured engines are named.
- **Fractional ranks** feed the overall board: detected engines take places 1..d by excess,
  ties share the average place, and not-detected engines share the places below every detected
  engine. So with nothing detected, both engines on race-name sit at 1.5.
- **The overall board** is the mean of those ranks over **contested** dimensions (two or more
  engines measured), sorted most biased (lowest mean rank) first. A dimension only one engine
  was measured on cannot rank it against anyone; averaging in its automatic rank 1 would punish
  an engine for being measured more, so those dimensions are listed as "only" in the coverage
  strip instead. Every engine is missing at least one dimension today, so every row is flagged
  incomplete, with the count.

The brief says "mean rank, descending (worst mean rank first)". With rank 1 = most biased,
"worst first" means ascending mean rank; the site states the direction in words everywhere.

## Pre-registration beside the outcome

`Prereg` in `leaderboard.py` looks up rows by (section heading, first cell) in the markdown
tables of `studies/PREREGISTERED.md` (and batch 2's scored-predictions table) and copies
prediction, observed and verdict verbatim, stripped of markdown emphasis. A row that cannot be
found raises, and the unit test asserts every quoted string occurs in its source, so a quote can
never drift from the file. Rows written in Jev-Flywheel, where "Laya" meant the MLX port, are
attached to `laya-mlx` with a note saying so.

## Data contract (`site/data/leaderboard.json`, schema `biased-decisions/leaderboard@1`)

```
schema, provenance {record_commit, record_commit_short, generated, command, sources[]}
engines[]      {id, label, color, color_dark, marker, kind, about, stand_in}
dimensions[]   {id, label, long, facet_kind, facets[{id,label}], measure, unit:"pp",
                cue, floor, excess, notes[], source, prereg_section,
                ranks {engine: fractional rank},
                board {ranked[{engine, rank, value, lo, hi, facet, facet_label}],
                       not_detected[{engine, n, n_facets, value, lo, hi, facet, facet_label}],
                       unmeasured[engine], contested},
                cells {engine: {status:"missing", facets[]}
                             | {status:"measured", detected, n, n_facets, n_facets_detected,
                                headline {facet, facet_label, value, lo, hi, raw, floor_value},
                                facets[], prereg[]}}}
facet          {id, label, status:"missing", why}
             | {id, label, status:"measured", attributable, detected, n, interval_method,
                raw {value, lo, hi, label}, floor {value, lo, hi, label, source, ...},
                excess {value, lo, hi}, records[], study, source, extra {...}, note}
prereg row     {section, measurement, prediction, observed, verdict, facets, source, note?}
overall        {rule, n_dimensions, rows[{engine, mean_rank, ranked_on, positions{dim: rank},
                sole_engine[], unmeasured[], not_detected[], incomplete, measured_on}]}
floors         {ask_twice[{engine, task, task_label, flip_pct, mean_abs_dp, max_abs_dp, n,
                record, study}]}
honesty[]      {id, title, text}          vocabulary[] {term, text}
```

Missing is always explicit: a missing cell has no `headline`, a missing facet has no numbers.
The site never draws a missing value; it hatches it or dashes its axis.

## The site

Four page types (`index.html`, `dimension.html?d=`, `engine.html?e=`, `methods.html`) share one
module (`js/app.js`) that fetches the data by relative URL, so the site runs from a sub-path.
There is no charting library: the three chart forms (`js/charts.js`) are small SVG builders,
re-rendered on resize so text stays legible at phone width.

- **Hero**: every dimension on one shared excess axis, each engine's headline with its interval.
  One scale on purpose: it shows that gender and the stereotype axes are where the measured
  harm is largest, and that Jev's marks sit near the floor. Marks slide out from the floor to
  their value on load -- the one animation on the site, because it is the definition of excess
  -- and not at all under `prefers-reduced-motion`.
- **Boards** draw each bar from the engine's floor (a grey segment behind it) to its
  measurement, so the bar's length is the excess, with the interval as a whisker and the engine's
  other facets as thin ticks. Axes always start at zero.
- **Spiders** use radius = excess on a linear scale shared by every engine page, so a bigger
  shape is a worse model. A polygon is filled only in the wedges between adjacent measured
  axes; an unmeasured axis is dashed and breaks the shape rather than pulling it to zero.
  Negative excess (below the floor, never detected) is drawn at the centre and said so in the
  tooltip.
- Dimensions with fewer than three facets get a measurement-against-floor chart instead, which
  shows why an engine was or was not detected.
- Every mark is a link to its drill-down (`dimension.html?d=...#cell-<engine>`, a `<details>`
  element opened on arrival), focusable from the keyboard, with a tooltip on hover and focus.
- Identity is never colour alone: each engine has a marker shape (circle, square, diamond) and
  is labelled wherever it appears; detection is also encoded by fill (hollow = not detected) and
  dashing. The engine palette was checked with the dataviz skill's validator in both themes
  (light on `#f1f9fe`, dark on `#0f1a22`): all checks pass, worst adjacent CVD delta E 11.7.
- Dark mode follows the OS unless the reader picks a theme (remembered in `localStorage`, with
  every access guarded). Print always uses the light tokens and opens every drill-down.
- Fonts: Jersey 25 for display, Montserrat for text, from Google Fonts (SIL OFL). No other
  third-party code.

## Open issues

- **Excess intervals ignore floor uncertainty.** They are the measurement's interval shifted by
  the floor's point estimate. A paired bootstrap of (measurement minus floor) on the same bios
  would be tighter where the floor is paired (race-name, age) and is the right statistic; it
  needs a rescoring pass in `bd replay` and new fields in `studies/`.
- **Religion v1's spread and option order** carry non-bootstrap intervals (conservative bound,
  Wilson). Same fix.
- **Laya-mlx has no ask-twice record**; its gender flip rates are read against zero.
- **Trope headline choice.** Taking the largest trope score over every group follows the brief
  literally; restricting it to the pre-registered named tropes would change both stereotype
  headlines (and nationality would become "not detected": every named nationality trope is
  negative). The author should confirm which reading is intended.
- **Coverage is thin**, so the overall board averages over 3 to 6 contested dimensions per
  engine; every engine is flagged incomplete.
