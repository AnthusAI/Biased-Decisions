# Dataset survey: regulated-decision tasks

Compiled 2026-09-23 from primary sources (dataset pages, licence files, papers). Every claim below
carries a link; where a licence or access term could not be confirmed from a primary source, it is
marked "not confirmed" rather than assumed.

## The coverage problem

Every task in this project today draws on one dataset, Bias in Bios: real professional bios,
recast as occupation-pair questions (surgeon vs physician, nurse vs physician, teacher vs
professor, paralegal vs attorney, and three more added since) plus batch-2 screening questions
(greedy, violent, honest, and so on) asked about the same bios, plus a regulated-screening batch
(shortlist, lease, credit, safety, appointment) that reuses the same bio pool again. Gender has
seven tasks built this way. Race, age, disability, religion, nationality, veteran status, and
sexuality/gender identity each have one or two, and all of them are the same dataset asked the
same shape of question with a different inserted clause.

That concentration is a real limitation for a benchmark that claims to measure "decision bias"
rather than "bias in one occupation-classification task." Two gaps follow from it:

1. **Depth.** A dimension with one task and one question type has no way to show whether a finding
   generalizes past that one question. The regulated-screening batch (docs/regulated-decisions-preregistration.md) 
   is a first step — it keeps the bio corpus but changes the question — but every version of the
   text is still a bio.
2. **Breadth.** Regulators do not write rules about occupation classification. ECOA, the Fair
   Housing Act, Title VII, USERRA, and the other regimes this project already cites govern named
   decisions — credit approval, lease approval, hiring, claims, triage, benefits eligibility — and
   the harness has no task built from the kind of text or question those decisions actually use:
   a loan application, a tenancy application, a claim narrative, a clinical note.

This document surveys datasets that could close both gaps, prioritizing tasks that map onto a
named regulatory regime, because bias on a regulated decision is a compliance question a reader
can act on, not just an interesting number.

### Coverage matrix: dimensions x task types

"Today" is a task the harness already runs. "Proposed" is unchecked; see the shortlist below for
which proposals are recommended first.

| Dimension | Today | Proposed (this survey) |
|---|---|---|
| Gender | 7 Bias-in-Bios occupation tasks, batch-2 stereotype questions, regulated-screening batch | discrim-eval decision scenarios (loan, credit line, visa, bail, etc.); Q-Pain pain-management vignettes; German Credit templated applications |
| Race | 1-2 (batch-2, regulated-screening) | discrim-eval; Q-Pain; Jigsaw/Civil Comments identity terms (content-moderation domain); CrowS-Pairs / BBQ as an external cross-check, not a new task |
| Age | 1-2 | discrim-eval (native 9-level age variable); Q-Pain; German Credit (native age field) |
| Disability | 1-2 | discrim-eval (not natively covered — would need clause insertion); BBQ disability-status category as cross-check |
| Religion | 1-2 (batch-2) | BBQ religion category as cross-check; clause-insertion on CFPB complaint narratives (credit/lending domain) |
| Nationality / immigration | 1-2 (regulated-screening) | German Credit "foreign worker" native field; CFPB narratives; discrim-eval (not native) |
| Veteran status | 1-2 (dedicated preregistration) | CFPB "Servicemember" tag narratives (native, no clause needed); USERRA-mapped hiring scenario in discrim-eval-style template |
| Sexuality / gender identity | 1-2 | HUD same-sex/transgender paired-testing summary data (native, but see access risk below); discrim-eval (not native) |

## Recommended datasets

### 1. Anthropic discrim-eval

**What it is.** 9,450 (explicit) + a matched implicit set of templated prompts spanning 70
decision scenarios ("approve this loan," "grant this visa," "grant bail," "issue a press pass,"
and similar), each filled with age (20-100, nine levels), gender (male/female/non-binary), and
race (white, Black, Asian, Hispanic, Native American) in the explicit set, or an implied version
via name in the implicit set. Hugging Face: https://huggingface.co/datasets/Anthropic/discrim-eval .
Paper: Tamkin et al., "Evaluating and Mitigating Discrimination in Language Model Decisions,"
https://arxiv.org/abs/2312.03689 .

**Real or templated.** Fully templated — a fixed scenario sentence with demographic slots filled
in, not real text. This is the dataset's main limitation for this project (see risks).

**Task and question.** Each scenario already ends "Please answer the above question with either
'yes' or 'no'," where yes is defined to be the outcome favorable to the person (grant the loan,
grant bail, etc.) — a direct fit for this project's `noul` question type with no rewriting needed.
Example scenario categories: loan approval, credit line increase, insurance approval, visa
approval, apartment lease approval, parole/bail, job offer — several of these duplicate task types
this survey recommends building from real text (credit, lease), so discrim-eval is best used as a
fast, cheap, templated companion arm alongside a real-text version of the same decision, not a
replacement for one.

**Dimensions and cue insertion.** Native slot-fill for age, gender, race — no clause insertion or
name-swap needed, which also means no floor-edit design is needed in the way this project uses
floors for real text; discrim-eval's own "explicit vs implicit" split already functions as its
built-in control comparison. Disability, religion, nationality, and veteran status are not native
variables and would require extending the template set, which is out of scope for a "use as-is"
recommendation.

**Regulation mapped.** ECOA/Reg B (loan, credit-line scenarios), Fair Housing Act (lease
scenarios), and general anti-discrimination principles for the rest; the scenarios were not written
against specific US statutes, so the regulation mapping is this project's addition, not the
dataset's.

**Licence and redistribution.** CC-BY-4.0, confirmed from the Hugging Face dataset card
(https://huggingface.co/datasets/Anthropic/discrim-eval , licence field `cc-by-4.0`). CC-BY permits
redistribution of the data itself and of derived text and model outputs, with attribution.

**Access.** Open download from Hugging Face, no registration or DUA.

**Risks.** Fully synthetic template text is exactly the "synthetic-template artificiality" this
project has tried to avoid by using real bios; a reviewer could discount a discrim-eval finding as
"the model pattern-matched a stereotyped prompt template," a criticism real-text tasks are built to
resist. Best framed as a fast, free cross-check run alongside a real-text task on the same decision
type, not a standalone task.

### 2. CFPB Consumer Complaint Database narratives

**What it is.** Consumer-submitted narrative text describing a complaint against a financial
company, published only where the consumer opted in, with the Bureau's stated practice of scrubbing
directly identifying information before publication. Landing page:
https://www.consumerfinance.gov/data-research/consumer-complaints/ . Terms of publication:
https://www.consumerfinance.gov/complaint/data-use/ . Government dataset, catalogued at
https://catalog.data.gov/dataset/consumer-complaint-database . Hundreds of thousands of narratives
are available; a 2015 Bureau announcement cited over 7,700 narratives as an early milestone
(https://www.consumerfinance.gov/about-us/newsroom/cfpb-publishes-over-7700-consumer-complaint-narratives-about-financial-companies/),
and the live database has grown far past that since.

**Real or templated.** Real text, written by consumers, already scrubbed of direct identifiers by
the Bureau before publication.

**Task and question.** The natural fit is a claims/dispute-handling decision: "Should this
complaint be escalated for expedited review?" or "Is this complaint likely to result in monetary
relief to the consumer?" (`noul`), or a choice between complaint dispositions. This is the one
dataset in this survey whose native text already carries two of the axes this project needs:
narratives are tagged `Servicemember` and `Older American` by the Bureau's own intake process
(confirmed on the terms-of-use page), so veteran status and age can be measured as a **native
attribute contrast** — comparing outcomes on Servicemember-tagged versus untagged narratives of
similar content — rather than by clause insertion, which removes one whole class of risk (an
inserted clause reading as artificial).

**Dimensions and cue insertion.** Veteran status and age: native tag, no insertion. Race, gender,
religion, disability, nationality: not tagged, would need clause insertion (a name swap or an
inserted descriptive clause) on top of the real narrative text, with a same-shape floor clause
matching this project's existing convention.

**Regulation mapped.** UDAAP (unfair, deceptive, or abusive acts and practices) for complaint
handling generally; Reg E (electronic fund transfers) and Reg Z (truth in lending) for the
product-specific subset of complaints; ECOA/Reg B where the complaint concerns a credit decision.

**Licence and terms.** U.S. government work; CFPB's data-use page states complaints are published
"without information that directly identifies you," and the database is distributed as open
government data via data.gov. No explicit CC licence statement was found on the CFPB pages
themselves; U.S. federal government works are not subject to copyright domestically (17 U.S.C.
§105), which is the basis for treating it as redistributable, but this project should not assert a
specific CC licence for it without a firmer citation — flagged as "not confirmed" pending a direct
citation to the CFPB's own licence language, if one exists.

**Access.** Open, no registration: web UI, CSV bulk download, and a public REST API with CSV export
that does not require a key.

**Risks.** Scrubbing is the Bureau's own automated/manual process, not this project's; residual PII
in narrative free text is possible despite the stated scrubbing standard, and this project would
need its own PII check before publishing edited items or cached model outputs built from these
narratives. Narrative content already names financial products and sometimes company names, which
is a different disclosure profile than a bio.

### 3. HMDA (Home Mortgage Disclosure Act) loan-level data

**What it is.** Loan-level mortgage application and origination data reported by financial
institutions, published by the FFIEC/CFPB. Landing page: https://ffiec.cfpb.gov/data-publication
. Fields include applicant race, ethnicity, sex, age, income, loan outcome (originated, denied,
etc.), and denial reason — structured fields, not free text.

**Real or templated.** Real records, but structured/tabular, not narrative text — using it here
would mean synthesizing an application narrative from the structured fields (e.g., "A 34-year-old
applicant requesting a $310,000 conventional loan..."), which converts a real dataset into a
templated one and reintroduces the artificiality risk discrim-eval already carries. Recommended
only as a source of realistic, regulator-published *distributions* (income, loan amount, denial
reason mixes by group) to make a templated credit task's parameters non-arbitrary, not as a source
of text to publish directly.

**Task and question.** Would support a "approve this mortgage application" `noul` task if rendered
as narrative.

**Dimensions.** Race, ethnicity, sex, age all native fields.

**Regulation mapped.** ECOA/Reg B and the Fair Housing Act — HMDA is itself a fair-lending
enforcement data source; using it to build a fair-lending task is the most directly on-point
regulatory match in this whole survey.

**Licence.** U.S. government data; no licence restriction found, publicly downloadable in full.
https://ffiec.cfpb.gov/data-publication/modified-lar .

**Access.** Open, no registration, nationwide loan-level files downloadable directly.

**Risks.** Because it is not narrative text, any task built from it is templated by construction;
label leakage is a real concern if denial reason or outcome fields are used to write the narrative,
since the "decision" the model is asked to make could then be recoverable from features the
narrative itself would leak (e.g., stating the exact loan-to-income ratio associated with the
historical denial). Best used as a parameter source, not a text source.

### 4. German Credit (UCI Statlog / South German Credit)

**What it is.** 1,000 loan applicants, 20 attributes (checking-account status, credit history,
purpose, credit amount, employment duration, personal status and sex, age, "foreign worker"
status, and more), labeled good/bad credit risk. UCI page:
https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data ; corrected version:
https://archive.ics.uci.edu/dataset/522/south+german+credit .

**Real or templated.** Real historical records (Germany, 1973-1975 per the South German Credit
documentation), but as structured categorical/numeric fields — not narrative text. Same
templating caveat as HMDA: a task would have to synthesize an application narrative from the
fields.

**Task and question.** "Approve this loan application" `noul`, mirroring the regulated-screening
batch's `credit` question exactly.

**Dimensions and cue insertion.** Age and "foreign worker" (a direct nationality/immigration proxy)
are native fields, usable with minimal templating; "personal status and sex" is native but the
attribute is known to be a documented coding error in the original 1994 release (conflating marital
status and sex into one field) — the South German Credit correction should be used instead of the
original Statlog version for this reason.

**Regulation mapped.** ECOA/Reg B.

**Licence.** CC BY 4.0, confirmed on the UCI dataset page.

**Access.** Open download, no registration.

**Risks.** Small (1,000 rows), decades-old, non-US context (German credit categories do not map
cleanly to US credit report fields); templated-from-tabular artificiality as above; useful mainly
as a second, independently-sourced credit-decision task to compare against a CFPB- or HMDA-derived
one, not as a first choice on its own.

### 5. Q-Pain

**What it is.** 55 real-clinical-context pain-management vignettes (acute, chronic, post-op, and
cancer pain scenarios), each ending in a question about whether and how much opioid analgesia to
prescribe, built by clinicians and validated by two independent internal-medicine physicians for
credibility. PhysioNet: https://physionet.org/content/q-pain/1.0.0/ . Paper: Logé et al., "Q-Pain:
A Question Answering Dataset to Measure Social Bias in Pain Management,"
https://arxiv.org/abs/2108.01764 .

**Real or templated.** Vignettes are written by clinicians to be realistic, then demographically
perturbed (race and gender variants of the same vignette) — a controlled template built from
clinically grounded content, a middle case between fully real text (Bias in Bios) and fully
synthetic templates (discrim-eval).

**Task and question.** "Should this patient be prescribed [drug] at [dose]?" — maps directly onto
this project's `noul` format, and the dataset already ships gender and race variants of the same
55 base vignettes, i.e. a built-in floor/non-floor structure requiring no new floor design.

**Dimensions and cue insertion.** Race and gender are native (the dataset's own perturbation
axes); other dimensions would require this project's own clause insertion on top of the vignette
text.

**Regulation mapped.** ACA Section 1557 (nondiscrimination in health programs and activities) —
directly on point, since Section 1557 explicitly reaches clinical decision-support and triage
tools.

**Licence.** CC BY-SA 4.0 (ShareAlike), confirmed at
https://www.physionet.org/content/q-pain/view-license/1.0.0/ . ShareAlike requires that derivative
datasets (this project's edited items) be released under the same or a compatible licence — a
constraint this project's own publication would need to honor (its edited items and results would
need a CC BY-SA-compatible licence for this task specifically, not necessarily for the whole repo,
but the safest path is to license the derived Q-Pain-based files themselves as CC BY-SA 4.0).

**Access.** Open on PhysioNet; PhysioNet credentialing (a MIMIC-style DUA) applies to some
PhysioNet content but Q-Pain's own license page states CC BY-SA 4.0 with no additional credentialed
access step described on that page — this project should re-confirm at download time whether a free
PhysioNet account (not a DUA) is required, since PhysioNet's platform generally requires an account
for any download regardless of the content's own licence.

**Risks.** Only 55 base vignettes (times perturbations) is small; opioid-prescribing questions are
higher-sensitivity content than an occupation or credit question and would need a clear stimuli
disclaimer, following this project's existing convention (see the regulated-decisions
pre-registration's "stimuli disclaimer" rule).

### 6. Jigsaw Civil Comments (with identity annotations)

**What it is.** Public comments from the Civil Comments platform (2015-2017, roughly 50
English-language news sites), extended by Jigsaw with toxicity and identity-mention annotations
(covering gender, sexual orientation, religion, race/ethnicity, disability, and more) and used to
build the Perspective API. TensorFlow Datasets catalog:
https://www.tensorflow.org/datasets/catalog/civil_comments ; Hugging Face mirror:
https://huggingface.co/datasets/google/civil_comments .

**Real or templated.** Real user-written text (public comments), not templated.

**Task and question.** A genuinely different domain and task type from everything else in this
survey: content moderation. "Should this comment be removed/flagged for [identity attack /
harassment]?" (`noul`). This would diversify task type, not just add another decision-under-a-name
task, and moderation is itself a text classification decision plausibly performed by fast
System-1-style models in production.

**Dimensions and cue insertion.** Identity terms are native to the comment text (a comment already
mentions "Muslim," "gay," "Black," etc., where relevant) rather than inserted by this project,
which is a different and useful design: the cue is what the text is about, not a clause spliced
into unrelated text. This also means the standard floor-edit design (same-shape floor clause) does
not directly apply and would need its own design — likely swapping the identity term for a
same-shape neutral term ("a person") rather than inserting a clause.

**Regulation mapped.** Not a regulated-decision domain in the ECOA/FHA/Title VII sense; better
framed as a distinct task-type diversification (content moderation) alongside the
regulation-mapped tasks, not folded into the regulatory-compliance framing.

**Licence.** CC0, confirmed via the Hugging Face and TensorFlow Datasets pages
(https://huggingface.co/datasets/google/civil_comments , 
https://www.tensorflow.org/datasets/catalog/civil_comments). CC0 is the most permissive licence in
this survey — no attribution or ShareAlike constraint.

**Access.** Open download, no registration (also available via the original Jigsaw Kaggle
competition page).

**Risks.** The identity-attack labels were produced by crowdworkers and are themselves a
contested, imperfect ground truth (this is well documented in Jigsaw's own bias-in-labeling
follow-up work); this project would be using the raw comments and doing its own model-bias
measurement, not relying on Jigsaw's labels as ground truth, which sidesteps most of that risk. The
comments are unmoderated public internet text and will include offensive and disturbing content by
construction — needs the same handling care as batch-2's stereotype questions, arguably more.

### 7. CrowS-Pairs and BBQ (cross-checks, not new tasks)

**What they are.** CrowS-Pairs: 1,508 minimal-pair sentences contrasting a stereotyping and an
anti-stereotyping sentence across nine bias types (https://github.com/nyu-mll/crows-pairs). BBQ:
templated ambiguous/disambiguated question sets across nine social dimensions, with intersectional
race x gender/SES examples (https://github.com/nyu-mll/BBQ). Both are masked-language-model /
multiple-choice benchmarks, not decision-task datasets in this project's sense.

**Real or templated.** Both templated.

**Licence.** CrowS-Pairs: CC BY-SA 4.0, confirmed on Hugging Face
(https://huggingface.co/datasets/nyu-mll/crows_pairs). BBQ: CC-BY-4.0, confirmed via the GitHub
repository's licence badge and LICENSE file
(https://github.com/nyu-mll/BBQ/blob/main/LICENSE) — open clone, no registration form found on the
repository despite a secondary source suggesting one; treat that secondary claim as unconfirmed
and rely on the primary repository, which shows a plain CC-BY-4.0 file.

**Access.** Both open download, no registration.

**Recommendation.** Neither maps to a regulated decision or produces the kind of text this
project's decision tasks need (a person being evaluated for an outcome); both are better used as
external validity cross-checks — comparing this project's own measured bias ranking against BBQ's
or CrowS-Pairs' published model rankings — than as a new task built from them.

## Rejected, and why

- **Kiva loan descriptions** (https://www.kaggle.com/datasets/kiva/data-science-for-good-kiva-crowdfunding).
  Real borrower-written loan descriptions with country, sector, and gender fields, which looked
  promising for a lending task. Rejected for now because the loan descriptions describe
  micro-enterprise borrowers in developing economies applying to a non-profit crowdfunding
  platform, not applicants under US ECOA/Reg B or a comparable regulated regime — it does not map
  to the "directly regulated" priority this survey was asked to lead with, and Kaggle's page did
  not resolve to a fetchable licence statement in this pass (would need re-confirmation before any
  future use; not confirmed either way here).
- **Lending Club borrower descriptions** (https://www.kaggle.com/datasets/wordsforthewise/lending-club).
  Real US peer-to-peer loan applications with a borrower-written `desc` free-text field and a
  `title` field — a strong candidate on paper for an ECOA-mapped credit task with real applicant
  text. Reported by secondary sources as CC0 (public-domain-equivalent), but this project could not
  independently confirm the licence field from Kaggle's own page in this pass (Kaggle pages are
  JavaScript-rendered and did not return licence text to a page fetch). Not rejected outright —
  flagged for a follow-up licence confirmation directly on kaggle.com before use, since the `desc`
  field was reportedly deprecated by Lending Club in 2016 for new loans, which would cap how much
  real free text is actually available in the fuller 2007-2018 file.
- **Djinni recruitment dataset** (https://huggingface.co/datasets/lang-uk/recruitment-dataset-job-descriptions-english).
  150,000 job descriptions and 230,000 anonymized CVs, MIT licence, confirmed. Rejected for this
  round because the CVs are Ukrainian IT-sector job-platform data with anonymization of unstated
  completeness — protected-attribute fields (gender, name, nationality) are either stripped or
  unverified, which cuts against this project's insertion-based design (it needs a real bio to
  insert a clause into, not an already-anonymized one), and the domain (IT hiring outside the US)
  is a weaker fit for Title VII/ADEA/ADA framing than a US-context resume set would be. Worth a
  second look if a US-context, non-anonymized resume corpus with a compatible licence turns up.
- **BBQ / CrowS-Pairs as new tasks** (rather than cross-checks). Rejected as *tasks* — see section 7
  above — because they are multiple-choice bias probes about groups in the abstract, not a
  regulated decision being made about a described person; kept as cross-check benchmarks instead.
- **Zack et al. 2024 (Lancet Digital Health) / NEJM Healer vignettes**
  (https://github.com/elehman16/gpt4_bias). Rejected on licence grounds: the repository ships code
  and outputs but states no licence, and the underlying case vignettes originate from NEJM
  Healer — a proprietary NEJM Group clinical-education product — so redistributing the vignette
  text itself is very likely restricted by NEJM's own copyright even though the analysis code and
  GPT-4 output files sit in an unlicensed public repo. This is exactly the "DUA/copyright forbids
  publishing derived text" case this survey was asked to screen out. Would need a direct licence
  from NEJM Group before reconsidering.
- **HUD paired-testing / same-sex and transgender housing study public-use files**
  (https://www.huduser.gov/portal/datasets/paired-testing-pilot-study-of-housing-discrimination-against-same-sex-couples-and-transgender-individuals-public-use-files.html).
  This is the one dataset in the candidate list that would give sexuality/gender-identity a
  Fair-Housing-Act-mapped, real-world-methodology task. Rejected for now because the public-use
  files are coded outcome data from HUD's own paired-testing protocol (matched tester pairs
  contacting real landlords), not narrative text describing an applicant — there is no applicant
  bio or application text to insert a clause into, and this pass could not confirm from HUD's page
  what format the public-use files are actually in or under what terms they can be redistributed
  once downloaded (the page did not return content to a direct fetch in this pass). Flagged for a
  follow-up read of the actual file layout before ruling it in or out permanently.
- **Bertrand and Mullainathan (2004) resume-audit replication materials**
  (https://www.openicpsr.org/openicpsr/project/116023/version/V1/view). The original resumes (with
  "very African-American-sounding" and "very White-sounding" names) are exactly the kind of
  controlled, real-format resume text this project's employment-dimension tasks need, mapped
  directly to Title VII. Rejected for this round because ICPSR-hosted replication data typically
  carries a click-through data-use agreement rather than an open licence, and this pass could not
  confirm ICPSR's specific redistribution terms for this project; ICPSR DUAs are the paradigm case
  named in this project's own instructions as disqualifying ("a DUA that forbids publishing derived
  outputs rules it out") — needs that DUA read in full before use, not assumed permissive.
- **HMDA and German Credit as direct text sources** (rather than parameter sources). Both are
  accepted above only as *parameter* sources for a synthesized narrative task, and rejected as
  *text* sources in their own right, because both are structured/tabular and using them as text
  would mean writing the applicant narrative ourselves — which is templating, not real text, and
  loses this project's stated preference for editing a real document over guessing at a synthetic
  one.
- **EEOC or court case-summary text.** Considered per the brief but not pursued to a specific
  dataset in this pass: EEOC litigation summaries and court opinions are real, regulation-mapped
  text, but they describe a completed legal outcome (the discrimination finding is often the point
  of the document), which creates severe label leakage for a task that is supposed to ask a model
  to make the decision fresh — the source text would need heavy rewriting to remove the outcome,
  at which point it is no longer "real text" in the sense this project uses the term. Not
  recommended without a specific corpus that separates fact pattern from outcome; none was
  identified with confidence in this pass.

## Ranked shortlist: next five to eight tasks

1. **CFPB complaint narratives, `Servicemember` tag, UDAAP-mapped escalation question.** Real
   text, a fully native attribute contrast (no clause insertion, no floor design needed), open
   government data, and it directly extends veteran status past its current one dedicated
   pre-registration into a second, structurally different task and domain.
2. **CFPB complaint narratives, `Older American` tag, same escalation question.** Same dataset,
   same native-tag design, extends age past batch-2/regulated-screening with a second real-text
   domain at near-zero marginal licensing risk once the escalation task above is built.
3. **Q-Pain, ACA Section 1557-mapped prescribing question, race and gender variants.** Clinically
   grounded vignettes, a built-in floor/non-floor perturbation design already matching this
   project's convention, and the one dataset here that reaches a health-decision domain the
   project has no task in today. CC BY-SA obligation is manageable if scoped to the derived files
   for this task.
4. **Jigsaw Civil Comments, content-moderation `noul` task, native identity-term cue.** The
   strongest task-type diversification in this survey (moderation, not a person-evaluation
   decision), CC0 (cleanest licence of any candidate), and covers gender, religion, race/ethnicity,
   and disability in one dataset without any clause-insertion engineering.
5. **discrim-eval, run as a fast free companion arm on the loan/credit-line and lease scenarios
   specifically** (not the full 70), reported alongside a real-text credit/lease task rather than
   standalone, to see whether a templated and a real-text version of the same ECOA/FHA-mapped
   decision agree. CC-BY-4.0, native age/gender/race, zero engineering cost since the prompts are
   ready to send as-is.
6. **South German Credit, `foreign worker` native field, ECOA-mapped credit question**, as a
   second, independently sourced credit task to compare against a CFPB- or Lending-Club-derived
   one once licence confirmation on the latter lands; useful mainly for triangulation given its
   age and non-US context.
7. **Lending Club `desc`/`title` free text, ECOA-mapped credit question** — highest potential value
   of any candidate here (real US applicant text, a regulated decision, at a large scale) but
   blocked behind confirming Kaggle's CC0 claim directly and checking how much free text survives
   in the years after the field's 2016 deprecation; do the licence check first, then this moves to
   position 1 or 2.
8. **HUD same-sex/transgender paired-testing public-use files, Fair Housing Act-mapped**, contingent
   on a follow-up read of the actual file format; if it turns out to include tester narrative text
   rather than only coded outcomes, this becomes the strongest candidate in the whole survey for
   sexuality/gender identity, since nothing else here reaches that dimension with real,
   regulation-mapped text.

## Licence red flags, summarized

- **BBQ / CrowS-Pairs:** clear CC-BY-4.0 / CC-BY-SA-4.0 from primary sources, contradicting a
  secondary claim (found in search results, not verified against the primary repo) that BBQ
  requires a registration form and prohibits redistribution — that secondary claim should not be
  repeated as fact.
- **Zack et al. / NEJM Healer vignettes:** likely blocked by NEJM's own copyright on the source
  vignettes; the analysis repo's lack of a licence file does not clear the underlying content.
- **Bertrand and Mullainathan replication data (ICPSR):** likely gated by an ICPSR click-through
  DUA; disqualifying if that DUA forbids redistributing derived outputs, which is the project's
  own stated bar — needs the DUA text read before any further work.
- **Kiva and Lending Club (Kaggle):** licence claims in this document for Lending Club (CC0) rest
  on secondary sources, not a directly fetched Kaggle licence field; Kiva's licence was not
  resolved at all in this pass. Both need a direct confirmation on kaggle.com before either is
  used.
- **HMDA and German Credit:** clean on licence (government data; CC BY 4.0), but both are
  structured data, not text — using either as a "real text" task requires synthesizing narrative
  text from fields, which is templating dressed as real text and should be labeled as such if
  used.
- **CFPB Consumer Complaint Database:** treated here as redistributable on the strength of its
  status as U.S. government data and its own public-access design (open API, bulk CSV, no DUA
  encountered), but no explicit CC-licence statement was found on the CFPB's own pages; flagged as
  "not confirmed" rather than asserted with a specific licence name.
