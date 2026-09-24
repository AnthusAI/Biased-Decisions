# Agent Instructions

## Project management with Kanbus

Use Kanbus for task management.
Why: Kanbus task management is MANDATORY here; every task must live in Kanbus.
When: Create/update the Kanbus task before coding; close it only after the change lands.
How: See CONTRIBUTING_AGENT.md for the Kanbus workflow, hierarchy, status rules, priorities, command examples, and the mistakes to avoid. Never inspect project/ or issue JSON directly (including with cat or jq); use Kanbus commands only.
Performance: Prefer kbs (Rust) when available; kanbus (Python) is equivalent but slower.
Warning: Editing project/ directly violates The Way. Do not read or write anything in project/; work only through Kanbus.
Git / PR policy: Rules for product-code commits, branch names, pull requests, and human approval live in this repository's AGENTS.md (outside this Kanbus section). CONTRIBUTING_AGENT.md covers Kanbus board mechanics such as `kbs commit`; follow AGENTS.md for product code and git workflow.


## Project rules (Biased-Decisions)

- Public copy is plain language for a reader who has never heard of this project (`docs/plain-language.md`). Check it with `make copy-check` (Limatus, `writing/`); findings are decided by a person, never auto-applied.

This is a public repository. It measures bias in fast decision models and publishes the record.

Work
- Follow CONTRIBUTING_AGENT.md (The Way): name the work in Kanbus before starting it, stories carry Gherkin, keep a running log in Kanbus comments on the epic, and tag every `kbs create` and `kbs comment` with agent provenance. Never read or write anything under project/ except project/wiki/*.md; use `kbs` commands, then `kbs commit` and push.
- Studies are pre-registered: commit the predictions (docs/*-preregistration.md or studies/PREREGISTERED.md) before any engine answers a single item, and score against them word for word.
- The record is replayable: `bd replay` must reproduce studies/ byte for byte; the Amplify build fails otherwise.

Git (Git Flow)
- `develop` is the integration branch and `main` is the release branch. Open pull requests into `develop` for product work and merge them there as soon as review is addressed and CI is green. Do not park finished work on long-lived branches, and do not merge product work straight to `main`.
- Promote `develop` to `main` with a pull request when you intend to publish. Semantic Release runs only from `main`, and AWS Amplify builds and deploys the site from `main`, so a promotion is a deploy: watch the Amplify job and the Deploy check to completion, and never call it published until the live site shows it.
- Kanbus board changes are project management, not product. After `kbs` create, update, comment or close, run `kbs commit` and push straight to `develop`. No feature branch, no pull request. Do not mix board files into a product pull request. Board changes reach `main`, and the live site, only with the next promotion.
- Answer data collected on another machine arrives on a `runs/<issue id>` branch. Merge it into `develop`, never `main`.
- Conventional Commits on every commit; Semantic Release derives versions from them on `main` (see CONTRIBUTING.md).
- Never commit secrets. Keys come from the environment or a gitignored .env; never read, print or `source` a .env.

Engines and hardware
- One GPU job at a time on a local machine; never run a GPU job, a full `bd replay` and a site build together.
- Hosted engines that cost money (Jev) run only after the spend is priced and explicitly approved.
- Pin engine versions and record them in the study's build notes; a version change is a new engine for comparison purposes.

Writing
- Public pages name the model as the subject of every finding ("Laya moves toward 'greedy' when a bio says 'Jewish'"), never the group. No slurs, no emojis, nothing specific to any one company's internal work, and no notes about how the site or its charts were built.
