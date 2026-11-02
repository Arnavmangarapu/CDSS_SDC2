# 06 — Setup, configuration, and operations

[Documentation index](README.md) · [Previous: verification](05_CLAIMS_VERIFICATION_AND_SAFETY.md) · [Next: API and UI](07_API_AND_FRONTEND.md)

## 1. Understand what a fresh checkout contains

The repository contains source code, manifests, synthetic fixtures, and selected aggregate results. It does not contain populated databases, cached models, large biomedical files, API keys, or raw publisher snapshots. Installing Python packages is only the first part of setup.

The checked development environment uses Python 3.14. The dependency list is not pinned, so compatibility with a different Python/package combination must be checked rather than assumed. Docker is needed for the supplied database helpers; it is not used to containerize the whole application.

## 2. Clone the implementation branch

```bash
git clone --branch claim-verification https://github.com/Arnavmangarapu/CDSS_SDC2.git
cd CDSS_SDC2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For PowerShell, activate with `.\.venv\Scripts\Activate.ps1`; Bash helper scripts need Bash/WSL or equivalent manual Docker commands. Repository access must be available to your Git account.

In the supplied local workspace, change into the nested `code/` folder before running project commands. The parent workspace is not the Git repository.

## 3. Configure the local environment

For a new checkout without an existing `.env`:

```bash
cp .env.example .env
```

If `.env` already exists, edit it without replacing its keys. [Settings](../backend/config.py) loads the repository-root `.env`; `.gitignore` excludes it. Keep keys out of documentation and commits.

### Database settings

| Variable | Default | Used for |
| --- | --- | --- |
| `NEO4J_URI` | `bolt://localhost:7687` | Graph importer and runtime driver |
| `NEO4J_USER` | `neo4j` | Neo4j login |
| `NEO4J_PASSWORD` | `password` | Development login matching helper script |
| `QDRANT_URL` | `http://localhost:6333` | Vector import and runtime queries |
| `VECTOR_COLLECTION_TEXTBOOKS` | `medical_textbooks_v2` | Active textbook collection |
| `VECTOR_COLLECTION_GUIDELINES` | `clinical_guidelines` | Pinned guideline collection |
| `VECTOR_COLLECTION_DRUG_LABELS` | `clinical_drug_labels` | Pinned label collection |

The helper password is a local development default. Changing it in `.env` does not change an already-created database's credentials.

### Model and provider settings

`VECTOR_EMBEDDER_MODEL`, `VECTOR_EMBEDDER_REVISION`, `VECTOR_RERANKER_MODEL`, and `VECTOR_RERANKER_REVISION` define the local retrieval models. Changing an encoder requires compatible indexed vectors, not just a different environment value. A blank reranker setting disables its optional loading.

`GEMINI_API_KEY`, `COHERE_API_KEY`, `MISTRAL_API_KEY`, and `OPENROUTER_API_KEY` enable their model-provider paths. `SERPER_API_KEY` enables optional web discovery. Blank provider keys are skipped.

The configured fallback order is Gemini Flash Lite, Gemini Flash, Cohere, Mistral, then OpenRouter. The actual model identifiers are defined in [llm_fallback.py](../backend/services/llm_fallback.py). They are code defaults, not a promise that a provider still offers the alias or grants the account access.

### Data path settings and a current caveat

Settings include `DATASETS_DIR`, `HPO_PATH`, `MONDO_PATH`, `KG_PATH`, `DRUGCENTRAL_DIR`, and dataset-specific literature paths. Some ingestion/evaluation tools read them.

However, `get_pipeline()` currently constructs HPO, MONDO, KG-constructor, and DrugCentral paths directly under the repository's `datasets/` directory. The textbook importer also uses its fixed repository-relative textbook directory. Editing a path setting alone does not relocate every runtime input. Keep the expected layout unless you also update and verify the code path that reads it.

`VECTOR_COLLECTION_PUBMEDQA` and `VECTOR_COLLECTION_MEDQA` exist in settings but are not queried by the current `VectorRetriever` analysis path.

## 4. Obtain local inputs

Follow [the data inventory](04_DATA_INGESTION_AND_RETRIEVAL.md) and [publisher/path guide](../datasets/DATASET_GUIDE.md). Required files include the two ontologies, DrugCentral names and targets, PrimeKG CSV, and the selected textbook files.

Do not place exam questions or answer explanations in the textbook input directory. Pinned publisher snapshots are fetched separately after the manifest is reviewed. A source's download availability does not settle its redistribution terms.

## 5. Start database services

For a fresh machine without the helper containers:

```bash
./run_neo4j.sh
./run_qdrant.sh
```

These run `neo4j:5.18.0` and the untagged `qdrant/qdrant` image, with named data volumes. The Qdrant image is not pinned by the script. Both helpers publish development ports without explicit localhost-only bindings.

If those exact containers already exist and are stopped:

```bash
docker start neo4j
docker start qdrant
```

Use `docker ps -a` to identify your actual containers first. The historical local experiment used differently named working containers; do not start a second pair on ports already in use. Do not delete volumes to resolve a name or port conflict.

## 6. Prepare models and build indexes

Use fresh manifest/output paths. Preserve existing stores before changing them.

```bash
python -m ingestion.prepare_models
python -m ingestion.populate_neo4j --manifest evaluation/runs/local-graph-build/manifest.json
python -m ingestion.populate_qdrant --manifest evaluation/runs/local-textbook-build/manifest.json
```

`prepare_models` downloads both the configured encoder and reranker; runtime and import encoding subsequently load locally. Graph ingestion streams the CSV and merges the selected schema. Textbook ingestion refuses an existing collection.

To build an additional textbook collection:

```bash
python -m ingestion.populate_qdrant --collection medical_textbooks_review --manifest evaluation/runs/review-textbook-build/manifest.json
```

After verifying the new build, set `VECTOR_COLLECTION_TEXTBOOKS=medical_textbooks_review` and restart the API. The importer does not automatically switch the runtime setting.

### Pinned sources

```bash
python -m ingestion.authoritative_sources fetch
python -m ingestion.authoritative_sources verify
python -m ingestion.authoritative_sources ingest
```

`fetch` refuses bytes that differ from the manifest. If the live publisher document has changed, retain the failure and review/version the source rather than removing the checksum check.

`ingest` deletes and recreates the configured guideline and label collections. Keep them dedicated to this manifest. Use backups or new configured collection names when preserving a previous source index. Collection replacement is not transactional across the two source types.

## 7. Start the application

From the repository root:

```bash
python -m backend.main
```

Open `http://localhost:8000/ui/`. The default FastAPI interactive schema is at `http://localhost:8000/docs`, and its OpenAPI JSON is at `/openapi.json`.

`python -m backend.main` enables reload and binds `0.0.0.0:8000`. For a local development session with an explicit loopback binding, use:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The static frontend mount uses a relative `frontend` directory, so launch from the repository root. The first analysis can be slower because services initialize lazily.

## 8. Verify readiness in layers

```bash
curl http://localhost:8000/health
curl http://localhost:6333/collections
python -m ingestion.authoritative_sources verify
```

Expected API health response:

```json
{"status":"ok","service":"CDSS Backend"}
```

This only confirms the API process. Separately check Neo4j connectivity and the `ClinicalEntity` schema, active Qdrant collection dimensions/counts, local model cache, source snapshot verification, and actual provider access. A successful health response is not pipeline readiness or clinical validation.

## 9. Run a synthetic analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"case_text":"A 57-year-old woman with confirmed hypertension currently takes amlodipine. She has no known drug allergies."}'
```

Inspect missing BP, renal function, potassium, and other unresolved facts rather than expecting a cleared treatment. Use [the demo guide](11_DEMO_AND_EXPLANATION_GUIDE.md) for a review-oriented walkthrough.

## 10. Troubleshooting

| Symptom | Likely reason and useful check |
| --- | --- |
| “Not a git repository” in the supplied workspace | Enter the nested `code/` directory |
| StaticFiles directory error | Start from the repository root containing `frontend/` |
| Docker container name exists | Inspect/start the existing container instead of rerunning `docker run` |
| Database port already used | Identify the current service; avoid a second competing container |
| Neo4j authentication/connection error | Check running container, password, URI, and driver connectivity |
| No graph candidates | Check symptoms/links, actual graph schema, and positive relation coverage; zero can be valid |
| Vector retriever unavailable | Check cached encoder revision, Qdrant URL, and initialization log |
| Cross-encoder unavailable | Run model preparation; dense fallback may operate but changes ranking |
| Qdrant dimension mismatch | Use an index built with the configured encoder; 384- and 768-dimensional stores are incompatible |
| Textbook importer refuses collection | Pick a new collection name and fresh manifest path |
| Source checksum mismatch | Publisher bytes changed or wrong local snapshot; review and pin a version |
| No authoritative passages | Case may be outside scope, or source/index/model loading failed |
| All claims unverified | Expected for general proposals; inspect source gaps and rule scope |
| Supported warning absent | Explicit facts or exact label section may not have been retrieved |
| Slow request | Cold initialization, sequential calls, multiple fallbacks, reranking, or adaptive retries |
| Provider timeout/429/invalid JSON | Inspect provider availability and trace; do not equate failure with a clinical result |
| UI request/render error | Inspect API response and browser console, then refresh to avoid stale assets |

## 11. Backups, logs, and operating limits

Read [DATABASE_CHECKPOINT.md](../DATABASE_CHECKPOINT.md) before using historical rollback commands. Its archives and restore script are local ignored artifacts, not guaranteed to exist in a fresh clone. Record your own container image identities, volumes, collection settings, and checksums for a new environment.

The API uses console output, not a governed audit log. Retry feedback and search terms can appear in logs; case content also goes to configured providers. Use synthetic cases for demonstrations. There is no implemented clinical-record storage, user-account system, retention policy, rate limit, or deployment hardening layer.

This documentation change does not require a database rebuild. Reading the guides should not be confused with executing all their operational commands against an existing environment.
