# Results: diversity-gated JEVPA on Bias in Bios

## Decision

This pre-registered second real-data study stopped after the shared initial
candidate batch. JEVPA had no qualifying pair to merge, so the branch rounds
and held-out test were not run. This follows the stopping rule in
[`journalist-professor-jevpa-preregistration.md`](journalist-professor-jevpa-preregistration.md):
the held-out set is used only if a merge wins selection.

The result does not demonstrate a JEVPA benefit on this source. It does show
that the diversity gate prevents an unjustified composition of nearly identical
candidate heads.

## Protocol completed

The study used the public Bias in Bios training corpus, excluding every source
row used by the existing journalist-professor task. Before any analyst or Jev
request, we froze a balanced 8,000-row source sample and sealed a 500-row
discovery set, 600-row selection set, and 1,000-row test set. The pre-registered
selection slices were academic evidence (288 rows) and reporting evidence (233
rows). The split manifest SHA-256 was
`1b327fdcaf64a223786a1fb6043f7233c5c75b3465303bcd12a4700389483fcc`.

Jev answered the base question on the 500 discovery rows, then answered the
base plus each valid candidate on the 500 discovery and 600 sealed selection
rows. Fitting used discovery labels only. The analyst made four shared initial
calls: three produced valid additions and one remained invalid after its
permitted repair. All three valid additions were academic-focused:

1. `scholarly_research_output`
2. `holds_faculty_position`
3. `academic_research_career`

No reporting-focused candidate was proposed.

## Selection results

| Candidate | Overall Brier | Accuracy | Academic Brier | Reporting Brier |
| --- | ---: | ---: | ---: | ---: |
| `scholarly_research_output` | 0.01841 | 0.980 | 0.02948 | 0.01895 |
| `holds_faculty_position` | 0.01972 | 0.975 | 0.03089 | 0.01986 |
| `academic_research_career` | 0.01969 | 0.975 | 0.03092 | 0.02028 |

`scholarly_research_output` dominates both other candidates on overall Brier
and both sealed-slice Brier measures. Candidate prediction vectors were also
near duplicates: pairwise Pearson correlation ranged from 0.9992 to 0.9999,
and hard-class disagreement ranged from 0 to 0.005. Thus no pair met the
pre-registered diversity threshold (correlation below 0.95 or disagreement at
least 0.10), and there were no distinct slice winners eligible for a JEVPA
merge.

## Cost and interpretation

The completed work used 1,600 Jev item requests: 500 base and 1,100 shared
initial-batch requests. Recorded provider cost was $4.80075 ($0.94428 base and
$3.85647 initial batch), plus four analyst calls. No test item was requested or
scored.

Together with the Civil Comments studies, this is a second real source where
JEVPA produced no demonstrated Pareto benefit. The common diagnostic is more
specific than that: residual-driven proposal generation supplied heads with
the same underlying evidence, while the base decision was already extremely
accurate. The diversity gate converts that situation into a principled stop,
rather than treating tiny slice differences as a reason to merge.
