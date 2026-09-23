# Leaderboard design

Written 2026-09-23. A public, static leaderboard built from the committed record: `studies/*.jsonl`
in, `site/` out, nothing that isn't already in the repo.

## Purpose

The leaderboard ranks decision models by measured bias, most biased at the top. It is a
measurement of harm, not a contest. There are no scores, no medals, and no "invariance" number
that lets a model look good for being biased but not too biased. A model with a large excess over
the floor sits at the top of its dimension's board because that is where the harm is largest, full
stop.

## Dimensions

One board per dimension: gender pronouns, race names, inserted age, disability, religion,
nationality tropes, and whatever this project adds later — sexuality, veteran status, regulated
screening decisions. Each dimension gets its own ranking; there is no dimension a model can skip
without that gap being visible on the overall board (see below).

## Per-dimension ranking

Within a dimension, engines rank descending on excess over the floor:

- For occupation-cue tasks (the invariance pattern), excess is flip rate minus the floor's flip
  rate.
- For stereotype-trope axes, excess is the largest trope score among that axis's questions.

Each bar carries a 95% interval as whiskers (the same paired-bootstrap interval, 1,000 resamples,
seed 0, already used across this project's studies), and the floor is drawn faintly behind the
bars for scale, not as a competitor in the ranking.

An engine whose interval includes the floor is not placed on the ranked bars. It is listed below
the board under a heading of "no bias detected at this floor, n = ..." with its sample size shown.
That wording is deliberate: absence of evidence at this sample size is not a clean bill of health,
and the board does not imply otherwise by omitting the engine or burying it at the bottom of the
ranked list.

## Overall board

One additional board ranks engines by mean rank across dimensions, descending (worst mean rank
first, same as every other board on this site). An engine that is missing one or more dimensions
is flagged incomplete on this board. It is never scored as if the missing dimensions were zero
bias, and it is never advantaged by having fewer dimensions measured. Incomplete engines are
visibly marked, not silently averaged in.

## Spider charts

One polygon per engine, one axis per dimension, radius equal to that dimension's excess bias. The
polygon grows outward as bias increases, so a large polygon is a bad model, not a good one — this
is the inverse of a typical "capability" spider chart and the legend says so explicitly. A
dimension the engine hasn't been measured on is drawn as a dashed axis rather than pulled to zero,
so an unmeasured dimension never reads visually as "no bias."

## Drill-down per cell

Clicking any bar or polygon vertex opens a task-level table for that engine/dimension cell:

- Each task's point estimate and 95% CI
- The cue text used and its floor
- The record file in `studies/` that the number replays from
- The pre-registered prediction for that task (from the matching `docs/*-preregistration.md` file,
  where one exists) shown beside the measured outcome, so agreement or disagreement with the
  pre-registration is visible at the cell level, not just asserted in prose

## Honesty panel

Every page on the site carries the panel (`#read-first`), written for a general reader: four or
six short cards, never five, so its grid fills one, two or three columns with no orphan. It is
open on the home page and folded to its heading elsewhere. Each card is a claim with one to three
sentences and, where it helps, one example from the board. The cards must keep saying:

- Each test changes one detail and leaves every other clue in place, so an effect is the least a
  model reacts to a trait, not the full extent of it.
- The order in which the two options are listed changes the answers; every other number is
  conditional on each task's fixed order.
- Every number replays from the committed record; nothing is live-scored and nothing is left out
  (with a link to the data file).
- Trope questions measure the model, not the people described in the bios.

The rest explain the floor and why small percentages matter at scale. Every percentage in a card
is a number on the board (`leaderboard_test`). No stand-in comparator is on the board, so the
panel does not mention one.

## Build

- `bd report --json` reads `studies/*.jsonl` and writes one `leaderboard.json` (per-dimension
  rankings, the overall mean-rank table, not-detected lists, and per-cell drill-down data,
  including the pre-registration/outcome pairing where applicable).
- A static site under `site/` renders `leaderboard.json`. No backend: vanilla JS plus a small
  charting library, built to run from a plain file server or GitHub Pages.
- GitHub Pages publishes the site on each release, so the published leaderboard version always
  equals the record commit it was built from.

## Palette

Jev blue `#0389d7`, Laya magenta `#d03382`, neutral gray `#8a949c`, background `#f1f9fe`. Each
additional engine gets one more colour, chosen to stay distinguishable against these four and
against each other on both the bar boards and the spider charts.
