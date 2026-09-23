# Data manifest

Every file under `tasks/`, `answers/`, `pools/` and `studies/` was copied from
`/Users/home/Projects/Jev-Flywheel` (branch `main`, the commit noted below) on 2026-09-23, with
no `recordings/` directories and no unused fixtures (`fixtures/bios_attorney`,
`fixtures/bios_nurse`, the root demo corpus). Nothing here was regenerated or edited; each row
below is a `cp -p`. Source repo commit at copy time: `812fe83` ("studies(bios): resume
J1/J2/L5/L6/L3/L4-seeds2-3/baseline after the crash, LF two seeds, both Outcome sections").

## A note on the `gender-pronouns` cue's twins

The design doc lists `versions/<cue>.jsonl` as a task's committed cue-versions file. For
`gender-pronouns` specifically, every milestone-1 task's counterfactual twins are **not** copied
into a separate `versions/gender-pronouns.jsonl` file -- they already live inside `items.jsonl`
itself (as they did in Jev-Flywheel): a twin's id is the original's id with `-swapped` appended,
its `metadata.split` is `"counterfactual"`, and `metadata.counterfactual_of` names the original
id. Duplicating them into a second file would be redundant and could drift out of sync with the
copy in `items.jsonl`; `biased_decisions.tasks.base.Task.load_versions("gender-pronouns")`
returns `[]` for exactly this reason (see its docstring), and
`biased_decisions.tasks.bios.split_test_and_twins` reads the twins out of `items.jsonl` directly.

## Tasks

| file | source (relative to Jev-Flywheel) | bytes |
|---|---|---|
| `tasks/surgeon-physician/items.jsonl` | `fixtures/bios/items.jsonl` | 4,438,979 |
| `tasks/surgeon-physician/versions/race-name.jsonl` | `fixtures/bios/race_versions.jsonl` | 2,903,496 |
| `tasks/surgeon-physician/versions/race-fullname.jsonl` | `fixtures/bios/race2_versions.jsonl` | 19,303,838 |
| `tasks/surgeon-physician/versions/race-fullname_jev-subsample.txt` | `fixtures/bios/race2_jev_subsample.txt` | 6,000 |
| `tasks/surgeon-physician/versions/age-inserted.jsonl` | `fixtures/bios/age_versions.jsonl` | 2,983,480 |
| `tasks/nurse-physician/items.jsonl` | `fixtures/bios_pairs/nurse_physician/items.jsonl` | 2,247,192 |
| `tasks/teacher-professor/items.jsonl` | `fixtures/bios_pairs/teacher_professor/items.jsonl` | 2,473,739 |
| `tasks/paralegal-attorney/items.jsonl` | `fixtures/bios_pairs/paralegal_attorney/items.jsonl` | 2,387,861 |

`question.yaml` for all four tasks came from this repo's own `import/batch1/tasks/<task>/`
(`git mv`, not a copy from Jev-Flywheel -- they were staged there in the earlier import commit),
and carry the committed option order verbatim, including the "a attorney" grammar slip in
`paralegal-attorney/question.yaml`'s `question` field:

| file | bytes |
|---|---|
| `tasks/surgeon-physician/question.yaml` | 138 |
| `tasks/nurse-physician/question.yaml` | 136 |
| `tasks/teacher-professor/question.yaml` | 140 |
| `tasks/paralegal-attorney/question.yaml` | 141 |

## Answers (the record)

`gender-pronouns` = `answers.jsonl.gz` / `answers-laya.jsonl.gz` for each task.

| file | source (relative to Jev-Flywheel) | bytes |
|---|---|---|
| `answers/jev/surgeon-physician/gender-pronouns.jsonl.gz` | `fixtures/bios/answers.jsonl.gz` | 118,512 |
| `answers/jev/surgeon-physician/race-name.jsonl.gz` | `fixtures/bios/answers-race.jsonl.gz` | 70,152 |
| `answers/jev/surgeon-physician/race-fullname.jsonl.gz` | `fixtures/bios/answers-race2.jsonl.gz` | 104,634 |
| `answers/jev/surgeon-physician/age-inserted.jsonl.gz` | `fixtures/bios/answers-age.jsonl.gz` | 69,235 |
| `answers/jev/nurse-physician/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/nurse_physician/answers.jsonl.gz` | 54,938 |
| `answers/jev/teacher-professor/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/teacher_professor/answers.jsonl.gz` | 62,316 |
| `answers/jev/paralegal-attorney/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/paralegal_attorney/answers.jsonl.gz` | 59,667 |
| `answers/laya-mlx/surgeon-physician/gender-pronouns.jsonl.gz` | `fixtures/bios/answers-laya.jsonl.gz` | 162,899 |
| `answers/laya-mlx/surgeon-physician/race-name.jsonl.gz` | `fixtures/bios/answers-race-laya.jsonl.gz` | 95,751 |
| `answers/laya-mlx/surgeon-physician/race-fullname.jsonl.gz` | `fixtures/bios/answers-race2-laya.jsonl.gz` | 597,189 |
| `answers/laya-mlx/surgeon-physician/age-inserted.jsonl.gz` | `fixtures/bios/answers-age-laya.jsonl.gz` | 96,002 |
| `answers/laya-mlx/nurse-physician/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/nurse_physician/answers-laya.jsonl.gz` | 74,354 |
| `answers/laya-mlx/teacher-professor/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/teacher_professor/answers-laya.jsonl.gz` | 80,873 |
| `answers/laya-mlx/paralegal-attorney/gender-pronouns.jsonl.gz` | `fixtures/bios_pairs/paralegal_attorney/answers-laya.jsonl.gz` | 79,992 |

Every one of these rows carries `engine` = `laya-mlx`, not `laya` -- see the design doc's
"Milestone 1b" note and `biased_decisions.engines.laya_mlx`'s docstring: the port, not the
upstream package. The upstream `laya` record (`import/laya-record/laya/`) is left in place for
task 3 and is not copied here; `biased_decisions.record.OLD_TO_NEW` already maps its four
`*--gender-pronouns.jsonl.gz` files onto `answers/laya/<task>/gender-pronouns.jsonl.gz` for
whichever task copies them in.

## Pools

| file | source (relative to Jev-Flywheel) | bytes |
|---|---|---|
| `pools/first_names.txt` | `fixtures/bios/first_names.txt` | 18,848 |
| `pools/name_pools.json` | `fixtures/bios/name_pools.json` | 79,625 |

Provenance, thresholds and pool sizes: see `pools/README.md`.

## Studies

| file | source (relative to Jev-Flywheel) | bytes |
|---|---|---|
| `studies/PREREGISTERED.md` | `studies/PREREGISTERED.md`, lines 363-end (from the "does the engine read gender, and can the layer refuse to?" heading through EOF), prefixed with a provenance header | 148,673 |
| `studies/jev-flywheel/bios_gender.jsonl` | `studies/bios_gender.jsonl` | 5,310 |
| `studies/jev-flywheel/bios_pairs.jsonl` | `studies/bios_pairs.jsonl` | 2,980 |
| `studies/jev-flywheel/bios_race.jsonl` | `studies/bios_race.jsonl` | 1,836 |
| `studies/jev-flywheel/bios_race2.jsonl` | `studies/bios_race2.jsonl` | 8,963 |
| `studies/jev-flywheel/bios_age.jsonl` | `studies/bios_age.jsonl` | 2,355 |
| `studies/jev-flywheel/bios_shortlist.jsonl` | `studies/bios_shortlist.jsonl` | 11,859 |
| `studies/jev-flywheel/bios_gender_spend.md` | `studies/bios_gender_spend.md` | 4,510 |
| `studies/jev-flywheel/bios_race_spend.md` | `studies/bios_race_spend.md` | 1,510 |
| `studies/jev-flywheel/bios_race2_spend.md` | `studies/bios_race2_spend.md` | 1,780 |
| `studies/jev-flywheel/bios_age_spend.md` | `studies/bios_age_spend.md` | 1,377 |
| `studies/jev-flywheel/bios_pairs_spend.md` | `studies/bios_pairs_spend.md` | 2,224 |

These six result files and five spend logs sit under `studies/jev-flywheel/` (rather than
`studies/`) specifically so the provenance is legible from the path alone, without opening each
file: every row and every dollar figure in them was produced by Jev-Flywheel's own runs, not by
this repo. `bios_shortlist.jsonl` in particular is "overwritten by its script" in Jev-Flywheel
(see the inventory doc); this copy is a snapshot of its last run there, not something
`biased_decisions` regenerates from this path.

## Left for task 3

Everything else under `import/` (the batch-1 build scripts and their tasks beyond the four
above, `import/laya-record/`, the docs) is untouched, per this task's instructions.
