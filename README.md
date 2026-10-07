# Multi-Agent Graph-RAG Clinical Decision Support Prototype

Research prototype for a clinician-facing differential diagnosis and evidence retrieval workflow. It is not validated for clinical use.

## Current architecture

Clinical case → clarifier and entity linker → retrieval orchestrator (Neo4j graph, Qdrant vectors, DrugCentral, web discovery) → evidence ranker → conflict detector → clinical fusion → confidence evaluator or retry → report.

Versioned guideline and drug-label retrieval, traceable patient-context extraction, and conditional claim proposals are implemented for a narrow adult hypertension source set. Claims remain unverified until the independent checks in the next step; medication-safety decisions and UI presentation are still planned. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for completion gates and progress, and [datasets/DATASET_GUIDE.md](datasets/DATASET_GUIDE.md) for the local data inventory.

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
