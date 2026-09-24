# Integration note: discrim-eval and BBQ (package discrim-bbq)

For the leaderboard integrator. Nothing here edits `leaderboard.py`, `compliance.py` or `site/`.
Plain wording follows `docs/plain-language.md`. No model has answered these tasks yet.

## What is in the repository

| piece | where |
|---|---|
| tasks | `tasks/discrim-eval/`, `tasks/bbq/` (README with source, licence, sha256 and counts; `build.py`, `build_test.py`) |
| shared builders | `biased_decisions/discrim_bbq.py` |
| scoring shapes | `REGULATED_SHAPE["discrim-eval"]` and `REGULATED_SHAPE["bbq"]` in `biased_decisions/scoring.py`; `bd replay` visits them like Q-Pain |
| answers to run | `queue/discrim-bbq.txt` (29,390 texts, about 25 minutes at the documented Laya rate; estimated, not measured) |
| Jev plan, no runs | `docs/jev-plan-discrim-bbq.md` |
| Kev registration | `docs/kev-coverage-discrim-bbq.json` and the amendment in `docs/kev-amendments.md` |

Rows are the regulated-shape rows of `studies/<task>-<cue>.jsonl`: `versions` (each with `mean_pts`,
`ci_pts`, `flip_vs_floor_pct`), `n` and `positive`, the same fields the shift board already reads for
Q-Pain.

## discrim-eval: three cells on three existing boards

The decision: 70 short hypothetical decisions about one person (approve a loan, grant a visa, prioritise
a kidney transplant), each ending with a question whose "yes" helps the person. A model that says "yes"
less often for some people than for others is treating them worse. The text is the dataset's own,
unchanged; only the stated race, gender or age of the person differs.

| cue | board | groups (version names) | comparison | rows per run |
|---|---|---|---|---|
| `race` | race | `black`, `asian`, `hispanic`, `native-american` | `white` | 2,800 texts, 560 sources |
| `gender` | gender | `female`, `non-binary` | `male` | 1,680 texts, 560 sources |
| `age` | age | `age-20` ... `age-50`, `age-70` ... `age-100` | `age-60` | 5,040 texts, 560 sources |

- **The comparison is not a harmless edit.** Unlike the cyclist or Peace Corps phrases, the reference
  is another value of the same characteristic (the same choice as Q-Pain's race and gender cells, and
  as the CFPB age cell). Label each cell "compared with a white man" and "compared with a 60-year-old",
  not "compared with a harmless edit". The reference person (white, male, 60) is this project's choice.
- **Age has eight versions.** The dataset card suggests one score for the younger ages (20 to 50) and one
  for the older (70 to 100), each against 60 (read on the card). The row has every age; the board
  can show `age-20` and `age-100` as the two ends, or the mean of each side, which the row supports but
  does not compute.
- **Items:** one task, `discrim-eval`; the 70 scenarios are pooled inside each row. Item ids in the texts
  are `discrim-00` to `discrim-95` (the dataset's own numbering has gaps; 70 exist). Version ids are
  `discrim-<scenario>-<background>-<cue>-<version>`, for example `discrim-07-age40-female-race-black`.
- **Sample size:** 560 sources (70 scenarios x 8 people) per cue; 9,520 version texts. The eight people
  per scenario are a fixed seeded draw of the other two characteristics.
- **Gender caveat for the page:** the dataset's own texts for the three genders differ in pronouns and in
  the phrase around the noun, not in one word. Say "the same decision written for a man, a woman or a
  non-binary person", not "we changed one word".
- **Compliance mapping.** Regulated in the sense the site uses: the decisions are about people's access
  to credit, housing, insurance, health care and similar. `docs/datasets-survey.md` (section 1) maps the
  loan and credit-line scenarios to the Equal Credit Opportunity Act and Regulation B and the lease
  scenarios to the Fair Housing Act, and says the scenarios were not written against any statute, so the
  mapping is this project's own. The quotations of the rules are in the compliance package
  (`docs/legal-sources.md` on the branch `feat/pkg-compliance-map`); I did not read that branch and copy
  nothing from it. For the site: "may bear on", and say the scenarios are invented, not real cases.

Proposed plain wording:

- Race: "We gave the model the same short decision (for example, whether to approve a loan) about a
  white person, a Black person, an Asian person, a Hispanic person or a Native American person, and
  asked whether the decision should go in the person's favour. We compared each with the white
  person."
- Gender: "The same decision written for a man, a woman or a non-binary person. We compared each with
  the man."
- Age: "The same decision written for a person aged 20 to 100. We compared each age with age 60."
- One-sentence definition for the page: a decision is a short description of one person and a request
  ("should we approve this loan?"); "in the person's favour" means the answer that helps them.

## BBQ: twenty-two cells, a check across categories, not a business decision

BBQ is a public benchmark of questions about two people in a short scene. The text is the benchmark's
own. Because the harness asks yes-or-no questions, each item is asked twice, once with each named
answer proposed ("Proposed answer: The grandfather"), and the model says whether the proposed answer
is correct. The row says how much more often the model accepts the answer that fits a stereotype than
the other person's answer. In an "unclear" scene (nothing says who is meant) both answers are wrong; in a
"clear" scene (a second sentence settles it) the balanced items make a model that reads well score
about zero.

| BBQ category | cues | board (proposal) |
|---|---|---|
| Age | `age-ambig`, `age-disambig` | age |
| Disability_status | `disability-status-ambig`, `-disambig` | disability |
| Gender_identity | `gender-identity-ambig`, `-disambig` | gender |
| Nationality | `nationality-ambig`, `-disambig` | nationality |
| Physical_appearance | `physical-appearance-ambig`, `-disambig` | **new board: appearance** (no board today) |
| Race_ethnicity | `race-ethnicity-ambig`, `-disambig` | race |
| Race_x_gender | `race-x-gender-ambig`, `-disambig` | race (and gender; one cell can sit on both) |
| Race_x_SES | `race-x-ses-ambig`, `-disambig` | race (and the new economic-status board) |
| Religion | `religion-ambig`, `-disambig` | religion |
| SES | `ses-ambig`, `-disambig` | **new board: income and wealth** (no board today) |
| Sexual_orientation | `sexual-orientation-ambig`, `-disambig` | sexuality |

- **Groups and control:** one group per cell, `bias-consistent` ("the person the stereotype fits");
  the comparison is `other` ("the other person"). Neither is a demographic group name; the benchmark's
  own group tags are in each item's metadata (`stereotyped_groups`) for a drill-down.
- **Which answer "fits the stereotype":** the benchmark's own file decides (`target_loc`); it is checked
  on nine of the eleven categories and **not checked** on Race_x_SES and Race_x_gender (see the task
  README). Do not put those two on a board before that is looked at again.
- **Items and ids:** `bbq-<category>-<example id>`; version ids add `-<cue>-<bias-consistent|other>`.
- **Sample size:** 300 items per cue (150 per balance stratum), 600 texts per cue, 13,200 in all; 6,600
  as-written texts (the "cannot be determined" answer proposed) as a reading check.
- **Not a regulated decision.** Nothing in BBQ is a decision about a person's outcome, so the compliance
  block should say so (`regulated: False`, no rule named) and the page should call it a public
  benchmark used as a cross-check, as `docs/datasets-survey.md` (section 7) proposes.
- **Not BBQ's own score.** BBQ reports accuracy and a bias score over three-way answers; this is a
  yes-or-no reading of the same design and its numbers must not be set beside published BBQ scores.

Proposed plain wording:

- "We took public test questions about two people in a short scene, for example a grandfather and a
  grandson trying to book a cab. We proposed each person as the answer to a question such as 'Who was
  not comfortable using the phone?' and asked the model whether the proposed answer is correct. We
  compare how often it accepts the person a stereotype would pick with how often it accepts the other
  person."
- One-sentence definition: BBQ is a public benchmark of questions that test whether a model leans on
  stereotypes when a scene does not say who is meant.
- Say once on the page that the scenes are invented and that a stereotype named in a test is a claim
  made by the benchmark's authors, not a fact.

## Kev

The registration is `docs/kev-coverage-discrim-bbq.json` (25 cells, 22,720 requests) with its amendment
in `docs/kev-amendments.md`, made before any Kev answer.
