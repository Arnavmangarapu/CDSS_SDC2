# 11 — Demo and explanation guide

[Documentation index](README.md) · [Interview questions](10_INTERVIEW_AND_REVIEW_QUESTIONS.md)

## 1. Thirty-second explanation

“This is a clinical decision support research prototype. A user enters a synthetic patient case. The system extracts facts, retrieves graph associations and relevant text, and asks a language model for structured possibilities. A separate gate checks exact source identities and a few applicability rules. The report shows candidate diagnoses, conditional options, missing checks, and source passages. General claims stay unverified; two narrow amlodipine label rules can create supported warnings.”

## 2. Two-minute explanation

Start with the problem: fluent generated medical text can look reliable even when the source is absent, irrelevant, or inappropriate for the patient.

Explain the input: the system receives one case as text. It extracts age, symptoms, conditions, current/stopped medicines, allergy state, BP, and selected missing facts. Medicines and allergies preserve original source phrases.

Explain retrieval: Neo4j supplies explicit biomedical associations. Qdrant supplies textbook and pinned guideline/label passages. A local encoder and optional cross-encoder rank text. General evidence suggests candidates; exact source passages have a separate citation identity.

Explain generation and checking: the model returns structured proposals. Claim normalization rejects invented or inappropriate citation IDs. The verifier checks those sources against local checksum-verified snapshots. General meaning and patient applicability still require review, so those claims remain unverified. Two explicit label rules handle the implemented amlodipine warning conditions.

Finish with evidence and scope: there are component tests and multiple dated development evaluations. The source corpus and medication rules are narrow, the QA pilot is incomplete, and independent clinical validation remains open.

## 3. Five-minute presentation outline

| Time | Topic | What to show |
| --- | --- | --- |
| 0:00–0:45 | Problem and scope | Why citation identity differs from claim correctness |
| 0:45–1:30 | Architecture | Diagram from guide 02 |
| 1:30–2:30 | Input and extraction | Synthetic case, explicit history, missing facts |
| 2:30–3:30 | Claims and citations | One unverified proposal and expandable source passage |
| 3:30–4:15 | Narrow safety behavior | Label rule requirements and unknown-history case |
| 4:15–5:00 | Evaluation and next steps | Dated results, deterministic baseline, independent review gap |

## 4. Prepare a demonstration

Before presenting, verify the API, Neo4j schema, Qdrant collections, local models, pinned snapshots, and provider access using [guide 06](06_SETUP_CONFIGURATION_AND_OPERATIONS.md). An API health response alone is insufficient.

Use only synthetic inputs. Record the code revision, source manifest version, active collection names, and provider used if the demonstration is captured. Do not claim live model output will exactly match a saved screenshot or run.

## 5. Case A: missing facts stay visible

```text
A 57-year-old woman with confirmed hypertension currently takes amlodipine.
She has no known drug allergies.
```

Show the extracted age/sex and current medicine. Show that “no known allergies” is an explicit reported state, not a safety clearance. Point to the missing BP and other unresolved checks. If treatment claims appear, show their conditions and unverified state.

Do not require a fixed diagnosis ordering or a particular proposal text as the success criterion. The useful behavior to inspect is how the system represents stated and absent facts.

## 6. Case B: explicit allergy with relevant exposure

```text
A 57-year-old woman has confirmed hypertension. She currently takes amlodipine.
She is allergic to amlodipine. Clinic BP 152/94.
```

Check that the allergy is extracted as explicit. If the exact contraindication passage was retrieved and trusted, inspect the supported warning and any conflicting amlodipine treatment proposal. Open its citation and explain the document version and section.

If the required source passage is absent, explain the unverified source gap instead of claiming the rule failed medically or that the medicine is safe. The end-to-end path depends on both fact extraction and relevant source retrieval.

## 7. Case C: current interacting medicine

```text
A 57-year-old woman with confirmed hypertension currently takes amlodipine and
simvastatin. She has no known drug allergies. Clinic BP 152/94.
```

Inspect current-medication statements, list status, retrieved interaction section, and the dose/interaction-review warning. Explain that the code detects a narrow source-backed review condition; it does not know the actual dose unless provided or issue a prescription.

## 8. Case D: unknown is different from absent

```text
A 57-year-old woman with confirmed hypertension currently takes amlodipine.
No allergy history was recorded. Clinic BP 152/94.
```

The key behavior is `allergy_status=unknown`, not an invented substance allergy and not `no_known_allergies`. Show the uncertainty finding if the amlodipine path runs. This phrase family exposed an earlier bug and now has regression tests.

## 9. Case E: source-scope boundary

```text
A 40-year-old woman has fever and cough. Clinic BP 110/70.
No current medications. No known drug allergies.
```

A normal BP in an otherwise unrelated case should not automatically trigger the narrow hypertension/amlodipine authoritative corpus. Any broader differential is still an unverified model proposal. This demonstrates the difference between candidate generation and source coverage.

## 10. A code walkthrough for reviewers

Open the following in order:

1. [routes.py](../backend/api/routes.py): show the complete processing sequence.
2. [patient.py](../backend/schemas/patient.py): show explicit status and missingness fields.
3. [patient_fact_extractor.py](../backend/services/patient_fact_extractor.py): show original-text anchoring.
4. [graph_retriever.py](../backend/services/graph_retriever.py) and [vector_retriever.py](../backend/services/vector_retriever.py): explain distinct retrieval roles.
5. [claim_synthesis.py](../backend/services/claim_synthesis.py): show required treatment conditions and citation normalization.
6. [claim_verifier.py](../backend/services/claim_verifier.py): show exact source comparison and general abstention.
7. [conflict_detector.py](../backend/agents/conflict_detector.py): show the two implemented label rules.
8. [report.py](../backend/schemas/report.py): show reference validation.
9. [app.js](../frontend/app.js): show claim status, source rendering, and missing-history text.
10. evaluation/INDEPENDENT_EVALUATION_PROTOCOL.md (`evaluation/INDEPENDENT_EVALUATION_PROTOCOL.md`, local checkpoint): explain how stronger evidence would be collected.

## 11. How to present results accurately

Give the date, task, numerator, denominator, and limit together. For example:

“On the reused 108-case synthetic safety comparison from 31 October, production extraction plus rules matched 106/108 exact warning/support cases. The deterministic baseline matched 108/108. These were fixed-proposal, supplied-label development cases, not independent clinical validation.”

For diagnosis results, distinguish the original 13 October MedQA run from the repaired 27 October run. For the three-dataset QA experiment, say “255/300 planned attempts recorded,” not “completed benchmark.” See [guide 08](08_TESTING_EVALUATION_AND_RESULTS.md).

## 12. Personal contribution and discussion

State only the parts you actually implemented, reviewed, or measured. The repository does not establish individual authorship or personal responsibilities. Prepare to explain a concrete design choice, a bug and its regression test, a tradeoff, and an improvement you would evaluate next.

Useful examples include global graph node identity, typed ontology linking, unknown-allergy handling, source object equality beyond IDs, separate evidence-role lists, and precision/recall tradeoffs in rule filtering. Use the question bank to practice both the happy path and failure cases.
