# The first-pass subsample (registered before any subsampled answer)

Most cells need thousands of answers per model. To put a number in every cell for every model
soon, the first pass answers a **fixed, nested subsample** of each cell, and a later pass grows it.
This rule is registered before any answer is collected under it, and it never looks at an answer.

## The rule

- **Item.** One original text together with everything derived from it: its twin, its edited
  versions and its controls. An item is kept or dropped as a whole, so a comparison never loses one
  side.
- **Order.** Within a task, items are ranked by `sha256("biased-decisions-subsample-1|<task>|<item id>")`,
  smallest first, where `<item id>` is the original text's id and ties break by id. The ranking does
  not depend on the cue, on the model, or on any answer. Every cell of a task draws from the same ranking;
  a cell with fewer eligible families (race and age need a place to insert a name or age) takes the first
  500 of those, so its sample overlaps heavily with, but is not always identical to, its neighbours'.
- **Committed samples come first.** A cell that already has a committed sample keeps it: the 500 bios Jev
  answered for `race-fullname` (`tasks/surgeon-physician/versions/race-fullname_jev-subsample.txt`) and the 500
  `ask-twice` items. Every model answers those same bios, and the ranking applies to every other cell.
- **Cap.** A cell answers its first **500 items** in that order. A cell with 500 items or fewer is
  answered in full. The number of requests follows from the versions per item (a pronoun-swap cell is
  two requests per item, so 1,000); the run manifests state the exact counts.
- **Nested.** The first 500 items are the first 500 of any larger sample. Growing the cap to 1,000
  or to every item only requests the items not yet answered; nothing collected is redone or dropped.
- **Every model.** Jev, Laya and Kev use the same order, so the first 500 items of a cell are the
  shared subsample. Answers a model already has beyond that (Laya answers every cell in full) are kept
  and are not discarded; a comparison between models uses the shared items.
- **Reporting.** Each result carries its sample size and is shown as partial until the cell is
  complete. A result with no clear effect at this size means "not detected here", not "none", because a
  small sample can miss a real effect.
- **What does not change.** The questions, versions, controls, scoring, intervals, models,
  checkpoints and stopping rules of each study's registration.

## Runs

Each run in Kanbus epic BD-996e20 is one task's still-missing cells for one model, with a manifest
under `docs/kev-runs/` or `docs/jev-runs/` that pins the same input files as the frozen coverage.
Results come back as answer files committed to a `runs/<issue id>` branch.

## Outcome (scored 2026-09-28)

The subsample rule was applied. The fixed, nested order (seeded by sha256 hash of task|item id) was used to select the first 500 items per cell for Jev and Kev engines. Laya answered full tasks (n=1,000–1,371 per task). Jev and Kev samples carry n=500 items each; gendered-language tasks show n=508 (one small cell at boundary of available eligible items). All answers respect the shared subsample: the first 500 items ranked by the common order are the overlap across engines. Nested property holds: 500-item samples are the head of any larger future sample; no item will be dropped on future growth.

| task | jev n | kev n | laya n | subsample applied |
|---|---|---|---|---|
| cfpb-escalate-family | 500 | 500 | 1000 | yes |
| surgeon-physician | 500 | 500 | 1371 | yes |
| gendered-advance-agentic-communal | 508 | 508 | 508 | yes |
| resume-screening-age-inserted | 500 | 500 | 500 | yes |
| small-business-loan-owner-age | 500 | 500 | 500 | yes |

Subsample 1 rule confirmed as implemented.

> **Deviations, 2026-09-28**: None found.

