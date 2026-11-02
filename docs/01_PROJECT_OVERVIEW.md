# 01 — Project overview

[Documentation index](README.md) · [Next: architecture](02_ARCHITECTURE_AND_CODE_MAP.md)

## 1. What is this project?

This project is a browser-based clinical decision support research prototype. A user enters a short patient case in ordinary English. The system extracts information, searches local biomedical data, asks a language model to propose a differential and conditional options, checks source identities, applies a small set of medication rules, and returns a structured report for review.

A **differential** is a ranked list of possible explanations for the case. A **conditional treatment option** is something to discuss if a condition and its prerequisites are confirmed. Neither is a diagnosis or a prescription issued by this software.

The main research idea is an **evidence-linked claim workflow**: each proposed statement is represented separately, with its conditions, unresolved checks, candidate citations, and verification state. This makes uncertainty visible instead of hiding it inside a fluent paragraph.

## 2. What problem does it address?

A language model can generate convincing text without a reliable source. A retrieved document can also be real but irrelevant to the patient. Biomedical relationships can suggest possibilities without establishing clinical truth.

The project addresses these problems by keeping several things separate:

1. What the patient statement explicitly says.
2. What the graph or textbook retrieval suggests.
3. Which exact guideline or label passage is linked.
4. What the model proposes.
5. What the verifier and implemented rules can establish.
6. What still needs clinician review.

For example, finding a hypertension treatment guideline does not show that a particular patient has hypertension. Finding an amlodipine label does not show that amlodipine is appropriate for that patient. The report should preserve those distinctions.

## 3. Intended users and actual scope

The interface is designed for clinician or researcher review. The current implementation is suitable for studying retrieval, traceability, extraction failures, and narrow rule behavior with synthetic examples.

The pinned authoritative corpus contains two document entries:

| Document | Declared scope | Jurisdiction |
| --- | --- | --- |
| NICE NG136 recommendations | Adult hypertension diagnosis and management; selected sections | England |
| One DailyMed amlodipine SPL label | Selected indications, contraindications, warnings, and interaction sections | United States |

The graph and textbooks are broader than this authoritative corpus. Therefore, the model can propose possibilities outside hypertension, while the source gate still has narrow coverage. Broad candidate generation does not mean broad clinical verification.

Independent clinician review of the pinned source selection remains pending in the manifest. Source identities, dates, and versions here are repository metadata, not a claim that the live publisher sites have been rechecked for this documentation.

## 4. What the user receives

The API returns three top-level objects:

- `patient_context`: extracted facts, normalized entities, source phrases, unknown states, and missing information.
- `retrieval`: counts of graph candidates, textbook items, DrugCentral matches, and authoritative passages.
- `report`: the differential, claims, safety findings, sources, missing checks, and limitations.

The UI groups the report into patient context, missing facts, differential candidates, investigations, treatment proposals, medication safety, and limitations. It displays claim states and exact source passages. It does not display the legacy confidence values as clinical probabilities.

## 5. Technology stack

| Technology | Why it is present |
| --- | --- |
| Python | Main implementation language for backend, ingestion, and evaluation |
| FastAPI and Uvicorn | HTTP API and application server |
| Pydantic and pydantic-settings | Typed objects, validation rules, and configuration |
| HTML, CSS, JavaScript | Static browser interface; no React or frontend build system |
| Neo4j and Cypher | Store and query selected biomedical relationships |
| Qdrant | Store and search passage embeddings |
| Sentence Transformers | Encode queries and passages as numeric vectors |
| CrossEncoder | Read query–passage pairs and rerank retrieved candidates |
| RapidFuzz | Match extracted phrases to normalized ontology names |
| Pandas | Read graph CSV batches and DrugCentral tabular data |
| Requests | Make model-provider, publisher-download, and optional search calls |
| Beautiful Soup and XML parsing | Extract structured sections from pinned HTML and SPL XML |
| pytest | Component and regression tests |
| Docker helper scripts | Start local development Neo4j and Qdrant containers |

The dependencies in [requirements.txt](../requirements.txt) are not version-locked. A reproduced environment therefore needs a separately recorded dependency inventory. There is no project-specific model training loop in the runtime path.

## 6. Why “Graph-RAG”?

**RAG** means retrieval-augmented generation: first retrieve useful information, then give it to the model when asking for an answer.

The graph side searches explicit phenotype–disease and drug–disease relationships. The text side searches textbook passages and, separately, pinned source passages. The fusion model sees selected candidate signals and permitted source IDs before generating proposals.

This is a combination of graph and text retrieval. It is not a trained graph neural network. The graph query is bounded and uses stored one-edge associations; it does not perform general multi-hop clinical reasoning.

## 7. Why “multi-agent”?

The backend divides work into named components such as `ClinicalClarifier`, `EvidenceRanker`, `ClinicalFusion`, and `ReportGenerator`. In this repository, these are Python classes called by the analysis route.

They are not independently running workers that debate or learn from one another. The production route and retrieval orchestrator run their steps synchronously and sequentially. The clarifier and fusion use an LLM; several other “agents” are deterministic Python logic. Explain the term in this concrete way during a review.

## 8. Important vocabulary

| Term | Simple meaning in this project |
| --- | --- |
| Ontology | A vocabulary that assigns stable identifiers to concepts and their names |
| HPO | Human Phenotype Ontology, used for symptom/phenotype linking |
| MONDO | A disease ontology, used for condition linking |
| PrimeKG | The biomedical graph source from which selected relations are imported |
| Embedding | A numeric representation used to find semantically similar text |
| Dense retrieval | Search by comparing query and passage vectors |
| Reranking | Reordering retrieved passages after examining query–passage pairs |
| Provenance | The recorded identity and origin of a source |
| SHA-256 | A checksum used to detect changes in bytes or serialized identity |
| Pinned source | A specific source version whose exact local bytes are checked |
| Claim | One proposed diagnosis, investigation, treatment, or warning statement |
| Entailment | Whether a passage actually supports the meaning of a claim |
| Applicability | Whether that support fits the particular patient and setting |
| Abstention | Leaving a decision unverified when support is insufficient |
| Ablation | Comparing versions that remove or change one part of a system |
| Holdout | Evaluation material kept separate from development decisions |
| Adjudication | Independent reviewers assessing labels and resolving disagreements |
| Calibration | Whether a reported probability agrees with observed outcome frequency |

## 9. What is implemented and what remains open?

Implemented features include a working API structure, static UI, typed report contracts, deterministic safety-fact extraction, ontology linking, graph and vector retrieval, model fallback, claim normalization, source identity checks, two narrow safety rules, bounded retries, and evaluation tooling.

Open work includes independent clinical evaluation, general semantic claim verification, a larger reviewed source corpus, multi-drug safety coverage, production authentication and operations, and a fully locked reproducible environment. The separate three-dataset QA pilot remains incomplete in its saved results.

## 10. A useful way to explain the contribution

“The project makes clinical proposals easier to inspect. It keeps patient facts, candidate evidence, exact citations, and verification status separate. It checks source identity and a small number of explicit medication rules, while leaving general clinical claims for independent review.”

This explanation matches the implementation more closely than saying the project diagnoses diseases, guarantees safe prescriptions, or proves that Graph-RAG is more accurate than an LLM.
