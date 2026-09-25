# Result: expanded Civil Comments JEVPA replication

The preregistered JEVPA mechanism was visible at the shared-initial stage but
did not survive the selection gate. Accordingly, the 1,000-row held-out test
was not requested or scored.

## Frozen data and initial candidates

The replication used the checksum-pinned Civil Comments validation parquet and
a new 30,000-row working sample disjoint from every row in the first study's
sample. The split-manifest SHA-256 was
`f51122322224c299440623547592ef1daad3f8cf28c7068a56d7a69d5af5429e`.
It contained 500 discovery labels, 500 slice-enriched selection rows, and
1,000 withheld rows. The selection slices had 181 threat rows and 212
identity-attack rows.

The 500 base predictions produced 72 discovery disagreements. Four constrained
initial calls each added one element. Candidate 2 won overall selection Brier
and the identity-attack slice; candidate 4 won the threat slice. This yielded
a Pareto pool of candidates 2 and 4, with distinct sealed-slice specialists.

| Candidate | Overall Brier | Threat Brier | Identity-attack Brier |
| --- | ---: | ---: | ---: |
| Initial 2, substantive argument | 0.18308 | 0.29447 | 0.26344 |
| Initial 4, targets person | 0.18413 | 0.29674 | 0.26112 |

## Branch and gate result

Greedy kept initial candidate 2. JEVPA merged candidates 2 and 4, then each
arm received two new one-element proposals. None of the four branch candidates
beat its arm's starting model on overall selection Brier.

The decisive comparison was therefore the retained greedy candidate versus the
two-specialist JEVPA merge:

| Selected model | Overall Brier | Accuracy |
| --- | ---: | ---: |
| Greedy initial candidate 2 | 0.18308 | 0.742 |
| JEVPA merge of candidates 2 and 4 | 0.18839 | 0.728 |

The merge was worse by 0.00531 Brier and 0.014 accuracy on selection. It did
not win selection, so the pre-registration requires stopping before final-test
requests. The result is mechanism-inconclusive: the retained candidates did
specialize, but their merge did not provide a usable decision-model benefit.

## Execution record

Jev completed 3,500 item requests: 500 base, 1,000 shared-initial, and 1,000
for each branch. The directly persisted reports record `$0.8849478` for base,
`$2.8687098` for greedy branch, and `$2.8225098` for Pareto branch. The shared
initial command was interrupted after cache writes completed, so its persisted
report was overwritten by a zero-request resume and cannot support an exact
token-cost claim. Its 1,000 completed item requests are visible in the cache.

An execution error also produced three duplicate analyst responses after a
local command window expired while the original process continued. The analysis
used the first response recorded for each of the four preregistered shared slots,
retained all seven responses in the local audit trail, and did not use the extra
responses for candidate selection. This is a protocol deviation and rules out
confirmatory interpretation; it does not alter the selection-gate calculation.
