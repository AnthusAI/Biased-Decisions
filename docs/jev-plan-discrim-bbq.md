# Jev plan for discrim-eval and BBQ (a plan only: nothing has been sent)

Status 2026-09-24: no Jev request has been made and none is authorised by this file. Laya answers both
tasks first (`queue/discrim-bbq.txt`).

## Requests

One request per text, one yes-or-no question each.

| task and cue | versions | requests |
|---|---|---|
| `discrim-eval` `race` | 70 x 8 x 5 | 2,800 |
| `discrim-eval` `gender` | 70 x 8 x 3 | 1,680 |
| `discrim-eval` `age` | 70 x 8 x 9 | 5,040 |
| `discrim-eval` as-written | 70 | 70 |
| `bbq`, 22 cues | 300 items x 2 answers each | 13,200 (600 per cue) |
| `bbq` as-written | 6,600 | 6,600 |
| **all** | | **29,390** (9,590 discrim-eval, 19,800 BBQ) |

A smaller first step that keeps both designs: `discrim-eval` `race` (2,800) plus four BBQ cues on
characteristics the site already covers (`age-ambig`, `religion-ambig`, `sexual-orientation-ambig`,
`disability-status-ambig`; 2,400), 5,200 requests, a subset of the full scope.

## Token counts

Measured with Laya's own tokenizer on the committed texts (`tokenizers`, from the local model cache);
this is not Jev's tokenizer, which was not run, so treat the figures as approximate.

| task | texts | text tokens in all | mean per text |
|---|---|---|---|
| `discrim-eval` (items and all versions) | 9,590 | 1,376,718 | 144 |
| `bbq` (items and all versions) | 19,800 | 1,284,619 | 65 |
| both | 29,390 | 2,661,337 | 91 |

Each request also carries the question (about 13 tokens) and the option names, and Jev's own request
format adds tokens of its own. The only measured Jev figure in this repository is about 384 input and 38
output tokens per request on Bias-in-Bios texts (`docs/jev-plan-gendered-language.md`, from
`studies/batch1_jev_spend.md`); it is a rough guide only, because the texts differ in length. No output-token count exists for these tasks.

## Price

**No price is known and none is invented here.** The repository records tokens, not dollars (see the note
in `docs/jev-plan-gendered-language.md`). Fill Jev's current input and output rates before any approval.

## Decisions before any send

1. Whether to run Jev on these tasks at all, after Laya's result.
2. Approve the first step (5,200 requests) once the two rates are filled in, then the rest task by task.
3. The as-written BBQ set (6,600) is a reading check; it can be dropped for Jev if only the shifts matter.
