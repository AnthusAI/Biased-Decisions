# Pre-registration: neutral-pronoun control and the accuracy cost of removing gender

Written 2026-09-23, **before any engine answered any neutral-pronoun version below**. Filed as
BD-1f42b782. Engine: upstream Laya 0.3.7 only; Jev is not run (no spend approved).

## Why

A reader asked whether stripping sex from a model's input creates more equal outcomes, or
whether it could as easily create more disparity, and whether the pronoun swap therefore says
anything about direction. The pronoun swap shows that the verdict depends on one word (disparate
treatment). It does not say which way the dependence runs, and it does not say what removing the
word costs. Two questions follow.

1. **Direction.** With the pronoun neutralised, does the verdict sit near the "he" verdict, near
   the "she" verdict, or between them?
2. **Cost.** What does removing the gender signal do to accuracy against the corpus label, and to
   the shortlist ratio?

## What the existing record already answers (observed before this document was written)

`studies/*-shortlist.jsonl`, cut 500, classification accuracy at P >= 0.5 against the corpus
label. Twin-averaging scores each bio under both pronouns and averages; it removes the signal by
averaging, not by deleting it.

| task | engine | accuracy as written | accuracy twin-averaged | ratio as written | ratio twin-averaged |
|---|---|---|---|---|---|
| paralegal / attorney | Laya | 0.7205 | 0.6655 | 0.48 | 0.79 |
| paralegal / attorney | Jev | 0.8545 | 0.8415 | 0.85 | 0.93 |
| nurse / physician | Laya | 0.8365 | 0.7965 | 0.65 | 1.24 |
| nurse / physician | Jev | 0.9430 | 0.9345 | 0.97 | 0.99 |

Removing the gender signal by averaging raised equality and lowered accuracy, by 4 to 5.5 points
for Laya and about 1 point for Jev. The corpus label is itself correlated with sex (most nurses in
the corpus are women), so a model that reads sex is partly reading a base rate. That is a reason
the accuracy falls, not a reason the verdict is acceptable: using a group's base rate to judge an
individual is the disparate treatment the swap measures. This paragraph is reported as observed,
not as a prediction.

## Design

Seven bios tasks (surgeon/physician, nurse/physician, teacher/professor, paralegal/attorney,
journalist/professor, architect/interior designer, dietitian/physician). The 2,000 test bios per
task, first names already redacted to `[name]`. Four versions of every bio:

| arm | rule |
|---|---|
| he | the bio with male pronouns and role nouns (the as-written text for a male bio, the swapped twin for a female bio) |
| she | the same with female forms |
| blank | every gendered pronoun replaced by "the person" (possessive "the person's"), gendered role nouns by "person"; no verb changes are needed |
| they | singular "they/them/their/theirs/themself" with verb agreement for a fixed list (is/are, was/were, has/have, does/do, and the negated forms) and a rule for regular third-person verbs directly after the pronoun |

Fixed before any run: the token lists are those of `swap_gender`'s amended rule. After rewriting,
any item that still contains a gendered token is dropped from that arm and counted; if more than 1%
of items are dropped on any task the arm is reported as failed on that task.

**Rule details, fixed 2026-09-23 before any run.** Reflexives (himself, herself) become "themself"
in both neutral arms, because "the person" cannot stand as an object of the same verb's subject.
Courtesy titles (Mr, Ms, Mrs, Miss, Sir, Madam) are removed in both arms. In the they arm, a
contraction of the pronoun with "is" or "has" ("she's") is ambiguous; an item containing one is
dropped from the they arm and counted, not guessed. The verb rule adjusts the first verb after the
pronoun, skipping up to two adverbs from a fixed list; verbs after "and" or a comma are not
adjusted, and the audit below shows how often that leaves an error.

**Grammar audit for the they arm.** Fifty random items per task are printed and read before
scoring. If more than 10% are ungrammatical, the they arm is reported as exploratory and the
blank arm carries the conclusion.

## Measurements

For each bio, P(positive) under each arm, paired by bio. Reported per task with a paired
bootstrap (1,000 resamples, seed 0):

- **Gap** G = mean(P_he - P_she). Reported only where its interval excludes zero and |G| >= 2
  points.
- **Position** lambda = mean(P_blank - P_she) / G, and the same for they. lambda = 1 means the
  neutral verdict equals the "he" verdict; 0 means it equals "she"; 0.5 means midway.
- **Shortlist and accuracy** on paralegal/attorney and nurse/physician: rank by P under the blank
  arm and the they arm, the same top-500 rule as the existing shortlist (`bd score` shortlist),
  reporting the four-fifths ratio, its interval, the tie-fair ratio and the accuracy.

## Predictions

Made before the run, each with what would refute it.

1. **Neutral falls between.** On at least four of the tasks where G is reportable, lambda for
   both neutral arms lies in [0.25, 0.75]. Refuted if lambda >= 0.75 on most (he is the default)
   or <= 0.25 on most (she is the marked form).
2. **The two neutral arms agree.** |P_blank - P_they| < 2 points on average on every task.
   Refuted otherwise; then the wording of the neutral form, not the absence of gender, moves the
   verdict, which is a finding in itself.
3. **Cost.** On paralegal/attorney, the blank-arm accuracy is 2 to 8 points below the as-written
   accuracy (0.7205) and the four-fifths ratio is between 0.70 and 1.20. Refuted if accuracy falls
   less than 2 points (the sex signal was not carrying the label) or more than 8 (the rewriting
   itself damages the bio).

## What each outcome would mean

- lambda near 1: the model treats "he" as the person and "she" as the departure from it. The
  harm of the swap is a penalty on "she".
- lambda mid-range: the pronoun pushes both ways; neither form is the default.
- lambda near 0: the model treats "she" as the person; the swap would then measure a favour to
  "he".
- Whatever lambda is, a gap G that exists is disparate treatment: the same work receives
  different verdicts when one word changes. The neutral arm says which form the model departs
  from. It does not change whether the departure is a problem.

## Not tested here

- Whether removing sex from **training** data changes any of this. The engines are trained by
  others; we cannot run the experiment.
- Whether including sex in **post-training** (RLHF) could push a model back toward equal outcomes.
  That needs a training run we have not designed.
- Jev. It would need the spend priced and approved first.

## Implementation, after this document is committed

A cue module (`biased_decisions/cues/neutral.py`, with its spec beside it) implementing the two
neutral rewrites and the leftover-token check; `bd build` writes `versions/neutral-blank.jsonl`
and `versions/neutral-they.jsonl` per task; `scripts/answer_task.py` answers them on Laya
(about 28,000 calls, under an hour); the position and shortlist measures are scored and replayed
into `studies/`. The leaderboard adopts them only after the replay is byte-for-byte.
