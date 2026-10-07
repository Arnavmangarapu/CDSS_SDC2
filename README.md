# Multi-Agent Graph-RAG Clinical Decision Support Prototype

Research prototype for a clinician-facing differential diagnosis and evidence retrieval workflow. It is not validated for clinical use.

## Current architecture

Clinical case → clarifier and entity linker → retrieval orchestrator (Neo4j graph, Qdrant vectors, DrugCentral, web discovery) → evidence ranker → conflict detector → clinical fusion → confidence evaluator or retry → report.

The proposed claim-linked guideline and medication-safety features are **planned**, not yet implemented. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the stepwise design, completion gates, Git checkpoints, and current progress. See [datasets/DATASET_GUIDE.md](datasets/DATASET_GUIDE.md) for the local data inventory.

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

## Recovery checkpoint

The current prototype before claim verification is saved in Git as `pre-claim-verification` (`e00a737`). The active implementation and rollback instructions are in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
