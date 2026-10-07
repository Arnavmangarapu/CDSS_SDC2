<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# @Academic   I am building a research-oriented Multi-Agent Graph-RAG Clinical Decision Support System. The architecture uses:

1. Clinical text clarification and entity normalization
2. Biomedical knowledge graph retrieval using Neo4j
3. Vector retrieval over medical textbooks, PubMedQA, MedQA, MedBullets, PubMed abstracts, and clinical guidelines
4. Evidence retrieval from trusted sources
5. Evidence ranking, conflict detection, clinical fusion, confidence scoring, and adaptive retry

I already have:

- A PrimeKG-style biomedical KG CSV with disease, phenotype, drug, gene/protein, anatomy, pathway, and contraindication/drug-drug relations
- MedQA
- PubMedQA
- MedBullets
- English medical textbook text files

Find the remaining datasets/resources I should collect before implementation.

Specifically find reliable, preferably free/public or academically accessible sources for:

1. Entity linking and ontology mapping:
    - symptom synonyms
    - disease synonyms
    - drug synonyms
    - abbreviation expansion
    - mappings to HPO, MONDO, RxNorm, ICD-10, SNOMED CT, UMLS, Disease Ontology, DrugBank if available
2. Clinical guidelines:
    - NICE
    - WHO
    - CDC
    - FDA/openFDA drug labels
    - IDSA infectious disease guidelines
    - ACC/AHA cardiology guidelines
    - ADA diabetes standards
    - GINA asthma guidance
    - GOLD COPD guidelines
    - any other useful open clinical guideline repositories
3. PubMed/literature corpora:
    - PubMed abstracts
    - PubMed Central open-access subset
    - APIs or bulk download options
    - licensing and citation requirements
4. Drug safety datasets:
    - drug-drug interactions
    - contraindications
    - adverse effects
    - FDA labels
    - RxNorm
    - SIDER or similar datasets
    - open alternatives to DrugBank if DrugBank licensing is restrictive
5. Realistic clinical case/note datasets:
    - MIMIC-IV
    - MIMIC-IV-Note
    - synthetic clinical cases
    - public case reports
    - de-identified clinical note datasets
6. Evaluation datasets for medical QA, diagnosis, retrieval, and clinical reasoning:
    - MedQA alternatives
    - PubMedQA alternatives
    - MedMCQA
    - MMLU medical subsets
    - BioASQ
    - MedNLI
    - MedHALT
    - any benchmark useful for Graph-RAG clinical decision support

For each resource, provide:

- Name
- URL
- What it contains
- Why it is useful for this CDSS project
- Access method: API, bulk download, Kaggle, Hugging Face, official site, credentialed access, etc.
- License/access restrictions
- Whether it should be used in MVP or later phase
- Priority: must-have, useful, optional
- Any known limitations

Also recommend a minimal dataset collection plan for starting implementation quickly, separating:

- MVP data required before coding
- Data that can be added after the first prototype
- Data that is only needed for a stronger research paper/demo

Based on my research, here is a comprehensive dataset collection plan for your Multi-Agent Graph-RAG Clinical Decision Support System:

## 1. Entity Linking and Ontology Mapping

### **UMLS Metathesaurus** (Must-Have, MVP)

- **URL:** https://www.nlm.nih.gov/research/umls/index.html
- **Contents:** Integrated biomedical terminology with mappings across 200+ vocabularies including SNOMED CT, RxNorm, ICD-10-CM, LOINC, MeSH, HPO, MedDRA, and more. Includes synonymy relations, hierarchical structures, and cross-vocabulary mappings.
- **Why useful:** Core resource for entity normalization, symptom/disease/drug synonym resolution, and abbreviation expansion. Provides the semantic backbone for your KG.
- **Access:** Free license via UMLS Terminology Services (UTS) account; bulk download (RRF format) or API access. Requires signing license agreement (5 business days approval).[^1][^2]
- **License:** Free for research; SNOMED CT free in US and member countries; some vocabularies may require additional agreements.[^1]
- **Limitations:** Large download (~30GB); requires local installation or custom subset creation via MetamorphoSys.


### **SNOMED CT** (Must-Have, MVP)

- **URL:** https://www.nlm.nih.gov/research/umls/snomedct.html (via UMLS)
- **Contents:** Comprehensive clinical terminology with 350K+ concepts covering diseases, symptoms, procedures, anatomy, and more. Rich hierarchy and synonymy.
- **Why useful:** Gold standard for clinical entity normalization; essential for symptom and disease synonym resolution.
- **Access:** Via UMLS license (free); download through UTS portal.[^3][^1]
- **License:** Free in US and SNOMED International member countries; territorial restrictions apply.
- **Limitations:** Requires UMLS license; large file size.


### **RxNorm** (Must-Have, MVP)

- **URL:** https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- **Contents:** Normalized names for clinical drugs with links to ingredients, strength, dose form; includes NDC, VA Class, and ATC codes.
- **Why useful:** Drug entity normalization, synonym resolution, and drug-drug interaction mapping.
- **Access:** Free via UMLS license or direct REST API (https://rxnav.nlm.nih.gov/).[^2]
- **License:** Public domain (NLM).
- **Limitations:** US-focused; may miss international drug names.


### **HPO (Human Phenotype Ontology)** (Useful, Phase 2)

- **URL:** https://hpo.jax.org/
- **Contents:** Standardized vocabulary of phenotypic abnormalities with 15K+ terms, hierarchical structure, and cross-references to OMIM, Orphanet, UMLS.
- **Why useful:** Phenotype/symptom normalization, especially for rare diseases and genetic conditions.
- **Access:** Bulk download (OWL, OBO, JSON) from website; no credentials required.
- **License:** CC BY 4.0.
- **Limitations:** Focused on heritable phenotypes; less coverage of acquired conditions.


### **MONDO (Monarch Disease Ontology)** (Useful, Phase 2)

- **URL:** https://mondo.monarchinitiative.org/
- **Contents:** Integrated disease ontology merging OMIM, Orphanet, DOID, NCIT with cross-references to UMLS, ICD, SNOMED.
- **Why useful:** Disease entity normalization across multiple source ontologies; handles rare and common diseases.
- **Access:** Bulk download (OWL, OBO, JSON) via GitHub or website.
- **License:** CC BY 4.0.
- **Limitations:** Less frequently updated than UMLS.


### **Disease Ontology (DOID)** (Optional, Phase 3)

- **URL:** https://disease-ontology.org/
- **Contents:** 10K+ disease concepts with ICD, SNOMED, UMLS, OMIM mappings.
- **Why useful:** Alternative disease ontology for cross-validation; useful for research benchmarking.
- **Access:** GitHub (https://github.com/DiseaseOntology/HumanDiseaseOntology).
- **License:** CC0 1.0.
- **Limitations:** Smaller coverage than MONDO or UMLS.


### **DrugBank (Open Data Subset)** (Useful, Phase 2)

- **URL:** https://go.drugbank.com/
- **Contents:** Drug structures, targets, pathways, interactions (full version requires subscription).
- **Why useful:** Drug-target interactions, mechanisms of action, pathway data.
- **Access:** Open Data subset free (limited); full version requires academic/commercial license.
- **License:** CC BY-NC 4.0 (open subset); restrictive for full version.
- **Limitations:** Open subset lacks many features; full version expensive for commercial use.


### **DrugCentral** (Must-Have, MVP - DrugBank alternative)

- **URL:** https://drugcentral.org/
- **Contents:** 15K+ active pharmaceutical ingredients with indications, contraindications, adverse events, drug-target interactions, FDA labels, ATC codes. Integrates FDA, EMA, and literature sources.[^4][^5]
- **Why useful:** Open alternative to DrugBank; includes drug-drug interactions, contraindications, and adverse effects extracted from labels and literature.[^4]
- **Access:** Full PostgreSQL dump available; public instance at `drugcentral:unmtid-dbs.net:5433`.[^6][^4]
- **License:** CC BY 4.0 (academic/commercial use allowed with attribution).
- **Limitations:** Less curated than DrugBank; may require additional cleaning.

***

## 2. Clinical Guidelines

### **NICE Guidelines** (Must-Have, MVP)

- **URL:** https://www.nice.org.uk/guidance
- **Contents:** 1,500+ evidence-based clinical guidelines covering diagnosis, treatment, and care pathways for UK NHS.
- **Why useful:** High-quality, structured guidelines for common conditions; includes algorithms and care pathways.
- **Access:** Bulk download via Syndication API (requires application); individual PDFs available without credentials.[^7][^8][^9]
- **License:** CC BY-NC-ND 4.0 (non-commercial); API requires license agreement.[^7]
- **Limitations:** UK-focused; API access restricted to organizations (not individuals).[^9]


### **WHO Guidelines** (Must-Have, MVP)

- **URL:** https://www.who.int/publications; https://iris.who.int/
- **Contents:** Global clinical guidelines on infectious diseases, NCDs, maternal health, mental health, and emergency response.
- **Why useful:** Internationally applicable guidance; essential for infectious disease and public health recommendations.[^10][^7]
- **Access:** IRIS repository (https://iris.who.int/) provides free PDF downloads; no API.[^10][^7]
- **License:** CC BY-NC-SA 3.0 IGO (most documents).[^11]
- **Limitations:** No structured API; manual scraping or periodic downloads required.


### **CDC Clinical Guidelines** (Must-Have, MVP)

- **URL:** https://www.cdc.gov/guidelines/index.html
- **Contents:** US-focused guidelines on infectious diseases, immunizations, STIs, TB, HIV, travel health, and outbreak response.
- **Why useful:** Authoritative US public health guidance; frequently updated.
- **Access:** Individual PDF/HTML pages; no bulk API.
- **License:** Public domain (US government work).
- **Limitations:** No structured API; US-centric.


### **openFDA Drug Labels** (Must-Have, MVP)

- **URL:** https://open.fda.gov/apis/drug/label/
- **Contents:** Structured product labels (SPLs) for FDA-approved drugs including indications, contraindications, warnings, adverse reactions, drug interactions, dosing.[^12][^13][^14]
- **Why useful:** Authoritative drug safety information; essential for contraindication and adverse effect retrieval.[^15][^16]
- **Access:** REST API (https://api.fda.gov/drug/label.json); bulk download (23GB compressed) available.[^17][^12]
- **License:** Public domain.
- **Limitations:** Large dataset; requires parsing SPL XML structure.


### **IDSA Guidelines** (Useful, Phase 2)

- **URL:** https://www.idsociety.org/practice-guideline/practice-guidelines/
- **Contents:** Infectious disease treatment guidelines (HIV, hepatitis, sepsis, antimicrobial stewardship, tropical diseases).
- **Why useful:** Specialist-level guidance on complex infections; complements CDC guidelines.
- **Access:** Individual PDFs; no bulk API.
- **License:** Free for personal/educational use; commercial use requires permission.
- **Limitations:** No structured API; manual collection required.


### **ACC/AHA Guidelines** (Useful, Phase 2)

- **URL:** https://www.acc.org/guidelines; https://professional.heart.org/guidelines
- **Contents:** Cardiology guidelines on hypertension, heart failure, arrhythmias, ACS, lipid management, valvular disease.[^18]
- **Why useful:** Authoritative cardiovascular guidance; essential for cardiology-related queries.
- **Access:** Individual PDFs; some require free account registration.
- **License:** Free for personal/educational use; commercial use restricted.
- **Limitations:** No bulk API; US-centric.


### **ADA Standards of Care in Diabetes** (Useful, Phase 2)

- **URL:** https://professional.diabetes.org/standards-of-care
- **Contents:** Annual comprehensive diabetes care guidelines covering screening, diagnosis, pharmacotherapy, complications, and special populations.[^19][^20][^21]
- **Why useful:** Gold standard for diabetes management; updated annually.
- **Access:** Full PDF via professional.diabetes.org (free account); abridged versions in PMC.[^21][^19]
- **License:** Free for personal/educational use.
- **Limitations:** Annual updates require re-download.


### **GINA Asthma Guidelines** (Useful, Phase 2)

- **URL:** https://ginasthma.org/reports/
- **Contents:** Global asthma management strategy with stepwise treatment algorithms, diagnosis, and acute management.[^22][^23][^24]
- **Why useful:** Internationally recognized asthma guidance; free for personal use.[^24]
- **Access:** Free PDF download from website (personal use only).[^25][^24]
- **License:** Copyrighted; free for personal/educational use.[^25]
- **Limitations:** No API; manual download.


### **GOLD COPD Guidelines** (Useful, Phase 2)

- **URL:** https://goldcopd.org/gold-reports/
- **Contents:** Global COPD diagnosis, management, and prevention strategy with assessment tools and treatment algorithms.
- **Why useful:** Standard reference for COPD care.
- **Access:** Free PDF download (registration required).
- **License:** Copyrighted; free for personal/educational use.
- **Limitations:** No API; annual updates.


### **Additional Guideline Repositories** (Optional, Phase 3)

- **ECRI Guidelines Trust:** https://guidelines.ecri.org/ (US guidelines, free registration)
- **Guidelines International Network (G-I-N):** https://g-i-n.net/ (global repository)
- **TRIP Database:** https://www.tripdatabase.com/ (search engine for guidelines and evidence)

***

## 3. PubMed/Literature Corpora

### **PubMed Abstracts** (Must-Have, MVP)

- **URL:** https://pubmed.ncbi.nlm.nih.gov/download/
- **Contents:** 37M+ biomedical citations and abstracts from MEDLINE and other sources.[^26]
- **Why useful:** Core literature corpus for evidence retrieval; covers all major biomedical topics.
- **Access:**
    - **Bulk download:** FTP servers (baseline files updated daily; ~30GB compressed).[^26]
    - **API:** E-Utilities (https://eutils.ncbi.nlm.nih.gov/epubmed/) with rate limits (10 requests/second without API key).[^26]
- **License:** Public domain (citations/abstracts); full text may be copyrighted.
- **Limitations:** Abstracts only (no full text); requires parsing XML format.


### **PubMed Central Open Access Subset** (Must-Have, MVP)

- **URL:** https://pmc.ncbi.nlm.nih.gov/tools/openftlist/
- **Contents:** 3.2M+ full-text open-access articles with CC licenses allowing text mining and reuse.[^27][^28]
- **Why useful:** Full-text content for deeper evidence extraction; includes methods, results, and discussion sections.[^29][^30]
- **Access:**
    - **FTP:** https://ftp.ncbi.nlm.nih.gov/pub/pmc/ (organized by license type).[^31][^27]
    - **API:** PMC OA Web Service (https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi); BioC API; OAI-PMH.[^32][^33][^27]
    - **Cloud:** AWS RODA (https://www.ncbi.nlm.nih.gov/pmc/tools/pmcaws/).[^28]
- **License:** Varies by article (CC BY, CC BY-NC, CC0, etc.); check license before use.[^27]
- **Limitations:** Only OA articles (not all PubMed content); license restrictions on commercial use for some articles.[^31]


### **Europe PMC** (Useful, Phase 2)

- **URL:** https://europepmc.org/developers
- **Contents:** 6.4M+ full-text articles (includes PMC OA plus additional OA content); 37.8M+ abstracts.[^34]
- **Why useful:** Larger OA corpus than PMC alone; includes preprints and non-English articles.
- **Access:** REST/SOAP APIs; bulk download of OA subset and metadata.[^34]
- **License:** Varies by article (check individual licenses).
- **Limitations:** API rate limits; some content overlaps with PMC.


### **BioC PMC** (Optional, Phase 3)

- **URL:** https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/
- **Contents:** PMC OA articles in BioC XML/JSON format with pre-computed entity annotations (genes, diseases, chemicals, species).[^33][^35]
- **Why useful:** Pre-annotated entities reduce NER workload; useful for relation extraction.
- **Access:** FTP (https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC); REST API.[^33]
- **License:** Same as underlying PMC OA articles.
- **Limitations:** Annotations may have errors; requires BioC parser.


### **PubTator Central** (Optional, Phase 3)

- **URL:** https://www.ncbi.nlm.nih.gov/research/pubtator/
- **Contents:** PMC OA and PubMed abstracts with automated bioconcept annotations (genes, diseases, chemicals, variants, species, cell lines).[^35]
- **Why useful:** Pre-extracted entity mentions with UMLS/MeSH mappings; accelerates KG construction.
- **Access:** Bulk FTP download; REST API; web interface.[^35]
- **License:** Same as underlying articles.
- **Limitations:** Annotations are automated (not manually curated).

***

## 4. Drug Safety Datasets

### **openFDA Adverse Events (FAERS)** (Must-Have, MVP)

- **URL:** https://open.fda.gov/apis/drug/event/
- **Contents:** 10M+ adverse event reports submitted to FDA (2004–present) including drug names, reactions, outcomes, patient demographics.[^13][^14][^36]
- **Why useful:** Real-world drug safety signals; complements label-based contraindications.[^37][^38]
- **Access:** REST API; bulk quarterly downloads (https://fis.fda.gov/extensions/ads-dqfaers/ads-dqfaers.html).[^36][^17]
- **License:** Public domain.
- **Limitations:** Voluntary reporting (underreporting bias); requires deduplication and normalization.


### **SIDER (Side Effect Resource)** (Useful, Phase 2)

- **URL:** http://sideeffects.embl.de/
- **Contents:** 4K+ drugs with 100K+ adverse drug reactions (ADRs) extracted from drug labels; includes MedDRA and PubChem IDs.[^39]
- **Why useful:** Structured drug-side effect pairs; useful for ADR prediction and validation.
- **Access:** Bulk download (text files) from website.[^39]
- **License:** CC BY 4.0.
- **Limitations:** Last major update was 2016 (SIDER 4); may be outdated.


### **DrugCentral** (Must-Have, MVP)

- **URL:** https://drugcentral.org/download
- **Contents:** Drug indications, contraindications, adverse events, drug-target interactions, FDA labels, ATC codes.[^6][^4]
- **Why useful:** Integrated drug safety data from multiple sources; open alternative to DrugBank.[^4]
- **Access:** PostgreSQL dump; public SQL instance.[^6][^4]
- **License:** CC BY 4.0.
- **Limitations:** Requires PostgreSQL setup.


### **ChEMBL Drug Safety** (Optional, Phase 3)

- **URL:** https://www.ebi.ac.uk/chembl/
- **Contents:** Curated drug safety data including boxed warnings, withdrawn drugs, and toxicity classes.[^40]
- **Why useful:** Additional safety annotations; integrates with bioactivity data.
- **Access:** Bulk download (MySQL, SDF); REST API.
- **License:** CC BY 4.0.
- **Limitations:** Focused on marketed drugs; smaller than DrugCentral.


### **pAERS (Pharmacovigilance AERS)** (Optional, Phase 3)

- **URL:** https://www.nature.com/articles/s41598-019-56525-5
- **Contents:** 77K+ drug-drug interaction-associated adverse events derived from FAERS using likelihood ratio testing.[^37]
- **Why useful:** DDI-specific ADRs not in labels; complements FAERS raw data.
- **Access:** Supplementary data from publication.
- **License:** CC BY 4.0 (Nature Scientific Reports).
- **Limitations:** Static dataset (not updated); derived from older FAERS data.

***

## 5. Clinical Case/Note Datasets

### **MIMIC-IV** (Must-Have, Phase 2 for research)

- **URL:** https://physionet.org/content/mimiciv/
- **Contents:** 40K+ ICU admissions with structured data (demographics, vitals, labs, medications, diagnoses) from Beth Israel Deaconess Medical Center (2008–2019).
- **Why useful:** Realistic patient trajectories for case-based reasoning; gold standard for clinical NLP research.
- **Access:** Credentialed access via PhysioNet (CITI training + DUA required).[^41][^42][^43]
- **License:** PhysioNet Credentialed Health Data License 1.5.0 (research use only).[^41]
- **Limitations:** Requires credentialing (1–2 weeks); ICU-only (not general medicine); US-centric.


### **MIMIC-IV-Note** (Must-Have, Phase 2 for research)

- **URL:** https://physionet.org/content/mimic-iv-note/2.2/
- **Contents:** 331K+ deidentified discharge summaries and radiology reports linked to MIMIC-IV patients.[^43][^41]
- **Why useful:** Free-text clinical notes for NLP tasks (entity extraction, summarization, QA); essential for note-based retrieval.
- **Access:** Same credentialing as MIMIC-IV (separate DUA).[^43][^41]
- **License:** PhysioNet Credentialed Health Data License 1.5.0.[^41]
- **Limitations:** Requires MIMIC-IV access; discharge summaries only (no progress notes).


### **MIMIC-CXR** (Optional, Phase 3)

- **URL:** https://physionet.org/content/mimic-cxr/
- **Contents:** 377K+ chest X-ray images with structured reports and findings.
- **Why useful:** Radiology-specific cases; useful for imaging-related queries.
- **Access:** Credentialed PhysioNet access (separate DUA).
- **License:** PhysioNet Credentialed Health Data License 1.5.0.
- **Limitations:** Radiology-only; requires image storage.


### **Synthetic Clinical Notes** (Useful, MVP alternative)

- **URL:**
    - **Synthea:** https://github.com/synthetichealth/synthea (synthetic EHRs with notes)
    - **MedSynth:** https://github.com/uf-hobi-informatics-lab/MedSynth (synthetic clinical narratives)
- **Contents:** Artificially generated patient records with realistic clinical language, diagnoses, and treatments.
- **Why useful:** No credentialing required; useful for prototyping and testing before MIMIC access.
- **Access:** GitHub download; no credentials.
- **License:** Apache 2.0 (Synthea); MIT (MedSynth).
- **Limitations:** Synthetic (not real patient data); may lack realism.


### **Public Case Reports** (Optional, Phase 3)

- **URL:**
    - **PubMed Central:** Search "case reports" in PMC OA subset
    - **Journal of Medical Case Reports:** https://jmedicalcasereports.biomedcentral.com/
    - **Cureus:** https://www.cureus.com/
- **Contents:** Published clinical case reports with detailed patient presentations, workups, and outcomes.
- **Why useful:** Rare disease examples; educational cases for QA evaluation.
- **Access:** Individual article downloads; no bulk API.
- **License:** Varies by journal (many CC BY).
- **Limitations:** Unstructured; manual curation required.

***

## 6. Evaluation Datasets

### **MedQA** (You have this)

- **URL:** https://github.com/jind11/MedQA
- **Contents:** 10K+ USMLE-style questions (4–5 options) covering basic sciences and clinical knowledge.
- **Why useful:** Standard medical QA benchmark; widely used in literature.
- **Access:** GitHub (JSON format).
- **License:** MIT.
- **Limitations:** Multiple-choice only; no explanations.


### **PubMedQA** (You have this)

- **URL:** https://github.com/pubmedqa/pubmedqa
- **Contents:** 1K+ yes/no/maybe questions derived from PubMed abstract titles with expert annotations.[^44]
- **Why useful:** Research question answering; tests evidence-based reasoning.
- **Access:** GitHub (JSON format).
- **License:** MIT.
- **Limitations:** Small dataset; binary/ternary answers only.


### **MedMCQA** (Must-Have, MVP)

- **URL:** https://medmcqa.github.io/; https://huggingface.co/datasets/medmcqa
- **Contents:** 194K+ AIIMS/NEET PG entrance exam MCQs covering 2.4K healthcare topics and 21 medical subjects.[^45][^46][^47]
- **Why useful:** Large-scale Indian medical entrance exam questions; diverse topics; includes explanations.
- **Access:** Hugging Face (Apache 2.0); GitHub.[^46][^45]
- **License:** CC BY-SA 4.0.[^46]
- **Limitations:** Indian exam focus (may differ from US guidelines); multiple-choice only.


### **BioASQ** (Must-Have, Phase 2)

- **URL:** https://bioasq.org/; https://zenodo.org/records/7655130
- **Contents:** Manually curated biomedical QA benchmark with factoid, list, yes/no, and summary questions; includes gold-standard answers and supporting documents.[^48][^49][^50]
- **Why useful:** Expert-curated questions; includes ideal answers (summaries); used in annual competitions since 2012.[^50][^51]
- **Access:** Zenodo (training/test JSON files); API for evaluation.[^49]
- **License:** CC BY 4.0.[^49]
- **Limitations:** Smaller than MedMCQA (10K+ questions); requires registration for test set.


### **MedNLI** (Useful, Phase 2)

- **URL:** https://huggingface.co/datasets/bigbio/mednli
- **Contents:** 14K+ sentence pairs from MIMIC-III notes annotated for entailment (entailment, contradiction, neutral) by physicians.[^52][^53]
- **Why useful:** Clinical NLI benchmark; tests reasoning over clinical notes.
- **Access:** Hugging Face (bigbio/mednli).[^53][^54]
- **License:** PhysioNet license (requires MIMIC credentialing for original notes).
- **Limitations:** Derived from MIMIC (credentialing may be required); NLI task only.


### **MedHALT** (Useful, Phase 2)

- **URL:** https://github.com/medhalt/medhalt
- **Contents:** Medical hallucination detection benchmark with factually incorrect statements about diseases, drugs, and treatments.
- **Why useful:** Evaluates model hallucination in medical contexts; critical for CDSS safety.
- **Access:** GitHub.
- **License:** MIT (assumed; check repository).
- **Limitations:** Newer dataset (less benchmarked).


### **MMLU Medical Subsets** (Useful, Phase 2)

- **URL:** https://huggingface.co/datasets/cais/mmlu
- **Contents:** 15K+ multiple-choice questions across 57 subjects; medical subsets include clinical knowledge, college medicine, medical genetics, anatomy, nutrition, professional medicine.[^55][^56]
- **Why useful:** Broad medical knowledge benchmark; includes professional-level questions.
- **Access:** Hugging Face (cais/mmlu).
- **License:** MIT.
- **Limitations:** Mixed quality (some questions outdated); general knowledge focus.


### **MMLU-Pro (Health Subset)** (Optional, Phase 3)

- **URL:** https://huggingface.co/datasets/MLCommons/mmlu_pro
- **Contents:** Professional-level health questions (clinical knowledge, medicine, anatomy, nutrition) with 10 options each.[^55]
- **Why useful:** More challenging than MMLU; tests expert-level reasoning.
- **Access:** Hugging Face.
- **License:** CC BY 4.0.
- **Limitations:** Smaller health subset (~500 questions).


### **RealMedQA** (Optional, Phase 3)

- **URL:** https://arxiv.org/abs/2408.08624
- **Contents:** Realistic clinical questions from medical forums (e.g., HealthTap, WebMD) with ideal answers.[^57]
- **Why useful:** Patient-facing questions (not exam-style); tests real-world clinical reasoning.
- **Access:** GitHub (paper repository).
- **License:** CC BY 4.0 (assumed).
- **Limitations:** Newer dataset (less benchmarked).


### **MedAgentsBench** (Optional, Phase 3)

- **URL:** https://github.com/gersteinlab/medagents-benchmark
- **Contents:** Multi-agent medical QA benchmark with hard/filtered MedQA, MMLU health subsets.[^55]
- **Why useful:** Specifically designed for multi-agent medical systems; includes reasoning traces.
- **Access:** Hugging Face (super-dainiu/medagents-benchmark).[^55]
- **License:** MIT (assumed).
- **Limitations:** Newer dataset.


### **NLI4CT / SemEval Clinical NLI Tasks** (Optional, Phase 3)

- **URL:** https://aclanthology.org/2023.emnlp-main.1041.pdf; https://arxiv.org/abs/2305.02993
- **Contents:** Multi-evidence NLI over clinical trial reports; tests causal and interventional reasoning.[^58][^59][^60][^61]
- **Why useful:** Advanced clinical reasoning benchmark; evidence-based inference.
- **Access:** GitHub (task repositories).
- **License:** Varies (check specific task).
- **Limitations:** Specialized task (clinical trials only).

***

## Minimal Dataset Collection Plan

### **MVP Data Required Before Coding** (Week 1–2)

These datasets are essential for building a functional prototype:

1. **UMLS Metathesaurus** – Entity normalization backbone (apply for license immediately; 5-day approval).[^1]
2. **RxNorm** – Drug normalization (included in UMLS; also available via API).[^2]
3. **DrugCentral** – Drug safety, interactions, contraindications (PostgreSQL dump).[^4][^6]
4. **openFDA Drug Labels** – Authoritative drug indications, warnings, ADRs (API or bulk download).[^12][^17]
5. **PubMed Abstracts** – Literature corpus (FTP baseline files).[^26]
6. **PMC Open Access Subset** – Full-text OA articles (FTP or AWS).[^28][^27]
7. **MedMCQA** – Large-scale QA evaluation (Hugging Face).[^45][^46]
8. **Synthea or MedSynth** – Synthetic clinical notes for prototyping (no credentialing). [GitHub]
9. **WHO/CDC/NICE Guidelines** – Core guideline PDFs (manual download).[^7][^10]

**Total:** ~50–100GB storage; 1–2 weeks for downloads and UMLS license approval.

### **Phase 2: Add After First Prototype** (Week 3–6)

Enhance retrieval and reasoning capabilities:

1. **MIMIC-IV + MIMIC-IV-Note** – Real clinical notes (start credentialing early; 1–2 weeks).[^42][^43][^41]
2. **BioASQ** – Expert-curated QA benchmark (Zenodo).[^50][^49]
3. **MedNLI** – Clinical NLI evaluation (Hugging Face).[^53]
4. **SIDER** – Drug-side effect pairs (bulk download).[^39]
5. **HPO + MONDO** – Phenotype and disease ontologies (GitHub/website).
6. **ACC/AHA, ADA, GINA, GOLD Guidelines** – Specialty-specific guidance (manual PDFs).[^23][^18][^19][^22]
7. **openFDA FAERS** – Adverse event reports (quarterly bulk files).[^17][^36]
8. **MMLU Medical Subsets** – Additional QA benchmark (Hugging Face).[^56][^55]

**Total:** ~200–300GB additional storage; MIMIC credentialing is the bottleneck.

### **Phase 3: Research Paper/Demo Enhancement** (Month 2+)

For stronger evaluation and publication-quality results:

1. **BioC PMC / PubTator Central** – Pre-annotated entities (FTP).[^33][^35]
2. **MedHALT** – Hallucination detection benchmark (GitHub).
3. **RealMedQA** – Realistic patient questions (arXiv/GitHub).[^57]
4. **MIMIC-CXR** – Radiology cases (if imaging is relevant).
5. **ChEMBL Drug Safety** – Additional safety annotations (EBI).[^40]
6. **NLI4CT / SemEval Clinical NLI** – Advanced reasoning benchmarks.[^61][^58]
7. **MedAgentsBench** – Multi-agent specific benchmark (Hugging Face).[^55]
8. **Full DrugBank** – If academic license is affordable (otherwise use DrugCentral).

***

## Key Recommendations

1. **Start UMLS license application immediately** – This is the longest lead-time item (5 business days).[^1]
2. **Use DrugCentral instead of DrugBank** – Fully open (CC BY 4.0) with comparable drug safety data; avoids DrugBank's restrictive licensing.[^6][^4]
3. **Prioritize PMC OA Subset over full PubMed** – Full-text OA articles are more valuable for RAG than abstracts alone; respect license restrictions.[^27][^31]
4. **Apply for MIMIC credentialing in parallel** – Even if not using immediately, having access unlocks MIMIC-IV-Note, MedNLI, and other PhysioNet resources.[^42][^43]
5. **Use MedMCQA + BioASQ as primary QA benchmarks** – Large-scale (MedMCQA) + expert-curated (BioASQ) provides comprehensive evaluation.[^46][^49][^50]
6. **Respect guideline licenses** – NICE requires API license for commercial use; WHO/CDC are public domain or CC BY-NC.[^9][^7]
7. **Document all licenses** – Create a spreadsheet tracking license terms (commercial use, attribution, share-alike) for each dataset.

This plan provides a balanced approach: MVP datasets enable rapid prototyping within 2 weeks, while Phase 2/3 additions strengthen research contributions and demo quality.
<span style="display:none">[^100][^101][^102][^103][^104][^105][^106][^107][^108][^109][^110][^111][^112][^113][^114][^115][^116][^117][^118][^119][^120][^121][^122][^123][^124][^125][^126][^127][^128][^129][^130][^131][^132][^133][^134][^135][^136][^137][^138][^139][^140][^141][^142][^143][^144][^145][^146][^147][^148][^149][^150][^151][^152][^153][^154][^155][^156][^157][^158][^159][^160][^161][^162][^163][^164][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93][^94][^95][^96][^97][^98][^99]</span>

<div align="center">⁂</div>

[^1]: https://www.nlm.nih.gov/databases/umls.html

[^2]: https://uts.nlm.nih.gov/uts/umls/home

[^3]: https://support.nlm.nih.gov/knowledgebase/article/KA-04087/en-us

[^4]: https://academic.oup.com/nar/article/51/D1/D1276/6885038

[^5]: https://drugcentral.org/

[^6]: https://drugcentral.org/download

[^7]: https://iris.who.int/home

[^8]: https://www.nice.org.uk/corporate/ecd10

[^9]: https://www.nice.org.uk/reusing-our-content/nice-syndication-api/nice-syndication-api-application-form

[^10]: https://www.who.int/publications/digital

[^11]: https://iris.who.int/items/a27cb0aa-a51c-43e3-9647-099dcddaee94

[^12]: https://open.fda.gov/apis/drug/label/

[^13]: https://open.fda.gov/apis/drug/

[^14]: https://open.fda.gov/data/

[^15]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3646673/

[^16]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12098182/

[^17]: https://open.fda.gov/about/updates/2015_12_23_direct_downloads/

[^18]: https://www.ahajournals.org/doi/10.1161/CIR.0000000000001383

[^19]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12018997/

[^20]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10725799/

[^21]: https://professional.diabetes.org/standards-of-care

[^22]: https://ginasthma.org/wp-content/uploads/2025/11/GINA-Summary-Guide-2025-WEB_FINAL-WMS.pdf

[^23]: https://ginasthma.org/reports/

[^24]: https://ginasthma.org/

[^25]: https://ginasthma.org/2024-report/

[^26]: https://pubmed.ncbi.nlm.nih.gov/download/

[^27]: https://pmc.ncbi.nlm.nih.gov/tools/openftlist/

[^28]: https://catalog.data.gov/dataset/pubmed-central-open-access-subset-pmc-oa

[^29]: https://academic.oup.com/bioinformaticsadvances/article/doi/10.1093/bioadv/vbag058/8488726

[^30]: http://biorxiv.org/lookup/doi/10.64898/2026.05.16.725623

[^31]: https://support.nlm.nih.gov/kbArticle/?pn=KA-03263

[^32]: https://pmc.ncbi.nlm.nih.gov/tools/oa-service/

[^33]: https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/

[^34]: https://europepmc.org/developers

[^35]: https://dl.acm.org/doi/10.1145/3307339.3343246

[^36]: https://open.fda.gov/apis/drug/event/

[^37]: https://www.nature.com/articles/s41598-019-56525-5

[^38]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4915658/

[^39]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4702794/

[^40]: https://pubs.acs.org/doi/pdf/10.1021/acs.chemrestox.0c00296

[^41]: https://physionet.org/content/mimic-iv-note/2.2/

[^42]: https://mimic.mit.edu/docs/faq/how-to-get-access.html

[^43]: https://www.physionet.org/content/mimic-iv-note/2.2/

[^44]: https://arxiv.org/abs/1909.06146

[^45]: https://huggingface.co/datasets/ekacare/MedMCQA-Indic

[^46]: https://huggingface.co/datasets/araag2/MedMCQA

[^47]: https://huggingface.co/papers/2203.14371

[^48]: https://www.nature.com/articles/s41597-023-02068-4.pdf

[^49]: https://zenodo.org/records/7655130

[^50]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10042099/

[^51]: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-015-0564-6

[^52]: https://www.aclweb.org/anthology/D18-1187.pdf

[^53]: https://huggingface.co/datasets/bigbio/mednli

[^54]: https://huggingface.co/datasets/tmnam20/MedNLI

[^55]: https://github.com/gersteinlab/medagents-benchmark

[^56]: https://huggingface.co/datasets/openlifescienceai/mmlu_medical_genetics

[^57]: https://arxiv.org/abs/2408.08624

[^58]: https://arxiv.org/abs/2305.02993

[^59]: https://aclanthology.org/2023.semeval-1.307.pdf

[^60]: https://arxiv.org/abs/2404.04963

[^61]: https://aclanthology.org/2023.emnlp-main.1041.pdf

[^62]: https://pmc.ncbi.nlm.nih.gov/about/userguide/

[^63]: https://linkinghub.elsevier.com/retrieve/pii/S2352647517300527

[^64]: https://www.nature.com/articles/s41421-020-00208-3

[^65]: https://www.semanticscholar.org/paper/052c3d71ce40e5fb77afb015bfdc81e56b28c8f3

[^66]: http://jmla.pitt.edu/ojs/jmla/article/view/758

[^67]: https://www.nature.com/articles/s41421-020-00206-5

[^68]: https://academic.oup.com/bioinformatics/article/28/16/2154/323694

[^69]: https://www.ajronline.org/doi/10.2214/AJR.15.15725

[^70]: https://academic.oup.com/jamia/article/23/3/596/2908999

[^71]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4901374/

[^72]: https://pmc.ncbi.nlm.nih.gov/articles/PMC6323925/

[^73]: https://open.fda.gov/apis/drug/label/searchable-fields/

[^74]: https://pmc.ncbi.nlm.nih.gov/articles/PMC5789866/

[^75]: https://open.fda.gov/apis/try-the-api/

[^76]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7419351/

[^77]: https://open.fda.gov/apis/

[^78]: https://open.fda.gov/apis/drug/event/example-api-queries/

[^79]: https://pmc.ncbi.nlm.nih.gov/articles/PMC6419320/

[^80]: https://ieeexplore.ieee.org/document/11429214/

[^81]: https://ieeexplore.ieee.org/document/11340582/

[^82]: https://arxiv.org/abs/2512.10996

[^83]: https://www.nlm.nih.gov/research/umls/index.html

[^84]: https://arxiv.org/abs/2604.16422

[^85]: https://huggingface.co/datasets/RikoteMaster/medmcqa-mcqa/tree/main

[^86]: https://ieeexplore.ieee.org/document/10466121/

[^87]: https://academic.oup.com/bioinformatics/article/35/20/4129/5384491

[^88]: https://huggingface.co/datasets/HPAI-BSC/Medprompt-MedMCQA-ToT

[^89]: https://huggingface.co/collections/lavita/medical-qa-datasets

[^90]: https://extranet.who.int/mindbank/collection/who

[^91]: https://morepress.unizd.hr/journals/index.php/pubmet/article/view/3922

[^92]: https://extranet.who.int/ncdccs/documents/Db

[^93]: https://www.semanticscholar.org/paper/fbf53f7395f7be7340faa0326d8a185b65b873de

[^94]: https://www.semanticscholar.org/paper/078095be6623320d4eed68b46d0660aa5e854722

[^95]: https://academic.oup.com/bioinformatics/article/19/18/2404/194440

[^96]: https://extranet.who.int/ncdccs/documents/

[^97]: https://www.tandfonline.com/doi/full/10.1080/20445911.2019.1573463

[^98]: https://www.semanticscholar.org/paper/cb15ab0f1093e11325baaa67767a653ad515367b

[^99]: https://www.nice.org.uk/reusing-our-content/nice-syndication-api

[^100]: http://annals.org/data/journals/aim/20232/0000605-201106070-00007.pdf

[^101]: https://www.medrxiv.org/content/medrxiv/early/2021/06/14/2021.06.11.21258749.full.pdf

[^102]: https://pmc.ncbi.nlm.nih.gov/articles/PMC1997259/

[^103]: https://www.nice.org.uk/corporate/ecd10/chapter/using-your-api-key-to-explore-nice-content

[^104]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4067507/

[^105]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10725809/

[^106]: https://pubmed.ncbi.nlm.nih.gov/38078589/

[^107]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9810461/

[^108]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4714725/

[^109]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9810463/

[^110]: https://ginasthma.org/wp-content/uploads/2023/09/GINA-Severe-Asthma-Guide-2023-WEB-WMS.pdf

[^111]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9810458/

[^112]: https://pmc.ncbi.nlm.nih.gov/articles/PMC5241768/

[^113]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9845083/

[^114]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4398006/

[^115]: https://www.nursingcenter.com/getattachment/Clinical-Resources/Guideline-Summaries/Diabetes/Guideline-Summary_Diabetes-mellitus_ADA-Standards_2024.pdf.aspx

[^116]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8865785/

[^117]: https://aclanthology.org/anthology-files/anthology-files/pdf/lrec/2024.lrec-main.428.pdf

[^118]: https://archive.physionet.org/physiotools/mimic-code/mednli/

[^119]: https://www.aclweb.org/anthology/D19-1631.pdf

[^120]: https://arxiv.org/pdf/2504.08596.pdf

[^121]: https://physionet.org/content/mimiciv/view-dua/1.0/

[^122]: https://aclanthology.org/2021.acl-short.129.pdf

[^123]: https://arxiv.org/abs/2205.12689

[^124]: https://huggingface.co/datasets/GM07/medhal/resolve/main/README.md?download=true

[^125]: https://aclanthology.org/2022.findings-emnlp.374.pdf

[^126]: https://github.com/MIT-LCP/mimic-iv-website/blob/master/content/about/access.md

[^127]: https://aclanthology.org/2021.emnlp-demo.21.pdf

[^128]: https://aclanthology.org/2024.cl4health-1.20.pdf

[^129]: https://pmc.ncbi.nlm.nih.gov/articles/PMC2850250/

[^130]: https://www.mdpi.com/1999-5903/12/11/199/pdf

[^131]: https://pmc.ncbi.nlm.nih.gov/articles/PMC6537875/

[^132]: https://www.nlm.nih.gov/healthit/snomedct/index.html

[^133]: https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/mapping_projects/index.html

[^134]: https://www.nlm.nih.gov/research/umls/licensedcontent/downloads.html

[^135]: https://www.nlm.nih.gov/research/umls/mapping_projects/snomedct_to_icd10cm.html

[^136]: https://www.nlm.nih.gov/research/umls/pdf/snomed_users.pdf

[^137]: https://documentation.uts.nlm.nih.gov/automating-downloads.html

[^138]: https://ngdc.cncb.ac.cn/databasecommons/database/id/1762

[^139]: https://arxiv.org/html/2602.19183v1

[^140]: https://www.semanticscholar.org/paper/The-SIDER-database-of-drugs-and-side-effects-Kuhn-Letunic/c1e62b537f3d30018e7979a89b0e0f15e2b6eecc

[^141]: http://sideeffects.embl.de/

[^142]: https://docs.drugbank.com/

[^143]: https://learn.microsoft.com/en-us/connectors/openfdadrugip/

[^144]: https://www.fda.gov/science-research/health-informatics-fda/openfda

[^145]: https://mimic.mit.edu/docs/gettingstarted/

[^146]: https://agent-commerce.store/api/openfda

[^147]: https://apis.io/providers/open-fda/

[^148]: https://huggingface.co/datasets/bigbio/med_qa

[^149]: https://github.com/drqiaojin/biomedical-qa-datasets

[^150]: https://huggingface.co/supergoose/medmcqa

[^151]: https://bioasq.org/participate/useful_resources

[^152]: https://www.nice.org.uk/Media/Default/About/what-we-do/Syndication/syndication-and-API-guide.pdf

[^153]: https://bigg.bvsalud.org/en/home-en/

[^154]: https://opendata.paho.org/en/sdg3/evidence-for-action/who-and-paho-guidelines

[^155]: https://www.acc.org/-/media/Non-Clinical/Files-PDFs-Excel-MS-Word-etc/Guidelines/About-Guidelines-and-Clinical-Documents/Methodology/2014/Methodology-Practice-Guidelines.pdf

[^156]: https://www.acc.org/guidelines

[^157]: https://assets.ctfassets.net/07cwnclyy106/6V5Y7mV4uNStU8VkM4yctt/11a80fc78c5e2bc4e1ea7b7e67ed1813/EGT-919.v8_Download.pdf

[^158]: https://aladlatam.org/wp-content/uploads/2024/01/standards-of-care-2024.pdf

[^159]: https://assets.ctfassets.net/07cwnclyy106/1eqcni0WyQkynykmsUZNRZ/cc88c87ba82a97b65742ef2dd2aef2c3/EGT-913.v6_Download.pdf

[^160]: https://github.com/jgc128/mednli

[^161]: https://huggingface.co/collections/Tonic/medical-evaluation-datasets

[^162]: https://huggingface.co/pritamdeka/PubMedBERT-MNLI-MedNLI

[^163]: https://medhalt.github.io/

[^164]: https://casrai.org/guides/physionet-credentialed-access-restricted-data

