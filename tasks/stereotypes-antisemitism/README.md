# stereotypes-antisemitism

Pool A of the antisemitic-tropes-in-depth study (`docs/antisemitic-tropes-preregistration.md`,
Kanbus story BD-4dded2). Not a binary-choice task in the sense
`biased_decisions.tasks.base.Task` expects -- this `question.yaml` carries 24 independent yes/no
questions (the batch-2/veteran/sexuality "stereotype grid" schema: `questions.<key>.question` and
`questions.<key>.trope_consistent_answer`, here with an added `questions.<key>.trope` grouping
key), not `options`/`positive`/`group_attribute`. It is read directly by this study's own
scoring, not by `Task.load`.

## Source

2,000 items, 500 drawn from each of the four original Bias in Bios tasks already in this package
(`tasks/paralegal-attorney`, `tasks/surgeon-physician`, `tasks/teacher-professor`,
`tasks/nurse-physician`) already committed here -- see those tasks' own provenance in
`data/MANIFEST.md`. This is the **same pool batch 2 used** (`studies/batch2/README.md`), drawn
the same way: `random.Random(0).sample(sorted_test_ids, 500)` per task, re-sorted, so results sit
on the same denominator and are comparable cell-for-cell with batch 2's numbers. Built by
`biased_decisions.tasks.stereotype_pool.draw_pool()`; see that module's tests for the draw's
specification.

## Licence

Inherited from the four source tasks (Bias in Bios / De-Arteaga et al. 2019) -- see
`data/MANIFEST.md`.

## Build

```python
from biased_decisions.tasks.stereotype_pool import draw_pool
from biased_decisions.tasks.stereotype_versions import build_versions, ALL_CUES

pool = draw_pool()  # writes nothing; items.jsonl was written once from this call
for cue in ALL_CUES:
    rows, excluded = build_versions(pool, cue)  # writes versions/<cue>.jsonl
```

Deterministic given the four source tasks' own committed `items.jsonl` files -- no other input.

## Cue versions built

`versions/antisemitism-{secular,religious,nationality,role}.jsonl` (clause-insertion cues) and
`versions/antisemitism-surname.jsonl` (full-name cue, first name held constant, surname varied --
see `biased_decisions.cues.antisemitism`), built over this task's own 2,000-item pool rather than
over any of the four source tasks' full held-out sets. `_versions_build_summary.json` in this
directory records each cue's row and exclusion counts from the build that produced the committed
files.

## Questions

See `question.yaml`: six tropes (`greed_financial`, `banks_media_government`, `dual_loyalty`,
`wars`, `conspiracy`, `clannishness`), three independently worded questions plus one matched
non-trope control question each, all scored "yes" as the trope-consistent answer. Sources for
each trope are recorded in `docs/antisemitic-tropes-preregistration.md`, "Sources" and "Tropes and
questions" -- not repeated here to avoid the two documents drifting apart.

## No engine has answered any version of this task

Every file in `versions/` and `items.jsonl` is build-time output only (deterministic text
editing); no `answers/` directory exists for this task, and none should be created until the
pre-registration's Laya-first, Jev-priced-and-capped rules are followed.
