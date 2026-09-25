# Pre-registration: JEVPA on Civil Comments

This study tests whether retaining complementary moderation candidates improves a
decision model over greedy search on real, public comment text. It is separate
from `tasks/civil-comments-moderation`, whose low-toxicity, identity-neutral pool
exists for causal identity-insertion measurements and is not used here.

## Corpus and separation

Use the CC0 `google/civil_comments` validation parquet pinned by SHA-256. The
target is `toxicity >= 0.5`. Fix a seeded 30,000-row working sample before any
analyst call: 140 discovery labels, a 300-row selection set, and a 500-row
random final-test set; the remaining sampled rows are unused. The analyst sees
discovery text and the binary toxicity label only.

The source `threat` and `identity_attack` scores are never shown to the analyst
and never used for fitting. The selection set reserves 100 rows with each score
at or above 0.3, taking threat first and then nonselected identity-attack rows;
the remaining 100 rows follow the seeded source order. These fields define sealed
selection slices at score >= 0.3. Each must contain at least 50 toxic rows to
participate in Pareto retention. The final test remains random and unstratified.

## Arms and gates

Greedy and JEVPA receive four shared initial proposals and two further proposals
per arm. They share each valid candidate question and Jev answer cache. Every
head fits only the 140 discovery labels. Selection uses overall Brier; JEVPA also
retains a pool of at most four nondominated candidates on the sealed threat and
identity-attack slices.

The primary outcome is paired final-test Brier, JEVPA minus greedy. A positive
result requires: a JEVPA-only merge of candidates specializing in different
qualifying slices; Brier improvement of at least 0.005; and no accuracy loss over
0.02. If no qualifying, unique merge wins selection, stop before final scoring and
report a mechanism-inconclusive result.

No analyst or engine call may occur until the corpus builder writes and hashes the
three ID lists, the split hash, candidate budget, and request budget.

## Frozen execution declaration

The source SHA-256 is
`2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03`.
The generated split manifest SHA-256 is
`425505d0ef5744fefa36374364c0b4feab981f317d866685f2dbacc30bcddfad`.
At freeze time, the sealed selection slices contain 73 toxic threat rows and
82 toxic identity-attack rows; both pass the support rule. The final test has
26 toxic rows and remains unread until a winner is frozen.

The budget is eight analyst calls: four shared initial calls, then two greedy
and two JEVPA branch calls. Jev has at most three batches: 440 shared-initial,
880 branch, and 500 final-test item requests, for a cap of 1,820. The analyst
uses Bedrock `us.moonshotai.kimi-k3`, Standard tier. At the current US cross-
region rate of $3.30 per million input tokens and $16.50 per million output
tokens, the Jev forecast uses 1,000 input and 300 output tokens per request:
$14.88 for the 1,820-request ceiling. The study's provider-cost ceiling is
$20, including analyst calls. Stop a batch before exceeding either ceiling.
