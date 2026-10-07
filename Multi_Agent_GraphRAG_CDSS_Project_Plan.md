# Multi-Agent Graph-RAG Clinical Decision Support System

This is the active project plan. It intentionally contains only the chosen architecture and implementation direction. Historical notes and earlier conflicting drafts are archived under `archive/reference/` and should not be used as implementation instructions.

## 1. Objective

Build a research-oriented **Multi-Agent Graph-RAG Clinical Decision Support System (CDSS)** that combines:

- clinical text clarification and entity normalization
- biomedical knowledge graph retrieval
- biomedical vector retrieval
- trusted evidence retrieval
- evidence ranking
- conflict detection
- clinical fusion and reasoning
- confidence scoring
- adaptive retry for low-confidence cases
- final report generation with citations and limitations

The system is for education and research. It must not claim to diagnose patients or replace clinician judgment.

## 2. Final Architecture

Use a **fan-out retrieval architecture**. The clarifier produces one structured patient context. The retrieval orchestrator sends that same context independently to graph, vector, and evidence retrievers. Their outputs are fused only after retrieval.

```text
Patient Query / Clinical Case
        │
        ▼
Clinical Text Clarifier + Entity Normalizer
        │
        ▼
Structured Patient Context + Linked Medical Entities
        │
        ▼
Retrieval Orchestrator
        │
        ├──────────────► Graph Retriever
        │                  Neo4j over biomedical KG
        │
        ├──────────────► Vector Retriever
        │                  Qdrant/FAISS over textbooks and QA contexts
        │
        └──────────────► Evidence Retriever
                           PubMed/openFDA/guideline cache
        │
        ▼
Evidence Ranking Agent
        │
        ▼
Conflict Detection Agent
        │
        ▼
Clinical Fusion + Reasoning Agent
        │
        ▼
Diagnosis and Recommendation Agent
        │
        ▼
Confidence Evaluation Agent
        │
        ├── confidence sufficient ──► Final Clinical Report
        │
        └── confidence low ─────────► Adaptive Query Optimizer
                                      │
                                      ▼
                                   Retry Retrieval
```

## 3. Design Rules

- There is one active architecture: fan-out retrieval followed by fusion.
- Do not implement a strict linear chain where graph retrieval depends on vector retrieval or vice versa.
- Every module must use typed schemas, preferably Pydantic.
- Every final medical claim must be traceable to either:
  - a graph path,
  - a retrieved document chunk,
  - a guideline/source citation,
  - or a clearly marked limitation.
- The system must preserve the original patient context throughout the full pipeline.
- Live web search is not required for MVP. Use local data, PubMed API/cache, and openFDA API/cache first.
- Adaptive retry must have a hard limit. Start with maximum 2 retries.
- Do not index test-set answers into the vector database used for evaluating those same test sets.
- Do not commit large datasets to GitHub.

## 4. Active Dataset Sources

See `datasets/DATASET_GUIDE.md` for detailed dataset descriptions.

Active local datasets:

```text
datasets/kg.csv
datasets/ontologies/hpo/hp.obo
datasets/ontologies/mondo/mondo.obo
datasets/drugcentral/
datasets/literature/MedQA/
datasets/literature/MedMCQA/
datasets/literature/pubmedqa-master/
datasets/literature/medbulltes5op/
```

Data usage:

| Component | Data source |
|---|---|
| Graph Retriever | `datasets/kg.csv` imported into Neo4j |
| Entity Normalizer | HPO, MONDO, DrugCentral names, KG node names |
| Vector Retriever | MedQA textbooks, PubMedQA contexts, selected training explanations |
| Drug Safety | DrugCentral, KG drug edges, later openFDA |
| Evaluation | MedQA, MedMCQA, PubMedQA, MedBullets |

## 5. Recommended Technology Stack

Backend:

- Python 3.11+
- FastAPI
- Pydantic
- pytest
- structured logging

Graph:

- Neo4j
- Cypher

Vector:

- Qdrant recommended
- FAISS acceptable for local MVP

Embeddings:

- start with one embedding model that is easy to run
- later compare biomedical vs general embeddings

LLM:

- keep provider configurable
- implement rule-based/fallback behavior where possible so tests can run without paid LLM calls

Frontend:

- not required for MVP
- add after backend pipeline and evaluation work

## 6. MVP Scope

The MVP should implement backend-only functionality:

1. load and parse HPO/MONDO into lookup tables
2. load KG node names and build basic entity linker
3. import KG into Neo4j or create a local graph retrieval fallback
4. chunk MedQA English textbooks
5. build a vector index
6. implement fan-out retrieval
7. implement evidence ranking
8. implement basic conflict detection
9. implement clinical fusion
10. implement confidence scoring
11. implement final report generation
12. run at least one evaluation script

Not required for MVP:

- frontend
- MIMIC
- full PubMed bulk download
- full PMC OA download
- unrestricted live web search
- image/radiology support
- EHR/FHIR integration

## 7. Implementation Order

Follow this order:

1. Create clean project structure.
2. Add `.gitignore` and `.env.example`.
3. Add dependency file.
4. Add Pydantic schemas.
5. Add dataset path configuration.
6. Implement ontology parser for HPO and MONDO.
7. Implement KG CSV scanner and entity lookup.
8. Implement entity linker.
9. Implement KG import/retriever.
10. Implement document chunker.
11. Implement vector index builder/retriever.
12. Implement DrugCentral lightweight parser.
13. Implement retrieval orchestrator.
14. Implement evidence ranker.
15. Implement conflict detector.
16. Implement clinical fusion.
17. Implement confidence evaluator.
18. Implement adaptive retry.
19. Implement report generator.
20. Implement FastAPI endpoints.
21. Implement evaluation scripts.
22. Add tests and docs.

## 8. Success Criteria

The implementation is successful when:

- datasets are detected by a verification command
- HPO and MONDO terms can be parsed
- patient text can be converted into structured context
- entities can be linked to ontology/KG candidates
- graph retrieval returns candidate diseases and graph paths
- vector retrieval returns cited chunks
- evidence is ranked and fused
- final report includes differential diagnoses, evidence, confidence, limitations, and safety disclaimer
- low-confidence cases trigger limited retry
- MedQA or MedMCQA evaluation can run reproducibly

## 9. Main Handoff Documents

Use these files as the source of truth:

```text
Multi_Agent_GraphRAG_CDSS_Project_Plan.md
IMPLEMENTATION_SPEC.md
ANTIGRAVITY_PROMPT.md
datasets/DATASET_GUIDE.md
```

Do not use files under:

```text
archive/reference/
```

as active instructions.

