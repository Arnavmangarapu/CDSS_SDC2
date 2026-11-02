# Project documentation: start here

> **Publication scope:** This is a documentation-only branch based on the existing GitHub `claim-verification` head. The guides describe local checkpoint `a3a3412`; its eight unpublished implementation/research commits are not part of this branch. Some existing source files here are therefore older. Unavailable checkpoint references appear as code paths, not links.

This guide explains the **Evidence-linked Graph-RAG Clinical Decision Support System (CDSS)** in simple English, from the first user input to the final report. It is written for new developers, project evaluators, interviewers, and researchers.

Documentation date: **2 November 2026**. The implementation was checked against the source tree based on commit `a3a3412` on the `claim-verification` branch. These documents describe that code; saved experiments describe the dated versions that produced them.

## Reading order

| File | What you will learn |
| --- | --- |
| [01 — Project overview](01_PROJECT_OVERVIEW.md) | The problem, purpose, scope, technologies, and key terms |
| [02 — Architecture and code map](02_ARCHITECTURE_AND_CODE_MAP.md) | Components, boundaries, schemas, and responsibilities of the source files |
| [03 — End-to-end request flow](03_END_TO_END_REQUEST_FLOW.md) | Every step of an analysis, including fallback and retries |
| [04 — Data, ingestion, and retrieval](04_DATA_INGESTION_AND_RETRIEVAL.md) | Input datasets, graph construction, embeddings, reranking, and source indexing |
| [05 — Claims, verification, and safety](05_CLAIMS_VERIFICATION_AND_SAFETY.md) | Citation checks, claim states, missing facts, and the two implemented label rules |
| [06 — Setup, configuration, and operations](06_SETUP_CONFIGURATION_AND_OPERATIONS.md) | Installation, environment variables, startup, backups, and troubleshooting |
| [07 — API and frontend](07_API_AND_FRONTEND.md) | Request and response contracts, UI behavior, and error handling |
| [08 — Testing, evaluation, and results](08_TESTING_EVALUATION_AND_RESULTS.md) | Offline checks, experiment designs, metrics, dated results, and their limits |
| [09 — Limitations and future work](09_LIMITATIONS_AND_FUTURE_WORK.md) | Current gaps, design tradeoffs, and a practical improvement plan |
| [10 — Interview and review questions](10_INTERVIEW_AND_REVIEW_QUESTIONS.md) | A broad question bank with short, project-specific answers |
| [11 — Demo and explanation guide](11_DEMO_AND_EXPLANATION_GUIDE.md) | Short explanations, a presentation outline, and a reproducible demonstration |

For a first reading, follow the numbers. Before running the project, read 04 and 06. Before presenting results, read 08 and 09. For interview preparation, study 10 after understanding the request flow in 03.

## The central idea

The system proposes clinical possibilities and shows where evidence came from. It separates **finding a document** from **proving that a statement is correct for a patient**. Those are different tasks.

General model-generated diagnosis, investigation, and treatment claims remain `unverified` after the independent gate. Two narrow amlodipine label rules can produce `supported` medication warnings, and the allergy rule can mark a proposed amlodipine treatment `conflicting`. This is a research prototype, with a pinned source scope of adult hypertension and one amlodipine label. It has no completed independent clinical validation.

## How to read the examples

- Patient examples are synthetic and explain software behavior.
- JSON examples marked “illustrative” are not captured model outputs.
- A “source ID” means a stable `SourcePassage.id`, not the temporary ID of a general retrieval item.
- A metric always belongs to a particular dataset, task, implementation, and date.
- Setup commands assume the repository root is the current directory. In this supplied workspace that root is the nested `code/` directory.

## Relationship to existing documents

The root [README](../README.md) remains the short entry point. [ARCHITECTURE.md](../ARCHITECTURE.md) and [ARCHITECTURE_DIAGRAM.md](../ARCHITECTURE_DIAGRAM.md) provide additional architecture views. [datasets/DATASET_GUIDE.md](../datasets/DATASET_GUIDE.md) gives the local input inventory. [evaluation/README.md](../evaluation/README.md) preserves historical experiment details, and the independent evaluation protocol (`evaluation/INDEPENDENT_EVALUATION_PROTOCOL.md`, local checkpoint) explains the newer controlled workflow.

Older documents and result snapshots are historical records. For the current importer, ranking behavior, and API path, use these numbered guides together with the linked source code. If implementation changes, update the relevant guide and its examples in the same change.
