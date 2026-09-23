# import/: raw material carried over from the Jev-Flywheel session scratchpad (2026-09-23)

Staging area only. Everything here was produced outside this repo and is moved into the
harness layout by the build; nothing here is read by the harness at run time.

- batch1/: the batch-1 fixtures (three new tasks, ordered question.yaml for all seven, the
  disability / religion / religion-v2 / ask-twice versions), the Jev record for batch 1
  (answers/jev/), the build scripts, BUILD.md, spend.md and the scoring script/rows for the
  religion-v2 and reversed-order follow-up.
- laya-record/: the original (upstream `laya` 0.3.7, PyTorch on MPS) record for all seven
  tasks and every batch-1 cue, file per (task, cue): laya/<task>--<cue>.jsonl.gz; OUTCOME.md
  is the milestone-1b port-vs-original outcome.
- docs/: the design, the inventory of what Jev-Flywheel provides, and the batch-1 and batch-2
  pre-registrations with their recorded outcomes.
