# Milestone 1b outcome: the original Laya reproduces the MLX port (recorded 2026-09-23)

Engine: upstream `laya` 0.3.7 (`laya.load()` default English checkpoint, PyTorch on MPS), questions built
from each task's committed scorecard with the committed option order. Compared against the committed
`laya-mlx` record (aac6fef/laya-mlx, 0.1.0).

| task | port flip % | original flip % | verdict agreement | max abs dP |
|---|---|---|---|---|
| surgeon-physician | 7.95 | 7.95 | 3,996 / 4,000 | 0.013 |
| nurse-physician | 13.50 | 13.45 | 3,999 / 4,000 | 0.013 |
| teacher-professor | 7.65 | 7.75 | 3,998 / 4,000 | 0.006 |
| paralegal-attorney | 17.85 | 17.85 | 3,998 / 4,000 | 0.019 |

Predictions (written before any upstream answer): flip rates within +/-1.0 point: RIGHT on all four
(largest difference 0.1). Direction within 3 points: RIGHT (100% vs 99.3-100%). Accuracy within 1
point: RIGHT (identical to three decimals). Ordering unchanged: RIGHT.

Deviation: the first comparison listed the options in a different order than the committed scorecards
on three tasks and disagreed on 5-8% of verdicts; that is how the option-order effect was found (see
batch-1 pre-registration, section D). It was redone with the committed order; both runs are kept
(answers/ = wrong order for three tasks, answers-ordered/ = committed order).

Files here are the canonical `laya` record for the harness: answers/laya/<task>/gender-pronouns.jsonl.gz.
