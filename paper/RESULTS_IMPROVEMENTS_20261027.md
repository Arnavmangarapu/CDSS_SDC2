# First results improvement pass

Completed on 27 October 2026. Source checkpoint: `81f3887` (`CDSM before results improvement`). Both databases were cold-copied, restored into separate containers and inventory-verified before changes. Original containers and volumes remain stopped and unchanged; full archives and restoration instructions are in `local_backups/before-results-improvement-20261027/`.

## Chang applied
candidate s
- Imported positive and negative HPO phenotype–disease associations into a distinct `ClinicalEntity` schema keyed by global PrimeKG node index, with reverse edges deduplicated. Negative associations lower cores instead of supporesting a disease.
- Restricted entity linking to the relevant vocabulary: HPO for symptoms, MONDO for conditions, and drug vocabulary for medicines/allergens.
- Built a new collection from the complete First Aid and Pathoma files: 1,134 passages instead of 156. Existing textbook and authoritative-source collections are preserved.
- Excluded the 17,109-passage `medical_literature` collection after inspection found 384-dimensional embeddings and exam question/answer payloads. It is not a clean replacement for the 768-dimensional textbook index.
- Retrieve 20 textbook candidates and rerank to five with the revision-pinned `cross-encoder/ms-marco-MiniLM-L-6-v2`. Merge guideline and label results by relevance instead of putting all guidelines first.
- Route the hypertension/amlodipine sources to cases within their scope. A normal BP reading in an unrelated case no longer triggers the entire narrow source corpus.
- Preserve longer evidence passages under a bounded prompt budget; reserve separate space for graph and textbook evidence so graph matches cannot crowd out all text.
- Supply a JSON Schema for Gemini synthesis, omit reasoning-only parts from response JSON, and retain independent client validation and clinical verification gates.
- Correct unknown-allergy phrases so missing documentation cannot become an asserted allergen.

## Diagnosis agreement on the same 36 MedQA vignettes

Both runs requested Gemini Flash Lite (`gemini-3.5-flash-lite`) at temperature zero, no provider fallback and no adaptive retrieval retries. Vignette choices and answer keys were withheld from inference. Exact normalized aliases and all 36 cases remain in each denominator. The new run evaluates the combined changes; it does not isolate individual contributions. Provider model aliases and generation can vary between runs.

| Configuration | Before top 1 | After top 1 | Difference | Before top 3 | After top 3 | After empty/unavailable | After usable synthesis |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLM alone | 18/36 (50.0%) | 18/36 (50.0%) | +0.0 pp | 18/36 (50.0%) | 19/36 (52.8%) | 0/36 | 36/36 |
| Text RAG | 11/36 (30.6%) | 19/36 (52.8%) | +22.2 pp | 11/36 (30.6%) | 19/36 (52.8%) | 1/36 | 36/36 |
| Graph + text RAG | 8/36 (22.2%) | 17/36 (47.2%) | +25.0 pp | 8/36 (22.2%) | 18/36 (50.0%) | 2/36 | 36/36 |

All-arm synthesis failures: 0/108, versus 5/108 before. HTTP statuses in the new run: {"200": 144}. Generated answers were not retried to improve scores.

| Configuration | After top 1 Wilson 95% interval | Median end-to-end latency | p95 end-to-end latency |
| --- | ---: | ---: | ---: |
| LLM alone | 34.5%–65.5% | 7.62 s | 10.12 s |
| Text RAG | 37.0%–68.0% | 7.93 s | 10.94 s |
| Graph + text RAG | 32.0%–63.0% | 8.29 s | 13.04 s |

Latency includes the evaluation wrapper's pacing and any transport retry waits. These are exploratory measurements from one selected public exam subset, not clinical diagnostic accuracy or independent replication. The same benchmark was used to diagnose the original system, so gains require confirmation on a new untouched test set.

## Retrieval on ten frozen source probes

| Measure | Before | After |
| --- | ---: | ---: |
| Precision@1 | 0.600 | 0.900 |
| Recall@5 | 0.667 | 1.000 |
| Hit rate@5 | 0.600 | 1.000 |
| MRR@10 | 0.667 | 0.925 |
| nDCG@10 | 0.670 | 0.863 |

Median retrieval-only latency increased from 40.8 ms to 688.4 ms with reranking. Full-context recall remains 12/12 and required-fact coverage remains 13/13. These ten probes were written from the same 26 passages; no new independent relevance labels were created.

## Medication safety and provenance

| Measure | Before | After |
| --- | ---: | ---: |
| Structured warning recall | 72/72 (100.0%) | 72/72 (100.0%) |
| Text-extracted warning recall | 68/72 (94.4%) | 72/72 (100.0%) |
| Text-extracted warning precision | 68/68 (100.0%) | 72/72 (100.0%) |
| Unknown/conflicting-allergy abstention | 20/24 (83.3%) | 24/24 (100.0%) |
| Allergy-status classification | 104/108 (96.3%) | 108/108 (100.0%) |

Valid provenance controls: 26/26. Altered inputs rejected: 132/132. These safety cases still use a fixed treatment proposal and supplied label passages. They do not establish end-to-end prescribing safety. Claim meaning and patient applicability remain subject to independent clinical review.

## Graph and corpus checks

On the 36 saved baseline contexts, re-linking the frozen symptom strings within HPO and querying the corrected graph produced candidates in 34/36 cases, compared with 0/36 before. This check uses no new model calls and does not assess candidate correctness.
The new end-to-end graph arm produced candidates in 33/36 cases. Newly extracted symptom strings may differ from the frozen-context coverage check.

| Clinical relationship type | Stored distinct edges |
| --- | ---: |
| DRUG_CONTRAINDICATED_FOR | 30675 |
| DRUG_INDICATED_FOR | 9388 |
| PHENOTYPE_ABSENT_IN_DISEASE | 1193 |
| PHENOTYPE_SUPPORTS_DISEASE | 150317 |

Textbook sources: First_Aid_Step1.txt, Pathoma_Husain.txt. Both are complete files, not a complete medical library. The old corpus and the Q&A collection remain stored but are not the active retrieval corpus.

## Validation and rollback

Component regression checks: 74 passed. Local HTTP, extraction and database integration checks with external models disabled: 7 passed. The legacy live-diagnosis assertion was not used as an offline clinical correctness test. Frozen safety/provenance challenges and source checks ran separately. Diagnosis and retrieval metrics were replayed from captured results for reproducibility.

Backups were verified by restoring them into the working containers before modifications. See `DATABASE_CHECKPOINT.md` and the local backup folder for instructions. Git checkpoint `81f3887` contains the original source; current implementation changes are available in the working tree for review. No original Docker volume was rebuilt or deleted.

## Remaining work

Use a new untouched development/test split and independently judged retrieval questions; expand the curated textbook and authoritative-source coverage; obtain blinded clinical support/applicability labels; run component ablations to separate graph, corpus, reranker, prompt and schema effects. Do not infer clinical safety from source checksum acceptance or these synthetic labels.
