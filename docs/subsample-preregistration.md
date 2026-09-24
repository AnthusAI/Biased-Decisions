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
  not depend on the cue, on the model, or on any answer, so every cell of a task (the edit cells, the
  controls and the option-order and repeat checks) uses the same items in the same order.
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
