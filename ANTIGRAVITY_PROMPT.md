# Prompt for Antigravity

Copy-paste the prompt below into Antigravity.

---

You are implementing a backend-first research prototype in this repository:

```text
/home/arnav/Documents/codes/sdc2/code
```

Project: **Multi-Agent Graph-RAG Clinical Decision Support System**

Read these files first and treat them as source of truth:

```text
Multi_Agent_GraphRAG_CDSS_Project_Plan.md
IMPLEMENTATION_SPEC.md
datasets/DATASET_GUIDE.md
```

Do not use files under:

```text
archive/reference/
```

as active instructions. They are historical context only.

## Required Architecture

Implement only this architecture:

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

Graph, vector, and evidence retrieval must fan out from the same structured patient context. Do not implement a strict sequential retrieval chain.

## Current Data

The data is already downloaded. Use these paths:

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

Do not commit datasets to Git.

## Your Implementation Task

Create a clean backend implementation with this structure:

```text
backend/
├── agents/
├── api/
├── schemas/
├── services/
├── config.py
└── main.py
ingestion/
evaluation/
tests/
docs/
```

Add:

```text
.gitignore
.env.example
requirements.txt or pyproject.toml
README.md
```

## First Milestone

Implement these first:

1. dataset inspection script
2. HPO/MONDO OBO parser
3. entity lookup and fuzzy linker
4. clinical clarifier producing a Pydantic `PatientContext`
5. KG CSV scanner or Neo4j import skeleton
6. lightweight graph retriever
7. textbook chunker
8. vector retriever skeleton with a local fallback
9. `/health` and `/analyze` FastAPI endpoints

Use deterministic/rule-based logic where possible. Do not make basic tests depend on paid LLM APIs.

## Required Safety Behavior

The final report must include a disclaimer:

```text
This is an educational/research decision-support output and is not a medical diagnosis. A licensed clinician must review all findings.
```

Never write:

```text
The patient has X.
```

Use:

```text
The evidence supports considering X as part of the differential diagnosis.
```

## Demo Case

Make this case work end-to-end:

```text
A 58-year-old man with diabetes and hypertension presents with crushing chest pain radiating to the left arm, sweating, nausea, and shortness of breath. He takes metformin and lisinopril. No known drug allergies.
```

Expected output should include:

- extracted symptoms and conditions
- linked entities where possible
- graph/vector evidence placeholders or real retrieved evidence
- myocardial infarction / acute coronary syndrome as a high-priority differential if evidence supports it
- ECG and troponin as suggested investigations
- emergency/urgent evaluation warning
- citations/evidence IDs
- confidence score
- limitations

## Constraints

- Do not delete user data.
- Do not move or rewrite datasets.
- Do not download new large datasets.
- Do not build frontend yet.
- Do not implement contradictory architectures.
- Do not index evaluation answer keys into retrieval collections.
- Keep modules testable.
- Add tests for parsers, linker, clarifier, and API health.

## Deliverables

When complete, provide:

1. files created/modified
2. how to install dependencies
3. how to run dataset inspection
4. how to start backend
5. how to call `/analyze`
6. known limitations
7. next steps

Start by inspecting the repo, then implement milestone 1.

