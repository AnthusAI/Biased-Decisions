# Veteran status, sexuality and gender identity: imported studies

Two studies pre-registered in `docs/veteran-status-preregistration.md` and
`docs/sexuality-gender-identity-preregistration.md`, built and answered by Laya outside this
repository and imported here as replayable tests.

| file | what it is |
|---|---|
| `veteran-status-RESULTS.md`, `sexuality-RESULTS.md` | the studies' own results write-ups, as produced (only the pre-registration path was made relative) |
| `veteran-status-design-a.jsonl`, `sexuality-design-a.jsonl` | the studies' own scored rows for the occupation decisions (design A); `bd replay` reproduces their shifts and flip rates (`tests/veteran_sexuality_replay_test.py`) |
| `veteran-status-design-b.jsonl`, `sexuality-design-b.jsonl` | the studies' own scored rows for the stereotype questions (design B). **Staged, not reproduced**: no scorer in this repository reads design B yet; they are the numbers the general stereotype scorer of the batch-2 import must reproduce |

The replayed rows are `studies/<task>-veteran-status.jsonl`, `<task>-sexuality.jsonl` and
`<task>-gender-identity.jsonl`, written by `bd replay` like every other cue.

## What answered

Every answer is Laya, the original PyTorch package, recorded as `laya-upstream:0.3.7`, which is
this repository's `laya` engine. Version 0.3.7 is no longer installable from the package index; the
sexuality run installed it from the upstream tag `v0.3.7` (commit
`2f3c81a16230a3defa45edde45a15b2bde356b54`) with `transformers` 5.17.0 and `torch` 2.14.0, and the
model weights resolved to commit `5e7b2b1b8ca2ecdd3f2322d94069c9b6ce7e844b` of
`convaiinnovations/laya`. `laya.load()` takes no revision, so the package version does not pin the
weights. The veteran run's environment was not recorded at the time, so whether it used the same
weights commit cannot be confirmed.

## A partial run of a newer version, left out

While the 0.3.7 install was blocked, the sexuality study answered part of design A with
`laya-upstream:0.3.9` (`laya==0.3.9`, the newest release) as a drift record. That run is
**incomplete** (three of its 14 design-A files finished, one more half done, no design B) and is
therefore **not imported**: no `laya-0.3.9` record exists in `answers/`. Where it overlapped, its
first spot-check answer matched the 0.3.7 answer exactly (same weights); nothing further was
compared. If it is ever completed it belongs under its own engine name, never under `laya`.

## Scored differently from the study scripts, on purpose

The studies' scripts drew one random stream across all tasks and read interval ends by linear
interpolation. The harness scores each cell on its own (seed 0, 1,000 resamples, the house
percentile), so interval ends differ by a few hundredths of a point and always fall on the same
side of zero. Shifts, flip rates and counts agree at two decimals.
