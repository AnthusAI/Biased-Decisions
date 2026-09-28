# Pre-registration: credit-score calibration for loan approval decisions

Written 2026-09-28 before any model is asked a version newly defined here. This is a calibration-only study. It measures at what credit score and collateral level each engine's approval probability reaches 85% ("strong"), ~50% ("borderline"), and 15% or below ("weak") on small-business-loan decisions, to inform the design of the subsequent nationality study in the same contexts.

## Purpose and boundaries

The small-business-loan task asks, "Should this loan application be approved?" on synthetic applications with controlled strength (0 to 1). Earlier runs showed Laya approves ~95% and Jev ~17% across the item pool, so "borderline approval" differs per engine. We need to identify, for each engine and collateral level, the credit-score rung where approval probability is most stable and near the chosen thresholds, to design borrower profiles for the nationality study.

This study does not measure discrimination or bias; it measures engine calibration only. No nationality or demographic variables are present in any version.

## Bases

The first 20 items of the standard `small-business-loan` task (IDs 0000–0019), drawn from the deterministic generator with seed 0. See `tasks/small-business-loan/items.jsonl`.

| ID | Strength | Collateral in base |
|----|----------|-------------------|
| small-business-loan-0000 | 0.5592 | equipment and receivables |
| small-business-loan-0001 | 0.5889 | none |
| small-business-loan-0002 | 0.4241 | none |
| small-business-loan-0003 | 0.6332 | none |
| small-business-loan-0004 | 0.5572 | none |
| small-business-loan-0005 | 0.6276 | equipment and receivables |
| small-business-loan-0006 | 0.3975 | equipment |
| small-business-loan-0007 | 0.5783 | equipment |
| small-business-loan-0008 | 0.5331 | none |
| small-business-loan-0009 | 0.4990 | equipment |
| small-business-loan-0010 | 0.6038 | equipment and receivables |
| small-business-loan-0011 | 0.5637 | equipment and receivables |
| small-business-loan-0012 | 0.5436 | none |
| small-business-loan-0013 | 0.5606 | equipment and receivables |
| small-business-loan-0014 | 0.5486 | equipment |
| small-business-loan-0015 | 0.5858 | equipment and receivables |
| small-business-loan-0016 | 0.5100 | equipment |
| small-business-loan-0017 | 0.5651 | none |
| small-business-loan-0018 | 0.6053 | equipment and receivables |
| small-business-loan-0019 | 0.5869 | equipment and receivables |

## Versions

For each base item, create versions that replace two sentences:

1. **Credit score**: the sentence "The personal credit score of the principal is N." is replaced with N ∈ {560, 580, 600, 620, 640, 660, 680, 700, 720, 740, 760, 780, 800} (13 rungs).
2. **Collateral**: the collateral sentence is replaced with one of:
   - `secured`: "The loan would be secured by the equipment."
   - `none`: "We can offer no collateral."

Version count: 20 bases × 13 credit scores × 2 collateral levels = **520 versions**.

Version ID format: `{base_id}-credit-ladder-c{score}-{collateral}`, e.g., `small-business-loan-0000-credit-ladder-c560-secured`.

Metadata per version:
- `cue`: `"credit-ladder"`
- `source_id`: ID of the base item
- `version`: `"c{score}-{collateral}"` e.g., `"c560-secured"`
- `credit_score`: integer (560–800)
- `collateral`: string (`"secured"` or `"none"`)

Generated deterministically, committed in `tasks/small-business-loan-ladder/versions/credit-ladder.jsonl` before any model answers.

## Engines and reproducibility

Run Laya first, pinned as `laya-upstream:0.3.21` (see `docs/full-nationality-loan-contexts-preregistration.md` for version rationale).

Kev: to run later on the Kev host; schedule unknown.

Jev: to run only after the spend is priced and explicitly approved (not included in this pre-registration).

Store answers as `answers/{engine}/small-business-loan-ladder/credit-ladder.jsonl.gz` with a `.metadata.json` sidecar recording the engine and version (see prior loan runs for format). Scoring outputs go in `studies/small-business-loan-ladder-credit-ladder.jsonl` (one row per engine; must be deterministic and reproduce byte-for-byte on replay).

## Analysis and predictions

For each engine (and separately per collateral level), compute the following from the 520 answers:

1. **Approval probability**: for each version, the probability `p = probabilities["yes"]` (the confidence the model assigns to "yes").
2. **Approval decision**: approve if `p ≥ 0.5`, otherwise deny.
3. **Per-rung aggregation**: for each credit score rung (560, 580, …, 800):
   - Mean approval probability `p_bar` across the 20 bases (with seed-0 probability, fixed base sample).
   - Approval rate: the number of the 20 bases with `p ≥ 0.5`.
   - Percentile-bootstrap interval: resample the 20 bases 1,000 times with seed 0 (bootstrap); for each resample, compute the approval rate; report the 2.5th and 97.5th percentile.

4. **Rung classification** (per collateral level):
   - **Strong** (≥85% approval): the lowest rung (scanning upward from 560) whose approval rate is ≥ 85%. If no rung reaches 85%, record "not reached".
   - **Borderline** (~50%): the rung whose approval rate is closest to 50%. Record the approval rate, not "50 (exact)".
   - **Weak** (≤15% approval): the highest rung (scanning downward from 800) whose approval rate is ≤ 15%. If no rung reaches 15%, record "not reached".

5. **Linear fit** (diagnostic, not scored): fit approval rate against credit score separately for each collateral level using simple linear interpolation between rungs; report the slope (percentage-point change per 10-point score increase).

## Pre-registered predictions

Verbatim predictions to be scored against the outcome:

> **Laya**: approval rate is at least 50% at every rung for secured loans, and 'weak' (<= 15%) is not reached for either collateral level. Laya's mean p rises by less than 10 points from 560 to 800.

> **Jev**: approval rate is below 50% at 560 for both collateral levels and rises with credit score; the borderline rung for secured loans is higher than 640.

> **Kev**: approval rate rises with credit score for both collateral levels.

## Outcome

*To be filled after Laya (and optionally Kev and Jev) run and are scored.*
