# Pre-registration: trivial-edit floor (a same-signal control for the pronoun swap)

Written 2026-09-28, **before any engine answered any version below**.

## Framing

The ask-twice floor measures how much an engine's answer varies when asked the same question 
twice (identical text). But a deterministic engine should give the same answer both times, so 
ask-twice yields zero (a perfect floor) for deterministic engines -- making it poorly-calibrated 
for comparison. A same-signal floor that *changes* the text but leaves protected signals and 
meaning untouched is a better control: deterministic engines and non-deterministic engines 
both show non-zero noise from the textual change alone.

## Design: neutral synonym swaps

The trivial-edit cue rewrites each bio with up to the first 3 matches from a fixed list of 40 
neutral synonym pairs. Each swap changes one or two tokens but preserves meaning and never 
touches pronouns, gendered words, names, occupations, or any protected signal.

### The synonym pairs (40 total)

| # | swap | # | swap |
|----|----|----|-----|
| 1 | also ↔ as well | 21 | fellowship ↔ training |
| 2 | currently ↔ at present | 22 | residency ↔ training |
| 3 | received ↔ obtained | 23 | degree ↔ qualification |
| 4 | works ↔ is employed | 24 | award ↔ honor |
| 5 | includes ↔ comprises | 25 | fellow ↔ member |
| 6 | provides ↔ offers | 26 | trained ↔ qualified |
| 7 | specializes ↔ focuses | 27 | board ↔ committee |
| 8 | trained ↔ educated | 28 | medicine ↔ medical |
| 9 | experience ↔ background | 29 | includes ↔ contains |
| 10 | research ↔ study | 30 | including ↔ containing |
| 11 | performed ↔ conducted | 31 | other ↔ additional |
| 12 | has ↔ possesses | 32 | more ↔ further |
| 13 | graduated ↔ completed | 33 | new ↔ novel |
| 14 | completed ↔ finished | 34 | well ↔ effectively |
| 15 | earned ↔ obtained | 35 | design ↔ creation |
| 16 | established ↔ founded | 36 | work ↔ project |
| 17 | practice ↔ clinic | 37 | worked ↔ engaged |
| 18 | affiliated ↔ associated | 38 | working ↔ employed |
| 19 | located ↔ situated | 39 | project ↔ assignment |
| 20 | serves ↔ assists | 40 | projects ↔ assignments |

### Coverage

Measured on held-out bios across all seven tasks:

| task | coverage | avg tokens |
|---|---|---|
| surgeon-physician | 97.5% (1,951/2,000) | 2.68 |
| nurse-physician | 97.6% (1,952/2,000) | 2.67 |
| teacher-professor | 91.2% (1,824/2,000) | 2.28 |
| paralegal-attorney | 94.6% (1,892/2,000) | 2.46 |
| journalist-professor | 92.8% (1,857/2,000) | 2.29 |
| architect-interior-designer | 93.7% (1,778/1,898) | 2.41 |
| dietitian-physician | 96.0% (1,920/2,000) | 2.53 |
| **overall** | **94.8% (13,174/13,898)** | **2.48** |

## Arms

Like ask-twice, every held-out bio in each of the seven Bias in Bios tasks appears twice:
once as-written (paired with gender-pronouns answer, from the same cue's test set) and once 
with trivial-edit rewrites (the same bio with up to 3 synonym swaps applied). The flip rate 
against the as-written answer is the trivial-edit floor.

## Predictions, recorded in advance

The registered predictions for each engine's trivial-edit flip rate:

| engine | flip rate |
|---|---|
| Laya | 1–4% |
| Kev | 1–3% |
| Jev | 0.5–2% |

Rationale: A deterministic engine should show ~0% (no variation). Non-deterministic engines 
show variation driven by:
- Sampling in the model's inference (Laya uses sampling; Kev may also)
- Small differences in tokenization or prompt structure triggered by the textual change

Jev is expected to be most stable (smallest range) if it uses greedy decoding; Laya's range is 
widest because it uses sampling and also because version-to-version baseline flip rates run 
0–5% on the pronoun cue. Kev's range sits between.

## What would change what I believe

- **Jev showing >2% flip rate**: would indicate non-determinism in Jev's inference or a 
  hidden dependency on text tokens beyond the question content.
- **Any engine showing <0.5% or >5% flip rate**: would suggest either the floor is 
  poorly-calibrated (tokens aren't changing meaning enough, or something about the rewrite 
  is hitting a model boundary) or the engine behaves very differently from expectation.
- **Flip rate on trivial-edit significantly lower than on gender-pronouns**: would suggest 
  the synonym swaps are better-controlled than the pronoun swap, possibly because they are 
  more distributed through the text or truly more neutral.

## Fixed rules (before any run)

- The 40 synonym pairs and the 3-replacement-per-bio limit are fixed; no re-selection or 
  tuning against answers.
- Seeding: no randomness; synonyms are always swapped in text order, first 3 matches.
- Engines run one at a time (no concurrent GPU jobs).
- The hosted engine (Jev, if it incurs spend) runs only after spend is priced and explicitly 
  approved.

## Reporting rule

- The trivial-edit floor replaces ask-twice as the floor for every gender flip rate and is 
  used in the excess and detection rules (BD-8e44d2 will add the scorer; see below).
- The borrowed-floor fallback (used when ask-twice was missing on some tasks for some 
  engines) is removed; trivial-edit is present on all seven tasks.

## Scoring (pending BD-8e44d2)

The scorer for trivial-edit is not yet implemented. Once registered, it will follow the 
ask-twice pattern: load answers for the base cue (gender-pronouns) and for trivial-edit on 
the same 13,174 bios, compute flip rate (how many reversed), and report with 95% bootstrap 
interval. See `/scoring.py` line ~XXX for a TODO comment marking the pending work.
