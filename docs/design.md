# Biased-Decisions: design for milestone 1

Repo: github.com/AnthusAI/Biased-Decisions (public, MIT, "Copyright (c) 2026 Anthus AI Solutions").
Purpose: a benchmark harness for bias in fast decision models (System 1 models: Jev, Laya, whatever
ships next). Causal counterfactuals on real text, with control floors, reported in the decision's own
currency. Milestone 1 ports everything the Jev-Flywheel bias studies produced and replays every
published number offline. No new engine calls, no new spend.

## Vocabulary (fixed; use these names in code, docs and RESULTS.md)

- **engine**: a model that answers a typed question about a text and returns a probability per option.
  Adapters: `jev` (typesafe-sdk, needs TYPESAFE_API_KEY), `laya` (laya-mlx, Apple silicon, free).
- **task**: a corpus + one choice question + a positive class + the group attribute used for gaps.
  Milestone 1 tasks (all Bias in Bios, first names redacted): `surgeon-physician` (positive: surgeon),
  `nurse-physician` (physician), `teacher-professor` (professor), `paralegal-attorney` (attorney).
- **cue**: a deterministic edit that changes one protected signal and nothing else, plus its **floor**
  (an equally trivial edit that changes no protected signal). Milestone 1 cues:
  `gender-pronouns` (swap_gender; no floor: the swap is the only edit), `race-name` (first attempt,
  18 B&M names; floor = second white name), `race-fullname` (Rosenman/Census pools, 4 names × 4
  groups; floor = white vs white), `age-inserted` (34/35/61/62; floors 34v35, 61v62).
- **measurement**: (engine, task, cue) → rows. Metrics: `flip_rate` (+95% bootstrap CI, 1,000
  resamples, seed 0), `floor_flip_rate`, `mean_abs_delta_p`, `signed_shift` (per group, with CI),
  `direction_share`, `recall_gap` (group A minus group B on the positive class), and the
  **shortlist** block: top-N four-fifths ratio with CI, tie-fair ratio, tie block size, counterfactual
  counts (in-only-if-swapped / out-if-swapped per group), engine-alone twin averaging.
- **record**: committed answer caches (`answers/<engine>/<task>/<cue>.jsonl.gz`) so `bd replay`
  reproduces every row without a key. The record is the unit of reproducibility; spend logs sit
  beside it.

## Package layout

```
biased_decisions/
  __init__.py
  engines/{base.py, jev.py, laya.py}        # answer(texts, question) -> [{"probabilities": {...}, "choice": ...}]
  cues/{base.py, gender.py, names.py, fullname.py, age.py, redaction.py}
  tasks/{base.py, bios.py}                  # loads a task's items.jsonl + builds twins via a cue
  metrics/{flips.py, shifts.py, shortlist.py, bootstrap.py}
  record.py                                 # read/write answer caches; cache-key = (engine, task, cue, item id, version)
  report.py                                 # RESULTS.md generator from studies/*.jsonl
  cli.py                                    # `bd` : list | build | answer | score | replay | report
tasks/<task>/{items.jsonl, question.yaml, versions/<cue>.jsonl}   # committed fixtures
answers/<engine>/<task>/<cue>.jsonl.gz                             # committed record
pools/{first_names.txt, name_pools.json}                          # SSA/Rosenman/Census derived, provenance in a README
studies/{PREREGISTERED.md, *.jsonl, *_spend.md}                   # ported verbatim, with a provenance note
RESULTS.md                                                        # generated; one table per cue, engines as columns
README.md, LICENSE, pyproject.toml, Makefile, tests/
```

## Commands

- `bd list` — engines, tasks, cues, and which (engine, task, cue) cells have a record.
- `bd build <task> --cue <cue>` — write the cue's versions file from items.jsonl (deterministic, seeded).
- `bd answer <engine> <task> --cue <cue> [--price-only]` — fill the record (needs a key or a GPU; never run in milestone 1).
- `bd score <engine> <task> --cue <cue>` — rows from the record → `studies/<task>-<cue>.jsonl`.
- `bd replay` — score every cell that has a record; `make replay` wraps it and must reproduce every
  number in Jev-Flywheel's studies/*.jsonl (bit-for-bit on rates and counts; CIs within bootstrap noise
  when seeds match, identical when the same seed and resample count are used).
- `bd report` — regenerate RESULTS.md.

## Porting rules

- Copy code, don't import jev_flywheel; the harness must install standalone. Keep function names and
  behaviour identical where a published number depends on them (swap rule incl. the amended
  protected phrases and Miss/Sir/Madam; the redaction rule; name pools thresholds; age insertion and
  eligibility; tie-fair ratio; bootstrap seeds).
- Keep both swap-rule versions selectable: `gender-pronouns` (amended rule) and the original rule the
  published twins were built with, so replay matches the record; note it in RESULTS.md.
- Specs next to modules (`*_test.py`), pytest; port the existing bias specs; add a replay regression
  test that compares scored rows against a committed copy of Jev-Flywheel's rows (tolerances stated).
- Pre-registration convention carried over: `studies/PREREGISTERED.md` keeps the ported sections
  verbatim with a header noting their origin; new studies append in the same skeleton (question,
  arms, predictions table, what would change what I believe, rules, reporting rule, deviations, outcome).
- README voice: Anthus house style (plain, specific, numbers from files, no marketing), sections:
  what it measures and why (one paragraph, link the three articles), the vocabulary, quickstart
  (`make install && make replay`), how to add an engine / a task / a cue, how to run on your own data
  (milestone 2; say so), the record and spend logs, what it does not do (mitigation lives in Jev-Flywheel).
- RESULTS.md: generated; header with the date and the record's commit; one table per cue with engines
  as columns and tasks as rows; a shortlist table; footnotes for floors, lower-bound caveats, the
  swap-rule artefacts, and which cells are missing and why.

## Out of scope for milestone 1

New engines, new cues (dialect), your-own-data CLI, the learning-loop arms, any Jev or Laya call.

## Milestone 1b: the original Laya, not only the port (added 2026-09-23)

Every published Laya number came from `laya-mlx` (checkpoint `aac6fef/laya-mlx`, an FP16 Apple-silicon
conversion of one upstream checkpoint). The upstream `laya` package (github.com/NandhaKishorM/laya,
Apache-2.0, `pip install laya`, PyTorch, CPU or MPS) is the model as released and should be the
canonical `laya` engine; the port becomes `laya-mlx`, a second engine kept for comparison.

Plan: add `engines/laya.py` (upstream, via `laya.load()`; the port moves to `engines/laya_mlx.py`);
answer the `gender-pronouns` cue on all four tasks with the upstream model (free, local; ~26,000
texts); score; add a "port vs original" table to RESULTS.md. Pre-registered predictions, written
before any upstream answer exists: flip rates within ±1.0 point of the MLX numbers on every task
(7.65 / 7.95 / 13.5 / 17.85), direction shares within 3 points, accuracies within 1 point, the
four-pair ordering unchanged. If any task differs by more than that, the port is not a faithful
stand-in and every article number gets a footnote naming the difference; if all four agree, the
articles get one sentence saying the original reproduces the port. Either way the answers are
committed to the record so the check replays offline.

## Engine: a local LLM classifier with logprob confidence (added 2026-09-23, author's request)

Add `engines/llama.py`: a zero-shot LLM classifier in the style of
github.com/AnthusAI/Classification-with-Confidence — the same question and options rendered as a
prompt to a local Llama (via transformers on MPS or an MLX build), the answer read from the
logprobs of the option tokens (no sampling), and the probabilities normalised over the options so
the engine returns the record's shape. It is the "slow thinking" comparator without an API bill;
a variant that asks for a one-line reason first (chain of thought, then the answer token) gives the
System 1 vs System 2 contrast a number. Milestone: after batch 1's Laya runs; Laya-only-first policy
applies (free engines before Jev spend).

## Option order is part of a task (added 2026-09-23)

`question.yaml` carries `options:` as an ordered list and the record is keyed by it; `bd build`
refuses to answer a task whose committed order differs from the record's. See batch-1
pre-registration, section D, for why.
