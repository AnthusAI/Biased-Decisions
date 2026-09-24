# Jev plan for the housing, lending and hiring tasks (a plan only: nothing has been sent)

Status 2026-09-24: no Jev request has been made and none is authorised by this file. Laya answers the
whole design first (`queue/housing-lending.txt`); Jev is priced and capped before any send, following
`docs/jev-plan-gendered-language.md`.

## Requests

One request per text, each a single yes-or-no question. Every text is synthetic, so no personal data
leaves the repository.

| task | cue | requests | text tokens (Laya tokenizer) |
|---|---|---|---|
| `tenant-inquiry-viewing` | `race-name` | 3,000 | 287,775 |
| | `family-status` | 5,000 | 479,595 |
| | `disability` | 2,000 | 191,638 |
| | `religion` | 5,000 | 481,595 |
| | as-written | 1,000 | 90,319 |
| `small-business-loan` | `owner-identity` | 6,000 | 528,282 |
| | `owner-age` | 2,000 | 180,094 |
| | `race-name` | 3,000 | 260,017 |
| | as-written | 1,000 | 81,047 |
| `resume-screening` | `race-name` | 3,000 | 208,274 |
| | `age-inserted` | 2,000 | 143,616 |
| | `disability` | 2,000 | 138,616 |
| | `veteran-status` | 3,000 | 214,424 |
| | `religion` | 5,000 | 349,040 |
| | as-written | 1,000 | 63,808 |
| **Full scope** | | **44,000** | **3,698,139** |

Token counts are of the text alone, with Laya's own tokenizer; Jev's tokenizer and its wrapper around
the question and options are not measured here, so the input figure sent to Jev is larger by an
amount only a priced first send can show.

## Suggested order

1. **Go/no-go subsample, 6,000 requests, priced first:** the first 500 items (id order) of
   `tenant-inquiry-viewing/race-name` (1,500), `small-business-loan/owner-identity` (3,000) and
   `resume-screening/race-name` (1,500); about 0.51 million text tokens. This replaces the wrapper
   estimate with a measured one.
2. Then family by family, only after the go/no-go is read against the pre-registered predictions:
   the housing cells (15,000 plus 1,000), the lending cells (11,000 plus 1,000), the resume cells
   (15,000 plus 1,000).

Output is a probability per option; the only output figure on record is Jev's measured 38 tokens per
request on the biography tasks (`docs/jev-plan-gendered-language.md`), which would put the full scope
at about 1.7 million output tokens. No dollar price is recorded in the repository and none is invented
here.

## Decisions before any send

1. Approve the go/no-go (6,000 requests) once Jev's two rates are filled in.
2. Cap: 44,000 requests plus at most 5% retries, approved family by family, not as one number.
3. A Jev runner for these tasks is `scripts/answer_task.py` with the Jev engine as it exists on main;
   its build flag and cache behaviour were not changed here.
4. Kev's registration is separate: `docs/kev-amendments.md`.

## First-pass subsample

The still-unanswered cells of this plan are first answered on the fixed, nested subsample of `docs/subsample-preregistration.md` (500 items per cell); the design, questions, versions and scoring above are unchanged.
