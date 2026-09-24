# stereotypes-veteran

Design B of the veteran-status study (`docs/veteran-status-preregistration.md`): does saying a
person is a veteran move a model's answers to trait questions toward a stereotype? Eight yes/no
questions (greed, violence, arrogance, worldliness, diligence, honesty, rigidity, loyalty) are put
to the same 2,000 biographies, each with one clause inserted ("A veteran of the Iraq war, ", "A
veteran of the Navy, "), plus a harmless floor clause of the same size ("A veteran of the Peace
Corps, "). The clauses and questions are test stimuli chosen because the stereotypes are
documented in the sources the pre-registration cites; they are not claims about any group.

**Status: imported, not scored.** This task holds the versions, the questions and one model's
answers. It is not scored by `bd replay`, is not on the leaderboard, and has no scorer yet: the
general trope scorer arrives with the batch-2 import (`tasks/stereotypes`). The staged numbers the
study itself produced are in `studies/veteran-sexuality/veteran-status-design-b.jsonl` and
`veteran-status-RESULTS.md`, for that scorer to be checked against.

## Sources

* The pool is `tasks/stereotypes/items.jsonl` (2,000 held-out Bias in Bios biographies, 500 per
  original task; sha256 `61d86f92be4feac94e4756e9c25521700b283590e1d80eb5e30ffe25636fc512`), brought in by
  the batch-2 import. It is not copied here. Same corpus, licence note and redaction as the four
  original tasks.
* `versions/veteran.jsonl` (3 versions x 2,000 = 6,000 rows): the clause inserted before the first
  subject pronoun, pronoun lower-cased (`biased_decisions.cues.insertion.insert_clause`), the
  same clauses as `veteran-status` on the seven occupation tasks
  (`biased_decisions.cues.insertion.VETERAN_STATUS`).
  `tests/veteran_sexuality_stereotypes_test.py` rebuilds it from the pool byte for byte as soon as
  the pool is present.
* `question.yaml`: the eight questions and the answer a stereotype would predict. Six are the
  batch-2 questions verbatim; `rigidity` and `loyalty` are new in this study.

## Answers

`answers/laya/stereotypes-veteran/veteran.jsonl.gz`, 6,000 rows, one per version row, all eight
questions per row. Model string `laya-upstream:0.3.7` (this repository's `laya` engine, the
original PyTorch build). Record shape as every other record; each answer is `type: noul` with the
probability of "yes".

## sha256

```
76f5f290c6a18edeae3b1fe13c981b527e5ba0b47117dd4e17ef50767bfcb58b  versions/veteran.jsonl
ef017e21140e46f4ae08fd4eb1413edbb5975e670b484e0b33830113ac70f59f  question.yaml
```
