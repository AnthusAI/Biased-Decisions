# stereotypes-sexuality

Design B of the sexuality and gender-identity study
(`docs/sexuality-gender-identity-preregistration.md`): does saying a person is gay, lesbian,
bisexual, straight or transgender move a model's answers to trait questions toward a stereotype?
Seven yes/no questions (greed, violence, arrogance, worldliness, diligence, honesty,
safeguarding) are put to the same 2,000 biographies, each with one clause inserted. The clauses and
questions are test stimuli chosen because the stereotypes are documented in the sources the
pre-registration cites; they are not claims about any group.

**Status: imported, not scored.** This task holds the versions, the questions and one model's
answers. It is not scored by `bd replay`, is not on the leaderboard, and has no scorer yet: the
general trope scorer arrives with the batch-2 import (`tasks/stereotypes`). The staged numbers the
study itself produced are in `studies/veteran-sexuality/sexuality-design-b.jsonl` and
`sexuality-RESULTS.md`, for that scorer to be checked against.

## Sources

* The pool is `tasks/stereotypes/items.jsonl` (2,000 held-out Bias in Bios biographies, 500 per
  original task; sha256 `61d86f92be4feac94e4756e9c25521700b283590e1d80eb5e30ffe25636fc512`), brought in by
  the batch-2 import. It is not copied here. Same corpus, licence note and redaction as the four
  original tasks.
* `versions/sexuality.jsonl` (4 versions x 2,000 = 8,000 rows): `primary` is "A gay man, " for the
  biographies of men and "A lesbian, " for those of women; `bisexual` ("A bisexual man, " / "A
  bisexual woman, "), `straight` ("A straight man, " / "A straight woman, ") and the floor
  `floor-married` ("A married man, " / "A married woman, "). The clause matches the biography's own
  pronoun, so it never swaps the pronoun.
* `versions/gender-identity.jsonl` (2 versions x 2,000 = 4,000 rows): `transgender` ("A transgender
  man, " / "A transgender woman, ") and the floor `floor-woman` ("A man, " / "A woman, ").
* Both are the pool with the clause inserted before the first subject pronoun, pronoun
  lower-cased (`biased_decisions.cues.insertion.insert_clause`);
  `tests/veteran_sexuality_stereotypes_test.py` rebuilds them from the pool byte for byte as soon
  as the pool is present.
* `question.yaml`: the seven questions and the answer a stereotype would predict. Six are the
  batch-2 questions verbatim; `safeguarding` is new in this study and its predicted answer is "no".

## Answers

`answers/laya/stereotypes-sexuality/sexuality.jsonl.gz` (8,000 rows) and
`gender-identity.jsonl.gz` (4,000 rows), all seven questions per row. Model string
`laya-upstream:0.3.7` (this repository's `laya` engine, the original PyTorch build). Record shape as
every other record; each answer is `type: noul` with the probability of "yes".

## sha256

```
916c21e1a3fb1ccea6ae242ba207193c91167aa10147b8634690548f0359d09f  versions/sexuality.jsonl
1b67a3cfb628ff8dff0a3140276f16e428d069d1b7284b3259cb69e0c9e25376  versions/gender-identity.jsonl
566010a159ff79937e2cec2c28facb83e98328ff6b920bb8d1a5b678a721db43  question.yaml
```
