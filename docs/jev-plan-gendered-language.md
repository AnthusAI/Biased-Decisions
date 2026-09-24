# Jev plan for the gendered-language studies (a plan only: nothing has been sent)

Status 2026-09-24: no Jev request has been made and none is authorised by this file. Jev is priced
and capped first, per `docs/gendered-language-preregistration.md` ("Rules") and the free-models-first
convention; Laya answers the whole design first (`queue/gendered-language.txt`).

## Scope (the three strongest-sourced pairs, on the 2,000-biography pool)

Pairs: `assertive-bossy`, `direct-abrasive`, `confident-aggressive`. Eligible biographies: 1,872 (see
the pre-registration's Deviations; the registered two-task scale of about 48,000 for Design 1 became
the pool because the tasks were built on the pool).

| step | requests | commands (Jev runner form) |
|---|---|---|
| Go/no-go subsample, priced before anything else | 5,000 | first 500 eligible biographies (id order) of `gendered-management/assertive-bossy` (2,000), `gendered-advance/agentic-communal` (2,000), `gendered-word-choice/assertive-bossy` (1,000) |
| Design 1, `gendered-management`, 3 pairs x 7,488 | 22,464 | one request per version text, cues `assertive-bossy`, `direct-abrasive`, `confident-aggressive` |
| Design 2, `gendered-word-choice`, 3 pairs x 3,744 | 11,232 | same three cues; the per-row question and option order are sent as stored |
| Design 3, `gendered-advance`, 1 cue x 7,488 | 7,488 | cue `agentic-communal` |
| Full scope | 41,184 | the go/no-go subsample is a subset of it |

Cap: 41,184 requests plus at most 5% retries, to be approved family by family, not as one number.
The Jev runner for these tasks does not exist yet; it must accept the per-row question for
`gendered-word-choice` (as `scripts/answer_wordchoice.py` does for Laya) before any request is sent.

## Price estimate

The repository records tokens, not dollars: `studies/batch1_jev_spend.md` and
`studies/jev-flywheel/*_spend.md` state that no price per request is exposed anywhere, so **no dollar
price is recorded in the repository docs and none is invented here**. What is recorded, measured on Jev's
own bio requests (`jev-1.13.0`, batch 1's first file: 4,000 requests, 1,537,513 input and 150,058
output tokens), is about 384 input and 38 output tokens per request.

| scope | requests | input tokens (about) | output tokens (about) |
|---|---|---|---|
| go/no-go | 5,000 | 1.9 million | 0.19 million |
| Design 1 | 22,464 | 8.6 million | 0.84 million |
| Design 2 | 11,232 | 4.3 million | 0.42 million |
| Design 3 | 7,488 | 2.9 million | 0.28 million |
| full scope | 41,184 | 15.8 million | 1.5 million |

Cost = input tokens x Jev's input rate + output tokens x Jev's output rate. Fill the two rates from
Jev's current price page before approval; then the full scope is 15.8 x (input rate per million) +
1.5 x (output rate per million) in dollars. The word-choice question is a little longer than a yes/no
question, so its input count is a slight underestimate; the go/no-go run replaces this estimate with
a measured one.

## Decisions before any send

1. Approve the go/no-go (5,000 requests) once the two rates are filled in.
2. Read the go/no-go against the registered predictions' Jev columns; go on to the full scope only if the
   spend and the result justify it.
3. Kev and Jev share none of these requests; Kev's registration is in `docs/kev-amendments.md`.
