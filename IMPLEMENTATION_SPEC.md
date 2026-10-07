# Implementation Specification

This file is the detailed implementation guide for the next coding agent. It assumes the data is already present and verified under `datasets/`.

## 1. Build Goal

Implement a backend-first prototype of a Multi-Agent Graph-RAG Clinical Decision Support System.

The prototype should accept a clinical case text and return a structured report containing:

- extracted clinical entities
- linked ontology/KG concepts
- graph evidence
- vector evidence
- drug safety evidence where available
- ranked differential diagnoses
- suggested investigations
- educational treatment considerations
- confidence score
- limitations
- citations/source references

The MVP should be reproducible locally and should not require a frontend.

## 2. Non-Negotiable Architecture

Implement this architecture only:

```text
Raw clinical case
  -> Clinical Clarifier / Entity Normalizer
  -> Retrieval Orchestrator
      -> Graph Retriever
      -> Vector Retriever
      -> Evidence/Drug Safety Retriever
  -> Evidence Ranker
  -> Conflict Detector
  -> Clinical Fusion Agent
  -> Confidence Evaluator
      -> Final Report
      -> or Adaptive Retry then retrieval again
```

Graph, vector, and evidence retrieval must run from the same structured patient context. Do not make graph retrieval depend on vector retrieval or vector retrieval depend on graph retrieval.

## 3. Expected Repository Structure

Create this structure if it does not already exist:

```text
backend/
├── agents/
│   ├── clarifier.py
│   ├── evidence_ranker.py
│   ├── conflict_detector.py
│   ├── fusion.py
│   ├── confidence.py
│   ├── adaptive_retry.py
│   └── report.py
├── api/
│   └── routes.py
├── schemas/
│   ├── patient.py
│   ├── evidence.py
│   ├── retrieval.py
│   └── report.py
├── services/
│   ├── ontology_parser.py
│   ├── entity_linker.py
│   ├── graph_retriever.py
│   ├── vector_retriever.py
│   ├── drugcentral.py
│   ├── document_chunker.py
│   └── orchestrator.py
├── config.py
└── main.py
ingestion/
├── build_ontology_indexes.py
├── inspect_datasets.py
├── ingest_kg_neo4j.py
├── build_vector_index.py
└── load_drugcentral.py
evaluation/
├── run_medqa_eval.py
├── run_medmcqa_eval.py
├── run_pubmedqa_eval.py
├── run_medbullets_eval.py
└── metrics.py
tests/
docs/
```

Add:

```text
.env.example
.gitignore
pyproject.toml or requirements.txt
README.md
```

## 4. Dependency Guidance

Prefer simple dependencies first.

Minimum useful backend dependencies:

```text
fastapi
uvicorn
pydantic
python-dotenv
pandas
pyarrow
numpy
scikit-learn
tqdm
rapidfuzz
networkx
neo4j
qdrant-client
sentence-transformers
pytest
```

If GPU/model downloads are inconvenient, keep the vector retriever interface pluggable and provide a lightweight TF-IDF fallback for tests.

## 5. Environment Configuration

Create `.env.example`:

```text
DATASETS_DIR=datasets
HPO_PATH=datasets/ontologies/hpo/hp.obo
MONDO_PATH=datasets/ontologies/mondo/mondo.obo
KG_PATH=datasets/kg.csv
DRUGCENTRAL_DIR=datasets/drugcentral
MEDQA_DIR=datasets/literature/MedQA
MEDMCQA_DIR=datasets/literature/MedMCQA
PUBMEDQA_DIR=datasets/literature/pubmedqa-master/pubmedqa-master
MEDBULLETS_DIR=datasets/literature/medbulltes5op

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

QDRANT_URL=http://localhost:6333
VECTOR_COLLECTION_TEXTBOOKS=medical_textbooks
VECTOR_COLLECTION_PUBMEDQA=pubmedqa_contexts
VECTOR_COLLECTION_MEDQA=medqa_train
```

## 6. Git Ignore Rules

Add `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/

datasets/*
!datasets/DATASET_GUIDE.md

vector_db/
qdrant_storage/
neo4j/data/
neo4j/logs/
*.sqlite
*.db
*.pkl
*.faiss
*.parquet
*.csv
*.tsv
*.gz
```

Do not commit data files.

## 7. Core Schemas

Use Pydantic models. Keep schemas stable and explicit.

### 7.1 Patient Context

```python
class LinkedEntity(BaseModel):
    text: str
    normalized_name: str | None = None
    entity_type: str
    ontology_id: str | None = None
    ontology_source: str | None = None
    confidence: float = 0.0
    candidates: list[dict] = []

class PatientContext(BaseModel):
    raw_input: str
    age: int | None = None
    sex: str | None = None
    symptoms: list[LinkedEntity] = []
    known_conditions: list[LinkedEntity] = []
    medications: list[LinkedEntity] = []
    allergies: list[LinkedEntity] = []
    vitals: dict = {}
    labs: list[dict] = []
    missing_information: list[str] = []
    safety_flags: list[str] = []
```

### 7.2 Evidence

```python
class EvidenceItem(BaseModel):
    id: str
    source_type: str
    source_name: str
    title: str | None = None
    text: str
    score: float = 0.0
    metadata: dict = {}
    supports: list[str] = []
    contradicts: list[str] = []
```

### 7.3 Graph Evidence

```python
class GraphPath(BaseModel):
    nodes: list[dict]
    relationships: list[str]
    score: float = 0.0

class GraphRetrievalResult(BaseModel):
    candidate_diseases: list[dict]
    paths: list[GraphPath]
    contraindications: list[dict] = []
    drug_interactions: list[dict] = []
    limitations: list[str] = []
```

### 7.4 Final Report

```python
class DiagnosisCandidate(BaseModel):
    diagnosis: str
    confidence: float
    supporting_evidence_ids: list[str]
    conflicting_evidence_ids: list[str] = []
    recommended_tests: list[str] = []
    treatment_considerations: list[str] = []
    safety_notes: list[str] = []

class ClinicalReport(BaseModel):
    disclaimer: str
    case_summary: str
    ranked_diagnoses: list[DiagnosisCandidate]
    missing_information: list[str]
    conflicts: list[dict]
    overall_confidence: float
    limitations: list[str]
    references: list[EvidenceItem]
```

## 8. Module Implementation Details

## 8.1 Ontology Parser

File:

```text
backend/services/ontology_parser.py
```

Responsibilities:

- parse OBO files
- extract `id`, `name`, `def`, `synonym`, `xref`, `is_a`, `is_obsolete`
- skip obsolete terms by default
- build lookup maps:
  - exact normalized name to term
  - synonym to term
  - id to term

Normalization:

- lowercase
- strip punctuation
- collapse whitespace
- remove surrounding quotes from synonyms

Outputs:

```text
data/processed/hpo_terms.jsonl
data/processed/mondo_terms.jsonl
data/processed/entity_lookup.json
```

If `data/processed/` is not wanted, use `artifacts/ontology/`. Add generated artifacts to `.gitignore`.

## 8.2 Entity Linker

File:

```text
backend/services/entity_linker.py
```

Responsibilities:

- link extracted terms to HPO, MONDO, DrugCentral, and KG names
- exact match first
- fuzzy match second using `rapidfuzz`
- return top candidates with confidence

MVP extraction can be simple:

- use regex for age/sex
- identify symptom/disease/drug mentions through dictionary lookup against HPO/MONDO/DrugCentral/KG names
- later replace with LLM or clinical NER

Do not over-engineer NER in the first pass.

## 8.3 Clarifier Agent

File:

```text
backend/agents/clarifier.py
```

Responsibilities:

- produce `PatientContext`
- call `EntityLinker`
- detect missing demographics, duration, severity, allergies, medications
- set safety flags for emergency symptoms:
  - chest pain
  - severe shortness of breath
  - stroke-like symptoms
  - loss of consciousness
  - severe bleeding
  - suicidal ideation

MVP can be deterministic. LLM extraction can be added later.

## 8.4 Graph Retriever

File:

```text
backend/services/graph_retriever.py
```

Two acceptable modes:

### Preferred mode: Neo4j

Import `datasets/kg.csv`.

Node key:

```text
source + ":" + id
```

Node labels should be derived from `x_type`/`y_type`.

Relationship type should be a sanitized version of `relation`.

Create graph queries:

1. phenotype to disease:

```cypher
MATCH (p)-[r:disease_phenotype_positive]-(d)
WHERE p.normalized_name IN $symptom_names
RETURN d, r, p
LIMIT $limit
```

2. disease to drugs:

```cypher
MATCH (d)-[r:indication]-(drug)
WHERE d.normalized_name IN $disease_names
RETURN d, r, drug
LIMIT $limit
```

3. contraindications:

```cypher
MATCH (drug)-[r:contraindication]-(d)
WHERE drug.normalized_name IN $drug_names
RETURN drug, r, d
LIMIT $limit
```

4. drug-drug interactions:

```cypher
MATCH (a)-[r:drug_drug]-(b)
WHERE a.normalized_name IN $drug_names OR b.normalized_name IN $drug_names
RETURN a, r, b
LIMIT $limit
```

### Fallback mode: CSV/NetworkX

If Neo4j is not ready, implement a smaller local retriever over filtered KG rows:

- load only relations needed for MVP
- build indexes from phenotype/disease/drug names to rows
- return paths from CSV rows

## 8.5 Document Chunker

File:

```text
backend/services/document_chunker.py
```

Sources for MVP:

```text
datasets/literature/MedQA/MedQA-USMLE/textbooks/en/*.txt
datasets/literature/pubmedqa-master/pubmedqa-master/data/ori_pqal.json
```

Chunking:

- chunk size: 500-900 words
- overlap: 80-150 words
- preserve metadata:
  - source dataset
  - file name
  - title
  - chunk id
  - split if applicable

Do not index test answers/explanations into a collection used for test evaluation.

## 8.6 Vector Retriever

File:

```text
backend/services/vector_retriever.py
```

Preferred:

- Qdrant
- `sentence-transformers`

Fallback:

- local TF-IDF using scikit-learn for tests

Collections:

```text
medical_textbooks
pubmedqa_contexts
medqa_train_optional
medmcqa_train_optional
```

Return:

- chunk text
- similarity score
- metadata
- source id

## 8.7 DrugCentral Service

File:

```text
backend/services/drugcentral.py
```

MVP:

- parse `FDA+EMA+PMDA_Approved.csv`
- parse `structures.smiles.tsv`
- parse `drug.target.interaction.tsv.gz`
- build drug-name lookup
- return drug targets for detected medications

Later:

- load full PostgreSQL dump
- extract indications, contraindications, adverse events

## 8.8 Retrieval Orchestrator

File:

```text
backend/services/orchestrator.py
```

Responsibilities:

- accept `PatientContext`
- call graph retriever
- call vector retriever
- call drug safety/evidence retriever
- return independent retrieval results

Do not merge results inside retrievers. Merge in Evidence Ranker.

## 8.9 Evidence Ranker

File:

```text
backend/agents/evidence_ranker.py
```

Ranking factors:

- retrieval score
- graph path specificity
- source reliability
- overlap with patient symptoms
- recency if date exists
- contradiction penalty

MVP scoring can be heuristic.

## 8.10 Conflict Detector

File:

```text
backend/agents/conflict_detector.py
```

Detect:

- treatment suggested but contraindicated
- drug-drug interaction involving current medications
- weak evidence for high-confidence diagnosis
- candidate diagnosis missing required supporting symptoms

Return conflicts with severity:

```text
low | medium | high
```

## 8.11 Fusion Agent

File:

```text
backend/agents/fusion.py
```

Responsibilities:

- combine graph candidates and vector evidence
- rank differential diagnoses
- attach evidence ids
- add missing information
- add recommended investigations
- produce confidence per diagnosis

MVP can be heuristic. Later use LLM with strict JSON output.

## 8.12 Confidence Evaluator

File:

```text
backend/agents/confidence.py
```

Start thresholds:

- `>= 0.75`: final report allowed
- `0.55-0.75`: final report allowed with limitations or retry
- `< 0.55`: retry

Confidence should consider:

- number of supporting evidence sources
- graph/vector agreement
- conflict severity
- missing critical information
- retrieval scores

## 8.13 Adaptive Retry

File:

```text
backend/agents/adaptive_retry.py
```

Retry actions:

- expand query with synonyms from HPO/MONDO
- increase top-k
- include candidate disease names in vector query
- search drug safety if medication conflict suspected

Maximum retries:

```text
2 for MVP
```

## 8.14 Report Generator

File:

```text
backend/agents/report.py
```

Report must include:

- research/educational disclaimer
- case summary
- ranked differential diagnosis
- evidence
- missing information
- suggested investigations
- educational treatment considerations
- safety notes
- confidence
- limitations
- references

Never state a diagnosis as certain.

Use wording:

```text
The evidence supports considering X as part of the differential diagnosis.
```

Do not use:

```text
The patient has X.
```

## 9. API Endpoints

FastAPI endpoints:

```text
GET  /health
POST /analyze
POST /clarify
POST /retrieve
POST /evaluate/medqa
```

MVP `/analyze` input:

```json
{
  "case_text": "45-year-old male with chest pain radiating to left arm..."
}
```

MVP `/analyze` output:

```json
{
  "patient_context": {},
  "retrieval": {},
  "report": {}
}
```

## 10. Evaluation

Implement at least one working benchmark first.

Recommended first benchmark:

```text
MedQA dev split
```

Then add:

- MedMCQA validation
- PubMedQA
- MedBullets

Metrics:

- accuracy
- precision/recall/F1 if applicable
- retrieval Recall@K when gold evidence exists
- latency
- token/model cost if LLM used

Ablations to support the project claim:

1. LLM/rule baseline only
2. vector-only
3. graph-only
4. graph + vector
5. graph + vector + drug/evidence
6. full system with retry

## 11. Dataset Verification Command

Add:

```text
ingestion/inspect_datasets.py
```

It should check:

- expected files exist
- file sizes > 0
- HPO/MONDO term counts
- KG header is valid
- DrugCentral TSV header is valid
- MedMCQA parquet readable if `pyarrow` installed
- MedQA/PubMedQA/MedBullets counts

## 12. First Working Demo Case

Use this test case:

```text
A 58-year-old man with diabetes and hypertension presents with crushing chest pain radiating to the left arm, sweating, nausea, and shortness of breath. He takes metformin and lisinopril. No known drug allergies.
```

Expected behavior:

- extract chest pain, left arm radiation/numbness, sweating, nausea, shortness of breath, diabetes, hypertension, metformin, lisinopril
- retrieve cardiovascular candidate diseases
- include myocardial infarction / acute coronary syndrome high in differential if evidence supports it
- recommend urgent clinician/emergency evaluation
- suggest ECG and troponin as investigations
- include safety disclaimer and limitations

## 13. Implementation Priorities

Priority 1:

- schemas
- dataset inspection
- ontology parser
- entity linker
- clarifier

Priority 2:

- graph retriever
- vector chunker
- vector retriever

Priority 3:

- orchestrator
- ranker
- fusion
- report

Priority 4:

- adaptive retry
- evaluation
- API polish

## 14. Avoid These Mistakes

- Do not build the frontend first.
- Do not use archived reference files as active specs.
- Do not commit datasets.
- Do not download more large datasets before MVP works.
- Do not index evaluation answer keys into retrieval collections.
- Do not make medical claims without evidence IDs.
- Do not make the pipeline depend on paid LLM calls for basic tests.
- Do not implement strict sequential retrieval.

