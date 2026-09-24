# stereotypes

Batch 2 of the benchmark: does naming a religion or a nationality move a model's answers toward a
stereotype? Six yes/no questions (greed, violence, arrogance, worldliness, diligence, honesty) are
put to the same 2,000 biographies, each with one clause inserted such as "A devout Muslim, " or
"An American, ", and each axis has a harmless floor clause of the same size ("A devoted gardener, ",
"A keen cyclist, "). The clauses and questions are test stimuli chosen because these stereotypes are
documented in the sources the pre-registration cites (BBQ, Parrish et al. 2022; ADL and Pew
surveys); they are not claims about any group. Pre-registration: `studies/PREREGISTERED.md`,
section "Batch 2".

## Sources

* `items.jsonl`: 2,000 biographies from the held-out split of the four original Bias in Bios tasks
  (`surgeon-physician`, `nurse-physician`, `teacher-professor`, `paralegal-attorney`; same corpus,
  licence note and redaction as those tasks). Those biographies whose first subject pronoun opens
  a sentence are eligible; 500 per task are drawn with `random.Random(0)`. Ids are
  `<source task>-<original id>` because two source tasks share physician biographies.
* `versions/religion.jsonl` (6 versions x 2,000) and `versions/nationality.jsonl` (8 x 2,000): the
  clause inserted before the first subject pronoun, pronoun lower-cased
  (`biased_decisions.cues.insertion.insert_clause`).
* `question.yaml`: the six questions and the answer a stereotype would predict.

## Build

Rebuilt from the four source tasks by `biased_decisions/stereotypes.py`, registered in
`biased_decisions/build.py` (`build_stereotype_items`, then `build("religion" | "nationality",
task)`); `biased_decisions/stereotypes_test.py` checks each rebuild against the files below byte
for byte.

## sha256

```
61d86f92be4feac94e4756e9c25521700b283590e1d80eb5e30ffe25636fc512  items.jsonl
dfcb903b2d7dad9524f444b045a633d79c6b8a9e3941881c15c64ec08d80d768  versions/religion.jsonl
828aad665c6901228018edc633b3164c1fbcf5ef9595c7057d705a5ae2dafb6a  versions/nationality.jsonl
69459c61da996e8f4de93945861933e01b9cbc1e0e9b29509ca5b55489d00f0e  question.yaml
```

## Answers

`answers/laya/stereotypes/{as-written,religion,nationality}.jsonl.gz` (2,000 + 12,000 + 16,000
rows): Laya, the original PyTorch build, model string `laya-upstream:0.3.7`, six `noul` answers per
text in one call (`answers.<question>.noul` is P(yes)). Imported unchanged from the build in which
they were produced; sha256 of the gzip files:

```
2fb45f8a6f31f5f2893779dd3c54dbd0892fabcd129e4d1c3f7baab97b0edd1f  as-written.jsonl.gz
4f3dba84bc649ecf54034d1995a8453146cdbd884005c3d6e110b369d4e45440  religion.jsonl.gz
6ed69957567f2c3b369f734735cf7856a854c5f4d672e2b1cd8b509d0d45499a  nationality.jsonl.gz
```

## Scoring

`bd replay` writes `studies/stereotypes-religion.jsonl` and `studies/stereotypes-nationality.jsonl`
via `biased_decisions/metrics/tropes.py`; the rows reproduce `studies/batch2/stereotypes-laya.jsonl`
at its published precision. See `docs/integration/batch2-import.md`.
