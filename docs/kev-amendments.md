# Amendments to the Kev study registration

`docs/kev-preregistration.md` freezes Kev's coverage at commit `9dfa868` (54 cells,
`docs/kev-coverage.json`) and says that incoming coverage is added by a committed amendment and
manifest **before any Kev answer exists for it**. Each amendment below is one such commit. A new
manifest is built with `python -m scripts.make_kev_manifest` (same schema, same pinned checkpoint,
every input file pinned by sha256, request counts from the collector's own dry run) and is collected
with `python -m scripts.run_kev_study collect --manifest <file> ...`, which re-checks every hash and
count before it creates a client. The model, checkpoint, backend, precision, calibration, one-request-
at-a-time rule, resource guards and stopping rules of the original registration apply unchanged.

## Amendment 1: antisemitic tropes in depth (2026-09-23)

Registered before any Kev answer on these cells. Study design, questions, cue forms, controls and
scoring are those of `docs/antisemitic-tropes-preregistration.md` (a study written for Laya and Jev;
its predictions are for those models and are not restated for Kev).

- **Manifest:** `docs/kev-coverage-antisemitism.json`: 12 cells, **34,930 requests**, one request per
  text, each carrying all 24 yes-or-no questions (six stereotypes, three wordings each, plus a negative,
  non-stereotype control for each).
  - `stereotypes-antisemitism` (2,000 real biographies): as-written (2,000), religious (5,512), secular
    (6,890), nationality (6,890), community role (5,512), surname (3,926).
  - `loan-narratives-antisemitism` (200 synthetic loan narratives): as-written (200), religious (800),
    secular (1,000), nationality (1,000), community role (800), surname (400).
- **Kev predictions: none.** These cells are descriptive extensions for Kev. Every tested contrast is
  published, not only the clear ones: each wording, each control question, each cue form.
- **Timing:** unknown for a 24-question request (the registered pilot timed single-question requests at
  about 175 ms). The first 20 texts of `as-written` are the timing pilot for this amendment; no choice
  of sample depends on answers. Collect the cells in the order listed above.
- **Scoring:** the study's own scorer (per-cue trope score against matched other groups and the harmless
  edit, 1,000-resample paired interval, Holm within each stereotype), unchanged.

## Amendment: batch 3 stereotypes and added nationalities (2026-09-23)

Registered before any Kev answer on these cells. Study design, questions, clauses, controls and
scoring are those of `docs/batch3-preregistration.md` (written for Laya; its directional
predictions are for Laya and are not restated for Kev).

- **Manifest:** `docs/kev-coverage-batch3.json`: 8 cells, **96,000 requests**, one request per text,
  each carrying all 20 yes-or-no questions (18 stereotype questions and two negative controls). Task
  `stereotypes-batch3` (2,000 real biographies): as-written (2,000), orientation (10,000), race
  (12,000), nationality-x (28,000, batch 2's seven nationalities plus Israeli, Palestinian, Russian,
  Ukrainian, South Korean and Japanese), china (10,000), india (12,000), africa (12,000), family
  (10,000).
- **Kev predictions: none.** These cells are descriptive extensions for Kev. Every cell is
  published, including controls and weak-source groups.
- **Timing:** unknown for a 20-question request; the first 20 texts of `as-written` are the timing
  pilot, and no choice of sample depends on answers. Collect in the order listed above.
- **Scoring:** the study's own scorer (`biased_decisions/stereotypes_batch3.py` over
  `biased_decisions/metrics/tropes.py`: trope score against matched other groups and the harmless
  edit, 1,000-resample paired interval, Holm within each group across its stereotype questions),
  unchanged.

Later amendments (one per new package of tests) are appended here with their manifests before any Kev
answer on those cells: the batch 2 stereotype import, the batch 3 stereotypes and added nationalities, the
CFPB complaint tasks, the gendered-language studies, discrim-eval and BBQ, the housing and lending tasks,
and brand bias.
