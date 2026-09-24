# stereotypes-batch3

Batch 3 of the benchmark: does naming a group move a model's answers toward a stereotype that a
published source documents? Twenty yes/no questions are put to the same 2,000 biographies as batch 2
(`tasks/stereotypes/`), each with one clause inserted, such as "A Japanese national, " or "A native
of Henan province, ", and each axis has a harmless same-shape clause as its floor. The clauses and
questions are test stimuli chosen because a source documents the stereotype; they are not claims
about any group. Pre-registration: `docs/batch3-preregistration.md`.

## Axes and versions

One versions file per axis (`versions/<axis>.jsonl`, rows are groups plus the floor times 2,000):
`nationality-x` (14 versions: batch 2's seven nationalities, six new, floor), `race` (6), `china`
(5), `india` (6), `africa` (6), `orientation` (5), `family` (5). The clause is inserted before the
first subject pronoun, pronoun lower-cased (`biased_decisions.cues.insertion.insert_clause`);
gendered clauses follow the bio's gender. `question.yaml` lists every question, the answer a
stereotype predicts, the axes it is scored on and the source.

## Sources (read only; none is redistributed here)

* SeeGULL v2 (Google Research, CC BY 4.0), `stereotypes_global_v2.csv`, sha256
  `0262db0b96c402e9340c88ee3e176af3591ff9f33fbf81541d35afbb7a81157d`, from
  `github.com/google-research-datasets/seegull`; `stereotypes_indian_states.csv`, sha256
  `1267e2358f44952453fb0f06193fe453c001f615b27b771c0a0959786826f2f3`.
* AfriStereo (arXiv 2511.22016), SAFARI (arXiv 2602.22404), IndRegBias (arXiv 2601.06477),
  WinoQueer (arXiv 2306.15087): read in full for the passages cited in the pre-registration.
* Verified directly in the source check (`docs/batch3-preregistration.md`, "Sources"): Pew Research,
  CKGSB, MIT Technology Review, Wikipedia (Anti-Henan sentiment, Hukou), ChinaFile, The Nanjinger,
  University of Huddersfield, a PMC review of pregnancy discrimination. Secondary sources read for
  this study: Journalist's Resource on Leavitt et al. 2015; Wikipedia on stereotypes of African
  Americans and of Hispanic and Latino Americans.
* Bios: the four original Bias in Bios tasks (same corpus, licence note and redaction as
  `tasks/stereotypes/`); `items.jsonl` is byte-identical to `tasks/stereotypes/items.jsonl`.

## Build

`biased_decisions/stereotypes_batch3.py`, registered in `biased_decisions/build.py`
(`build_stereotype_batch3_items`, then `build("<axis>", task)`); `biased_decisions/stereotypes_batch3_test.py`
checks each rebuild against the files below byte for byte.

## sha256

```
61d86f92be4feac94e4756e9c25521700b283590e1d80eb5e30ffe25636fc512  items.jsonl
26e21d691889260dd623a35db8291f5309f61f166286ab5b639708119c1cc54d  question.yaml
c7d439dbac0bf30e3bb7ab4ad94976f39f5e672d98e07a498a2e1b39855934fa  versions/nationality-x.jsonl
4768e5dad5e531d91c33920622350c7529911628bdd4d0f2b4884e2328d3844b  versions/race.jsonl
760a3239b0e79770f3f249dd96fe07d99ba8de15b0eacee7a6c47f537d97b053  versions/china.jsonl
2bb7cdf0fd5eb57660ca8502bb18c0fed0c0a16018af6f6a3809795b9e4645cd  versions/india.jsonl
245f3fe074276786dae278988fbf029a2dd08e6cea62190f84d5493b73b57bef  versions/africa.jsonl
e1feb06d661da0a833901ba2954b0486127e8547e7bac6d17be49fcae8cb23cd  versions/orientation.jsonl
fbb43d30bcebdd51bf84f52e37a31cc53786aaa8c03a2a9b0c11f0a9aa387e46  versions/family.jsonl
```

## Answers

None yet. `queue/batch3-global.txt` lists the Laya answer commands (`scripts/answer_tropes.py
stereotypes-batch3 <plan> --build laya`, 96,000 texts).

## Scoring

`bd replay` writes `studies/stereotypes-batch3-<axis>.jsonl` via `biased_decisions/metrics/tropes.py`,
plus a Holm-adjusted verdict per group and stereotype question.
