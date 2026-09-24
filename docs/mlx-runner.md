# Running the answer scripts on either Laya build

Both `scripts/answer_task.py` (one question per text) and `scripts/answer_tropes.py` (many
questions per text) take `--build laya|laya-mlx`. The default is `laya`.

| Build | Package | Records go to | `model` string in each row |
|---|---|---|---|
| `laya` | PyTorch `laya` 0.3.7 | `answers/laya/<task>/<cue>.jsonl.gz` | `laya-upstream:0.3.7` |
| `laya-mlx` | Apple MLX `laya-mlx` 0.1.0 | `answers/laya-mlx/<task>/<cue>.jsonl.gz` | `laya-mlx:0.1.0` |

```bash
python3 scripts/answer_task.py   <task> <cue> --build laya-mlx
python3 scripts/answer_tropes.py <task> as-written --build laya-mlx
```

## Interpreters

- `laya`: any environment with `laya==0.3.7` (for example the `laya-venv-0.3.7` venv in the tooling folder).
- `laya-mlx`: an environment with `laya-mlx==0.1.0`, `pyyaml` and this repository on `PYTHONPATH`.
  Run with `PYTHONPATH=<worktree> <interpreter> scripts/answer_tropes.py ...`.

The MLX path applies the harness guards in `biased_decisions/engines/laya_mlx.py`: it refuses any
request the 512-token window would silently truncate.

## Measurements (20 texts, 24 noul questions, `stereotypes-antisemitism`, first 20 rows of `items.jsonl`)

Both runs happened while a long PyTorch job held the GPU, so times are indicative only.

- MLX: 35.7 s (0.6 texts/s). PyTorch: 37.6 s (0.5 texts/s). Under this contention the two are
  about equal; a speed advantage was not demonstrated. Single-question speed was not measured.
- The noul (P(yes)) question type works on the MLX path. Each row has all 24 answers in the same shape
  as PyTorch (`type`, `noul`, `confidence`, `action`); MLX rounds to 3 decimals in the row.
- Maximum absolute difference in P(yes) against the existing PyTorch record
  (`answers/laya/stereotypes-antisemitism/as-written.jsonl.gz`, same 20 texts, 480 answers): 0.0092;
  mean 0.00025.
- Existing bios records, `paralegal-attorney/gender-pronouns`, 4000 rows, `answers/laya` against
  `answers/laya-mlx`: maximum absolute difference in P is 0.0194. That is larger than "three
  decimals" (0.0005); most answers agree closely, but a few differ in the second decimal (FP16
  conversion).

## Recommendation

Use `laya-mlx` for runs where a difference up to about 0.02 in a single probability is acceptable
(group-level rates are unaffected in practice), and keep one build per study: never mix builds inside
a study's comparison of a cue against its control. Where numbers must match the published PyTorch
records exactly, use `laya`. Re-measure speed when the GPU is free before scheduling large queues on MLX.
