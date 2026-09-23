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
        | astro build (site/, static output)
site/dist/<path>/index.html              one static page per path, charts drawn in the browser
                                         from a JSON payload inlined in each page
```

`bd report --json` reads the scored cells rather than rescoring the record (the only files it
opens besides them are the committed bios and answers it quotes as examples), and every number it
emits is one a committed file already carries, so any value on
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

## Data contract (`site/data/leaderboard.json`, schema `biased-decisions/leaderboard@2`)

Version 2 adds `dimensions[].breakdown` (below) and a `groups` field on batch-2 pre-registration
rows; every version-1 field is unchanged, value for value.

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
prereg row     {section, measurement, prediction, observed, verdict, facets, groups?, source, note?}
breakdown      {group_kind: "religion"|"nationality"|"name group"|null, item_kind: "task"|"question",
                groups[{id, label, clause}], items[{id, label, question, options?, positive?,
                trope?, trope_consistent_answer?, note?}],
                cells[{group|null, item, prereg: bool, engines {engine: facet}, example|null}],
                levels[{kind: "group"|"item"|"cell", group|null, item|null,
                        ranks, board, heads {engine: headline summary as in cells}}],
                pending[prereg row with engine, observed: null, verdict: "not yet measured"],
                example_note|null}
example        {task, source_id, engine, positive, question, chosen,
                versions[{id, label, segments[[text, changed 0|1]], options[]}] (two),
                answers {engine: [{p, choice}, {p, choice}]}, records[], texts[]}
overall        {rule, n_dimensions, rows[{engine, mean_rank, ranked_on, positions{dim: rank},
                sole_engine[], unmeasured[], not_detected[], incomplete, measured_on}]}
floors         {ask_twice[{engine, task, task_label, flip_pct, mean_abs_dp, max_abs_dp, n,
                record, study}]}
honesty[]      {id, title, text}          vocabulary[] {term, text}
```

Missing is always explicit: a missing cell has no `headline`, a missing facet has no numbers.
The site never draws a missing value; it hatches it or dashes its axis.

### The breakdown

Every dimension has two axes: **groups** (a religion, a nationality, a name group; empty where the
cue has no group, as for the pronoun swap) and **items** (the tasks, or batch 2's trope
questions). A **cell** is one (group, item) pair and carries one facet per engine, in the same
shape as a dimension facet. The dimension's own `facets` are one reading of the cells: for a
two-axis dimension, each item's largest cell over the groups (the rule the author kept for the
stereotype headlines), so the dimension headline always equals the largest detected cell (a unit
test checks it).

`levels` holds a board for every level that gets a page: each group and each item when its axis
has more than one value, and each cell when both do. A level's board is built by the same
`_summary` and `_board` functions as the dimension board: its facets are the cells under it, the
headline is the largest detected excess among them, not-detected engines are listed with n and
never ranked, unmeasured engines are named. A dimension with a single cell (race by first name,
age) has no levels: its own page is the leaf.

Per-cell additions, all taken from files already committed:

- **Batch-2 cells** (`_batch2_cells`): the trope score as the measurement, with the identity
  clause, the floor clause, the question wording, both mean probabilities of the trope-consistent
  answer, the raw shift against the floor, the flip rate, the axis's general "any label" effect,
  and `direction`: `trope` (detected), `reverse` (the interval lies below zero: the opposite of the
  trope, shown and labelled, never ranked) or `none`. The clauses are quoted from the
  pre-registration and the unit test checks they occur there verbatim; so do each question's
  "trope it tests" and the pending Jev predictions, which have no outcome yet.
- **Religion v2 cells**: each religion's own shift against "A devoted gardener," per task, with
  the unattributed rule applied to every religion on nurse / physician.
- **`prereg`** marks a cell a pre-registered prediction names by group and question (Jewish x
  greed, Muslim x violence, American x arrogance and worldliness, German and Chinese x
  diligence).
- **`example`** (`biased_decisions/leaderboard_examples.py`): one committed bio in the two versions
  the cue compares, a word-level diff marking the edited words, and every engine's answers to both
  versions from `answers/`. The bio is chosen by a fixed rule, stated on the page: for the engine
  most biased on that cell (else the largest excess), the largest change in its probability of
  the task's positive label among bios whose verdict flipped, in the direction of its average
  shift for shift measures. It is the clearest case, not a typical one, and the page says so.
  Batch-2 cells have no example: their record is not in this repository, so their pages show the
  question, the clause and the two mean probabilities instead.

## URLs

Every page has a real path, built from ids in the data contract. The scheme:

```
/                                         the overall board
/<dimension>/                             a dimension's board and its breakdown
/<dimension>/<group>/                     one group            /stereotype-nationality/american/
/<dimension>/<item>/                      one question or task /stereotype-religion/greed/
/<dimension>/<group>/<item>/              one cell             /stereotype-religion/jewish/greed/
/engines/   /engines/<engine>/   /engines/<engine>/<dimension>/
/methods/
/data/leaderboard.json                    the data contract itself
/og/<path with "--" for "/">.png          each page's Open Graph image
```

The reasoning:

- **Ids, not indexes.** Every segment is an id the data contract already uses (`gender-pronouns`,
  `jewish`, `greed`, `surgeon-physician`, `laya-mlx`): lowercase, hyphenated, readable aloud,
  and stable as long as the id is. A unit test checks each is a URL-safe slug, that none collides
  with a reserved top-level name (`engines`, `methods`, `data`, `og`), and that group ids and item
  ids never collide within a dimension.
- **Only axes that vary are in the path.** A group and an item share the second segment because
  their id sets are disjoint; the third segment exists only where both axes vary. So race by full
  name is `/race-fullname/black/` (it has one task), gender is `/gender-pronouns/nurse-physician/`
  (it has no group), and a single-cell dimension is just `/age-inserted/`. The shortest path that
  names a thing is its address, and every prefix of an address is itself a page.
- **Group before item.** `/stereotype-religion/jewish/greed/` reads as "Jewish, asked about
  greed", and its parent `/stereotype-religion/jewish/` is the group page, which is the question a
  reader from that group arrives with. The item page (`/stereotype-religion/greed/`) is a sibling,
  reached from the cell's breadcrumb-adjacent links.
- **Dimensions at the root.** They are the site's main subject, and `/stereotype-nationality/` is
  shorter than `/dimensions/stereotype-nationality/`. Engines get a prefix because an engine id
  could one day equal a dimension id.
- **Trailing slash, always.** Astro builds `/<path>/index.html` (`build.format: "directory"`,
  `trailingSlash: "always"`), which every static host serves at the slash path without rewrites.
  Canonical URLs, Open Graph URLs and every internal link use the slash form.
- **`#` only for a position within a page.** On any page, `#<engine>` is that engine's row or
  block (`/stereotype-religion/jewish/greed/#laya`), and a `<details>` it names opens on arrival.
  Nothing is routed by fragment or query string.
- **Legacy addresses redirect.** `dimension.html?d=<dim>#cell-<engine>` goes to `/<dim>/#<engine>`,
  `engine.html?e=<engine>` to `/engines/<engine>/`, `methods.html` to `/methods/`. A static host
  cannot redirect on a query string, so these are three small static pages (`site/public/`) that
  redirect in the browser, with a no-JavaScript fallback to the board.
- **Every page carries** a `<title>` naming the thing and its dimension, a description that leads
  with the finding (for a cell, the plain-language sentence), a canonical URL, Open Graph and
  Twitter tags, and an Open Graph image. The images are 1200 x 630 cards rendered at build time
  from an SVG template by resvg (WebAssembly; no native dependency) with the site's own fonts,
  vendored under `site/src/og/fonts/` (SIL OFL). If those fonts are missing the build still
  succeeds and pages simply omit `og:image`.
- **`SITE_URL`** (build environment) is the public origin for canonical and Open Graph URLs;
  `BASE_PATH` serves the site from a sub-path. Internal links are root-relative with the base.

## The site

An Astro project in `site/` (static output only, dependencies pinned by `package-lock.json`).
Every page is generated at build time from the data file: its text, tables, rankings, examples
and metadata are static HTML; `src/lib/site.js` holds every rule the pages need (lookups, the URL
scheme, chart payloads, titles, descriptions and the plain-language sentences), so the page
templates hold markup only. Charts are drawn in the browser by `src/scripts/charts.js` (no
charting library, re-rendered on resize so text stays legible at phone width) from a small JSON
payload inlined in each page, with every link precomputed; nothing is fetched at runtime.

Page types: the overall board; a dimension (board, then the breakdown as a group x item matrix
or a ranked forest, the spider or measurement-vs-floor chart, each engine's table); a group or
item (its own board, a forest of every row ranked most biased first, a table); a leaf (a cell, or
an item or group with a single cell: the board, the plain-language sentence per engine, the full
measurement table, the measurement-vs-floor chart, the example or the stimulus, the
pre-registered prediction and outcome, links to the neighbouring cells); an engine; an engine on
one dimension; methods; 404.

- **Forests** are the new chart form: one row per question, group or task, every engine's value
  with its interval on one signed axis around the floor, sorted most biased first. A solid
  whisker below zero is the reverse of the trope; a dashed one includes the floor.

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
- Every mark is a link to its drill-down page, focusable from the keyboard, with a tooltip on
  hover and focus.
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
- **Trope headline choice.** Decided: the dimension headline stays the largest trope score over
  every group and question. The pre-registered tropes are labelled and each has its own page
  (`/stereotype-religion/jewish/greed/`, `/stereotype-nationality/american/arrogance/`).
- **Examples are extreme by construction.** The rule picks the largest change, and the page says
  it is not typical. A "median bio" example beside it would show the typical case.
- **Stimulus artefacts show in examples.** The full-name cue also replaced some non-name tokens
  (an insurer's name); first-name redaction in Bias in Bios misses some names. Both are in the
  committed stimuli and are shown as they are, with a note.
- **Coverage is thin**, so the overall board averages over 3 to 6 contested dimensions per
  engine; every engine is flagged incomplete.
