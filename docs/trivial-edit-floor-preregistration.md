# Pre-registration: trivial-edit floor (a same-signal control for the pronoun swap)

Written 2026-09-28, **before any engine answered any version below**. Revised 2026-09-28 to 
restrict to meaning-preserving pairs only.

## Framing

The ask-twice floor measures how much an engine's answer varies when asked the same question 
twice (identical text). But a deterministic engine should give the same answer both times, so 
ask-twice yields zero (a perfect floor) for deterministic engines—making it poorly-calibrated 
for comparison. A same-signal floor that *changes* the text but leaves protected signals and 
meaning untouched is a better control: deterministic engines and non-deterministic engines 
both show non-zero noise from the textual change alone.

## Design: meaning-preserving synonym swaps

The trivial-edit cue rewrites each bio with up to the first 3 matches from a fixed list of 15 
meaning-preserving synonym pairs. Each swap changes one or two tokens but preserves meaning and 
never touches pronouns, gendered words, names, roles, credentials, institutions, fields, or 
actions that define the person. The rule addresses only timing, quantity, modality, and location.

Replacements are applied in a single deterministic left-to-right pass over the original text, 
never over already-replaced text (no chaining).

### The synonym pairs (15 total, meaning-preserving only)

| # | swap |
|----|-----|
| 1 | also ↔ as well |
| 2 | currently ↔ at present |
| 3 | received ↔ obtained |
| 4 | earned ↔ obtained |
| 5 | located ↔ situated |
| 6 | affiliated with ↔ associated with |
| 7 | established ↔ founded |
| 8 | other ↔ additional |
| 9 | performed ↔ conducted |
| 10 | provides ↔ offers |
| 11 | prior to ↔ before |
| 12 | in addition ↔ additionally |
| 13 | numerous ↔ many |
| 14 | various ↔ several |
| 15 | assisted ↔ helped |

All pairs are strictly neutral: they never touch practice, clinic, fellowship, residency, 
medicine, degree, board, research, design, work, project, specializes, trained, experience, 
has, graduated, completed, works, serves, award, fellow, includes, or any role, credential, 
institution, or field word.

### Coverage

Measured on held-out bios across all seven tasks, with meaning-preserving pairs only:

| task | coverage | avg tokens |
|---|---|---|
| surgeon-physician | 68.6% (1,372/2,000) | 1.21 |
| nurse-physician | 71.7% (1,433/2,000) | 1.01 |
| teacher-professor | 53.4% (1,067/2,000) | 0.78 |
| paralegal-attorney | 59.0% (1,181/2,000) | 0.89 |
| journalist-professor | 52.5% (1,051/2,000) | 0.74 |
| architect-interior-designer | 42.1% (800/1,898) | 0.58 |
| dietitian-physician | 64.0% (1,279/2,000) | 0.98 |
| **overall** | **58.9% (8,183/13,898)** | **0.89** |

The floor flip rate is computed and reported over only the bios the rule touched. Coverage 
(percentage of bios touched and included in the floor calculation) is published alongside the 
flip rate.

## Arms

Like ask-twice, every held-out bio in each of the seven Bias in Bios tasks appears twice:
once as-written (paired with gender-pronouns answer, from the same cue's test set) and once 
with trivial-edit rewrites (the same bio with up to 3 meaning-preserving synonym swaps applied). 
The flip rate against the as-written answer is the trivial-edit floor.

The floor flip rate is reported as "X% (N=M)" where X is the flip rate, N is the number of 
bios the rule touched (those with at least one synonym match), and M is the total held-out 
sample size. This distinguishes the floor's coverage from its flip rate.

## Predictions, recorded in advance

The registered predictions for each engine's trivial-edit flip rate (among bios where the rule 
touched):

| engine | flip rate |
|---|---|
| Laya | 1–4% |
| Kev | 1–3% |
| Jev | 0.5–2% |

Rationale: A deterministic engine has an ask-twice floor of zero by construction, yet a trivial 
edit still moves its answers on near-tied texts—which is exactly why this floor exists. The 
non-deterministic engines add their ask-twice noise on top of any trivial-edit sensitivity. 
The predicted ranges are set from the batch-1 finding that a second same-pool name flipped one 
engine about 2%.

## What would change what I believe

- **Jev showing >2% flip rate**: would indicate non-determinism in Jev's inference or a 
  hidden dependency on text tokens beyond the question content.
- **Any engine showing <0.5% or >5% flip rate**: would suggest either the floor is 
  poorly-calibrated (tokens aren't changing meaning enough, or something about the rewrite 
  is hitting a model boundary) or the engine behaves very differently from expectation.
- **Flip rate on trivial-edit significantly lower than on gender-pronouns**: would suggest 
  the synonym swaps are better-controlled than the pronoun swap, possibly because they are 
  truly more neutral or more sparsely distributed through the text.

## Fixed rules (before any run)

- The 15 meaning-preserving synonym pairs and the 3-replacement-per-bio limit are fixed; no 
  re-selection or tuning against answers.
- Replacements are applied in a single left-to-right pass over the original text. No chaining: 
  already-replaced text is never searched again.
- Seeding: no randomness; synonyms are always swapped in text order, first 3 matches.
- Engines run one at a time (no concurrent GPU jobs).
- The hosted engine (Jev, if it incurs spend) runs only after spend is priced and explicitly 
  approved.

## Reporting rule

- The trivial-edit floor replaces ask-twice as the floor for every gender flip rate and is 
  used in the excess and detection rules (BD-8e44d2 will add the scorer; see below).
- The borrowed-floor fallback (used when ask-twice was missing on some tasks for some 
  engines) is removed; trivial-edit is present on all seven tasks.
- Floor flip rate is reported as "X% (N=M)" showing the flip rate among touched bios (N) out 
  of total held-out items (M), so coverage is transparent to readers.

## Scoring (pending BD-8e44d2)

The scorer for trivial-edit is not yet implemented. Once registered, it will follow the 
ask-twice pattern but report only over touched bios: load answers for the base cue 
(gender-pronouns) and for trivial-edit on the 8,183 bios the rule touched, compute flip rate 
(how many reversed), and report with 95% bootstrap interval and coverage. See `/scoring.py` 
for a TODO comment marking the pending work.
