# Pre-registration: expanded Civil Comments JEVPA replication

This is a new experiment after the first Civil Comments feasibility study did
not produce complementary candidates. It does not amend that result.

## Frozen corpus and blindness

The source is the CC0 `google/civil_comments` validation parquet, SHA-256
`2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03`.
The first study shuffled the source with seed `20260925` and reserved its first
30,000 rows as its complete working sample. This replication excludes every one
of those rows. It shuffles the remaining source with seed `20260926`, freezes a
new 30,000-row working sample, then writes its identifiers and manifest before
any analyst or Jev request.

The frozen sample supplies 500 discovery rows, 500 selection rows, and 1,000
random final-test rows. The selection set first reserves 150 rows with
`threat >= 0.3`, then 150 as-yet-unselected rows with `identity_attack >= 0.3`,
then fills from the pre-shuffled remainder. Discovery text and the binary target
`toxicity >= 0.5` are the only source fields shown to the analyst or placed in
the fitting workspace. `threat`, `identity_attack`, and every selection/test
label remain sealed until deterministic selection or final reporting.

The sealed threat and identity slices use a source score threshold of `0.1`.
Each must contain at least 50 toxic examples before it is included in Pareto
retention. This support check is recorded at corpus freeze but is not shown to
the analyst. The frozen split-manifest SHA-256 is
`f51122322224c299440623547592ef1daad3f8cf28c7068a56d7a69d5af5429e`.
At freeze time, the sealed threat slice contains 115 toxic rows and the sealed
identity-attack slice contains 121; both qualify. The held-out test contains
65 toxic rows and remains unread until a winner is frozen.

## Search and comparison

The base question is the same holistic toxicity moderation question as the
feasibility study. The analyst receives its residuals over the 500 discovery
labels and makes four shared initial calls. Host validation requires each call
to add exactly one new text-answerable element and forbids retirements and
rewordings; an invalid response gets one repair attempt. This is an execution
constraint, not a request for the analyst to choose among slice labels.

All valid shared candidates receive the same Jev answer cache. Greedy chooses
the lowest overall selection Brier candidate. JEVPA keeps at most four
nondominated candidates across overall selection Brier and the two qualifying
sealed-slice Briers. Each arm receives two further analyst calls using its
current retained candidates. Candidate proposals, rejected proposals, question
wording, cache fingerprints, and all actual Jev usage are retained.

The primary outcome is paired final-test Brier, JEVPA minus greedy. A positive
mechanism result requires a JEVPA-only merge of candidates specializing in
different qualifying slices, a Brier improvement of at least `0.005`, and no
accuracy loss greater than `0.02`. If a qualifying, distinct-specialist merge
does not win selection, stop before final requests and report that the mechanism
was not demonstrated.

## Fixed budget

There are eight analyst calls: four shared initial calls, two greedy calls, and
two JEVPA calls. Jev receives at most 4,500 item requests: 500 base discovery,
1,000 shared-initial discovery/selection, 2,000 branch discovery/selection, and
1,000 final-test. The first run measured 348,913 input and 67,740 output tokens
for 580 requests, costing `$2.2691229` at the documented Kimi K3 rates. This
replication forecasts conservatively at 800 input and 180 output tokens per
request, or `$25.245` for the 4,500-request ceiling at `$3.30`/million input and
`$16.50`/million output tokens. The provider ceiling, including analyst calls,
is `$35`; stop before a batch that would cross it.
