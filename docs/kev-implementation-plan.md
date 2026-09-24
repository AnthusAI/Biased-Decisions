# Kev implementation work order

Epic: BD-dc51ca. Lead: Codex GPT-6. Implementation: GPT-6 Luna, BD-ce3f5c.
Behavior specification: BD-505817. Study and coordination: BD-8dafac.

## Goal and boundaries

Add an independent Kev engine to the same experiments used for the other engines.
Use the committed stimuli, questions, option order, scoring, and floors. New bias
tasks are being developed in another session; consume their shared task definitions
after they land. That session also owns consolidating the Laya implementations.

Work in `/Users/home/Projects/Biased-Decisions/.worktrees/kev` on `codex/kev-engine`, initially based on
`c7e2358`. Do not edit the other checkout. Read AGENTS.md and CONTRIBUTING_AGENT.md.
Use `KANBUS_NO_DAEMON=1 kbs` for board access. The lead handles board writes and git
publication during the first implementation slice to avoid concurrent mutations.
Never read or write issue JSON directly, or read, print, or source `.env`.

The Mac reboot removed the original temporary worktree. The committed branch and
board state survived; uncommitted adapter files did not. Continue in this persistent
worktree. Checkpoint completed implementation slices in git and push promptly.
Use one implementation agent and small offline tests during recovery; do not load
model weights, launch GPU inference, or run a full replay or site build.

## Implementation sequence

1. Read the engine protocol, Jev adapter and its tests, answering module, task
   loader, scorer contracts, CLI, reports, and `scripts/answer_task.py` and tests.
   The CLI currently only preflights collection; the script actually collects but
   hardcodes the Laya output directory. Preserve its existing defaults.
2. Write failing adapter specifications before production code. Verify unchanged
   question names, instructions and ordered criteria; multiple questions; bounded
   finite probabilities; exact option coverage; valid chosen label; response
   provenance; missing configuration; optional imports; and fresh requests for
   repeated identical inputs. Never memoize ask-twice answers.
3. Implement `KevEngine` using the standard `/v1/systemone` API. Keep endpoint/key
   configuration independent from Jev. Never fall back to Jev credentials or an
   implicit paid endpoint. Prefer the existing optional SDK if it supports this
   isolation; otherwise use a small explicit transport and explain the decision.
   Retain actual response metadata rather than substituting the engine label.
4. Add a generic resumable collector, preserving existing runner compatibility.
   Load task definitions and shared cue registrations rather than copying a Kev
   task list. Provide a plan/dry-run path with pending counts and no model calls.
   Unsupported experiments must be reported explicitly.
5. Preserve each scorer's record contract. Gender records need originals plus
   twins. Ask-twice requests must be independent of the baseline. Option-order
   experiments need reversed criteria, with labels preserved. New decision tasks
   must retain their question name rather than being renamed Occupation.
6. Resume from both completed and partial records. Validate input fingerprints,
   question/order, checkpoint, server revision, backend, dtype and calibration.
   Refuse incompatible resumes. Flush each answer, retain deterministic item order,
   and finalize atomically. Do not silently discard corrupt partial records.
7. Test tiny synthetic tasks: interruption and resume, zero calls on completed
   rerun, changed input/model rejection, a newly registered task, and offline
   scoring of the produced record. Keep synthetic test fixtures out of published
   answer records. Adding an unmeasured engine must not alter existing rankings.
8. Wire the adapter into factory/dependency checks and engine registries. Add
   report metadata without changing Laya consolidation or existing measurements.
9. Run targeted offline adapter, collector, registry and reporting tests. Use an
   isolated environment or explicit PYTHONPATH for this worktree. Report the exact
   commands and results. Draft `docs/kev.md` with configuration and usage; distinguish
   adapter tests from unverified hardware support.
10. Send the lead the diff summary, test evidence, blockers, and required review
    decisions. Leave issues open until the corresponding work lands.

## Runtime and study sequence owned by the lead

1. Resolve immutable upstream server and model revisions; record checkpoint size,
   base revision, backend, dtype, calibration and relevant dependency versions.
2. Inventory currently registered experiments and the upcoming coverage changes.
   Record a baseline coverage manifest and a pending list. Do not reinterpret or
   rewrite the other session's stimuli, preregistrations, or Laya identity.
3. Commit predictions, timing protocol and reporting rules before any benchmark
   item is answered. A model or execution-configuration change gets a distinct
   study identity; do not silently combine results.
4. Coordinate access to the local GPU with the other sessions. Run only one GPU
   job at a time, and never alongside a full replay or site build. Time a small
   preregistered pilot before estimating the complete run. Paid hosted inference
   requires priced, explicit user approval.
5. Collect the shared coverage, score offline, and report all planned outcomes,
   including missing and failed cells. Keep runtime and spend notes.
6. At a clean checkpoint, fetch the other session's merged coverage and Laya
   consolidation, integrate changes, rerun affected contract tests, regenerate
   the pending coverage plan, and collect only preregistered compatible additions.
7. Verify replay and reports before landing the completed comparison. A working
   adapter alone does not complete the epic.

## Upstream verification

The [official Kev repository](https://github.com/jaredpalmer/kev), checked on
2026-09-23, now documents an MLX serving path for Qwen3.5 on Apple silicon. The
repository's earlier model survey predates that support. Do not use the survey's
hardware claims as implementation requirements. Read the official API and runtime
source at the revision selected for the study. `/v1/models` exposes loaded model
details; a deployment alias such as `kev-latest` is not an immutable checkpoint ID.

No model calls, model-weight downloads, GPU jobs, full replay, or site builds belong
to the initial offline implementation slice. The lead resolves experimental
ambiguities while Luna continues independent implementation and test work.
