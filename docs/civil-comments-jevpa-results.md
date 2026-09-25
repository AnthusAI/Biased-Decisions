# Civil Comments JEVPA result

**Result:** mechanism-inconclusive. The study stopped before final-test scoring
because the preregistered Pareto mechanism gate did not pass.

## Frozen corpus and spending

This run used the committed Civil Comments pre-registration and its frozen source
SHA-256 `2e0eb65474e7e1290df8689fc93eea783160c898c09ae15382c0a9662367bd03`.
The frozen split-manifest SHA-256 was
`425505d0ef5744fefa36374364c0b4feab981f317d866685f2dbacc30bcddfad`.

The discovery-base batch completed 140 of 140 Jev requests: 51,286 input and
4,620 output tokens, estimated $0.2455. The shared-initial batch completed 440
of 440 requests: 297,627 input and 63,120 output tokens, estimated $2.0236.
No branch or final-test Jev request was made.

The sealed selection slices had 116 threat rows (73 toxic) and 143
identity-attack rows (82 toxic). The held-out 500-row test remained sealed.

## Candidate selection

Four shared analyst slots were attempted. One response was invalid after its
allowed repair was truncated. Of the three parseable proposals, one reworded the
holistic toxicity question. Its 140 reworded-holistic answers had not been
priced or collected in the shared batch, so it was excluded rather than silently
using answers to different wording. The two candidates with complete answer
coverage were fit only on the 140 discovery labels.

| candidate | elements | overall Brier | threat Brier | identity-attack Brier |
|---|---|---:|---:|---:|
| initial:3 | identifiable-person target; political opinion | 0.2952 | 0.4465 | 0.4140 |
| initial:4 | personal insult or profanity | 0.2976 | 0.4511 | 0.4188 |

`initial:3` is lower on every selection objective. It is therefore the only
member of the Pareto pool. There are no distinct slice specialists and no
JEVPA-only compatible merge. The pre-registration requires stopping before
final scoring in this case, so the study makes no claim about held-out benefit.

## Interpretation

The real corpus supported the sealed slices and the analyst generated plausible
moderation questions, but this run did not create the complementary retained
candidates that JEVPA needs. It is evidence that the mechanism did not activate
on this fixed split, not evidence that greedy search wins in general.
