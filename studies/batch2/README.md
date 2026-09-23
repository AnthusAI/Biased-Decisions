# Batch 2: stereotype and trope axes (staged, not yet in the harness)

`stereotypes-laya.jsonl` and `RESULTS.md` are byte-for-byte copies (`cp -p`, 2026-09-23) of
`var/batch2/results.jsonl` and `var/batch2/RESULTS.md` from the Biased-Decisions tooling checkout,
where batch 2 (pre-registered in `studies/PREREGISTERED.md`, section "Batch 2") was built and
answered by the original `laya` 0.3.7 only. The answer record (`answers/laya/stereotypes/...`) and
the scoring script live in that staging area and are **not yet ported into this package**: `bd
replay` does not produce these rows and cannot regenerate them.

They are here as a second, clearly labelled data source for the leaderboard (`bd report --json`
reads them and marks every number that came from them with `"source": "batch2-staging"`). When
batch 2 is ported into the harness, this directory is replaced by `bd replay` output and the
leaderboard's second source goes away.
