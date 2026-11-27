# 06 — Setup, configuration, and operations

[Documentation index](README.md) · [Previous: verification](05_CLAIMS_VERIFICATION_AND_SAFETY.md) · [Next: API and UI](07_API_AND_FRONTEND.md)

## 1. Understand what a fresh checkout contains

The repository contains source code, manifests, synthetic fixtures, and selected aggregate results. It does not contain populated databases, cached models, large biomedical files, API keys, or raw publisher snapshots. Installing Python packages is only the first part of setup.

The checked development environment uses Python 3.14. The dependency list is not pinned, so compatibility with a different Python/package combination must be checked rather than assumed. Docker is needed for the Compose database services; it is not used to containerize the whole application.

## 2. Clone the implementation branch

```bash
git clone --branch fix/windows-linux-runtime https://github.com/Arnavmangarapu/CDSS_SDC2.git
cd CDSS_SDC2
python3 -m venv .venv-linux
source .venv-linux/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, run `python -m venv .venv` then `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. Use `.\.venv\Scripts\python.exe` in place of `python` below, or activate with `.\.venv\Scripts\Activate.ps1`. Keep separate environments when Windows and WSL share one checkout. Paths under `/mnt/d` belong to WSL. If your checkout is on a Windows drive, create the WSL virtual environment on the Linux filesystem (for example, `python3 -m venv ~/.venvs/cdss`) to avoid slow imports through the mount. Repository access must be available to your Git account.

In the supplied local workspace, change into the nested `code/` folder before running project commands. The parent workspace is not the Git repository.

## 3. Configure the local environment

For a new checkout without an existing `.env`:

```bash
cp .env.example .env
```

In PowerShell, use `Copy-Item .env.example .env`.

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

### Data paths

The app reads `HPO_PATH`, `MONDO_PATH`, and `DRUGCENTRAL_DIR` from the repository’s `.env`. The graph importer reads `KG_PATH`, and the textbook importer looks under `MEDQA_DIR/MedQA-USMLE/textbooks/en`. Relative values start at the repository root. Use forward-slash relative paths for a checkout shared by Windows and WSL. If files are outside the repository, use native absolute paths in each environment. Keep the pinned authoritative snapshots at the paths in their source manifest.

`VECTOR_COLLECTION_PUBMEDQA` and `VECTOR_COLLECTION_MEDQA` exist in settings but are not queried by the current `VectorRetriever` analysis path.

## 4. Obtain local inputs

Follow [the data inventory](04_DATA_INGESTION_AND_RETRIEVAL.md) and [publisher/path guide](../datasets/DATASET_GUIDE.md). Required files include the two ontologies, DrugCentral names and targets, PrimeKG CSV, and the selected textbook files.

Do not place exam questions or answer explanations in the textbook input directory. Pinned publisher snapshots are fetched separately after the manifest is reviewed. A source's download availability does not settle its redistribution terms.

## 5. Start database services

For a fresh setup, start Docker Desktop or Docker Engine, then run this from the repository root in PowerShell or a Linux shell:

```bash
docker compose up -d
```

Compose uses named data volumes and publishes the database ports on localhost. For a WSL app, run the services in the same environment or configure `NEO4J_URI` and `QDRANT_URL` with addresses reachable from WSL. The volumes persist when you use `docker compose stop`.

If those exact containers already exist and are stopped:

```bash
docker start neo4j
docker start qdrant
```

Use `docker ps -a` to identify your actual containers first. The historical local experiment used differently named working containers; do not start a second pair on ports already in use. Do not delete volumes to resolve a name or port conflict.

## 6. Prepare models and build indexes

Use fresh manifest/output paths. Preserve existing stores before changing them. Run preparation in each operating system you use, since Hugging Face uses its local cache under that OS's user account.

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

`python -m backend.main` listens at `127.0.0.1:8000`. To enable reload while editing locally, use:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Run from the repository root so Python can find the `backend` module. The first analysis can be slower because services initialize lazily.

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
| `No module named backend` | Run the launch command from the repository root |
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
