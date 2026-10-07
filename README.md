# Multi-Agent Graph-RAG CDSS

Backend-first research prototype for a Multi-Agent Graph-RAG Clinical Decision Support System.

## Start Here

Use these files as the source of truth:

```
Multi\_Agent\_GraphRAG\_CDSS\_Project\_Plan.md  
IMPLEMENTATION\_SPEC.md  
ANTIGRAVITY\_PROMPT.md  
datasets/DATASET\_GUIDE.md
```

Historical notes, the base paper PDF, raw Perplexity output, older architecture notes, and the dataset ZIP are archived under:

```
archive/reference/
```

Do not use archived files as active implementation instructions.

## Active Architecture

```
Clinical case  
  -\> Clarifier / Entity Normalizer  
  -\> Fan-out Retrieval Orchestrator  
      -\> Graph Retriever  
      -\> Vector Retriever  
      -\> Evidence / Drug Safety Retriever  
  -\> Evidence Ranker  
  -\> Conflict Detector  
  -\> Clinical Fusion  
  -\> Confidence Evaluator  
  -\> Final Report or Adaptive Retry
```

## Active Data

```
datasets/kg.csv  
datasets/ontologies/hpo/hp.obo  
datasets/ontologies/mondo/mondo.obo  
datasets/drugcentral/  
datasets/literature/MedQA/  
datasets/literature/MedMCQA/  
datasets/literature/pubmedqa-master/  
datasets/literature/medbulltes5op/
```

See `datasets/DATASET\_GUIDE.md` for details.

## Immediate Implementation Target

Implement milestone 1 from `IMPLEMENTATION\_SPEC.md`:

1. dataset inspection

2. HPO/MONDO parser

3. entity linker

4. clinical clarifier

5. graph retriever skeleton

6. vector retriever skeleton

7. FastAPI `/health` and `/analyze`

Do not build the frontend first.


How to run

### 1. Activate Environment & Install Dependencies

### **source venv/bin/activate**

pip install -r requirements.txt

### 2. Start the Docker Databases

./run\_qdrant.sh

./run\_neo4j.sh


python -m backend.main

or

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload


how to stop

docker stop qdrant neo4j

deactivate
