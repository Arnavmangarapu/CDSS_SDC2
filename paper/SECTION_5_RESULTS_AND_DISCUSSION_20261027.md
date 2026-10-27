# 5. RESULTS AND DISCUSSION

## 5.1 Diagnostic evaluation

The revised system was evaluated on the same 36 selected MedQA-USMLE diagnosis vignettes, with answer options and answer keys withheld during inference. All three configurations requested the same model, Gemini Flash Lite (`gemini-3.5-flash-lite`), at temperature zero, with provider fallback and adaptive retrieval retries disabled. Patient context was extracted once per vignette and shared across configurations within each run. Generated answers were not retried to improve agreement. Results represent open-ended agreement with examination answer keys, rather than clinical diagnostic accuracy or a standard multiple-choice MedQA score.

**Table 2. Revised MedQA diagnosis results (36 cases per configuration).**

| Configuration | Top-1 match | Top-3 match | Cases with no ranked diagnosis |
| --- | ---: | ---: | ---: |
| LLM only | 18/36 (50.0%) | 19/36 (52.8%) | 0/36 |
| Text RAG | 19/36 (52.8%) | 19/36 (52.8%) | 1/36 |
| Graph + text RAG | 17/36 (47.2%) | 18/36 (50.0%) | 2/36 |

Top-1 match indicates agreement between the first ranked diagnosis and the keyed diagnosis under the predefined normalized-alias matching procedure. Top-3 match indicates that the keyed diagnosis occurred among the first three candidates. All 36 cases remain in each denominator, including cases with an empty differential.

Text RAG achieved the highest observed top-1 agreement, exceeding LLM only by one case, or 2.8 percentage points. Graph + text RAG remained below both configurations. The 95% Wilson intervals for top-1 agreement were 34.5–65.5% for LLM only, 37.0–68.0% for text RAG and 32.0–63.0% for graph + text RAG. These estimates are imprecise, and the small observed difference does not establish a reliable diagnostic advantage from retrieval.

A separate controlled pre-revision run on 27 October 2026 obtained top-1 matches of 18/36, 11/36 and 8/36 for LLM only, text RAG and graph + text RAG, respectively. Relative to that run, the revised text and graph + text configurations improved by 22.2 and 25.0 percentage points. These comparisons use the controlled pre-revision run, rather than the older results obtained with mixed model providers. Because graph ingestion, corpus coverage, reranking, prompting and output formatting were revised together, the improvements cannot be attributed to an individual component.

All 108 revised synthesis outputs passed the output-processing checks, compared with five synthesis failures in the controlled pre-revision run. Successful processing did not always produce a ranked diagnosis, as shown in Table 2. Median end-to-end latencies were 7.62 s, 7.93 s and 8.29 s for LLM only, text RAG and graph + text RAG, with corresponding 95th percentiles of 10.12 s, 10.94 s and 13.04 s. These measurements include evaluation pacing and any transport retry waits and should not be interpreted as production throughput.

The corrected graph returned disease candidates for 33/36 cases in the revised end-to-end graph configuration. A separate check using the saved baseline symptom strings, relinked within the HPO vocabulary, returned candidates for 34/36 cases, compared with none before correction. The two checks used different extracted contexts. Candidate availability demonstrates that the graph retrieval path is functioning; it does not establish candidate correctness or improved diagnosis.

## 5.2 Retrieval quality

Pinned-source retrieval was evaluated using the same 10 developer-written queries over 26 passages: 17 from NICE hypertension guidance and nine from one DailyMed amlodipine label. The reference set contained 12 directly relevant query–passage pairs and a checklist of 13 required facts. Relevance judgments were developer-defined and had not been independently adjudicated by clinicians. This evaluation concerns the pinned-source corpus, rather than retrieval across the textbook collection.

**Table 3. Revised pinned-source retrieval results.**

| Metric | @1 | @3 | @5 | @10 |
| --- | ---: | ---: | ---: | ---: |
| Precision@k | 0.900 | 0.333 | 0.240 | 0.120 |
| Micro Recall@k | 0.750 | 0.833 | 1.000 | 1.000 |
| Hit Rate@k | 0.900 | 0.900 | 1.000 | 1.000 |
| MRR@k | 0.900 | 0.900 | 0.925 | 0.925 |
| Mean nDCG@k | 0.900 | 0.795 | 0.863 | 0.863 |

Precision, recall, hit rate and MRR treat only direct-answer passages as relevant. Micro recall is calculated over the 12 directly relevant query–passage pairs. Mean nDCG uses graded relevance, with gains of 2^grade − 1 and logarithmic rank discounting; related passages therefore contribute to nDCG even when they do not count toward the binary metrics.

Following global reranking of guideline and drug-label results, precision@1 increased from 0.600 to 0.900 and micro recall@5 increased from 0.667 to 1.000. All four drug-label queries retrieved a directly relevant passage at rank one, correcting the earlier ordering in which their first relevant passages appeared at rank six. MRR@10 increased from 0.667 to 0.925. All 12 directly relevant query–passage pairs were retrieved within the first five results, indicating improved early ranking on these probes.

At a cutoff of 10, however, only 12/100 retrieved query–passage pairs were directly relevant, so full-context precision remained 0.120. The required-fact checklist remained fully covered at 13/13. Fact availability does not establish that generated claims correctly interpret or cite those facts. Median retrieval-only latency increased from 40.8 ms in the controlled pre-revision run to 688.4 ms, while the 95th percentile increased from 204.1 ms to 1,098.8 ms. The revised ranking therefore involved additional retrieval cost. Since the queries were written from the same small corpus and used during debugging, these results require confirmation on independently constructed retrieval questions.

## 5.3 Evaluation of medication safety

The medication-safety components were retested on the same 108 developer-generated synthetic cases using a fixed amlodipine treatment proposal. Cases included relevant allergies, unrelated drug allergies, look-alike names, medication interactions and unknown or conflicting allergy information. Expected outputs were defined before execution. All pinned label passages were supplied directly to the tested components; neither live retrieval nor language-model treatment generation was evaluated in this challenge.

**Table 4. Revised medication-safety results on 108 synthetic cases.**

| Metric | Structured facts | Text extraction |
| --- | ---: | ---: |
| Warning precision | 72/72 (100%) | 72/72 (100%) |
| Warning recall | 72/72 (100%) | 72/72 (100%) |
| Abstention for unknown or conflicting allergy status | 24/24 (100%) | 24/24 (100%) |
| Correct allergy-status classification | 108/108 (100%) | 108/108 (100%) |

Warning precision measures agreement between issued and expected warning events, while warning recall measures the proportion of expected warning events recovered. Warning-event denominators differ from the number of cases. Abstention measures whether uncertainty was retained when allergy status could not be established.

The structured-fact path retained its previous results. After correction of the deterministic text extractor, text-path warning recall increased from 68/72 (94.4%) to 72/72 (100%), and abstention for unknown or conflicting allergy status increased from 20/24 (83.3%) to 24/24 (100%). Allergy-status classification improved from 104/108 (96.3%) to 108/108 (100%). All four previously missed cases containing “No allergy history was recorded” now retained unknown allergy status and produced the expected uncertainty warning.

These results confirm recovery of the observed extraction failures on the frozen challenge set. They do not establish end-to-end prescribing safety: the cases and expected labels were developer-authored, the treatment proposal was fixed, the source scope covered one medicine, and independent clinician review remained pending.

## 5.4 Provenance integrity

The provenance verifier was retested without a language model using 26 valid source controls and 132 constructed alterations. Alterations targeted citation identifiers, retrieved identifiers, document versions, passage text, source types and source-snapshot checksums.

**Table 5. Revised provenance-verifier results.**

| Input condition | Observed decision |
| --- | ---: |
| Valid source controls | 26/26 accepted |
| Invented citation ID | 26/26 rejected |
| Wrong document version | 26/26 rejected |
| Modified passage text | 26/26 rejected |
| Wrong source type | 26/26 rejected |
| Forged retrieved ID | 26/26 rejected |
| Wrong snapshot SHA-256 | 2/2 rejected |
| All altered inputs | 132/132 rejected |

The verifier continued to accept all valid controls and reject all tested alterations. These results indicate that the tested source-identity and checksum checks remained intact after the revisions. They are regression tests of constructed mutations rather than independent clinical claim assessments. A passage can have valid provenance while failing to support a claim or apply to the patient. Consequently, provenance acceptance alone does not establish clinical correctness, and general generated claims remain unverified pending support and applicability review.

## 5.5 Discussion

The revised evaluation demonstrates improvements in retrieval ordering, output processing and handling of missing allergy information. Relevant pinned passages appeared earlier in the retrieved results, all revised synthesis outputs passed processing checks, and the four previously missed uncertainty warnings were recovered. Source-integrity checks retained their previous performance.

The graph correction restored candidate retrieval but did not produce a diagnostic advantage. Graph + text RAG achieved 17/36 top-1 matches, compared with 19/36 for text RAG and 18/36 for LLM only. This distinction shows why graph coverage and downstream answer agreement must be evaluated separately. Further work should examine candidate relevance and how graph associations influence synthesis rather than assuming that additional graph evidence improves the final answer.

The active textbook corpus increased from 156 passages to 1,134 passages drawn from the complete First Aid and Pathoma source files. This expanded the available candidate evidence but did not provide comprehensive medical coverage. Citable authoritative sources remained limited to adult hypertension guidance and one amlodipine label. The observed gains also followed several simultaneous implementation changes, so controlled component ablations are needed to distinguish their contributions.

The principal limitations are the small selected examination subset, reuse of the evaluation cases during debugging, developer-authored retrieval and safety labels, and the absence of independent clinical adjudication. Despite originating from a public test split, the reused cases now function as development evidence for this system. Model generation and provider-served model aliases may also vary between runs. Replaying saved outputs confirms metric reproducibility but does not constitute independent replication. Claim-support accuracy, unsupported-claim rate and treatment safety remain unestablished without independent reference judgments.

The findings therefore support an exploratory feasibility claim: the prototype can retrieve and preserve traceable evidence, retain uncertainty in the tested missing-information cases, and detect the evaluated source alterations. Stronger diagnostic and safety claims require a frozen implementation evaluated on an untouched case set, independently judged retrieval questions, component ablations and blinded clinical review of claim support and patient applicability.
