# Frozen adapted QA benchmark results — INCOMPLETE

**Partial run: 255/300 planned arm attempts recorded. Stopped on the provider's 500-requests-per-day quota. Do not present this as the completed 50-question-per-dataset experiment or as evidence of superiority.**

These are exam/research-question results, not patient diagnostic accuracy or clinical safety estimates.

The CDSS QA adapter runs the production graph/text clinical-report pipeline, followed by an added answer-selection call. The direct LLM baseline receives the same question, context and options without a report. The arms have different inference budgets; differences do not isolate graph or verification effects.

| Dataset | Arm | Correct / attempted | Accuracy (Wilson 95% CI) | Failed answers |
| --- | --- | ---: | --- | ---: |
| MedQA | llm_only | 35/41 | 85.4% (71.6%–93.1%) | 1 |
| MedQA | cdss_qa_adapter | 28/42 | 66.7% (51.6%–79.0%) | 10 |
| PubMedQA | llm_only | 35/41 | 85.4% (71.6%–93.1%) | 2 |
| PubMedQA | cdss_qa_adapter | 34/41 | 82.9% (68.7%–91.5%) | 2 |
| MedBullets | llm_only | 33/45 | 73.3% (59.0%–84.0%) | 1 |
| MedBullets | cdss_qa_adapter | 27/45 | 60.0% (45.5%–73.0%) | 4 |

For valid single-label outputs, micro precision, recall and F1 each equal accuracy. Class-level scores, macro-F1 and one-vs-rest specificity are in the JSON artifact. Failures remain in the accuracy denominator. Intervals are descriptive and do not account for public-test contamination or topic clustering.

Selection was frozen by a fixed SHA-256 ordering before inference, with source hashes and case IDs retained. Answers/explanations were withheld from model inputs. PubMedQA uses official test IDs and question-plus-abstract yes/no/maybe classification; MedQA and MedBullets use five-option exact label matches. The requested model is Gemini Flash Lite, temperature zero; provider fallback, adaptive retry, web discovery and DrugCentral are disabled.

The IEEE paper reports 47/50, 44/50 and 42/50 correct for MedQA, PubMedQA and MedBullets respectively. Those are external reported results on a different question selection; its PubMedQA scoring also differs. They must not be treated as a controlled baseline or evidence of superiority. Source: https://doi.org/10.1109/ACCESS.2025.3613340

Recorded retrieval totals were 0 graph disease candidates, 640 textbook items and 1280 pinned source passages across CDSS attempts with saved reports. Counts include repeated retrieval across questions. Retrieval counts do not establish relevance or claim support.

The clinical pipeline's narrow hypertension/amlodipine authoritative corpus and patient-case prompts limit applicability to general QA. The answer selector may rely on its own knowledge. No conclusion about MedRAGChecker, general claim-support accuracy, prescribing safety, or patient benefit follows.

Raw question text, keys and reports remain in the ignored run directory. Aggregate metrics were regenerated from every recorded arm attempt and matched the saved metrics exactly.
