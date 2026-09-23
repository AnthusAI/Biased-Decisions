# Writing for a reader who has never heard of this project

Every word on the public site is written for one person: someone smart who has never seen this
project, does not know machine learning, and is deciding whether a fast AI model can be trusted to
screen people. An HR lead, a lawyer, a journalist, a curious parent. If the person who built the
site cannot follow a sentence cold, the sentence is wrong. `site/test/plain-language.test.mjs`
fails the build on the words below, so the rule holds after this pass.

## The rules

1. **Say what it is, then why it matters, then what we found.** Every page opens with one plain
   sentence saying what the page shows. Numbers come after the reader knows what they measure.
2. **Name the model as the subject, and say what it did.** "Laya changed its answer on 17.85 of
   every 100 bios when only the word 'he' became 'she'." Never "the bias is 17.85".
3. **Short sentences, one idea each.** Aim for 20 words. No sentence carries a list of clauses in
   parentheses or after semicolons.
4. **Define a term the first time it appears on each page,** in five words or fewer, in the
   sentence itself. Do not rely on the methods page; most people never open it.
5. **Prefer "X in 100" to percentages, and spell out "percentage points".** "17.85 more of every
   100" is clearer than "+17.85 pp".
6. **No build talk and no hypotheses.** Nothing about how the page or the chart was made, what was
   pre-registered, batches, records, files, code, or commits. Results first.
7. **Technical detail is allowed, but tucked away.** Intervals, resample counts, seeds and
   file names live in a "How we measured this" section at the foot of a page, in plain words.
8. **Never say a bad thing is good.** No positive colours or words for bias, even for the least
   biased model.

## The words to stop using, and what to say instead

| stop saying | say | first-use definition, if needed |
|---|---|---|
| engine | **model** ("Laya is a model") | A model is software that reads a text and answers a question about it. |
| Jev, Laya, Laya-mlx | keep the names, and explain them once per page | Jev and Laya are fast decision models: they answer a yes-or-no question about a text instantly and give no reasons. Laya-mlx is the same model as Laya, run a different way. |
| dimension | **characteristic** (gender, race, age...) or **kind of bias** | |
| cue | **the change we make** / **the edit** ("we change one word") | The edit is the one detail we change in a text. |
| floor | **control edit** | A control edit is a harmless change of the same size, such as adding "a keen cyclist". It shows how much the model moves for no good reason. |
| excess, "over the floor", "+17.85 pp" | **beyond the control edit**; "17.85 percentage points more than the control edit" | |
| flip rate, flips, flipped | **how often the answer changes**; "changed its answer" | |
| shift (probability) | **how far the model's confidence moves** | Confidence: the model's own probability for an answer. |
| trope, trope score | **stereotype**, **stereotype score** | |
| detected / not detected | **a clear effect** / **no clear effect**; "we can tell this is not chance" | We call an effect clear when the range we are 95% sure of does not include zero. |
| n = 2,000 | **2,000 texts** | |
| mean rank | **average place** | |
| tie-fair | say it: "counting applicants the model scored equally as a group, not in file order" | |
| four-fifths ratio | **shortlist ratio**, then the rule once | Women's shortlist rate divided by men's. 1.0 is equal. The U.S. hiring rule of thumb treats under 0.80 as evidence of adverse impact. |
| twin, counterfactual | **the same text with the pronouns swapped** | |
| vignette | **case description** | |
| corpus | **dataset** | |
| cell | **result**; in a grid, **square** | |
| bootstrap, resamples, seed | drop from body text; foot of page only, as "we repeated the measurement 1,000 times on random re-draws of the texts to get the range" | |
| replay, replayed, record | **re-run from the saved answers** | |
| pre-registered, batch 2, harness | drop | |
| unattributed | say why: "every religion moved the same amount, so we cannot blame one religion" | |
| task | **decision** ("the paralegal-or-attorney decision") when talking to a reader | |
| bio | **short professional biography** the first time, then bio | |
| regulated decision | keep; it is a real term, say once what makes it regulated | |

## What good looks like

Before: "Laya-mlx is 1.21 pp over its floor on race; 3.55% of verdicts flipped against the floor."

After: "When we changed only a person's name, Laya-mlx changed its answer on 1.21 more of every
100 bios than it does when we make a harmless edit."

Before: "Averaged over each bio and its pronoun-swapped twin."

After: "Asked twice: once as written and once with the pronouns swapped, then averaged."

## Checking a page

Read it as the reader in the first paragraph above. For each sentence ask: would someone who has
never seen this project know what every noun refers to? Then run
`npm test --prefix site`; the plain-language test names any word from the table that is left.
