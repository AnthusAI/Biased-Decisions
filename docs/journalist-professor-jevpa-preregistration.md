# Pre-registration: diversity-gated JEVPA on Bias in Bios

This study tests JEVPA on a second real data source after Civil Comments showed
that distinct slice minima can arise from nearly identical predictors. The task
is to classify a professional biography as journalist or professor using the
public Bias in Bios training corpus.

## Corpus and blindness

Start from the cached Bias in Bios training parquet, SHA-256
`3169ba69ae80eef1da3e22f6337d5f024d98bd6cc23780ab4f475bdecc594bc9`. Exclude
every source row used by the existing journalist-professor task, then take a
balanced 8,000-row source sample: 4,000 journalists and 4,000 professors,
using seed `20260927`. Freeze 500 discovery rows, a 600-row selection set, and
a 1,000-row held-out test set before any analyst or Jev request. The analyst
sees only discovery text and the binary occupation label.

Two text-defined, sealed selection slices are registered before sampling:

* **Academic-evidence:** the biography contains a case-insensitive token from
  `professor`, `faculty`, `university`, `PhD`, `doctoral`, `research`, or
  `publication`.
* **Reporting-evidence:** the biography contains a case-insensitive token from
  `journalist`, `reporter`, `editor`, `newspaper`, `magazine`,
  `correspondent`, or `news`.

The selection set reserves 200 rows matching each slice, then fills the
remaining 200 from the seeded remainder. Slice membership, selection/test
labels, and gender are never presented to the analyst or used in fitting.

## Search and retention

The base question asks whether the biography describes a journalist or a
professor. Four shared initial analyst calls must each add exactly one
text-answerable element; retirements and rewordings are rejected. Greedy and
JEVPA share all valid candidates and their Jev answer cache. Each arm receives
two further calls.

Greedy selects minimum overall selection Brier. JEVPA retains at most four
nondominated candidates over overall, academic-evidence, and reporting-evidence
Brier, but only when every slice has at least 50 labeled selection examples.
It may merge candidates only if two retained candidates uniquely win different
sealed slices **and** their selection prediction vectors have Pearson
correlation below `0.95` or disagree in hard class on at least `10%` of rows.
These diversity conditions were chosen before this corpus is frozen to prevent
the Civil Comments near-duplicate failure.

The primary outcome is paired held-out Brier, JEVPA minus greedy. A positive
result requires a JEVPA-only qualifying merge, Brier improvement of at least
`0.005`, and no accuracy loss greater than `0.02`. If the merge does not win
selection, no held-out Jev request is made.

## Budget

At most 4,800 Jev item requests: 500 discovery base, 1,100 shared initial,
2,200 branch, and 1,000 final test. At 800 input and 180 output tokens per
request, that is `$26.93` at `$3.30`/million input and `$16.50`/million output;
the provider ceiling is `$35`, including analyst calls.
