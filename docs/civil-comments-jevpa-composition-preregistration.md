# Pre-registration: JEVPA head-composition study

The expanded Civil Comments replication found two distinct selection-slice
winners, but their jointly refit feature head lost to the greedy head. A
post-hoc diagnostic found that their predicted probabilities were highly
correlated (0.980) and that fixed equal-probability averaging was slightly
better on selection. This study tests that composition hypothesis on untouched
data; it makes no claim about the earlier selection result.

## Data and blindness

Use the checksum-pinned `google/civil_comments` validation parquet, SHA-256
`2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03`.
Exclude the complete 30,000-row working samples generated with seeds
`20260925` and `20260926`, then shuffle the remaining rows with seed
`20260927` and take a new 30,000-row sample. Freeze and hash identifiers for
500 discovery rows, 500 selection rows, and 1,000 random final-test rows before
any Jev request. The analyst is not used in this study.
The frozen split-manifest SHA-256 is
`c8bb56f3e056d02d05568fabca419d7ab8384cda442d71c9fb0d3a9fd456202d`.

All models fit only the discovery toxicity labels (`toxicity >= 0.5`). Selection
and test labels are withheld from fitting. Source `threat` and `identity_attack`
are retained only for descriptive secondary reporting; they do not select a
model in this study.

## Fixed models

Question wording is copied unchanged from the prior replication:

1. **Greedy:** holistic toxicity question plus `substantive_argument`.
2. **Early fusion:** the greedy questions plus `targets_person`, with one joint
   deterministic head fit.
3. **Late fusion:** fit the Greedy and `targets_person` heads separately, then
   predict `P(remove)` as their fixed arithmetic mean. No blend weight is tuned.

All questions are sent together in one Jev request per item. The primary
selection quantity is overall Brier. The final test is requested only if late
fusion has lower selection Brier than both Greedy and early fusion, with no
selection accuracy loss greater than 0.02 against Greedy. The primary test
outcome is late-fusion Brier minus Greedy Brier. A positive result requires an
improvement of at least 0.005 and no accuracy loss over 0.02.

## Budget

At most 2,000 Jev item requests are made: 1,000 discovery plus selection, then
1,000 final-test if and only if the selection gate passes. At the conservative
800 input and 180 output tokens per request, the Jev ceiling is `$11.22` at
`$3.30`/million input and `$16.50`/million output tokens. Stop before a batch
that would exceed `$15` total provider cost.
