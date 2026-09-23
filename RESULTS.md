# Results

Generated on 2026-09-23 from record commit `8385e12`. Regenerate with `make report` (or `bd report`); every number below is replayed from the committed record under `answers/` -- nothing here calls an engine.


## gender-pronouns: flip rate by task and engine

| task | Jev | Laya-mlx |
|---|---|---|
| surgeon-physician | flip 1.05% [0.65, 1.55]<br>floor: none (the swap is the only edit)<br>direction: 6.25%<br>recall gap: 5.50% | flip 7.95% [6.85, 9.20]<br>floor: none (the swap is the only edit)<br>direction: 0.72%<br>recall gap: 3.29% |
| nurse-physician | flip 3.30% [2.60, 4.10]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -2.19% | flip 13.50% [12.05, 15.05]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -1.60% |
| teacher-professor | flip 1.25% [0.80, 1.75]<br>floor: none (the swap is the only edit)<br>direction: 75.00%<br>recall gap: -5.15% | flip 7.65% [6.55, 8.85]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -9.10% |
| paralegal-attorney | flip 3.90% [3.10, 4.85]<br>floor: none (the swap is the only edit)<br>direction: 93.75%<br>recall gap: -5.53% | flip 17.85% [16.15, 19.55]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -8.84% |


## race-name: flip rate (surgeon-physician only)

| task | Jev | Laya-mlx |
|---|---|---|
| surgeon-physician | flip 0.89% [0.51, 1.40]<br>floor: 0.57% [0.25, 1.02]<br>direction: 71.43%<br>recall gap: — | flip 3.18% [2.36, 4.14]<br>floor: 2.36% [1.59, 3.12]<br>direction: 30.00%<br>recall gap: — |


## race-fullname: signed shift in P(surgeon) by group

Positive: the named group reads *more* like the positive class than the white names on the same bio.

| group | Jev (500) | Laya-mlx (all) | Laya-mlx (500) |
|---|---|---|---|
| white | (reference group) | (reference group) | (reference group) |
| black | -0.350% [-0.50, -0.19] | 0.460% [0.30, 0.62] | 0.700% [0.38, 1.02] |
| hispanic | -0.040% [-0.19, 0.14] | 1.440% [1.26, 1.62] | 1.540% [1.16, 1.90] |
| asian | -0.130% [-0.29, 0.03] | -0.160% [-0.32, -0.02] | -0.180% [-0.49, 0.13] |
| floor (white split in half) | 0.060% [-0.09, 0.24] | 0.080% [-0.10, 0.27] | 0.330% [-0.07, 0.75] |


## age-inserted (surgeon-physician only)

| measurement | Jev | Laya-mlx |
|---|---|---|
| 34 -> 61 flip | 1.300% [0.73, 1.95] | 0.970% [0.49, 1.54] |
| 34 -> 61 shift | 0.070% [-0.08, 0.23] | 0.690% [0.53, 0.87] |
| floor: 34 -> 35 flip | 0.890% [0.41, 1.46] | 0.490% [0.16, 0.97] |
| floor: 34 -> 35 shift | -0.060% [-0.16, 0.03] | 0.040% [-0.05, 0.12] |
| floor: 61 -> 62 flip | 0.570% [0.24, 0.97] | 0.650% [0.24, 1.14] |
| floor: 61 -> 62 shift | -0.000% [-0.11, 0.10] | -0.520% [-0.64, -0.39] |
| direction (older -> surgeon), of flips | 50.00% | 83.33% |


## Shortlist (top 500)

An invented employer ranks applicants by P(positive) and shortlists the top N; the EEOC four-fifths rule flags a women:men ratio under 0.8.

### paralegal-attorney (positive: attorney)

| engine | variant | women rate | men rate | 4/5 ratio [CI] | tie-fair | women in only as men | men out as women |
|---|---|---|---|---|---|---|---|
| Jev | engine_alone | 44.39% | 52.15% | 0.851 [0.733, 0.964] | 0.851 | 15 | 21 |
| Jev | twin_averaged | 47.26% | 50.60% | 0.934 [0.816, 1.054] | 0.909 | 17 | 0 |
| Laya-mlx | engine_alone | 28.88% | 60.07% | 0.481 [0.399, 0.547] | 0.481 | 82 | 147 |
| Laya-mlx | twin_averaged | 38.90% | 49.40% | 0.787 [0.688, 0.911] | 0.790 | 76 | 49 |

### nurse-physician (positive: physician)

| engine | variant | women rate | men rate | 4/5 ratio [CI] | tie-fair | women in only as men | men out as women |
|---|---|---|---|---|---|---|---|
| Jev | engine_alone | 49.10% | 50.50% | 0.972 [0.849, 1.103] | 0.947 | 4 | 9 |
| Jev | twin_averaged | 49.50% | 50.10% | 0.988 [0.872, 1.131] | 0.972 | 4 | 0 |
| Laya-mlx | engine_alone | 39.32% | 60.32% | 0.652 [0.580, 0.750] | 0.653 | 125 | 159 |
| Laya-mlx | twin_averaged | 54.49% | 44.09% | 1.236 [1.100, 1.418] | 1.248 | 74 | 55 |


## Footnotes

- **Floors.** A floor is an equally trivial edit that changes no protected signal (a second white name instead of the first, one age-adjacent year instead of a 27-year jump, half of one name pool against the other half). A cue's real effect is read against its floor, not against zero -- some flip rate is just noise from re-asking a near-tied item.
- **Flip rates are lower bounds.** Every milestone-1 corpus has first names redacted before a cue is applied, and gender-pronouns twins still swap pronouns and role nouns only, not every possible cue (a name left in place, for instance, is itself a gender cue the pronoun swap alone does not remove). A reported flip rate is a lower bound on an engine's sensitivity to the attribute, not an estimate of it.
- **The swap-rule artefacts.** `bd build`'s gender-pronouns twins use the pre-amendment rule (`biased_decisions.cues.gender.ORIGINAL_RULE`) because that is the rule the published twins in `tasks/*/items.jsonl` were actually built with -- checked byte-for-byte, not read off that module's own (incorrect) docstring claim that the amended rule built them. Measured against the 8,000 milestone-1 test bios: the amended rule's medical-phrase carve-out ("women's/men's health", etc.) would change 36 bios' twins (0.45%); its Miss/Sir/Madam pairs would change 11 (0.14%).
- **Option order is part of a task.** `question.yaml`'s `options:` list is ordered, and every probability in the record is keyed by that order; `bd build`/`bd answer` refuse to touch a cell whose committed order disagrees with the task file's current one. Every number in this file is under the order each task's `question.yaml` commits today.
- **Missing cells.** `race-name`, `race-fullname` and `age-inserted` exist only for `surgeon-physician` -- the other three tasks (`nurse-physician`, `teacher-professor`, `paralegal-attorney`) were only run on `gender-pronouns`, to check whether the gender result generalizes past surgeon/physician. Jev's `race-fullname` record covers only the 500-bio subsample in `tasks/surgeon-physician/versions/race-fullname_jev-subsample.txt` (drawn once, so Laya can be compared to Jev on identical bios); Laya-mlx's covers all eligible bios, and is reported both ways.
- Run nothing new: every number here is replayed from the committed record.
