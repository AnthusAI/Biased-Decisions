# Antisemitic-tropes-in-depth cues on the seven occupation tasks

The five antisemitic-tropes-in-depth cues (`antisemitism-secular`, `antisemitism-religious`,
`antisemitism-nationality`, `antisemitism-role`, `antisemitism-surname`) are built here on all
seven Bias in Bios occupation tasks (`paralegal-attorney`, `surgeon-physician`,
`teacher-professor`, `nurse-physician`, `dietitian-physician`, `architect-interior-designer`,
`journalist-professor`), the same occupation-invariance pattern the `disability`/`religion`/
`religion-v2` cues already use (does the occupation verdict itself move, not the trope-question
grid -- that grid is `stereotypes-antisemitism` and `loan-narratives-antisemitism`).

See `docs/antisemitic-tropes-preregistration.md` for the study these cues were built for,
`biased_decisions/cues/antisemitism.py` for the clause tables, surname pools, and their sources,
and `_antisemitism_insertion_build_summary.json` in this directory for each task/cue's row and
exclusion counts from the build that produced the committed `versions/antisemitism-*.jsonl` files
in every task's own directory.

Build (per task, per cue):

```python
from biased_decisions.build import build, write_versions
from biased_decisions.tasks.bios import load_task

task = load_task("paralegal-attorney")
result = build("antisemitism-secular", task)   # or -religious / -nationality / -role / -surname
write_versions(task, "antisemitism-secular", result)
```

Deterministic given each task's own committed `items.jsonl`; the surname cue additionally needs
spaCy (`pip install 'biased-decisions[build]'`), the same optional dependency `race-fullname`
already needs.

## No engine has answered any of these versions

Build-time output only (deterministic text editing); this study's rules require Laya to run
first, free, and Jev only after a priced, capped go/no-go decision -- see the pre-registration's
"Rules" section.
