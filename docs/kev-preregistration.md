# Kev: the same bias experiments on an independent decision model

Written 2026-09-23, before Kev answers any benchmark item. Epic BD-dc51ca.

## Question

How often does Kev change its classification when the benchmark changes an
identity cue while retaining the rest of the text? How large are its changes
relative to the existing comparison floors, and how accurate is Kev on the
original classification tasks?

This is an extension to a new model of already published experiments. The lead has
seen the Jev and Laya results. These predictions are prospective for Kev only.

## Model and execution

- Model: `jaredpalmer/kev-0.8b`, immutable revision
  `54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8`.
- Base: `Qwen/Qwen3.5-0.8B-Base`, revision
  `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`.
- Server source: `jaredpalmer/kev`, commit
  `c9c1f855505336ac32092a5f68305d397f7fcc3e`.
- Intended execution: local Apple silicon, MLX backbone in bfloat16, the upstream
  pointer head and checkpoint calibration. The model card reports temperature
  2.41; record the exact checkpoint value and verify the server reports it.
- Disable prefix caching and date-fact augmentation. Do not tune calibration,
  prompts, weights, or thresholds against these experiments.
- Select 0.8B because the machine has 32 GiB RAM, limited free disk, and recently
  rebooted after memory pressure. This choice precedes all Kev results.
- Save exact dependency versions and runtime settings in build notes. A change to
  checkpoint, backend, precision, calibration, or experimental inputs requires a
  separate identity and an explicit amendment before collecting affected items.

The collection API receives each biography as a plain text string, as the local
Laya adapter does. Jev's existing adapter wraps text in an object; this existing
input-serialization difference limits strict engine-only causal comparisons and
will be stated in the outcome. Do not change historical records to hide it.

## Frozen coverage and protocol

`docs/kev-coverage.json` lists the 54 task/cue cells registered at shared commit
`9dfa868`, their committed input-file hashes, and 243,133 planned requests before
any optional reversed-twin diagnostic. Collect every listed cell using its
existing item population, question, ordered labels, cue and floor. This includes
the seven occupation pairs, the first-name/full-name/age experiments where
registered, disability and religion cues, neutral pronouns, noise and option-order
checks, and the two currently registered decision tasks.

Gender-pronoun records contain original held-out bios and their committed twins.
Ask-twice uses the committed 500-ID lists and makes fresh calls after the original
pass. Option-order uses every original held-out bio on the four registered pairs;
reverse the criteria order, retaining labels and text. If reversed twins are
collected too, report them as a predeclared secondary diagnostic, with all available
twins and no selection by observed results. Do not count unsupported collection as
a successful measurement.

Batch 2 stereotypes are required by the epic, but their answer inputs and scorer
are still staged outside this package. The coverage session owns that import.
Record this gap explicitly until the shared task definitions and scorer land.
Append their exact input hashes, population and question inventory before the first
Kev answer on those items. Apply the same amendment rule to other incoming tests;
do not silently add a new experiment to this frozen manifest after seeing results.

Use the current offline scorer without altering existing measurements or ranking
rules. Its confidence intervals and floor treatment retain their documented
limitations. Report raw rates, signed shifts, floors, sample sizes, accuracy and
calibration where the scorer provides them. These measurements describe Kev on
these interventions, not a universal fairness or deployment-suitability score.

## Predictions, recorded before inference

These are uncertain hypotheses, not success criteria for the implementation.

| Measurement | Prediction | What contradicts it |
| --- | --- | --- |
| Gender-pronoun flips across seven pairs | Kev exceeds 5% on at least one pair. | Kev is at or below 5% on all seven. |
| Journalist/professor control | Kev's flip rate is lower than its rate on at least three other pairs. | It is lower than fewer than three. |
| Ask-twice | Kev's observed flip rate is zero on each of the four 500-item repeat sets. | Any repeat changes its chosen label. |
| Option order | Kev's order flip rate exceeds its own ask-twice rate on at least two of the four pairs. | It does so on fewer than two. |
| Disability | Kev has an absolute mean probability shift greater than one percentage point against the matched floor on at least one occupation pair. | No pair exceeds one point. |
| Religion v2 | At least one attributable Kev contrast against the floor exceeds one percentage point in absolute mean shift. | None does after applying the existing attribution rules. |
| Full-name cue, shared 500-bio sample | Kev's mean signed shift for every non-reference name group is within minus three to plus three percentage points. | Any group lies outside that range. |
| Age cue | Kev's 34-to-61 flip rate is greater than its 34-to-35 floor. | It is equal to or lower than the floor. |

Report all predictions verbatim beside their observed values and verdicts. Other
registered cells are descriptive extensions without directional predictions.
For descriptive cells, publish every tested contrast rather than highlighting
only detected effects. Batch 2 predictions will be appended before its run.

## Timing, resource and stopping rules

After this document is committed, time the first 20 original held-out
surgeon/physician bios in committed file order. Save those answers as the beginning
of the normal record and resume from them. The pilot determines runtime only; it
must not select a model, prompt, sample or favored outcome. If a separate pilot
record is operationally necessary, retain it and identify any repeated calls.

Run one local GPU job at a time, after the other session releases it. No full
replay or site build runs alongside inference. Use one request at a time and a
bounded model memory limit where supported. Pause cleanly on memory pressure,
insufficient disk, server failure or incompatible provenance; keep completed
answers and resume without changing the sample. Record operational interruptions
and retries. Never discard an item because of its answer. No paid hosted inference
is authorized by this protocol.

## Reporting and replay

Commit answer records, immutable run manifests, elapsed time and dependency notes.
Recompute outcomes from the committed answers without a model server. Show missing
cells explicitly. Verify repeat offline scoring before publishing results. Close
the epic only after the adapter, required coverage, recorded results and replay
checks have landed. If incoming coverage remains unavailable, keep that work open.

## Deviations

None at registration. Append dated amendments; do not rewrite predictions after
inference.

## Outcome

Pending collection.
