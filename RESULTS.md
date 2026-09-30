# Results

Generated on 2026-09-28 from record commit `3abafad`. Regenerate with `make report` (or `bd report`); every number below is replayed from the committed record under `answers/` -- nothing here calls an engine.


## gender-pronouns: flip rate by task and engine

| task | Jev | Laya | Laya-mlx | Kev |
|---|---|---|---|---|
| surgeon-physician | flip 1.05% [0.65, 1.55]<br>floor: none (the swap is the only edit)<br>direction: 6.25%<br>recall gap: 5.50% | flip 7.95% [6.85, 9.20]<br>floor: none (the swap is the only edit)<br>direction: 0.72%<br>recall gap: 3.29% | flip 7.95% [6.85, 9.20]<br>floor: none (the swap is the only edit)<br>direction: 0.72%<br>recall gap: 3.29% | flip 2.60% [1.95, 3.30]<br>floor: none (the swap is the only edit)<br>direction: 51.28%<br>recall gap: 0.46% |
| nurse-physician | flip 3.30% [2.60, 4.10]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -2.19% | flip 13.45% [12.00, 15.00]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -1.60% | flip 13.50% [12.05, 15.05]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -1.60% | flip 16.20% [14.45, 17.80]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -7.57% |
| teacher-professor | flip 1.25% [0.80, 1.75]<br>floor: none (the swap is the only edit)<br>direction: 75.00%<br>recall gap: -5.15% | flip 7.75% [6.60, 8.95]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -9.29% | flip 7.65% [6.55, 8.85]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -9.10% | flip 6.20% [5.15, 7.25]<br>floor: none (the swap is the only edit)<br>direction: 98.15%<br>recall gap: -5.85% |
| paralegal-attorney | flip 3.90% [3.10, 4.85]<br>floor: none (the swap is the only edit)<br>direction: 93.75%<br>recall gap: -5.53% | flip 17.85% [16.20, 19.50]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -8.84% | flip 17.85% [16.15, 19.55]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -8.84% | flip 7.90% [6.75, 9.15]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -6.54% |
| journalist-professor | flip 0.80% [0.40, 1.20]<br>floor: none (the swap is the only edit)<br>direction: 80.00%<br>recall gap: 0.12% | flip 1.80% [1.25, 2.40]<br>floor: none (the swap is the only edit)<br>direction: 35.00%<br>recall gap: 1.83% | — | flip 1.50% [1.00, 2.05]<br>floor: none (the swap is the only edit)<br>direction: 92.86%<br>recall gap: 1.28% |
| architect-interior-designer | flip 4.37% [3.53, 5.27]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -6.45% | flip 5.11% [4.21, 6.11]<br>floor: none (the swap is the only edit)<br>direction: 92.68%<br>recall gap: -8.00% | — | flip 8.54% [7.38, 9.80]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -7.12% |
| dietitian-physician | flip 2.05% [1.50, 2.65]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -0.42% | flip 6.50% [5.40, 7.60]<br>floor: none (the swap is the only edit)<br>direction: 93.33%<br>recall gap: -0.62% | — | flip 2.80% [2.10, 3.60]<br>floor: none (the swap is the only edit)<br>direction: 100.00%<br>recall gap: -0.82% |


## race-name: flip rate (surgeon-physician only)

| task | Jev | Laya-mlx | Kev |
|---|---|---|---|
| surgeon-physician | flip 0.89% [0.51, 1.40]<br>floor: 0.57% [0.25, 1.02]<br>direction: 71.43%<br>recall gap: — | flip 3.18% [2.36, 4.14]<br>floor: 2.36% [1.59, 3.12]<br>direction: 30.00%<br>recall gap: — | flip 1.80% [0.80, 3.00]<br>floor: 2.20% [1.00, 3.60]<br>direction: 33.33%<br>recall gap: — |


## race-fullname: signed shift in P(surgeon) by group

Positive: the named group reads *more* like the positive class than the white names on the same bio.

| group | Jev (500) | Laya-mlx (all) | Laya-mlx (500) | Kev (500) |
|---|---|---|---|---|
| white | (reference group) | (reference group) | (reference group) | (reference group) |
| black | -0.350% [-0.50, -0.19] | 0.460% [0.30, 0.62] | 0.700% [0.38, 1.02] | 0.000% [-0.15, 0.15] |
| hispanic | -0.040% [-0.19, 0.14] | 1.440% [1.26, 1.62] | 1.540% [1.16, 1.90] | -0.280% [-0.42, -0.12] |
| asian | -0.130% [-0.29, 0.03] | -0.160% [-0.32, -0.02] | -0.180% [-0.49, 0.13] | -0.370% [-0.53, -0.22] |
| floor (white split in half) | 0.060% [-0.09, 0.24] | 0.080% [-0.10, 0.27] | 0.330% [-0.07, 0.75] | 0.000% [-0.18, 0.19] |


## age-inserted (surgeon-physician only)

| measurement | Jev | Laya-mlx | Kev |
|---|---|---|---|
| 34 -> 61 flip | 1.300% [0.73, 1.95] | 0.970% [0.49, 1.54] | 1.200% [0.40, 2.40] |
| 34 -> 61 shift | 0.070% [-0.08, 0.23] | 0.690% [0.53, 0.87] | -0.230% [-0.32, -0.14] |
| floor: 34 -> 35 flip | 0.890% [0.41, 1.46] | 0.490% [0.16, 0.97] | 0.400% [0.00, 1.00] |
| floor: 34 -> 35 shift | -0.060% [-0.16, 0.03] | 0.040% [-0.05, 0.12] | -0.100% [-0.16, -0.03] |
| floor: 61 -> 62 flip | 0.570% [0.24, 0.97] | 0.650% [0.24, 1.14] | 0.200% [0.00, 0.60] |
| floor: 61 -> 62 shift | -0.000% [-0.11, 0.10] | -0.520% [-0.64, -0.39] | 0.060% [-0.01, 0.12] |
| direction (older -> surgeon), of flips | 50.00% | 83.33% | 0.00% |


## disability: shift in P(positive) vs the floor ("A cyclist, ")

| task | Jev wheelchair | Laya wheelchair | Kev wheelchair | shared/spread |
|---|---|---|---|---|
| surgeon-physician | -0.71 [-0.88, -0.52] (flip 1.24%) | -0.56 [-0.85, -0.30] (flip 1.97%) | +3.00 [+2.56, +3.42] (flip 3.20%) | — |
| nurse-physician | +1.41 [+0.99, +1.88] (flip 0.80%) | +2.01 [+1.60, +2.41] (flip 4.54%) | -0.28 [-0.77, +0.23] (flip 1.20%) | — |
| teacher-professor | +0.68 [+0.33, +1.09] (flip 1.40%) | -2.72 [-2.99, -2.44] (flip 5.49%) | +1.54 [+1.23, +1.88] (flip 2.60%) | — |
| paralegal-attorney | -0.64 [-0.87, -0.40] (flip 2.02%) | -1.71 [-2.04, -1.42] (flip 4.98%) | +0.60 [+0.16, +1.04] (flip 1.60%) | — |
| journalist-professor | +0.57 [+0.33, +0.83] (flip 0.80%) | +0.18 [-0.06, +0.42] (flip 1.44%) | +3.06 [+2.55, +3.58] (flip 3.00%) | — |
| architect-interior-designer | -0.87 [-1.22, -0.55] (flip 1.40%) | -2.84 [-3.15, -2.51] (flip 3.55%) | +3.24 [+2.81, +3.71] (flip 2.60%) | — |
| dietitian-physician | +0.23 [-0.11, +0.60] (flip 0.80%) | +0.15 [-0.11, +0.44] (flip 1.79%) | +2.17 [+1.79, +2.54] (flip 3.20%) | — |


## religion v1: shift in P(positive) vs the floor ("A keen gardener, ")

**Confounded.** The clause is "A practising X, " -- the word "practising" is shared with phrases like "practising physician"/"practising attorney" and the floor does not carry it, so the *shared* per-religion shift measures the word, not the religion. Only the between-religion contrasts (the spread column) are a religion finding here; see religion v2 below for a floor built to separate the two.

| task | Jev muslim | Jev christian | Jev jewish | Jev hindu | Laya muslim | Laya christian | Laya jewish | Laya hindu | Kev muslim | Kev christian | Kev jewish | Kev hindu | shared/spread |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| surgeon-physician | +0.93 [+0.54, +1.38] (flip 2.60%) | +0.22 [-0.11, +0.53] (flip 1.40%) | +0.49 [+0.16, +0.85] (flip 2.40%) | +1.29 [+0.85, +1.78] (flip 2.80%) | -2.85 [-3.25, -2.47] (flip 4.38%) | -3.78 [-4.17, -3.43] (flip 4.60%) | -2.15 [-2.52, -1.79] (flip 4.01%) | -2.34 [-2.75, -1.96] (flip 4.16%) | +1.46 [+1.13, +1.81] (flip 4.00%) | +1.07 [+0.77, +1.39] (flip 3.40%) | +1.66 [+1.35, +1.98] (flip 3.40%) | +2.01 [+1.68, +2.38] (flip 3.20%) | Kev: shared +1.55 [+1.25, +1.88], spread 0.95 |
| nurse-physician | +1.62 [+1.17, +2.14] (flip 1.20%) | +0.81 [+0.47, +1.18] (flip 1.00%) | +2.06 [+1.49, +2.66] (flip 1.80%) | +1.48 [+1.04, +1.97] (flip 1.20%) | +9.28 [+8.54, +10.04] (flip 11.70%) | +8.62 [+7.97, +9.31] (flip 11.34%) | +9.50 [+8.81, +10.24] (flip 11.34%) | +9.06 [+8.35, +9.82] (flip 11.12%) | +0.59 [+0.10, +1.11] (flip 3.00%) | -0.08 [-0.46, +0.34] (flip 2.60%) | +0.65 [+0.22, +1.11] (flip 3.20%) | +0.84 [+0.35, +1.33] (flip 2.80%) | Kev: shared +0.50 [+0.05, +0.93], spread 0.92 |
| teacher-professor | -0.43 [-0.85, -0.04] (flip 2.00%) | -0.36 [-0.71, -0.02] (flip 1.80%) | -0.67 [-1.05, -0.31] (flip 1.40%) | -0.80 [-1.17, -0.42] (flip 1.40%) | -0.16 [-0.44, +0.12] (flip 4.28%) | -0.16 [-0.40, +0.11] (flip 3.21%) | +0.28 [+0.03, +0.53] (flip 3.85%) | -0.81 [-1.08, -0.54] (flip 4.71%) | +0.09 [-0.28, +0.54] (flip 2.80%) | -0.43 [-0.82, +0.01] (flip 4.40%) | -1.04 [-1.42, -0.64] (flip 3.20%) | -1.27 [-1.67, -0.84] (flip 4.40%) | Kev: shared -0.66 [-1.03, -0.26], spread 1.36 |
| paralegal-attorney | +2.21 [+1.71, +2.76] (flip 2.40%) | +2.19 [+1.72, +2.70] (flip 2.60%) | +3.76 [+3.12, +4.44] (flip 3.40%) | +2.24 [+1.73, +2.76] (flip 2.40%) | +8.61 [+7.89, +9.46] (flip 11.26%) | +11.48 [+10.77, +12.23] (flip 14.01%) | +13.95 [+13.14, +14.83] (flip 17.11%) | +11.97 [+11.19, +12.86] (flip 15.16%) | +1.77 [+1.10, +2.48] (flip 3.20%) | +0.29 [-0.22, +0.82] (flip 2.60%) | +0.98 [+0.32, +1.63] (flip 3.20%) | +1.12 [+0.43, +1.87] (flip 3.20%) | Kev: shared +1.04 [+0.46, +1.67], spread 1.48 |
| journalist-professor | +0.31 [+0.00, +0.63] (flip 1.00%) | +0.35 [+0.15, +0.59] (flip 1.00%) | -0.06 [-0.31, +0.20] (flip 1.40%) | +0.52 [+0.25, +0.82] (flip 1.00%) | +0.59 [+0.33, +0.85] (flip 1.94%) | +1.37 [+1.11, +1.62] (flip 1.87%) | +0.66 [+0.41, +0.92] (flip 1.73%) | +0.86 [+0.59, +1.13] (flip 2.08%) | -2.68 [-3.27, -2.09] (flip 3.00%) | -2.32 [-2.91, -1.78] (flip 2.60%) | -3.08 [-3.68, -2.53] (flip 3.40%) | -2.34 [-2.94, -1.76] (flip 2.60%) | Kev: shared -2.61 [-3.18, -2.04], spread 0.76 |
| architect-interior-designer | +1.40 [+0.92, +1.93] (flip 1.80%) | +0.83 [+0.45, +1.22] (flip 1.60%) | +0.99 [+0.55, +1.44] (flip 1.00%) | +1.00 [+0.62, +1.42] (flip 1.40%) | -2.30 [-2.60, -1.99] (flip 3.17%) | -1.94 [-2.22, -1.66] (flip 2.89%) | -0.62 [-0.90, -0.36] (flip 2.99%) | -2.42 [-2.75, -2.12] (flip 3.73%) | +5.58 [+4.88, +6.33] (flip 5.60%) | +5.92 [+5.24, +6.70] (flip 5.40%) | +3.67 [+3.17, +4.20] (flip 4.80%) | +5.23 [+4.59, +5.95] (flip 4.80%) | Kev: shared +5.10 [+4.48, +5.77], spread 2.25 |
| dietitian-physician | +0.19 [-0.08, +0.50] (flip 0.60%) | +0.33 [+0.06, +0.62] (flip 0.80%) | +0.28 [-0.01, +0.63] (flip 1.20%) | +0.23 [-0.05, +0.52] (flip 0.60%) | +3.44 [+2.96, +3.93] (flip 4.78%) | +3.81 [+3.36, +4.27] (flip 5.08%) | +4.76 [+4.26, +5.32] (flip 6.28%) | +3.76 [+3.27, +4.28] (flip 5.31%) | +3.42 [+2.85, +4.00] (flip 4.00%) | +3.01 [+2.49, +3.51] (flip 4.00%) | +1.94 [+1.56, +2.36] (flip 3.20%) | +2.74 [+2.23, +3.27] (flip 4.00%) | Kev: shared +2.78 [+2.29, +3.27], spread 1.48 |


## religion v2: shift in P(positive) vs the floor ("A devoted gardener, ")

The floor ("a devoted gardener") mirrors the religion clauses' shape ("a devout Muslim") the way v1's "a keen gardener" did not, separating a religion-specific effect from the "any inserted description" effect. On nurse-physician and dietitian-physician, an unattributed shared shift remains even against this floor -- see the pre-registration's section E for the reading.

| task | Jev muslim | Jev christian | Jev jewish | Jev hindu | Laya muslim | Laya christian | Laya jewish | Laya hindu | Kev muslim | Kev christian | Kev jewish | Kev hindu | shared/spread |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| surgeon-physician | +0.99 [+0.64, +1.42] (flip 2.40%) | +0.23 [-0.01, +0.48] (flip 1.60%) | +0.52 [+0.22, +0.84] (flip 1.80%) | +1.14 [+0.77, +1.55] (flip 2.00%) | +0.33 [+0.07, +0.59] (flip 2.55%) | -0.48 [-0.72, -0.24] (flip 1.90%) | +0.56 [+0.30, +0.83] (flip 2.77%) | +0.32 [+0.07, +0.58] (flip 2.33%) | +2.62 [+2.22, +3.02] (flip 1.40%) | +2.71 [+2.30, +3.13] (flip 2.80%) | +2.78 [+2.38, +3.20] (flip 1.60%) | +3.73 [+3.27, +4.18] (flip 2.00%) | Kev: shared +2.96 [+2.55, +3.38], spread 1.11 |
| nurse-physician | +1.40 [+0.96, +1.84] (flip 0.80%) | +0.60 [+0.28, +0.95] (flip 1.00%) | +1.87 [+1.39, +2.39] (flip 1.60%) | +1.44 [+1.04, +1.88] (flip 1.40%) | +6.90 [+6.28, +7.57] (flip 8.71%) | +5.51 [+5.00, +6.07] (flip 6.66%) | +5.35 [+4.83, +5.89] (flip 6.44%) | +5.29 [+4.78, +5.84] (flip 6.14%) | +2.40 [+1.86, +2.99] (flip 3.80%) | +0.04 [-0.37, +0.46] (flip 2.00%) | +2.87 [+2.33, +3.43] (flip 3.80%) | +1.05 [+0.54, +1.57] (flip 3.00%) | Kev: shared +1.59 [+1.13, +2.09], spread 2.83 |
| teacher-professor | +0.68 [+0.34, +0.99] (flip 2.00%) | +0.68 [+0.38, +1.00] (flip 1.80%) | +0.74 [+0.40, +1.10] (flip 0.80%) | +0.74 [+0.40, +1.07] (flip 1.20%) | +0.61 [+0.36, +0.86] (flip 3.71%) | +0.21 [-0.02, +0.46] (flip 3.99%) | +0.86 [+0.61, +1.10] (flip 4.42%) | -0.18 [-0.42, +0.07] (flip 3.99%) | +2.15 [+1.79, +2.55] (flip 2.60%) | +1.37 [+1.00, +1.76] (flip 2.60%) | +1.53 [+1.14, +1.91] (flip 2.00%) | +1.38 [+1.01, +1.78] (flip 3.00%) | Kev: shared +1.61 [+1.26, +1.99], spread 0.78 |
| paralegal-attorney | +2.14 [+1.67, +2.64] (flip 2.80%) | +2.22 [+1.78, +2.69] (flip 2.80%) | +3.28 [+2.69, +3.87] (flip 3.80%) | +1.72 [+1.29, +2.15] (flip 1.80%) | -1.28 [-1.61, -0.99] (flip 4.48%) | +1.55 [+1.25, +1.85] (flip 3.68%) | +0.10 [-0.24, +0.40] (flip 4.62%) | -1.00 [-1.31, -0.71] (flip 4.26%) | +5.10 [+4.25, +5.98] (flip 7.20%) | +2.51 [+1.97, +3.07] (flip 3.40%) | +4.61 [+3.89, +5.39] (flip 6.40%) | +4.11 [+3.43, +4.85] (flip 6.00%) | Kev: shared +4.08 [+3.41, +4.81], spread 2.60 |
| journalist-professor | +0.27 [-0.04, +0.59] (flip 0.80%) | +0.37 [+0.10, +0.64] (flip 1.00%) | -0.00 [-0.26, +0.28] (flip 1.40%) | +0.46 [+0.17, +0.78] (flip 1.00%) | +0.92 [+0.63, +1.16] (flip 2.37%) | +1.61 [+1.33, +1.85] (flip 2.30%) | +1.82 [+1.55, +2.07] (flip 2.73%) | +1.82 [+1.52, +2.08] (flip 2.73%) | -2.22 [-2.75, -1.70] (flip 2.80%) | -2.43 [-2.99, -1.91] (flip 3.80%) | -3.05 [-3.62, -2.51] (flip 4.80%) | -2.27 [-2.84, -1.75] (flip 2.80%) | Kev: shared -2.49 [-3.03, -1.99], spread 0.84 |
| architect-interior-designer | +1.49 [+1.04, +1.96] (flip 2.60%) | +0.94 [+0.50, +1.35] (flip 1.60%) | +1.09 [+0.64, +1.56] (flip 1.40%) | +1.07 [+0.68, +1.47] (flip 1.80%) | -1.28 [-1.62, -0.97] (flip 2.99%) | -1.05 [-1.36, -0.75] (flip 2.43%) | -0.82 [-1.16, -0.51] (flip 2.80%) | -1.82 [-2.14, -1.50] (flip 2.89%) | +6.24 [+5.56, +7.01] (flip 5.80%) | +5.88 [+5.23, +6.61] (flip 5.40%) | +4.86 [+4.28, +5.48] (flip 4.40%) | +6.05 [+5.39, +6.79] (flip 5.20%) | Kev: shared +5.76 [+5.11, +6.48], spread 1.38 |
| dietitian-physician | +0.14 [-0.14, +0.45] (flip 0.60%) | +0.41 [+0.14, +0.70] (flip 0.60%) | +0.26 [-0.02, +0.57] (flip 0.60%) | +0.22 [-0.05, +0.51] (flip 0.60%) | +1.33 [+1.07, +1.62] (flip 2.32%) | +0.87 [+0.62, +1.12] (flip 1.79%) | +0.31 [+0.05, +0.55] (flip 1.72%) | +1.14 [+0.85, +1.42] (flip 2.02%) | +3.88 [+3.29, +4.47] (flip 4.00%) | +2.65 [+2.19, +3.13] (flip 3.20%) | +2.28 [+1.85, +2.72] (flip 2.60%) | +2.90 [+2.40, +3.39] (flip 3.80%) | Kev: shared +2.93 [+2.44, +3.40], spread 1.60 |


## ask-twice: noise floor (same bio, asked a second time)

| task | Jev | Laya | Kev |
|---|---|---|---|
| surgeon-physician | flip 0.60%, mean |dP| 0.0059, max |dP| 0.1000 (n=500) | flip 0.00%, mean |dP| 0.0000, max |dP| 0.0000 (n=500) | flip 1.40%, mean |dP| 0.0042, max |dP| 0.0213 (n=500) |
| nurse-physician | flip 0.40%, mean |dP| 0.0048, max |dP| 0.1400 (n=500) | flip 0.00%, mean |dP| 0.0000, max |dP| 0.0000 (n=500) | flip 0.20%, mean |dP| 0.0028, max |dP| 0.0268 (n=500) |
| teacher-professor | flip 0.60%, mean |dP| 0.0099, max |dP| 0.1000 (n=500) | flip 0.00%, mean |dP| 0.0000, max |dP| 0.0000 (n=500) | flip 0.60%, mean |dP| 0.0039, max |dP| 0.0178 (n=500) |
| paralegal-attorney | flip 0.40%, mean |dP| 0.0060, max |dP| 0.1200 (n=500) | flip 0.00%, mean |dP| 0.0000, max |dP| 0.0000 (n=500) | flip 0.40%, mean |dP| 0.0024, max |dP| 0.0409 (n=500) |
| journalist-professor | — | — | — |
| architect-interior-designer | — | — | — |
| dietitian-physician | — | — | — |


## option-order: does the answer change when the options are listed the other way round?

The pre-registration's section D found Jev's order flip under 1% (1.0-2.8% across the four original tasks plus journalist-professor's exploratory run) and Laya's 3.25-7.80% (journalist-professor's 3.25% below the rest); the table below is the committed replay, limited to the four original tasks that carry a full option-order-reversed record. The gender-pronouns flip rate under both orders is reported where the engine answered the reversed order on the twins too.

| task | Jev | Laya | Kev |
|---|---|---|---|
| surgeon-physician | order flip 1.00% (max |dP| 0.1900, n=500) | order flip 6.60% (max |dP| 0.6416, n=2000)<br>gender flip: committed 7.95% / reversed 7.05% | order flip 5.80% (max |dP| 0.1268, n=500) |
| nurse-physician | order flip 1.00% (max |dP| 0.2300, n=500) | order flip 4.60% (max |dP| 0.4661, n=2000)<br>gender flip: committed 13.45% / reversed 14.10% | order flip 2.40% (max |dP| 0.2454, n=500) |
| teacher-professor | order flip 2.80% (max |dP| 0.2900, n=500) | order flip 7.80% (max |dP| 0.6653, n=2000)<br>gender flip: committed 7.75% / reversed 7.95% | order flip 5.00% (max |dP| 0.3565, n=500) |
| paralegal-attorney | order flip 1.20% (max |dP| 0.1800, n=500) | order flip 6.10% (max |dP| 0.4565, n=2000)<br>gender flip: committed 17.85% / reversed 19.60% | order flip 2.60% (max |dP| 0.2099, n=500) |
| journalist-professor | — | order flip 3.25% (max |dP| 0.4566, n=2000)<br>gender flip: committed 1.80% / reversed 2.00% | — |
| architect-interior-designer | — | order flip 4.79% (max |dP| 0.4461, n=1898)<br>gender flip: committed 5.11% / reversed 5.58% | — |
| dietitian-physician | — | order flip 4.80% (max |dP| 0.4814, n=2000)<br>gender flip: committed 6.50% / reversed 6.75% | — |


## Port vs original: laya-mlx vs laya, gender-pronouns

The Apple-silicon port (`laya-mlx`) against the original upstream package (`laya`), same questions, same committed option order.

| task | port flip % | original flip % | verdict agreement | max abs dP |
|---|---|---|---|---|
| surgeon-physician | 7.95 | 7.95 | 3,996 / 4,000 | 0.013 |
| nurse-physician | 13.50 | 13.45 | 3,999 / 4,000 | 0.013 |
| teacher-professor | 7.65 | 7.75 | 3,998 / 4,000 | 0.006 |
| paralegal-attorney | 17.85 | 17.85 | 3,998 / 4,000 | 0.019 |


## Shortlist (top 500)

An invented employer ranks applicants by P(positive) and shortlists the top N; the EEOC four-fifths rule flags a women:men ratio under 0.8.

### paralegal-attorney (positive: attorney)

| engine | variant | women rate | men rate | 4/5 ratio [CI] | tie-fair | women in only as men | men out as women |
|---|---|---|---|---|---|---|---|
| Jev | engine_alone | 44.39% | 52.15% | 0.851 [0.733, 0.964] | 0.851 | 15 | 21 |
| Jev | twin_averaged | 47.26% | 50.60% | 0.934 [0.816, 1.054] | 0.909 | 17 | 0 |
| Laya | engine_alone | 28.88% | 60.07% | 0.481 [0.398, 0.546] | 0.481 | 82 | 147 |
| Laya | twin_averaged | 39.14% | 49.40% | 0.792 [0.689, 0.909] | 0.792 | 74 | 47 |
| Laya | neutral_blank | 37.23% | 51.64% | 0.721 [0.624, 0.826] | 0.721 | 0 | 0 |
| Laya-mlx | engine_alone | 28.88% | 60.07% | 0.481 [0.399, 0.547] | 0.481 | 82 | 147 |
| Laya-mlx | twin_averaged | 38.90% | 49.40% | 0.787 [0.688, 0.911] | 0.790 | 76 | 49 |
| Kev | engine_alone | 30.31% | 53.70% | 0.564 [0.475, 0.671] | 0.564 | 63 | 73 |
| Kev | twin_averaged | 36.99% | 47.33% | 0.782 [0.668, 0.907] | 0.782 | 35 | 36 |

### nurse-physician (positive: physician)

| engine | variant | women rate | men rate | 4/5 ratio [CI] | tie-fair | women in only as men | men out as women |
|---|---|---|---|---|---|---|---|
| Jev | engine_alone | 49.10% | 50.50% | 0.972 [0.849, 1.103] | 0.947 | 4 | 9 |
| Jev | twin_averaged | 49.50% | 50.10% | 0.988 [0.872, 1.131] | 0.972 | 4 | 0 |
| Laya | engine_alone | 39.32% | 60.32% | 0.652 [0.582, 0.751] | 0.653 | 125 | 158 |
| Laya | twin_averaged | 54.49% | 44.09% | 1.236 [1.099, 1.420] | 1.251 | 73 | 55 |
| Laya | neutral_blank | 58.68% | 40.28% | 1.457 [1.267, 1.657] | 1.451 | 0 | 0 |
| Laya-mlx | engine_alone | 39.32% | 60.32% | 0.652 [0.580, 0.750] | 0.653 | 125 | 159 |
| Laya-mlx | twin_averaged | 54.49% | 44.09% | 1.236 [1.100, 1.418] | 1.248 | 74 | 55 |
| Kev | engine_alone | 21.96% | 77.15% | 0.285 [0.236, 0.330] | 0.285 | 278 | 155 |
| Kev | twin_averaged | 41.12% | 57.52% | 0.715 [0.618, 0.811] | 0.715 | 184 | 50 |


## Footnotes

- **Floors.** A floor is an equally trivial edit that changes no protected signal (a second white name instead of the first, one age-adjacent year instead of a 27-year jump, half of one name pool against the other half). A cue's real effect is read against its floor, not against zero -- some flip rate is just noise from re-asking a near-tied item.
- **Flip rates are lower bounds.** Every milestone-1 corpus has first names redacted before a cue is applied, and gender-pronouns twins still swap pronouns and role nouns only, not every possible cue (a name left in place, for instance, is itself a gender cue the pronoun swap alone does not remove). A reported flip rate is a lower bound on an engine's sensitivity to the attribute, not an estimate of it.
- **The swap-rule artefacts.** `bd build`'s gender-pronouns twins use the pre-amendment rule (`biased_decisions.cues.gender.ORIGINAL_RULE`) because that is the rule the published twins in `tasks/*/items.jsonl` were actually built with -- checked byte-for-byte, not read off that module's own (incorrect) docstring claim that the amended rule built them. Measured against the 8,000 milestone-1 test bios: the amended rule's medical-phrase carve-out ("women's/men's health", etc.) would change 36 bios' twins (0.45%); its Miss/Sir/Madam pairs would change 11 (0.14%).
- **Option order is part of a task.** `question.yaml`'s `options:` list is ordered, and every probability in the record is keyed by that order; `bd build`/`bd answer` refuse to touch a cell whose committed order disagrees with the task file's current one. Every number in this file is under the order each task's `question.yaml` commits today.
- **Missing cells.** `race-name`, `race-fullname` and `age-inserted` exist only for `surgeon-physician` -- the other three tasks (`nurse-physician`, `teacher-professor`, `paralegal-attorney`) were only run on `gender-pronouns`, to check whether the gender result generalizes past surgeon/physician. Jev's `race-fullname` record covers only the 500-bio subsample in `tasks/surgeon-physician/versions/race-fullname_jev-subsample.txt` (drawn once, so Laya can be compared to Jev on identical bios); Laya-mlx's covers all eligible bios, and is reported both ways.
- **Batch-1 (milestone 1b) coverage.** `disability` has a Jev record only for `surgeon-physician` and `paralegal-attorney` (Laya covers all seven); `religion` and `religion-v2` were only ever sent to Laya, never Jev; `ask-twice` and `option-order` exist only for the four original tasks (they reuse those tasks' 500-bio noise-floor subsample); the three new tasks (`journalist-professor`, `architect-interior-designer`, `dietitian-physician`) were answered by Jev and the upstream `laya` only, never `laya-mlx`. `bd list` shows exactly which `(engine, task, cue)` cells have a record.
- Run nothing new: every number here is replayed from the committed record.
