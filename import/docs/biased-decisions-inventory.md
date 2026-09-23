# Inventory: what the Jev-Flywheel bias studies depend on (read-only findings, 2026-09-23)

Source repo: /Users/home/Projects/Jev-Flywheel (branch main). Everything below was verified by reading.

## Modules to port (jev_flywheel/)
| module | third-party | internal imports | exports used |
|---|---|---|---|
| counterfactual.py | lazy `spacy` (`en_core_web_sm`) | none | swap_gender→Swap, redact_names/redact_names_batch→Redaction, DEFAULT_NAME_LIST, _load_nlp |
| names.py | none | none | NAMES (B&M 2004), insert_name, name_versions→NamedVersions, _SUBJECT_PRONOUN |
| fullname.py | none (lazy _load_nlp) | names._SUBJECT_PRONOUN; counterfactual._load_nlp | analyze_full_name→FullNamePlan, render_full_name→FullNameResult, apply_full_name, apply_full_name_full |
| age.py | none | names._SUBJECT_PRONOUN | insert_age→Insertion, eligible |
| invariance.py | none | none | DEFAULT_MAX_FLIP_RATE, flip_rate, passes_invariance_gate, gate_new_elements, … (port for completeness; not used by replay) |
| jev.py | lazy `typesafe_sdk` (AsyncTypeSafeClient, RetryPolicy) | none | JevSession(.ask(text, questions), .requests_sent/.input_tokens/.output_tokens, client_factory), JevAnswers |
| laya.py | lazy `laya_mlx` | none | LayaClient(.warm, .system_one, .model_name, .check_questions), to_laya_question, DEFAULT_CHECKPOINT="aac6fef/laya-mlx" |
| items.py | none | none | load_items(path)→List[Item] (.id, .text, .metadata) — only this is needed |
| evaluate.py | none | none | expected_calibration_error (+ reliability_bins) — the ONLY jev_flywheel import in the scoring path (bios_gender.py) |
| scorecard.py | pyyaml | features, head, models (stdlib) | Scorecard.from_yaml(text).questions() — used only by the answer builders |

## Scripts to port (scripts/)
- Builders: build_bios_fixtures.py, build_bios_pairs_fixtures.py (pandas + parquet from the HF URL; redact_names_batch, swap_gender), build_bios_race_fixtures.py (names.name_versions), build_bios_race2_fixtures.py (fullname.analyze_full_name/render_full_name; reads name_pools.json), build_bios_age_fixtures.py (age.eligible/insert_age), build_name_pools.py (pandas; needs Rosenman first/last tables, SSA baby names, Census 2010 surnames — all CC0/public domain; not committed).
- Answer builders: build_bios_jev_answers.py (dotenv, JevSession, Scorecard), build_bios_laya_answers.py (LayaClient). Output rows: {id, model, usage{input_tokens,output_tokens}, latency_ms, answers{"Occupation": {type, choice, confidence, probabilities{...}, [action]}}}.
- Scoring modules (stdlib only): bios_gender.py (Verdict(item_id, predicted, p_surgeon, truth, gender), accuracy, counterfactual_flip_rate, mean_abs_delta_p, flip_direction_share, tpr_gap_surgeon, ece, score_arm, write_rows (append mode), mentions_gender), bios_pairs.py (PAIR_INFO, flip_direction_share_toward_more_female, recall_gap_less_female, bootstrap_flip_ci, score_pair), bios_race.py, bios_race2.py (GROUPS, group_mean_p, majority_call, bootstrap_mean_ci), bios_age.py (signed_mean_shift, direction_older_surgeon_share, bootstrap_ci), bios_shortlist.py (stdlib; hardcoded to fixtures/bios_pairs/{paralegal_attorney,nurse_physician}; tie_fair; twin_averaged variant).
- Runners: run_bios_arms.py (J0/L0), run_bios_pairs.py (--pair, --engine, --copy-surgeon-physician), run_bios_race.py, run_bios_race2.py (--sample all|500), run_bios_age.py. Question name hardcoded "Occupation"; positive class "surgeon" for the surgeon studies, PAIR_INFO[pair]["less_female"] for pairs, "attorney"/"physician" for the shortlist.
- Scoring reads only: row["id"], row["answers"]["Occupation"]["choice"], ["probabilities"][positive]. `confidence` is never read (ECE is reconstructed from p).

## Fixtures needed for offline replay (~36 MB; skip every recordings/ dir and fixtures/bios_attorney, bios_nurse, and the root demo corpus)
- fixtures/bios/: items.jsonl 4.4M (6,000 + twins), answers.jsonl.gz 116K (8,000, Jev), answers-laya.jsonl.gz 159K; race_versions.jsonl 2.8M (4,713) + answers-race{,-laya}.jsonl.gz; race2_versions.jsonl 18M (31,488) + answers-race2.jsonl.gz (8,000, 500-bio subsample) + answers-race2-laya.jsonl.gz (31,488) + race2_jev_subsample.txt; age_versions.jsonl 2.8M (4,924) + answers-age{,-laya}.jsonl.gz; name_pools.json 78K; first_names.txt 18K; scorecards/v1.yaml (766 B; reference_full.yaml is byte-identical).
- fixtures/bios_pairs/{nurse_physician,paralegal_attorney,teacher_professor}/: items.jsonl (~2.3M each) + answers.jsonl.gz + answers-laya.jsonl.gz + scorecards/.
- studies rows to reproduce: bios_gender.jsonl (the J0/L0 rows: 3 of 18; the rest are loop arms), bios_pairs.jsonl (8), bios_race.jsonl (2), bios_race2.jsonl (3), bios_age.jsonl (2), bios_shortlist.jsonl (24; overwritten by its script). Spend logs: studies/bios_{gender,race,race2,age,pairs}_spend.md.

## Makefile targets (write to var/, append mode; rm -f first)
bios (run_bios_arms J0, L0), race (jev, laya), race2 (laya all, laya 500, jev 500), age (jev, laya), pairs (3 pairs × 2 engines + --copy-surgeon-physician). Each prints json rows and "Next: studies/PREREGISTERED.md, '<section>'".

## Tests to port
tests/bios_{gender,pairs,race,race2,age}_test.py (16+8+13+12+14 tests; import Verdict from bios_gender via sys.path), jev_flywheel/{counterfactual,names,fullname,age,invariance}_test.py (16+8+9+14+18; counterfactual has a spaCy skipif), jev_flywheel/{jev,laya,items}_test.py (16+12+16).

## Dependencies
Replay/scoring: stdlib + pytest. Engines: typesafe-sdk (Jev), laya-mlx==0.1.0 (Laya, Apple silicon), pyyaml, python-dotenv. Fixture rebuild: pandas + pyarrow (pyarrow is UNDECLARED in Jev-Flywheel — declare it). Redaction/full names: spacy>=3.8,<3.9 + en_core_web_sm wheel https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl. Python >=3.10. License MIT, Copyright (c) 2026 Anthus AI Solutions. pytest config: python_files ["*_test.py","test_*.py"].

## Pre-registration skeleton (carry over verbatim style)
"# Pre-registration: <question>" / "Written <date>, before <what must not have happened>" / ## The question (or The corpus / The scenario / The method) / ## Arms / ## Predictions, recorded in advance (table: measurement | prediction | range I would not be surprised by; Reasoning; Stated risk) / ## What would change what I believe / ## Rules, fixed before any run / ## Reporting rule / > **Deviations, <date>** blockquotes appended, never editing above / ## Outcome (recorded <date>; files) with a per-row verdict table, both engines side by side, Interpretation, Spend, What replays offline.
