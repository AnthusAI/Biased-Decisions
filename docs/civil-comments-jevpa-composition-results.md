# Result: JEVPA head-composition study

Late fusion did not replicate its exploratory selection advantage from the
previous Civil Comments study. The held-out test was therefore not requested or
scored, as pre-registered.

## Frozen data

This study used the third Civil Comments working sample, excluding the complete
30,000-row samples from both prior studies. Its frozen split-manifest SHA-256
is `c8bb56f3e056d02d05568fabca419d7ab8384cda442d71c9fb0d3a9fd456202d`.
It has 500 discovery rows, 500 selection rows, and 1,000 held-out rows.

The three fixed models all fit only the discovery labels: Greedy used the
substantive-argument question; early fusion jointly refit substantive argument
and targets-person; late fusion averaged the separately fitted Greedy and
targets-person heads without tuning a blend weight.

| Model | Selection Brier | Selection accuracy |
| --- | ---: | ---: |
| Early fusion | 0.05259 | 0.936 |
| Greedy | 0.05356 | 0.934 |
| Late fusion | 0.05406 | 0.934 |
| Targets-person specialist | 0.05558 | 0.926 |

Late fusion was 0.00050 Brier worse than Greedy, so it failed the predeclared
selection gate. This falsifies the narrow composition hypothesis on this fresh
sample: retaining two separately fitted heads and averaging them is not, by
itself, a reliable way to turn the observed Pareto specialization into benefit.

The broader lesson is stronger than either prior negative result. Slice minima,
even when distinct, do not establish practically independent predictive signal.
Future JEVPA retention should require both objective diversity and a measurable
prediction-diversity or conditional-improvement criterion before spending on a
merged or ensemble model.
