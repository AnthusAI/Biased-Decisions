# Glossary

**Engine** — a model that answers a typed question about a text and returns a probability per
option, not just a label. Jev and Laya are the two engines wired up so far; the [engine
coverage](engine-coverage.md) page lists the rest as candidates.

**Task** — a corpus, one choice question, a positive class, and the group attribute used for
recall gaps. `surgeon-physician`, `nurse-physician`, `teacher-professor`, and `paralegal-attorney`
are the four Bias in Bios tasks the harness ports.

**Cue** — a deterministic edit that changes one protected signal and nothing else, leaving
everything else in the text untouched. `gender-pronouns`, `race-name`, `race-fullname`, and
`age-inserted` are the milestone-1 cues; each item is asked about twice, as written and after the
edit, and a flip is a verdict that differs between the two.

**Floor** — an equally trivial edit that changes no protected signal, run alongside a cue so its
flip rate has a baseline: a race cue's floor swaps one white name for another white name, an
age cue's floor is a one-year age change instead of a 27-year one. A cue with only one possible
edit, like the gender-pronoun swap, has no floor.

**Measurement** — the row an (engine, task, cue) triple produces: flip rate and floor flip rate
with bootstrap confidence intervals, mean absolute change in probability, signed shift per group,
direction share, recall gap, and the shortlist block (top-N four-fifths ratio, tie-fair ratio, and
counterfactual shortlist counts).

**Record** — the committed answer cache an engine's run writes to
`answers/<engine>/<task>/<cue>.jsonl.gz`, one gzipped JSONL row per item holding the model's raw
answer. A record is the unit of reproducibility: scoring a published number needs the record file,
never a key or a GPU.

**Flip rate** — the share of items whose verdict changes between an item as written and its
counterfactual twin. It is a lower bound on an engine's sensitivity to a cue, not an estimate of
it, because a signal the cue does not touch (a first name left in place, for a gender cue) can
still carry the protected attribute.

**Signed shift** — the mean change in an engine's probability for the positive class between two
versions of the same item, kept signed so a study can tell which direction a group's answers moved
rather than only how often they moved.

**Direction share** — among the items that flipped, the share that moved in the predicted
direction. A direction share near 1.0 says the flips are not noise; a direction share near 0.5
says they could be.

**Trope score** — the shift for the group a named stereotype targets, minus the mean shift of the
other groups on the same axis, so a general "any label changes the answer" effect cancels out and
only the trope-specific part remains.

**Noul question** — a yes/no question type an engine answers with a single probability (of
"yes"), as opposed to a choice question answered with a probability per option.

**Option order is part of a task's definition** — a task's `question.yaml` lists its options in a
fixed order, and every engine's probabilities are keyed by option label under that order. A
shortlist ranking or a four-fifths ratio can depend on how ties break, so the order a record was
built under has to be reproducible from the committed file, never implied by dict iteration or
re-derived at read time.
