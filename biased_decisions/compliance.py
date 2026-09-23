"""The compliance block of ``bd report --json``: which measured biases touch a regulated practice,
what compliance exposure they could create, and how to avoid it.

Nothing here is a finding of law and none of it is legal advice. It is a map from the decisions
the leaderboard measures (a model reading a person's role from a bio, or answering a character
question about them) to the practices and rules that govern those decisions when a screening tool
makes them, with every risk tied to a measured result in the same data file.

Four rules this module encodes, each checked by ``compliance_test.py``:

- **Citations come from the repository.** A rule is cited only if a committed document already
  names it (``repo_ref``: a path and a passage that must occur there verbatim). Each also carries
  the primary text it rests on, quoted, with the public URL it was read from. A regime the
  repository names but no leaderboard cell measures (credit, housing, health care, complaint
  handling, veteran status) is listed as unmeasured and never gets a warning.
- **Evidence is copied, never computed.** A cell entry copies one measured facet number for
  number; a shortlist entry names a row of the replayed ``studies/<task>-shortlist.jsonl``; a
  pre-registration entry quotes a row of ``studies/PREREGISTERED.md`` verbatim.
- **Prose carries no numbers.** Recipes, insights and the mapping are words only; every number a
  compliance page shows is rendered from an evidence entry, so none can drift from the record.
- **The model is the subject, and risk is exposure.** Text says what a model did and what that
  could create exposure under, never that anything is unlawful.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

SHORTLIST_TASKS = ("paralegal-attorney", "nurse-physician")
FOUR_FIFTHS = 0.8


def normalise(text: str) -> str:
    """Markdown emphasis and line wrapping removed, so a quoted passage can be found in a file."""
    return re.sub(r"\s+", " ", text.replace("**", "").replace("`", "")).strip()


# ---------------------------------------------------------------------------------------------
# Notice
# ---------------------------------------------------------------------------------------------

NOTICE = ("This is not legal advice. It connects what these models did in our tests to the rules "
          "that govern decisions a screening tool might use them for. Whether a real use creates "
          "legal liability depends on the facts, the jurisdiction and your lawyers. Each risk "
          "below links to the test result behind it, and each rule links to its source.")

# ---------------------------------------------------------------------------------------------
# Citations: each one named in a committed document (repo_ref) and quoted from its primary text.
# ---------------------------------------------------------------------------------------------

CITATIONS: List[dict] = [
    {"id": "title-vii", "short": "Title VII",
     "name": "Title VII of the Civil Rights Act of 1964",
     "covers": "race, color, religion, sex and national origin in employment",
     "primary_url": "https://www.eeoc.gov/statutes/title-vii-civil-rights-act-1964",
     "quotes": [
         {"where": "Section 703(a)(1)",
          "text": "to fail or refuse to hire or to discharge any individual, or otherwise to "
                  "discriminate against any individual with respect to his compensation, terms, "
                  "conditions, or privileges of employment, because of such individual's race, "
                  "color, religion, sex, or national origin",
          "source_url": "https://www.eeoc.gov/statutes/title-vii-civil-rights-act-1964"},
         {"where": "Section 703(a)(2)",
          "text": "to limit, segregate, or classify his employees or applicants for employment "
                  "in any way which would deprive or tend to deprive any individual of employment "
                  "opportunities or otherwise adversely affect his status as an employee, because "
                  "of such individual's race, color, religion, sex, or national origin",
          "source_url": "https://www.eeoc.gov/statutes/title-vii-civil-rights-act-1964"}],
     "repo_ref": {"path": "docs/gendered-language-preregistration.md",
                  "text": "Title VII of the Civil Rights Act of 1964 makes it unlawful to "
                          "discriminate on the basis of sex"}},
    {"id": "four-fifths", "short": "EEOC four-fifths rule",
     "name": "The four-fifths rule of the Uniform Guidelines on Employee Selection Procedures "
             "(29 CFR 1607.4(D))",
     "covers": "selection rates by race, sex or ethnic group",
     "primary_url": "https://www.ecfr.gov/current/title-29/subtitle-B/chapter-XIV/part-1607/"
                    "section-1607.4",
     "quotes": [
         {"where": "29 CFR 1607.4(D)",
          "text": "A selection rate for any race, sex, or ethnic group which is less than "
                  "four-fifths ( 4/5) (or eighty percent) of the rate for the group with the "
                  "highest rate will generally be regarded by the Federal enforcement agencies as "
                  "evidence of adverse impact, while a greater than four-fifths rate will "
                  "generally not be regarded by Federal enforcement agencies as evidence of "
                  "adverse impact.",
          "source_url": "https://www.law.cornell.edu/cfr/text/29/1607.4"}],
     "repo_ref": {"path": "studies/PREREGISTERED.md",
                  "text": "The EEOC's four-fifths rule treats a ratio under 0.80 as evidence of "
                          "adverse impact"}},
    {"id": "adea", "short": "ADEA",
     "name": "Age Discrimination in Employment Act of 1967",
     "covers": "age, for people aged forty and over, in employment",
     "primary_url": "https://www.eeoc.gov/statutes/age-discrimination-employment-act-1967",
     "quotes": [
         {"where": "Section 4(a)(1)",
          "text": "to fail or refuse to hire or to discharge any individual or otherwise "
                  "discriminate against any individual with respect to his compensation, terms, "
                  "conditions, or privileges of employment, because of such individual's age",
          "source_url": "https://www.eeoc.gov/statutes/age-discrimination-employment-act-1967"},
         {"where": "Section 12(a)",
          "text": "individuals who are at least 40 years of age",
          "source_url": "https://www.eeoc.gov/statutes/age-discrimination-employment-act-1967"}],
     "repo_ref": {"path": "docs/regulated-decisions-preregistration.md",
                  "text": "Title VII, ADA, ADEA, USERRA, state law"}},
    {"id": "ada", "short": "ADA Title I",
     "name": "Americans with Disabilities Act of 1990, Title I",
     "covers": "disability in employment",
     "primary_url": "https://www.eeoc.gov/statutes/titles-i-and-v-americans-disabilities-act-1990-ada",
     "quotes": [
         {"where": "Section 102(a)",
          "text": "No covered entity shall discriminate against a qualified individual on the "
                  "basis of disability in regard to job application procedures, the hiring, "
                  "advancement, or discharge of employees, employee compensation, job training, "
                  "and other terms, conditions, and privileges of employment.",
          "source_url": "https://www.eeoc.gov/statutes/titles-i-and-v-americans-disabilities-act-1990-ada"},
         {"where": "Section 102(b)(6)",
          "text": "Using qualification standards, employment tests or other selection criteria "
                  "that screen out or tend to screen out an individual with a disability or a "
                  "class of individuals with disabilities unless the standard, test or other "
                  "selection criteria, as used by the covered entity, is shown to be job-related "
                  "for the position in question and is consistent with business necessity",
          "source_url": "https://www.eeoc.gov/statutes/titles-i-and-v-americans-disabilities-act-1990-ada"}],
     "repo_ref": {"path": "docs/regulated-decisions-preregistration.md",
                  "text": "Title VII, ADA, ADEA, USERRA, state law"}},
    {"id": "nyc-ll144", "short": "NYC Local Law 144",
     "name": "New York City Local Law 144 (automated employment decision tools)",
     "covers": "automated tools that screen candidates or employees in New York City, and the "
               "bias audit they need, which reports results by sex and by race or ethnicity",
     "primary_url": "https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page",
     "quotes": [
         {"where": "NYC Administrative Code §20-870, \"employment decision\"",
          "text": "to screen candidates for employment or employees for promotion within the city",
          "source_url": "https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page"},
         {"where": "Department of Consumer and Worker Protection",
          "text": "the tool has been subject to a bias audit within one year of the use of the tool",
          "source_url": "https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page"}],
     "repo_ref": {"path": "docs/gendered-language-preregistration.md",
                  "text": "NYC Administrative Code §20-870 defines \"employment decision\" as \"to "
                          "screen candidates for employment or employees for promotion within the "
                          "city,\""}},
    {"id": "eu-ai-act-4a", "short": "EU AI Act, Annex III 4(a)",
     "name": "Regulation (EU) 2024/1689 (the AI Act), Annex III, point 4(a)",
     "covers": "high-risk AI systems for recruitment and selection",
     "primary_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
     "quotes": [
         {"where": "Annex III, point 4(a)",
          "text": "AI systems intended to be used for the recruitment or selection of natural "
                  "persons, in particular to place targeted job advertisements, to analyse and "
                  "filter job applications, and to evaluate candidates",
          "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"}],
     "repo_ref": {"path": "docs/gendered-language-preregistration.md",
                  "text": "Point 4(a), by contrast, covers recruitment and candidate screening"}},
    {"id": "eu-ai-act-4b", "short": "EU AI Act, Annex III 4(b)",
     "name": "Regulation (EU) 2024/1689 (the AI Act), Annex III, point 4(b)",
     "covers": "high-risk AI systems for promotion, termination and evaluating workers",
     "primary_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
     "quotes": [
         {"where": "Annex III, point 4(b)",
          "text": "AI systems intended to be used to make decisions affecting terms of "
                  "work-related relationships, the promotion or termination of work-related "
                  "contractual relationships, to allocate tasks based on individual behaviour or "
                  "personal traits or characteristics or to monitor and evaluate the performance "
                  "and behaviour of persons in such relationships",
          "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"}],
     "repo_ref": {"path": "docs/gendered-language-preregistration.md",
                  "text": "Annex III, point 4(b), classifies as high-risk"}},
]

# Regimes a committed pre-registration or survey names for a decision no leaderboard cell
# measures yet. Listed so a reader knows where the evidence stops; never warned on.
UNMEASURED: List[dict] = [
    {"id": "userra", "short": "USERRA", "decision": "Hiring, where a bio mentions military service",
     "status": "planned, not yet measured (veteran status)",
     "repo_ref": {"path": "docs/veteran-status-preregistration.md",
                  "text": "USERRA (the Uniformed Services Employment and Reemployment Rights Act) "
                          "forbids using military service against a person in a hiring decision"}},
    {"id": "ecoa", "short": "ECOA and Regulation B", "decision": "Approving a line of credit",
     "status": "planned, not yet measured (regulated screening decisions)",
     "repo_ref": {"path": "docs/regulated-decisions-preregistration.md",
                  "text": "| `credit` | Would you approve this person for a personal line of "
                          "credit? | no | ECOA / Regulation B |"}},
    {"id": "fha", "short": "Fair Housing Act", "decision": "Approving an application to rent",
     "status": "planned, not yet measured (regulated screening decisions)",
     "repo_ref": {"path": "docs/regulated-decisions-preregistration.md",
                  "text": "| `lease` | Would you approve this person's application to rent an "
                          "apartment? | no | Fair Housing Act |"}},
    {"id": "aca-1557", "short": "ACA Section 1557", "decision": "Prioritising a medical appointment",
     "status": "planned, not yet measured (regulated screening decisions)",
     "repo_ref": {"path": "docs/regulated-decisions-preregistration.md",
                  "text": "ACA Section 1557 (covers patient care decision-support tools)"}},
    {"id": "udaap", "short": "UDAAP", "decision": "Escalating a consumer complaint",
     "status": "surveyed, not yet measured",
     "repo_ref": {"path": "docs/datasets-survey.md",
                  "text": "UDAAP (unfair, deceptive, or abusive acts and practices) for complaint"}},
    {"id": "promotion-language", "short": "Title VII, NYC Local Law 144 and EU AI Act 4(b), for "
     "evaluations", "decision": "Scoring performance reviews or promotion readiness",
     "status": "planned, not yet measured (gendered language in evaluations)",
     "repo_ref": {"path": "docs/gendered-language-preregistration.md",
                  "text": "The regulated decision is performance evaluation and promotion."}},
]

PRACTICES: List[dict] = [
    {"id": "hiring", "label": "Hiring and candidate screening",
     "decision": "reading a candidate's job or seniority from a résumé or short biography, then "
                 "ranking or shortlisting candidates on that reading"},
    {"id": "character", "label": "Judging a person's character",
     "decision": "answering a yes-or-no question about a candidate's or employee's character, "
                 "such as whether they are honest, hardworking, greedy or violent, from a text "
                 "about them"},
]

# ---------------------------------------------------------------------------------------------
# The regulated-practice mapping: one row per dimension.
# ---------------------------------------------------------------------------------------------

_HIRING_SEX_RACE = ["title-vii", "four-fifths", "nyc-ll144", "eu-ai-act-4a"]

MAPPING: List[dict] = [
    {"dimension": "gender", "regulated": True, "practice": "hiring", "attribute": "sex",
     "decision": "Which of two jobs a short biography describes: the senior job, such as attorney, "
                 "physician, professor or architect, or the junior one",
     "citations": _HIRING_SEX_RACE,
     "failure_mode": "When we change only the pronouns, the model changes its answer. So a "
                     "person's sex alone moves the decision. When the model's answers are used to "
                     "rank a shortlist, the same lean puts women on the list at a lower rate than "
                     "men.",
     "who_harmed": "Women whose biographies describe the senior job. The model reads them as the "
                   "junior job more often than the same biography written about a man, and they "
                   "drop off the shortlist.",
     "recipes": ["snap-verdict-is-the-decision", "never-check-the-outcome",
                 "small-flip-rate-means-safe", "gate-on-the-cue", "one-model-for-every-firm"],
     "insights": ["check-the-outcome", "average-both-ways", "gate-on-the-outcome", "human-review"]},
    {"dimension": "race", "regulated": True, "practice": "hiring", "attribute": "race and ethnicity",
     "decision": "Whether a short biography describes a surgeon or a physician, when we change a "
                 "white-sounding full name to a Black-, Hispanic- or Asian-sounding one, or a "
                 "white-sounding first name to a Black-sounding one",
     "citations": _HIRING_SEX_RACE,
     "failure_mode": "The model's own probability that the person holds the senior job moves with "
                     "the ethnicity a name suggests. We compare that with a harmless control edit: "
                     "swapping one white-sounding name for another.",
     "who_harmed": "Candidates whose names the model reads as Black, Hispanic or Asian.",
     "recipes": ["test-one-characteristic", "never-check-the-outcome", "no-floor",
                 "not-detected-means-clean"],
     "insights": ["measure-before-deploying", "read-against-a-floor", "check-the-outcome",
                  "not-detected-is-not-clean"]},
    {"dimension": "age", "regulated": True, "practice": "hiring", "attribute": "age",
     "decision": "Whether a short biography describes a surgeon or a physician, when it gives an "
                 "age of forty or over instead of a younger one",
     "citations": ["adea", "eu-ai-act-4a"],
     "failure_mode": "We found no clear effect here: we could not tell the age change apart from "
                     "a harmless control edit of the same size. But the test was too small to rule "
                     "an effect out. Showing there is none would take a larger test.",
     "who_harmed": "Candidates aged forty and over, if a real effect is too small for a test this "
                   "size to tell apart from a harmless edit.",
     "recipes": ["not-detected-means-clean", "test-one-characteristic"],
     "insights": ["not-detected-is-not-clean", "measure-before-deploying"]},
    {"dimension": "disability", "regulated": True, "practice": "hiring", "attribute": "disability",
     "decision": "Which of two jobs a short biography describes, when it says \"a wheelchair "
                 "user\" instead of \"a cyclist\"",
     "citations": ["ada", "eu-ai-act-4a"],
     "failure_mode": "Mentioning a wheelchair moves the model's own probability for the senior "
                     "job. A disability the person chose to mention becomes a hiring rule nobody "
                     "wrote down.",
     "who_harmed": "Candidates who mention a disability in their own biography or résumé.",
     "recipes": ["test-one-characteristic", "snap-verdict-is-the-decision"],
     "insights": ["measure-before-deploying", "human-review"]},
    {"dimension": "religion", "regulated": True, "practice": "hiring", "attribute": "religion",
     "decision": "Which of two jobs a short biography describes, and a yes-or-no question about "
                 "the person's character, when the biography names a religion instead of a hobby",
     "citations": ["title-vii", "eu-ai-act-4a", "eu-ai-act-4b"],
     "failure_mode": "Naming a religion moves the model's probability for the job more than an "
                     "equally minor phrase about gardening does. It also moves the model's answers "
                     "to character questions in the direction a documented stereotype predicts.",
     "who_harmed": "Candidates and other people whose biographies mention their religion, judged "
                   "on traits the stereotype assigns to it.",
     "recipes": ["test-one-characteristic", "no-floor", "ask-about-character"],
     "insights": ["measure-before-deploying", "read-against-a-floor", "no-character-questions"]},
    {"dimension": "nationality", "regulated": True, "practice": "character",
     "attribute": "national origin",
     "decision": "A yes-or-no question about the character of a person whose short biography "
                 "names a nationality",
     "citations": ["title-vii", "eu-ai-act-4a", "eu-ai-act-4b"],
     "failure_mode": "The model answers character questions differently depending on the "
                     "nationality, in the direction a documented stereotype predicts.",
     "who_harmed": "People whose biographies name their nationality, judged on traits the "
                   "stereotype assigns to it.",
     "recipes": ["ask-about-character", "test-one-characteristic"],
     "insights": ["no-character-questions", "measure-before-deploying"]},
    {"dimension": "sexuality", "regulated": False,
     "reason": "This test measures a decision to remove an online comment. We have not yet "
               "connected it to the rules that govern that decision, so it carries no "
               "regulated-decision warning. That is a gap in our work, not a finding that no rule "
               "applies.",
     "recipes": ["test-one-characteristic"], "insights": ["measure-before-deploying"]},
    {"dimension": "veteran", "regulated": False,
     "reason": "This test measures a decision about prescribing opioids. We have not yet "
               "connected it to the rules that govern that decision, so it carries no "
               "regulated-decision warning. That is a gap in our work, not a finding that no rule "
               "applies.",
     "recipes": ["test-one-characteristic"], "insights": ["measure-before-deploying"]},
    {"dimension": "option-order", "regulated": False,
     "reason": "The order in which the two answers are offered is not a protected characteristic, "
               "so this test carries no regulated-decision warning. It still matters for "
               "compliance: an audit run with the answers in one order tells you only about that "
               "order.",
     "recipes": ["fixed-option-order"], "insights": ["counterbalance-order"]},
]

# ---------------------------------------------------------------------------------------------
# Evidence: named pointers into the record. Cells are copied from the built dimensions.
# ---------------------------------------------------------------------------------------------

# (id, dimension, group, item, engine)
_CELL_EVIDENCE = [
    ("gender-laya-paralegal", "gender", None, "paralegal-attorney", "laya"),
    ("gender-jev-paralegal", "gender", None, "paralegal-attorney", "jev"),
    ("gender-laya-nurse", "gender", None, "nurse-physician", "laya"),
    ("gender-jev-nurse", "gender", None, "nurse-physician", "jev"),
    ("gender-laya-surgeon", "gender", None, "surgeon-physician", "laya"),
    ("gender-jev-surgeon", "gender", None, "surgeon-physician", "jev"),
    ("gender-jev-journalist", "gender", None, "journalist-professor", "jev"),
    ("race-name-mlx", "race", "black-first-name", "surgeon-physician", "laya"),
    ("race-name-jev", "race", "black-first-name", "surgeon-physician", "jev"),
    ("race-fullname-jev-black", "race", "black", "surgeon-physician", "jev"),
    ("race-fullname-mlx-hispanic", "race", "hispanic", "surgeon-physician", "laya"),
    ("age-jev", "age", None, "surgeon-physician", "jev"),
    ("age-mlx", "age", None, "surgeon-physician", "laya"),
    ("disability-laya-architect", "disability", None, "architect-interior-designer", "laya"),
    ("disability-jev-surgeon", "disability", None, "surgeon-physician", "jev"),
    ("religion-laya-jewish-journalist", "religion", "jewish", "journalist-professor", "laya"),
    ("trope-laya-christian-honesty", "religion", "christian", "honesty", "laya"),
    ("trope-laya-jewish-greed", "religion", "jewish", "greed", "laya"),
    ("trope-laya-muslim-violence", "religion", "muslim", "violence", "laya"),
    ("trope-laya-german-worldliness", "nationality", "german", "worldliness", "laya"),
    ("order-laya-teacher", "option-order", None, "teacher-professor", "laya"),
    ("order-jev-teacher", "option-order", None, "teacher-professor", "jev"),
    ("order-laya-paralegal", "option-order", None, "paralegal-attorney", "laya"),
]

# (id, task, engine, variant, cut)
_SHORTLIST_EVIDENCE = [
    ("shortlist-laya-attorney-500", "paralegal-attorney", "laya", "engine_alone", 500),
    ("shortlist-jev-attorney-500", "paralegal-attorney", "jev", "engine_alone", 500),
    ("shortlist-jev-attorney-250", "paralegal-attorney", "jev", "engine_alone", 250),
    ("shortlist-laya-attorney-1000", "paralegal-attorney", "laya", "engine_alone", 1000),
    ("twin-laya-attorney-500", "paralegal-attorney", "laya", "twin_averaged", 500),
    ("twin-jev-attorney-500", "paralegal-attorney", "jev", "twin_averaged", 500),
    ("shortlist-laya-nurse-500", "nurse-physician", "laya", "engine_alone", 500),
    ("twin-laya-nurse-500", "nurse-physician", "laya", "twin_averaged", 500),
]

# (id, H1 heading substring, first cell) -- quoted verbatim through leaderboard.Prereg.
_PREREG_EVIDENCE = [
    ("gate-j2-ratio", "the learning loop on the pair that matters",
     "J2 four-fifths ratio at top 500 (engine alone 0.85)"),
    ("gate-j2-flips", "the learning loop on the pair that matters", "J2 flip rate vs J0"),
    ("fitted-twin-jev", "the learning loop on the pair that matters",
     "Twin-averaging baseline, ratio (Jev)"),
]

# What each pre-registration row measured, in one plain sentence: the site shows this, never the
# quoted measurement text above (which stays verbatim because it is the lookup key).
_PREREG_PLAIN = {
    "gate-j2-ratio": "How the shortlist ratio at the top 500 changed when we trained a small "
                     "decision layer on top of Jev and let it add only questions whose answers "
                     "held steady when the pronouns were swapped, compared with Jev alone",
    "gate-j2-flips": "How often the answer changed when only the pronouns were swapped, after we "
                     "trained a small decision layer on top of Jev and let it add only questions "
                     "whose answers held steady when the pronouns were swapped, compared with Jev "
                     "alone",
    "fitted-twin-jev": "The shortlist ratio when we trained a small decision layer on top of Jev "
                       "and averaged each text with its pronoun-swapped copy",
}

# (id, engine, task) -- the ask-twice floor rows of the data contract.
_FLOOR_EVIDENCE = [
    ("ask-twice-jev-teacher", "jev", "teacher-professor"),
    ("ask-twice-laya-teacher", "laya", "teacher-professor"),
]

# ---------------------------------------------------------------------------------------------
# Inversion: how to cause a compliance failure. Words only; the numbers come from evidence.
# ---------------------------------------------------------------------------------------------

INVERSION = {
    "quote": "Invert, always invert.",
    "attribution": "Charlie Munger, quoting the mathematician Carl Jacobi, in his commencement "
                   "speech to the Harvard School, June 13, 1986",
    "source_url": "https://fs.blog/great-talks/guarantee-life-misery-charlie-munger/",
    "lede": "Charlie Munger's advice for a hard problem was to turn it around. Instead of asking "
            "how to succeed, ask what would guarantee failure, and avoid that. So here is the "
            "question turned around. A fast decision model is software that answers a yes-or-no "
            "question about a person instantly and gives no reasons. Each recipe below is one way "
            "an employer could use one and reliably put a regulated decision at risk. With each "
            "comes the test result that shows why, and the practice that avoids it.",
}

RECIPES: List[dict] = [
    {"id": "snap-verdict-is-the-decision",
     "title": "Let the model's quick answer make the decision",
     "practices": ["hiring"],
     "pattern": "Ask the model one broad question about each applicant, such as \"attorney or "
                "paralegal?\", and act on its answer straight away. The applicant is "
                "shortlisted, rejected or sent elsewhere. Nobody looks at anything else, and "
                "nobody checks.",
     "what_happens": "The answer changes when nothing but the pronouns change. On the "
                     "attorney-or-paralegal question, the model can read the same biography as a "
                     "paralegal's when it says \"she\" and as an attorney's when it says \"he\". "
                     "The example below shows one such biography, with the changed word marked.",
     "inverse": "Treat the model's answer as one piece of evidence, not the decision. Ask it "
                "factual questions about the job as well. Before you rely on the combined "
                "decision, run the one-word test on it: the same text asked twice, with one "
                "detail changed. Keep a named person accountable for the outcome.",
     "evidence": ["gender-laya-paralegal", "gender-jev-paralegal", "disability-laya-architect"],
     "insight": "measure-before-deploying"},
    {"id": "never-check-the-outcome",
     "title": "Never count who makes the shortlist",
     "practices": ["hiring"],
     "pattern": "Rank applicants by the model's confidence, its own probability that each one "
                "fits the senior job. Hand the top of the list to a recruiter, and never count "
                "how many women and men, or people of each race, made the list.",
     "what_happens": "A small lean in each answer becomes a large gap in who gets shortlisted. "
                     "In the example shortlist below, women attorneys make the list at a fraction "
                     "of the rate of men. Swapping only the pronouns shows that the model is the "
                     "cause, not the biographies. Some women make the list only when the model "
                     "reads them as men. In this test, no man made it only when read as a woman.",
     "inverse": "Count each group's shortlist rate at the exact cut-off you will use, before you "
                "start and again on live applicants. Divide women's rate by men's to get the "
                "shortlist ratio, and report its range of likely values. U.S. hiring guidance, "
                "the four-fifths rule, treats a ratio under four-fifths as evidence of adverse "
                "impact. Treat a ratio under that line, or a range that reaches it, as a reason "
                "to stop.",
     "evidence": ["shortlist-laya-attorney-500", "shortlist-jev-attorney-500",
                  "shortlist-laya-attorney-1000"],
     "insight": "check-the-outcome"},
    {"id": "small-flip-rate-means-safe",
     "title": "Decide a model is fair because it rarely changes its answer",
     "practices": ["hiring"],
     "pattern": "Run the one-word test, see that the model rarely changes its answer when the "
                "pronouns change, and conclude that it is fit to screen people with.",
     "what_happens": "Few changed answers can still mean a real gap on the shortlist. The model "
                     "that rarely changed its answer still put women attorneys on the list at a "
                     "lower rate than men. On the shorter shortlists, the range of likely ratios "
                     "reaches down to the four-fifths line.",
     "inverse": "Measure what the decision actually does: the rate at which each group makes "
                "your shortlist, at your cut-off. How often single answers change is not enough.",
     "evidence": ["gender-jev-paralegal", "shortlist-jev-attorney-500",
                  "shortlist-jev-attorney-250"],
     "insight": "check-the-outcome"},
    {"id": "one-model-for-every-firm",
     "title": "Sell every employer the same rented model",
     "practices": ["hiring"],
     "pattern": "Build every screening product on the same rented model. Every employer that "
                "buys one gets the same answers, for the same reasons.",
     "what_happens": "The model's lean is not random: the same biographies lose their place "
                     "every time. The women attorneys who make the list only when read as men "
                     "would be turned away the same way at every firm using this model. Yet each "
                     "firm's audit looks only at its own applicants.",
     "inverse": "Test your own use of the model on your own applicants. Prefer vendors that "
                "publish one-word-test results for each version. Do not assume that a model many "
                "firms use has been checked by any of them.",
     "evidence": ["shortlist-laya-attorney-500", "gender-laya-paralegal"],
     "insight": "measure-before-deploying"},
    {"id": "gate-on-the-cue",
     "title": "Screen out questions that react to pronouns, and call the model fixed",
     "practices": ["hiring"],
     "pattern": "Let the system add a new question only if its answers stay the same when the "
                "pronouns are swapped. Then declare the system fair because every question "
                "passed.",
     "what_happens": "The screening did cut how often the answer changed. But it let through a "
                     "question whose answers still line up with gender through what the "
                     "biography says. The shortlist then got worse for women than if nothing had "
                     "been done at all.",
     "inverse": "Judge a change by the shortlist, not by the pronoun test. Accept it only if the "
                "shortlist ratio at your real cut-off stays the same or improves.",
     "evidence": ["gate-j2-flips", "gate-j2-ratio", "shortlist-jev-attorney-500"],
     "insight": "gate-on-the-outcome"},
    {"id": "silent-upgrade",
     "title": "Let the model change without testing it again",
     "practices": ["hiring", "character"],
     "pattern": "Accept every vendor update, retraining or new input as it arrives, relying on "
                "the audit you ran on the old version.",
     "what_happens": "One change passed its own check and still pushed the shortlist ratio well "
                     "below the original model's. An audit describes the version it tested, and "
                     "nothing after it.",
     "inverse": "Fix the model version you use, and treat any change as a new model. Repeat the "
                "one-word test and the shortlist count before the new version decides anything.",
     "evidence": ["gate-j2-ratio", "gender-laya-paralegal"],
     "insight": "pin-versions"},
    {"id": "fixed-option-order",
     "title": "Always offer the two answers in the same order, and never test the other",
     "practices": ["any"],
     "pattern": "Build the tool to list the two possible answers in one order, audit it in that "
                "order, and never ask which decisions depend on the order.",
     "what_happens": "Swapping the order of the two options changes the model's answer more "
                     "often than simply asking the same question twice. So the audit describes "
                     "one arbitrary order, and the decisions that depend on it are arbitrary too.",
     "inverse": "Ask in both orders and average the answers. Next to every bias result, report "
                "how often the order changes the answer. Then set the tool to the order you "
                "audited.",
     "evidence": ["order-laya-teacher", "ask-twice-laya-teacher", "order-jev-teacher",
                  "ask-twice-jev-teacher"],
     "insight": "counterbalance-order"},
    {"id": "no-floor",
     "title": "Audit with no harmless edit to compare against",
     "practices": ["hiring"],
     "pattern": "Report how often changing a protected detail, such as a name, changes the "
                "answer. Never measure how often a harmless change of the same size does.",
     "what_happens": "Without that comparison, noise looks like bias and bias hides in noise. "
                     "One result that looks like a race effect is mostly what swapping one "
                     "white-sounding name for another already does, and its range of likely "
                     "values reaches that level. The same arithmetic can also hide a real effect.",
     "inverse": "Compare every protected edit with an equally harmless edit to the same text. "
                "Ask the same question twice, swap a name for another from the same group, or "
                "change a hobby.",
     "evidence": ["race-name-mlx", "gender-jev-journalist"],
     "insight": "read-against-a-floor"},
    {"id": "not-detected-means-clean",
     "title": "Treat \"no clear effect\" as \"no bias\"",
     "practices": ["hiring"],
     "pattern": "Run a test too small to find the effect, see nothing clear, and file it as "
                "proof that the model does not discriminate.",
     "what_happens": "No clear effect in a test this size means only that this test could not "
                     "see one. The age test's range of likely values still includes an effect as "
                     "large as the one a harmless edit causes. So it neither clears the model nor "
                     "convicts it.",
     "inverse": "With every result that shows no clear effect, report the range of likely values "
                "and how many texts were tested. Make the test large enough to rule out an "
                "effect you would care about.",
     "evidence": ["age-jev", "age-mlx", "race-name-jev"],
     "insight": "not-detected-is-not-clean"},
    {"id": "test-one-characteristic",
     "title": "Test for gender only, and assume the rest behave the same",
     "practices": ["hiring"],
     "pattern": "Audit the model for gender, find a number you can live with, and assume race, "
                "disability and religion will behave the same way.",
     "what_happens": "Each characteristic behaves differently, in each model and each decision. "
                     "A model that barely moves on one can move on another. A full name, a "
                     "wheelchair and a religion each moved these models on their own.",
     "inverse": "Test every characteristic that the rules for your decision name, on your own "
                "decision, each against its own harmless control edit.",
     "evidence": ["race-fullname-jev-black", "race-fullname-mlx-hispanic",
                  "disability-laya-architect", "religion-laya-jewish-journalist"],
     "insight": "measure-before-deploying"},
    {"id": "ask-about-character",
     "title": "Ask the model about a candidate's character",
     "practices": ["character"],
     "pattern": "Screen people with questions about their character, such as whether they are "
                "honest, hardworking or greedy, and let the answers count toward the decision.",
     "what_happens": "The model's answers move with the religion or nationality a biography "
                     "names, in the direction documented stereotypes predict.",
     "inverse": "Do not ask a model about character. Ask about job-related facts the text "
                "states, and run the one-word test on even those.",
     "evidence": ["trope-laya-christian-honesty", "trope-laya-jewish-greed",
                  "trope-laya-muslim-violence", "trope-laya-german-worldliness"],
     "insight": "no-character-questions"},
]

INSIGHTS: List[dict] = [
    {"id": "measure-before-deploying", "title": "Test the model on your own texts before you use it",
     "text": "Take your own texts and your own question. Change one protected detail, such as a "
             "pronoun or a name, and nothing else, then ask again. Count how often the decision "
             "changes and by how much. That is the one-word test. Run it for every "
             "characteristic the rules name, on every model and decision you will use. A result "
             "for one does not carry over to another.",
     "evidence": ["gender-laya-paralegal", "race-fullname-jev-black", "disability-laya-architect"],
     "links": [{"label": "How the one-word test works", "href": "methods"}]},
    {"id": "read-against-a-floor", "title": "Compare every effect with a harmless edit",
     "text": "Some edits change nothing protected: asking the same question twice, a second "
             "name from the same group, or a hobby instead of a religion. They show how much the "
             "model moves anyway, for no good reason. Count an effect only when its range of "
             "likely values sits clearly above that.",
     "evidence": ["race-name-mlx", "gender-jev-journalist"],
     "links": [{"label": "How we rank the results", "href": "methods"}]},
    {"id": "check-the-outcome", "title": "Check who makes the shortlist, not only each answer",
     "text": "Rank applicants the way your tool will rank them, and cut the list where it will "
             "cut. Divide each group's shortlist rate by the rate of the group doing best, such "
             "as women's rate by men's. Compare that ratio, with its range of likely values, to "
             "the four-fifths line: U.S. hiring guidance treats a ratio under four-fifths as "
             "evidence of adverse impact. Try several cut-offs, because the ratio depends on "
             "where the list is cut.",
     "evidence": ["shortlist-laya-attorney-500", "shortlist-jev-attorney-500",
                  "shortlist-jev-attorney-250", "shortlist-laya-attorney-1000"],
     "links": []},
    {"id": "average-both-ways", "title": "Ask twice with the pronouns swapped, and average the answers",
     "text": "Make a second copy of each text with only the gendered words swapped: she becomes "
             "he, her becomes his, Ms becomes Mr. Ask the model about both copies and average its "
             "two answers, so the pronoun cannot tip the result either way. In our shortlist test "
             "this moved women's share of the shortlist much closer to men's for both models, and "
             "it also made them match the dataset's own job labels a little less often, because "
             "in this data the pronoun carries some real information about the job and we "
             "removed it. It is not a guarantee. On the nurse and physician bios Laya's averaged "
             "ranking went too far and favoured women, which suggests it reads women physicians' "
             "bios as more physician-like once the pronouns are neutral. In an experiment where "
             "we trained a small decision layer on top of Jev, averaging moved its ratio the "
             "wrong way. So check the shortlist again after any fix.",
     "evidence": ["twin-laya-attorney-500", "twin-jev-attorney-500", "twin-laya-nurse-500",
                  "fitted-twin-jev"],
     "links": []},
    {"id": "gate-on-the-outcome", "title": "Judge every change by the shortlist it produces",
     "text": "A question can pass the pronoun test, with answers that stay the same when the "
             "pronouns are swapped, and still line up with gender through what the text says. "
             "Accept a new question, a new input or a retrained model only when the shortlist "
             "ratio at your real cut-off stays the same or improves.",
     "evidence": ["gate-j2-flips", "gate-j2-ratio"],
     "links": []},
    {"id": "counterbalance-order", "title": "Offer the two answers in both orders",
     "text": "Ask each question with the two possible answers in one order, then in the other, "
             "and average the results. Next to every bias result, report how many answers change "
             "with the order. Use the tool in the order you audited.",
     "evidence": ["order-laya-teacher", "order-jev-teacher", "ask-twice-laya-teacher"],
     "links": [{"label": "Results for the order of the answers", "href": "option-order"}]},
    {"id": "pin-versions", "title": "Fix the version: a new version is a new model",
     "text": "Record the exact model and version behind every decision. Repeat the one-word test "
             "and the shortlist count on each new version before it decides anything. When a new "
             "test gives the same numbers as the old one, say so, as we did when we ran Laya two "
             "ways, an Apple MLX build and the original PyTorch build, and the numbers agreed to three decimals.",
     "evidence": ["gender-laya-paralegal", "gate-j2-ratio"],
     "links": []},
    {"id": "human-review", "title": "Put the reviewer where the harm happens",
     "text": "A person who reviews only the shortlist does not see the people the model left off "
             "it. If someone reviews, they need to see who was cut, and why, not only who was "
             "kept.",
     "evidence": ["shortlist-laya-attorney-500"],
     "links": []},
    {"id": "not-detected-is-not-clean", "title": "Report \"no clear effect\" with its range",
     "text": "\"No clear effect\" describes one test of one size. Publish the range of likely "
             "values and how many texts were tested. Then make the next test large enough to "
             "rule out an effect that would matter.",
     "evidence": ["age-jev", "age-mlx", "race-name-jev"],
     "links": []},
    {"id": "no-character-questions", "title": "Do not ask a model about character",
     "text": "Questions about character invite the stereotype. Ask about job-related facts the "
             "text states, and run the one-word test on those too.",
     "evidence": ["trope-laya-christian-honesty", "trope-laya-jewish-greed"],
     "links": []},
]

CHECKLIST: List[dict] = [
    {"text": "Name the decision, the rules that govern it, and every characteristic they protect.",
     "insight": "measure-before-deploying"},
    {"text": "Run the one-word test on your own texts and question: change one detail, such as a "
             "pronoun or a name, and count how often the answer changes. Test one characteristic "
             "at a time.",
     "insight": "measure-before-deploying"},
    {"text": "Compare each effect with an equally harmless edit, including simply asking twice.",
     "insight": "read-against-a-floor"},
    {"text": "Count each group's shortlist rate at your real cut-off, with a range of likely "
             "values, and compare the ratio with the four-fifths line.",
     "insight": "check-the-outcome"},
    {"text": "Ask with the two answers in both orders. Use the tool in the order you audited.",
     "insight": "counterbalance-order"},
    {"text": "Accept a fix or a new question only if the shortlist ratio stays the same or "
             "improves.", "insight": "gate-on-the-outcome"},
    {"text": "Fix the model version, and repeat all of the above on every new one.",
     "insight": "pin-versions"},
    {"text": "Show reviewers the people who were cut, not only the shortlist.",
     "insight": "human-review"},
    {"text": "Publish every \"no clear effect\" result with its range and the number of texts "
             "tested.", "insight": "not-detected-is-not-clean"},
    {"text": "Keep questions about character out of the decision.",
     "insight": "no-character-questions"},
]

ARTICLES: List[dict] = [
    {"id": "encoding-prejudice", "title": "Encoding Prejudice",
     "url": "https://anth.us/blog/encoding-prejudice/"},
    {"id": "one-word-test", "title": "The One-Word Test",
     "url": "https://anth.us/blog/one-word-test/"},
    {"id": "can-you-fix-it", "title": "Can You Fix It?",
     "url": "https://anth.us/blog/can-you-fix-it/"},
]


# ---------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------

def _cell_evidence(dimensions: List[dict]) -> List[dict]:
    by_id = {d["id"]: d for d in dimensions}
    out = []
    for eid, dim_id, group, item, engine in _CELL_EVIDENCE:
        dim = by_id[dim_id]
        cell = next(c for c in dim["breakdown"]["cells"]
                    if c["group"] == group and c["item"] == item)
        f = cell["engines"][engine]
        if f["status"] != "measured":
            raise ValueError(f"evidence {eid}: {dim_id}/{group}/{item} not measured for {engine}")
        x = f.get("extra") or {}
        entry = {"id": eid, "kind": "cell", "dimension": dim_id, "group": group, "item": item,
                 "engine": engine, "measure": dim["measure"], "label": f["raw"]["label"],
                 "value": f["raw"]["value"], "lo": f["raw"]["lo"], "hi": f["raw"]["hi"],
                 "n": f["n"], "floor": f["floor"]["value"], "floor_label": f["floor"]["label"],
                 "excess": f["excess"], "detected": f["detected"],
                 "has_example": bool(cell["example"])}
        if "direction_toward_more_female_pct" in x:
            entry["direction"] = {"toward": x["more_female_label"].replace("_", " "),
                                  "pct": x["direction_toward_more_female_pct"]}
        out.append(entry)
    return out


def _one_laya(rows: List[dict]) -> List[dict]:
    """Laya is one model on the site. For each (variant, cut) take the MLX build's row where it has
    one and the original build's row otherwise, and say which build gave it."""
    order = {"laya-mlx": 0, "laya": 1}
    chosen: Dict[tuple, dict] = {}
    for r in rows:
        if r["engine"] not in order:
            chosen[(r["engine"], r["variant"], r["cut"])] = {**r, "build": r["engine"]}
            continue
        key = ("laya", r["variant"], r["cut"])
        if key not in chosen or order[r["engine"]] < order[chosen[key]["build"]]:
            chosen[key] = {**r, "engine": "laya", "build": r["engine"]}
    return list(chosen.values())


def _shortlist(root: Path) -> dict:
    pairs = []
    for task in SHORTLIST_TASKS:
        study = f"studies/{task}-shortlist.jsonl"
        raw = [json.loads(line) for line in
               (root / study).read_text(encoding="utf-8").splitlines() if line]
        pairs.append({"task": task, "study": study, "rows": _one_laya(raw)})
    return {"line": FOUR_FIFTHS, "pairs": pairs,
            "prereg_section": "The shortlist, in our study notes",
            "scenario": "Picture an employer with two thousand applications. It asks the model "
                        "one question about each person, ranks them by how likely the answer is "
                        "the senior job, and passes the top of the list to a recruiter. The "
                        "biographies and the question are real. The employer is invented. This "
                        "is one step of what a ranking tool does, not a whole ranking tool.",
            "twin_note": "This second table asks the model about each biography twice, once as "
                         "written and once with the pronouns swapped, and averages the two "
                         "answers. An average is not read as a man or as a woman, so the columns "
                         "about that are not shown."}


def _shortlist_evidence(shortlist: dict) -> List[dict]:
    rows = {(b["task"], r["engine"], r["variant"], r["cut"]): r
            for b in shortlist["pairs"] for r in b["rows"]}
    out = []
    for eid, task, engine, variant, cut in _SHORTLIST_EVIDENCE:
        if (task, engine, variant, cut) not in rows:
            raise ValueError(f"evidence {eid}: no shortlist row")
        out.append({"id": eid, "kind": "shortlist", "task": task, "engine": engine,
                    "variant": variant, "cut": cut})
    return out


def _prereg_evidence(prereg) -> List[dict]:
    out = []
    for eid, heading, first in _PREREG_EVIDENCE:
        row = prereg._row(heading, first, None)
        out.append({"id": eid, "kind": "prereg", "plain": _PREREG_PLAIN[eid],
                    "section": row["section"],
                    "measurement": row["measurement"] or first, "prediction": row["prediction"],
                    "observed": row["observed"], "verdict": row["verdict"],
                    "source": row["source"], "article": "can-you-fix-it"})
    return out


def _floor_evidence(floors: List[dict]) -> List[dict]:
    out = []
    for eid, engine, task in _FLOOR_EVIDENCE:
        row = next(r for r in floors if r["engine"] == engine and r["task"] == task)
        out.append({"id": eid, "kind": "floor", "engine": engine, "task": task,
                    "task_label": row["task_label"], "value": row["flip_pct"], "n": row["n"],
                    "record": row["record"]})
    return out


def build_compliance(root: Path, dimensions: List[dict], floors: List[dict], prereg) -> dict:
    shortlist = _shortlist(root)
    evidence = (_cell_evidence(dimensions) + _shortlist_evidence(shortlist)
                + _prereg_evidence(prereg) + _floor_evidence(floors))
    return {"notice": NOTICE, "citations": CITATIONS, "unmeasured": UNMEASURED,
            "practices": PRACTICES, "mapping": MAPPING, "evidence": evidence,
            "shortlist": shortlist, "inversion": INVERSION, "recipes": RECIPES,
            "insights": INSIGHTS, "checklist": CHECKLIST, "articles": ARTICLES}
