# Multi-Agent Graph-RAG Clinical Decision Support Prototype

Research prototype for a clinician-facing differential diagnosis and evidence retrieval workflow. It is not validated for clinical use.

## Current architecture

Clinical case → clarifier and entity linker → retrieval orchestrator (Neo4j graph, Qdrant vectors, DrugCentral, web discovery) → evidence ranker → conflict detector → clinical fusion → claim verifier and label safety checks → confidence retry heuristic → report.

Versioned guideline and drug-label retrieval, traceable patient-context extraction, conditional claim proposals, and a fail-closed verification gate are implemented for a narrow adult hypertension source set. Candidate claims remain unverified unless a narrow pinned-label safety rule applies. The report UI shows each claim's status, conditions, missing checks, and source section/date; it does not show an uncalibrated confidence percentage. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for completion gates and progress, and [datasets/DATASET_GUIDE.md](datasets/DATASET_GUIDE.md) for the local data inventory.

## Run locally

From this directory:

```bash
source venv/bin/activate
pip install -r requirements.txt
./run_qdrant.sh
./run_neo4j.sh
python -m backend.main
```

The API exposes `/health` and `/analyze`; the existing frontend is served at `/ui` on port 8000. Large datasets and database contents are local and excluded from Git. Copy `.env.example` to `.env` and supply keys in `.env`; never commit credentials.

`/analyze` retains `ranked_diagnoses`, `overall_confidence` (an uncalibrated legacy retry score), and `claims`. The report also includes `differential` entries linked by claim ID, `unassigned_diagnostic_claim_ids`, `investigation_claim_ids`, `treatment_claim_ids`, `medication_safety`, `evidence_completeness`, and `verification_failures`. Claims and source passages remain the authoritative detail records for these IDs. The UI presents missing allergy and medication information as unknown, never as a safety clearance.

## Pinned authoritative sources

The source manifest is [sources/hypertension/manifest.json](sources/hypertension/manifest.json). It pins the official NICE NG136 recommendations page and one DailyMed amlodipine label by version and SHA-256. The raw documents are stored under ignored `datasets/authoritative/` and need an independent clinician review before clinical use.

```bash
python -m ingestion.authoritative_sources fetch
python -m ingestion.authoritative_sources verify
python -m ingestion.authoritative_sources ingest
```

`fetch` refuses changed remote bytes; review and version the manifest before ingesting a changed source. `ingest` replaces the two dedicated Qdrant collections and leaves the textbook collection alone. Retrieved source passages carry exact section names, stable IDs, URL, version, and checksum. Serper snippets remain discovery leads and are not accepted as citation passages.

## Recovery checkpoint

The current prototype before claim verification is saved in Git as `pre-claim-verification` (`e00a737`). The active implementation and rollback instructions are in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
