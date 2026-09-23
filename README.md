# Biased-Decisions

A benchmark harness for bias in fast decision models -- the small, cheap classifiers ("System 1"
models) that stand between a document and a verdict: resume screens, triage queues, eligibility
checks. It runs causal counterfactuals on real text (the same document, with one protected
signal changed and nothing else) rather than correlational gaps, measures each effect against a
control floor (an equally trivial edit that changes no protected signal), and reports every
number in the decision's own currency -- a flip rate, a shift in the predicted probability, a
shortlist's four-fifths ratio -- rather than an abstract fairness score. The method and the first
results are written up at
[anth.us/blog/encoding-prejudice](https://anth.us/blog/encoding-prejudice/),
[anth.us/blog/one-word-test](https://anth.us/blog/one-word-test/) and
[anth.us/blog/can-you-fix-it](https://anth.us/blog/can-you-fix-it/).

Milestone 1 ports every Bias in Bios study [Jev-Flywheel](https://github.com/AnthusAI/Jev-Flywheel)
ran and replays every number it published, offline, from a committed record. Batch 1 (milestone
1b) adds three more occupation pairs, two insertion cues with floors, an ask-twice noise floor, an
option-order cue and the original upstream Laya as a second Laya engine, again all offline. No
engine is called and no money is spent running `make replay` or `make report` -- see "What it
does not do" below.

## Vocabulary

- **engine** -- a model that answers a typed question about a text and returns a probability per
  option. Three ship today: `jev`, `laya`, `laya-mlx` (see below).
- **task** -- a corpus, one choice question, a positive class, and the group attribute used for
  recall gaps. Seven today, all Bias in Bios with first names redacted: `surgeon-physician`
  (positive: surgeon), `nurse-physician` (physician), `teacher-professor` (professor),
  `paralegal-attorney` (attorney) from milestone 1; `journalist-professor` (professor, a
  near-zero gender-gap control), `architect-interior-designer` (architect, the corpus's largest
  gender gap) and `dietitian-physician` (physician) from batch 1.
- **cue** -- a deterministic edit that changes one protected signal and nothing else:
  `gender-pronouns` (swaps pronouns and gendered role nouns), `race-name` (a Bertrand &
  Mullainathan first name), `race-fullname` (a first *and* last name from four population
  groups), `age-inserted` (a stated age, 34/35/61/62) from milestone 1; `disability` (a
  wheelchair-user clause), `religion` (a "practising X" clause, confounded -- see below --
  reported only as between-religion contrasts), `religion-v2` (a "devout X" clause with a floor
  that shares its shape), `ask-twice` (no edit -- the same bio asked a second time, the noise
  floor every flip rate is read against) and `option-order` (the same question with its two
  options listed the other way round) from batch 1.
- **floor** -- an equally trivial edit that changes no protected signal: a second white name
  instead of the first, one age-adjacent year instead of a 27-year jump, half of one name pool
  measured against the other half. A cue's effect is read against its floor, not against zero.
- **measurement** -- one `(engine, task, cue)` cell scored into a row: a flip rate with a 95%
  bootstrap CI, a signed shift in the predicted probability, a direction share, a recall gap, or
  (for the two most gender-skewed pairs) a shortlist's four-fifths ratio.
- **record** -- the committed answer cache an engine's response goes into,
  `answers/<engine>/<task>/<cue>.jsonl.gz`. It is the unit of reproducibility: everything a
  measurement needs comes from the record, never from a live call.

## The engines

- **`jev`** -- the hosted engine, via `typesafe-sdk`. Needs `TYPESAFE_API_KEY`.
- **`laya`** -- the original upstream package as released
  (`github.com/NandhaKishorM/laya`, Apache-2.0, `pip install laya`, PyTorch, CPU or MPS).
- **`laya-mlx`** -- an independent Apple-silicon port of the same model (`pip install laya-mlx`,
  MLX). Every Laya number Jev-Flywheel published before this port and the original were told
  apart came from the port, checkpoint `aac6fef/laya-mlx`; that record is filed under `laya-mlx`
  here, not `laya`, so a reader never has to guess which one produced a given row. Batch 1's
  Laya answers (the three new tasks and every new cue) all come from `laya`, the upstream
  package -- see "Port vs original" in `RESULTS.md` for the check that the two agree.

## Quickstart

```
git clone https://github.com/AnthusAI/Biased-Decisions
cd Biased-Decisions
make install   # python3 -m venv .venv && pip install -e '.[dev]'
make replay    # score every (engine, task, cue) cell that has a record -- no engine is called
make report    # regenerate RESULTS.md from the record
```

`make test` runs the unit specs; `make check` runs `replay`, `report`, and the regression test
that every replayed number still matches Jev-Flywheel's published studies.

## Results

The full tables, with confidence intervals, floors and footnotes, are in
[RESULTS.md](RESULTS.md). Gender-pronouns flip rate by task (surgeon-physician's `laya-mlx`
number is the one the published articles lead with; the three batch-1 tasks were only answered
by `jev` and the upstream `laya`, so their `laya-mlx` cell is empty):

| task | jev | laya | laya-mlx |
|---|---|---|---|
| surgeon-physician | 1.05% | 7.95% | 7.95% |
| nurse-physician | 3.30% | 13.45% | 13.50% |
| teacher-professor | 1.25% | 7.75% | 7.65% |
| paralegal-attorney | 3.90% | 17.85% | 17.85% |
| journalist-professor (control) | 0.80% | 1.80% | -- |
| architect-interior-designer | 4.37% | 5.11% | -- |
| dietitian-physician | 2.05% | 6.50% | -- |

## How to add an engine

Write `biased_decisions/engines/<name>.py` implementing `biased_decisions.engines.base.Engine`
(one method, `async def answer(self, text, questions) -> Dict[str, dict]`, returning the
record's own answer shape). Import the underlying SDK lazily, inside the call that needs it, so
importing the module never requires it installed -- see `engines/jev.py`, `engines/laya.py` and
`engines/laya_mlx.py` for the pattern. Add the package as an optional dependency in
`pyproject.toml` under `[project.optional-dependencies]`, and add the engine's name to
`biased_decisions.scoring.ENGINES`.

## How to add a task

Add `tasks/<slug>/question.yaml` (question text, an ordered `options:` list, `positive`, and
`group_attribute`) and `tasks/<slug>/items.jsonl` (one row per bio: `id`, `text`, `metadata`
carrying at least `split`, `reference_label`, `gender`). Register the slug in
`biased_decisions.tasks.bios.BIOS_TASKS` and, in `biased_decisions.scoring.TASK_CUES`, which
cues it carries. `bd build <task> --cue gender-pronouns` writes gender twins straight from
`items.jsonl`; the other three cues need a versions file (see the next section) before `bd
score`/`bd replay` can read them.

## How to add a cue

A cue is a builder (in `biased_decisions/cues/`) plus a `bd build` entry in
`biased_decisions/build.py`'s `BUILDERS` and a scorer in `biased_decisions/scoring.py`'s
`SCORERS`. The builder takes a task's held-out items and returns versions with a `source_id`
back-reference in their metadata (see `build_race_name`/`build_age_inserted` for the shape); the
scorer builds a `biased_decisions.metrics.flips.Verdict` per version and calls (or adds) the
matching function in `biased_decisions/metrics/`. `bd build`'s own docstring and
`tests/replay_test.py`'s build specs are the check that a new builder is deterministic and
reproduces itself.

## Running on your own data

Milestone 2. The shape a task needs is already fixed -- `tasks/<slug>/items.jsonl` plus
`tasks/<slug>/question.yaml`, as above -- but the CLI does not yet ingest an arbitrary corpus
into that shape; today's seven tasks were built by hand from Bias in Bios. Milestone 2 is a `bd
import` (or equivalent) that takes a raw corpus and a question and produces the shape `bd build`
and `bd score` already know how to read.

## The record and spend logs

Every cell's answers live under `answers/<engine>/<task>/<cue>.jsonl.gz`; `bd list` shows which
cells exist. Every dollar or GPU-hour a record cost is logged next to the study it produced --
`studies/jev-flywheel/*_spend.md` for milestone 1, `studies/batch1_jev_spend.md` for batch 1's
Jev requests (Laya, upstream and port, is free and local) -- so a reader can see what each number
cost without re-running it.

## What it does not do

No mitigation: nothing here changes a model's answer, trains a fitted head, or steers a
prediction -- it only measures. No learning loop: the arms that adjust an engine's behavior over
repeated rounds live in [Jev-Flywheel](https://github.com/AnthusAI/Jev-Flywheel), not here.
Milestone 1 calls no engine at all; every number in `RESULTS.md` is replayed from a record built
before this package existed.

## Pre-registration

Every study is written up in `studies/PREREGISTERED.md` before any engine answers a single
question about its corpus: the question, the arms, a predictions table (recorded in advance, with
a range that would not be surprising), what would change what the prediction expected, the rules
fixed before any run, and a reporting rule. A study that deviates from its own plan appends a
blockquote (`> **Deviations, <date>**`) rather than editing what was written before the run, and
its Outcome section scores what happened against what was predicted, not the other way around.
New studies append to the file in the same skeleton; nothing already there is rewritten.

## License and data provenance

MIT (see `LICENSE`). [Bias in Bios](https://huggingface.co/datasets/LabHC/bias_in_bios)
(De-Arteaga et al., 2019) is MIT-licensed on the Hub; the `race-fullname` name pools
(`pools/name_pools.json`, `pools/first_names.txt`) are built from CC0 and public-domain sources
(Rosenman, Olivella & Imai 2023; SSA baby names; US Census 2010 surnames) -- see
`pools/README.md` for the exact provenance, thresholds and pool sizes.
