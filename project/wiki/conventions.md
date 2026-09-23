# Conventions

## Pre-registration before any run

Every study is written up before an engine answers a single question about it: the arms, the
predictions, and a "what would change what I believe" section that says in advance what result
would count as a miss. Once an arm starts, the pre-registration is not edited to fit what
happened — a change of plan is appended as a dated blockquote (`> **Deviation, <date>** ...`),
never folded into the original text, so the record shows what was decided going in versus what
was learned along the way. Outcomes are scored against the predictions that were written first,
not restated after the fact.

## One floor per cue

Every cue that measures a flip rate is paired with a floor of the same shape: an edit that
changes no protected signal, run and scored the same way as the cue itself, so a flip rate has
a baseline to compare against. A race cue's floor swaps one name for another name from the same
group; an age cue's floor is a one-year age change instead of a decades-wide one. A cue with only
one possible edit, such as the gender-pronoun swap, has no floor to pair it with.

## Numbers replay from the record

Every number in a published report is scored from a committed answer record, never from a fresh
engine call. `answers/<engine>/<task>/<cue>.jsonl.gz` holds the raw answers a run produced;
reproducing a published figure means reading that file, not asking an engine again. This is what
lets a reviewer, or a later session, check a number without a GPU or a key.

## Free engines before paid ones

An engine that runs for free on this machine (an Apple-silicon Mac) is run and scored before an
engine that costs money per request. Paid runs are priced with a dry run before anything is sent,
and every paid run has a request cap agreed before the first request goes out. Nothing paid is
sent without both a price and a cap in hand first.

## Conventional Commits

Commits on `main` follow [Conventional Commits](https://www.conventionalcommits.org/) because
releases are automated: a `Release` workflow runs semantic-release on every push, which reads the
commit types since the last release to pick the next version, update `CHANGELOG.md`, and cut a
GitHub release. `fix:` yields a patch, `feat:` a minor version, `feat!:` or a `BREAKING CHANGE:`
footer a major version; `chore:`, `docs:`, `test:`, `refactor:`, `style:`, and `ci:` release
nothing by default. See `CONTRIBUTING.md` at the repo root for the full form.

## Issues tracked in Kanbus

Work is tracked as Kanbus issues under `project/issues/`, never edited there by hand: `kbs create`,
`kbs comment`, and `kbs commit` write that state, and `kbs commit` is what stages and commits it.
The [initiatives, epics, and stories](../issues/) an engine adapter or study belongs to are linked
by their `kbs` id — see [engine coverage](engine-coverage.md) for the current set of open stories.
