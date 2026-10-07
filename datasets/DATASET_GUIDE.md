# Dataset Guide for Multi-Agent Graph-RAG CDSS

This document explains the datasets currently stored under `datasets/`, what each dataset contains, how it is organized, and how each one should be used in the Clinical Decision Support System project.

The project uses these datasets for four main purposes:

1. **Knowledge graph retrieval**: relationship-aware medical reasoning.
2. **Entity normalization**: mapping raw clinical text to standard disease, phenotype, and drug concepts.
3. **Vector retrieval**: semantic retrieval over textbooks, QA data, and explanations.
4. **Evaluation**: measuring answer accuracy and retrieval quality.

---

## 1. Current Dataset Layout

```text
datasets/
├── kg.csv
├── ontologies/
│   ├── hpo/
│   │   └── hp.obo
│   └── mondo/
│       └── mondo.obo
├── drugcentral/
│   ├── drugcentral.dump.11012023.sql.gz
│   ├── drugcentral.dump.11012023.sql
│   ├── drug.target.interaction.tsv.gz
│   ├── drug.target.interaction.tsv
│   ├── FDA+EMA+PMDA_Approved.csv
│   └── structures.smiles.tsv
└── literature/
    ├── MedQA/
    ├── MedMCQA/
    ├── medbulltes5op/
    └── pubmedqa-master/
```

---

## 2. Verification Summary

| Dataset | Local path | Verification status | Notes |
|---|---|---:|---|
| Biomedical KG | `datasets/kg.csv` | Present | ~937 MB CSV; ~8.1M edges inspected earlier. |
| HPO | `datasets/ontologies/hpo/hp.obo` | Present and readable | OBO text file; 20,413 `[Term]` entries detected. |
| MONDO | `datasets/ontologies/mondo/mondo.obo` | Present and readable | OBO text file; 63,267 `[Term]` entries detected. |
| DrugCentral dump | `datasets/drugcentral/drugcentral.dump.11012023.sql.gz` | Present and gzip-readable | PostgreSQL dump. |
| DrugCentral extracted dump | `datasets/drugcentral/drugcentral.dump.11012023.sql` | Present | Extracted copy of the same PostgreSQL dump; not a separate dataset. |
| DrugCentral target interactions | `datasets/drugcentral/drug.target.interaction.tsv.gz` | Present and gzip-readable | TSV with drug-target interaction rows. |
| DrugCentral extracted target TSV | `datasets/drugcentral/drug.target.interaction.tsv` | Present | Extracted copy of the same target interaction TSV; not a separate dataset. |
| DrugCentral approved drugs | `datasets/drugcentral/FDA+EMA+PMDA_Approved.csv` | Present and readable | Small CSV/id-name list. |
| DrugCentral structures | `datasets/drugcentral/structures.smiles.tsv` | Present and readable | TSV with SMILES/InChI structures. |
| MedMCQA | `datasets/literature/MedMCQA/*.parquet` | Present as Apache Parquet | Requires `pyarrow` or `fastparquet` to inspect rows locally. |
| MedQA | `datasets/literature/MedQA/` | Present | US train/dev/test and textbooks present. |
| PubMedQA | `datasets/literature/pubmedqa-master/` | Present | 1,000 original QA/context records plus 500 test labels. |
| MedBullets | `datasets/literature/medbulltes5op/` | Present | 297 test records, 10 validation records. |

---

## 3. Biomedical Knowledge Graph

### Path

```text
datasets/kg.csv
```

### Format

CSV with these columns:

```text
relation, display_relation,
x_index, x_id, x_type, x_name, x_source,
y_index, y_id, y_type, y_name, y_source
```

Each row represents one edge:

```text
x node --relation--> y node
```

Example relation types include:

- `disease_phenotype_positive`
- `disease_phenotype_negative`
- `disease_disease`
- `disease_protein`
- `drug_drug`
- `drug_effect`
- `drug_protein`
- `indication`
- `contraindication`
- `pathway_protein`

### Data Types Present

The KG contains biomedical nodes such as:

- disease
- effect/phenotype
- drug
- gene/protein
- anatomy
- biological process
- molecular function
- cellular component
- pathway
- exposure

### Project Use

Use this as the core **Graph-RAG source**.

Primary uses:

- symptom/phenotype to disease retrieval
- disease to drug indication retrieval
- contraindication lookup
- drug-drug interaction lookup
- disease comorbidity relationship retrieval
- disease-gene/protein/pathway evidence retrieval

### Implementation Notes

Import this into Neo4j.

Recommended node properties:

```text
id
name
type
source
normalized_name
```

Recommended relationship properties:

```text
relation
display_relation
```

Create indexes on:

- `id`
- `name`
- `normalized_name`
- `source`
- `type`

---

## 4. HPO: Human Phenotype Ontology

### Path

```text
datasets/ontologies/hpo/hp.obo
```

### Format

OBO ontology file.

Detected locally:

- data version: `hp/releases/2026-06-23`
- `[Term]` entries: 20,413
- synonym lines: 26,237
- xref lines: 18,066

### What It Contains

HPO provides standardized terms for human phenotypic abnormalities.

Examples of concept categories:

- clinical signs
- symptoms
- abnormal examination findings
- abnormal lab or imaging findings
- inherited/rare disease phenotypes

Each term may include:

- HPO ID, for example `HP:0001250`
- name
- definition
- synonyms
- parent-child hierarchy
- cross-references to other vocabularies

### Project Use

Use HPO for **symptom and phenotype normalization**.

Primary uses:

- map raw patient symptoms to phenotype IDs
- expand symptom synonyms
- improve graph matching against phenotype nodes in the KG
- support rare disease phenotype matching
- provide normalized labels for the Clinical Clarifier output

### Example Use in Pipeline

Raw input:

```text
shortness of breath
```

Possible normalized output:

```json
{
  "text": "shortness of breath",
  "normalized_name": "Dyspnea",
  "ontology_source": "HPO",
  "ontology_id": "HP:0002094"
}
```

### Implementation Notes

Parse these fields from the OBO file:

- `id`
- `name`
- `def`
- `synonym`
- `xref`
- `is_a`

Build a lookup table:

```text
lowercase name/synonym -> HPO ID(s)
```

---

## 5. MONDO: Disease Ontology

### Path

```text
datasets/ontologies/mondo/mondo.obo
```

### Format

OBO ontology file.

Detected locally:

- data version: `releases/2026-08-04`
- `[Term]` entries: 63,267
- synonym lines: 95,046
- xref lines: 147,924

### What It Contains

MONDO provides an integrated disease ontology that combines disease concepts and mappings from multiple biomedical resources.

Each term may include:

- MONDO ID
- disease name
- synonyms
- definitions
- hierarchy
- cross-references to OMIM, Orphanet, DOID, ICD, UMLS, SNOMED CT, and other sources

### Project Use

Use MONDO for **disease normalization**.

Primary uses:

- map extracted disease mentions to standard disease IDs
- match patient history against KG disease nodes
- normalize candidate diagnoses from graph/vector retrieval
- merge duplicate disease names from different sources
- support disease synonym expansion for retrieval

### Example Use in Pipeline

Raw input:

```text
heart attack
```

Possible normalized output:

```json
{
  "text": "heart attack",
  "normalized_name": "myocardial infarction",
  "ontology_source": "MONDO",
  "ontology_id": "MONDO:..."
}
```

### Implementation Notes

Parse these fields:

- `id`
- `name`
- `def`
- `synonym`
- `xref`
- `is_a`
- `is_obsolete`

Build a lookup table:

```text
lowercase disease name/synonym -> MONDO ID(s)
```

Use MONDO cross-references to connect with KG source IDs where possible.

---

## 6. DrugCentral

### Path

```text
datasets/drugcentral/
```

### Files Present

```text
drugcentral.dump.11012023.sql.gz
drugcentral.dump.11012023.sql
drug.target.interaction.tsv.gz
drug.target.interaction.tsv
FDA+EMA+PMDA_Approved.csv
structures.smiles.tsv
```

Both compressed and extracted versions of the DrugCentral SQL dump and target-interaction TSV are currently present. They contain duplicate content. Prefer the extracted `.sql`/`.tsv` files for local parsing if storage is not an issue. Prefer `.gz` files for archival/storage.

### What It Contains

DrugCentral is an open drug information resource.

It can include:

- drug names
- approved drugs
- drug structures
- targets
- mechanisms of action
- indications
- contraindications
- adverse events
- ATC codes
- label-derived information

### File Details

#### `drugcentral.dump.11012023.sql.gz`

PostgreSQL database dump.

Use this for the full DrugCentral dataset.

Local check:

```text
PostgreSQL database dump
Dumped from database version 10.11
```

#### `drug.target.interaction.tsv.gz`

Compressed TSV containing drug-target interaction data.

Detected columns include:

```text
DRUG_NAME
STRUCT_ID
TARGET_NAME
TARGET_CLASS
ACCESSION
GENE
SWISSPROT
ACT_VALUE
ACT_UNIT
ACT_TYPE
ACT_COMMENT
ACT_SOURCE
RELATION
MOA
MOA_SOURCE
ACTION_TYPE
TDL
ORGANISM
```

Use this before loading the full PostgreSQL dump if you want a lightweight first integration.

#### `FDA+EMA+PMDA_Approved.csv`

Small approved-drug list with DrugCentral ID and drug name.

Example row shape:

```text
5376,remdesivir
```

#### `structures.smiles.tsv`

TSV with chemical structure identifiers.

Detected columns:

```text
SMILES
InChI
InChIKey
ID
INN
CAS_RN
```

### Project Use

Use DrugCentral for **drug safety and pharmacology retrieval**.

Primary uses:

- drug normalization support
- drug-target relationships
- drug mechanism evidence
- drug indications
- contraindications
- adverse event lookup
- medication safety notes

### Implementation Notes

There are two practical integration paths:

#### Lightweight MVP path

Use:

```text
drug.target.interaction.tsv.gz
FDA+EMA+PMDA_Approved.csv
structures.smiles.tsv
```

This avoids setting up PostgreSQL immediately.

#### Full path

Load:

```text
drugcentral.dump.11012023.sql.gz
```

into PostgreSQL, then extract tables needed by your backend.

Expected future services:

- `drug_normalizer`
- `drug_target_lookup`
- `contraindication_lookup`
- `drug_safety_lookup`

---

## 7. MedMCQA

### Path

```text
datasets/literature/MedMCQA/
```

### Files Present

```text
train-00000-of-00001.parquet
validation-00000-of-00001.parquet
test-00000-of-00001.parquet
```

### Format

Apache Parquet.

Local file verification confirms the files are Parquet. Row-level inspection requires installing either:

```text
pyarrow
```

or

```text
fastparquet
```

### What It Contains

MedMCQA is a large-scale medical multiple-choice QA dataset based on medical entrance exam questions.

Typical fields include:

- question
- option A
- option B
- option C
- option D
- correct answer
- subject
- topic
- explanation, depending on dataset version

### Project Use

Use MedMCQA for **evaluation and optional vector retrieval**.

Primary uses:

- benchmark medical question-answering accuracy
- evaluate full pipeline against a larger QA set than MedQA
- create additional text chunks from explanations, if explanations are present
- compare LLM-only, vector-only, graph-only, and full Graph-RAG performance

### Recommended Use

For evaluation:

```text
question + options -> model answer -> compare against correct option
```

For retrieval indexing:

```text
question + correct answer + explanation -> vector document chunk
```

Only index explanations if they exist and are reliable. Do not index test-set answers into the retrieval database before evaluating, otherwise evaluation will be contaminated.

### Verification Command

Install Parquet support:

```bash
pip install pyarrow
```

Then inspect:

```python
import pandas as pd

for split in ["train", "validation", "test"]:
    path = f"datasets/literature/MedMCQA/{split}-00000-of-00001.parquet"
    df = pd.read_parquet(path)
    print(split, df.shape)
    print(df.columns)
    print(df.head(1).to_dict(orient="records")[0])
```

---

## 8. MedQA

### Path

```text
datasets/literature/MedQA/
```

### Important Subdirectories

```text
datasets/literature/MedQA/MedQA-USMLE/questions/
datasets/literature/MedQA/MedQA-USMLE/textbooks/
```

### What It Contains

MedQA contains USMLE-style medical multiple-choice questions and medical textbook text files.

Available US split counts:

- train: 10,178 records
- dev: 1,272 records
- test: 1,273 records

Available textbook files:

- 18 English medical textbooks
- Chinese textbook aggregate files also present

### Question Format

JSONL records with fields like:

```json
{
  "question": "",
  "answer": "",
  "options": {
    "A": "",
    "B": "",
    "C": "",
    "D": "",
    "E": ""
  },
  "meta_info": "",
  "answer_idx": ""
}
```

### Project Use

Use MedQA for:

- answer accuracy evaluation
- multiple-choice clinical reasoning benchmark
- textbook vector index construction
- baseline comparison with literature

### Important Evaluation Rule

Do not index MedQA test questions/answers into the vector database before evaluating on MedQA test. This would leak answers into retrieval.

Recommended:

- Use textbooks for retrieval.
- Use train/dev questions for development.
- Keep test split isolated for final evaluation.

---

## 9. PubMedQA

### Path

```text
datasets/literature/pubmedqa-master/pubmedqa-master/
```

### Important Files

```text
data/ori_pqal.json
data/test_ground_truth.json
```

### What It Contains

PubMedQA contains biomedical research questions derived from PubMed articles.

Local counts:

- `ori_pqal.json`: 1,000 records
- `test_ground_truth.json`: 500 labels

Typical record includes:

- PubMed ID
- question
- contexts/abstract sections
- long answer
- final yes/no/maybe answer

### Project Use

Use PubMedQA for:

- evidence-based QA evaluation
- vector retrieval over biomedical article contexts
- testing whether the system can answer from retrieved literature

### Important Evaluation Rule

Keep evaluation labels separate from the retrieval corpus when running benchmarks.

---

## 10. MedBullets

### Path

```text
datasets/literature/medbulltes5op/
```

### Files

```text
test.json
validation.json
```

### Format

JSONL-style records, despite the `.json` extension.

Local counts:

- test: 297 records
- validation: 10 records

### What It Contains

Medical multiple-choice questions with explanations.

Detected fields:

```text
question
choicesA
choicesB
choicesC
choicesD
choicesE
answer_idx
answer
explanation
link
```

### Project Use

Use MedBullets for:

- clinical reasoning evaluation
- explanation-based vector chunks
- comparison with the base paper, which evaluated on MedBullets

### Important Evaluation Rule

Do not index MedBullets test explanations if you evaluate on MedBullets test. Use validation or separate source material for retrieval.

---

## 11. How These Datasets Map to the Architecture

| Architecture component | Dataset/resource used |
|---|---|
| Clinical Clarifier | HPO, MONDO, DrugCentral names, KG node names |
| Entity Normalizer | HPO, MONDO, DrugCentral, later RxNorm/UMLS |
| Graph Retriever | `kg.csv` imported into Neo4j |
| Vector Retriever | MedQA textbooks, PubMedQA contexts, selected QA explanations, future guidelines |
| Evidence Retriever | PubMed API cache and future guideline documents |
| Drug Safety Checker | DrugCentral, KG contraindication/drug-drug edges, future openFDA |
| Evaluation | MedQA, MedMCQA, PubMedQA, MedBullets |
| Adaptive Retry | Uses retrieval failures and low-confidence evidence from all sources |

---

## 12. Recommended Ingestion Order

Use this order to avoid blocking implementation:

1. Parse HPO and MONDO into lightweight lookup tables.
2. Build KG import from `kg.csv` into Neo4j.
3. Build basic entity linker using KG node names + HPO + MONDO.
4. Build vector index over MedQA English textbooks.
5. Add PubMedQA contexts to a separate vector collection.
6. Add MedMCQA as an evaluation dataset.
7. Add DrugCentral lightweight TSV integration.
8. Load full DrugCentral PostgreSQL dump only after the core pipeline works.
9. Add guidelines and PubMed API cache.

---

## 13. Storage and Git Rules

Do not commit these datasets directly to GitHub.

Keep this in `.gitignore`:

```gitignore
datasets/*
!datasets/README.md
!datasets/DATASET_GUIDE.md
```

Large files currently include:

- `datasets/drugcentral/drugcentral.dump.11012023.sql.gz`
- `datasets/kg.csv`
- MedQA textbook corpus
- MedMCQA parquet files

Use Git only for:

- documentation
- ingestion scripts
- schema definitions
- small examples
- checksums if needed

---

## 14. Remaining Data Still Needed

The current dataset set is enough to start implementation.

Still needed later:

- RxNorm via RxNav API or local files
- UMLS after license approval
- selected clinical guideline PDFs/HTML
- PubMed API cache
- openFDA labels API cache
- optional MIMIC-IV/MIMIC-IV-Note for stronger research
- optional BioASQ for additional evaluation

---

## 15. Current Practical Status

The project now has enough data for:

- initial entity normalization
- initial KG retrieval
- initial vector retrieval
- drug-target lookup
- QA evaluation

Do not collect more large datasets before implementing the first ingestion and retrieval pipeline.
