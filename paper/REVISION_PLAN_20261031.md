# Research revision plan

Prepared 31 October 2026 as a planning and read-only assessment. Implementation was subsequently authorized and is documented in `paper/IMPLEMENTATION_STATUS_20261031.md`. The original audit below is retained for context; its diagnosis calculations use saved outputs, not new inference.

## Decision

Treat the current manuscript as a technical development study. Do not submit it as evidence that Graph RAG improves diagnosis or that the system establishes general medication safety. Build an independent evaluation around evidence provenance, preservation of uncertainty, and the usefulness of supported warnings. Diagnosis agreement is a secondary outcome unless the study question is deliberately changed before evaluation.

Suggested working title: **Evidence Provenance and Uncertainty Handling in a Retrieval Augmented Clinical Review Prototype**. This describes what is implemented without suggesting that arbitrary claims have already been semantically verified. Retitling does not itself establish novelty.

## What the assessment gets right and what needs qualification

| Point | Audit finding and decision |
| --- | --- |
| Reused test data | Correct. The 36 vignettes, ten retrieval probes and 108 safety cases informed development. Retain their original and revised results as development/regression evidence, explicitly separated from new held-out results. A perfect regression score is useful but does not estimate generalization. |
| Broken baseline | Correct in substance. Changes repaired candidate retrieval, corpus ingestion and output handling together. Incompatible embeddings belonged to the separate literature collection, which was excluded; do not imply that this precisely describes every old text-RAG failure. Call pre/post changes implementation repairs, not proof of a new model effect. |
| Tiny retrieval evaluation | Correct. P@1 improved on three of ten queries. The saturated 12/100 P@10 is uninformative for comparing these rankings, although the metric is not meaningless in general. Keep the ten probes as regression tests. |
| Safety tests bypassed the LLM | Correct for the safety benchmark. `run_med_safety.py` passes intended structured facts or runs `extract_safety_facts(text, {})`. Production `ClinicalClarifier.process` first requests LLM extraction, then merges deterministic checks with the returned hints. The deterministic extractor is a real production component, but its isolated benchmark is not an end-to-end evaluation. |
| No safety baseline | Correct. Add both a simple lexical baseline and a stronger deterministic status/negation baseline, alongside LLM-only and the deployed hybrid path. Give comparable methods the same facts/source access for the specific comparison being made. |
| Graph in title | Optional editorial choice. A negative result does not forbid describing a graph-based architecture. However, provenance and uncertainty are a more defensible focus; do not suggest graph superiority. |
| Missing paired statistics | Correct. Offline calculations are below. They remain exploratory because the data informed development. |
| Latency | Remove paced end-to-end numbers as performance evidence or move them to a clearly labeled operational appendix. Retrieval-only timings were separately measured and need not be discarded automatically. Future timers must separate compute/service time, queue/pacing waits and retry time. |
| Duplicated conclusion and declarations | Correct. The opening sentences of the interpretation and conclusion repeat verbatim. Rewrite the conclusion and obtain factual funding, conflicts, contributions, ethics applicability and AI-use disclosures from the authors. Never invent approvals or reviewer involvement. |
| Textbook provenance | Local paths are inside the MedQA textbook directory. Cite that provenance accurately, verify acquisition/reuse terms, and retain hashes and acquisition instructions rather than redistributing the books. Availability through a dataset does not establish reuse permission. |
| Public result files | Local commit `68e9b05` includes result summaries under `paper/`, including `RESULTS_IMPROVEMENTS_20261027.md`; a folder literally named `results/` is unnecessary. Raw runs are ignored. The cited GitHub repository and commit both returned 404 through the connector; public access is not verified and must be fixed or replaced with a suitable accessible artifact before submission. |

## Additional audit findings

### Existing paired diagnosis results

The saved revised run contains all 108 case/arm records. Re-scoring uses the current normalized top-1 answer-key matching procedure; empty/unavailable diagnoses count as incorrect. Two-sided exact McNemar uses the binomial distribution of the discordant pairs.

| A | B | A correct, B wrong | A wrong, B correct | Exact p |
| --- | --- | ---: | ---: | ---: |
| LLM only | Text RAG | 2 | 3 | 1.00 |
| LLM only | Graph plus text | 4 | 3 | 1.00 |
| Text RAG | Graph plus text | 2 | 0 | 0.50 |

These calculations reproduce the 18/36, 19/36 and 17/36 top-1 totals. They do not establish equivalence, rule out meaningful effects, or repair development-set reuse. For a future confirmatory analysis, prespecify the primary comparison; adjust additional pairwise tests, for example with Holm's method. Report paired effect sizes and confidence intervals as well as p-values.

### A fresh 100-case diagnosis set is not currently available under the same rule

The committed MedQA selector has only 89 eligible cases: 27 Step 1 and 62 Step 2/3. The old pilot used 36. Excluding those leaves 53; additionally excluding the 50 reserved MedQA questions in the separate QA pilot leaves **51** under this eligibility rule. This is a preliminary overlap audit, not certification that every remaining case is untouched: audit all past runs, manual reviews and corpus content before final selection.

Options are to use the genuinely unused eligible remainder as an explicitly small study; broaden diagnosis eligibility using rules fixed before outcome inspection; or obtain additional eligible material from another suitable source and report sources separately. Do not silently substitute general multiple-choice questions for the open-ended diagnosis task. A target of 100 is practical, not a power calculation or assurance that a 2.8 percentage-point difference will be detectable.

### Existing auxiliary QA experiment

The repository also contains a distinct, incomplete 255/300-attempt, three-dataset QA pilot. It has two arms, different inference budgets, and a different task from the 36-case diagnosis study. Exclude its used/reserved cases from a new holdout, preserve its failures and protocol, and do not blend it into the proposed three-arm test. Decide separately whether completing that pilot adds enough value to justify its API cost.

### Reproduction gaps

The fixed-model controlled wrapper used for the principal revised run is under ignored `evaluation/runs/comparison-20261027/run_controlled_benchmark.py`. Its hash is retained, but its executable source is not part of the tracked evaluation package. Promote the reusable runner and configuration into tracked evaluation code before the next freeze. The provider helper records a requested model ID rather than retaining the returned `modelVersion`; capture both in future runs.

## Ordered work plan

### 1. Define the study question and development boundary

Owner: authors with guide. Deliverable: short protocol agreed before more evaluation.

- Primary question: does the proposed evidence/uncertainty handling reduce incorrect supported warnings while retaining useful supported decisions within the declared source/rule scope?
- Separate source identity/integrity, passage-to-claim support, patient applicability and abstention into different outcomes. Checksum validity is not semantic support.
- Mark every previously inspected evaluation item as development evidence. Create an exclusion registry from all prior runs, not just the latest 36 cases.
- Set primary endpoints, baselines, inclusion rules, scoring, handling of ambiguity, missing outputs, transport recovery, maximum sample size and stopping rules in advance.
- Keep disease-neutral overall framing, but disclose the actual source, drug and rule coverage. Do not hide narrow coverage by removing its identifying details.

### 2. Prepare the system and harness on development data only

Owner: implementation work. Deliverable: tested, reproducible evaluation release.

- Record returned model version/response ID, requested model, prompts, generation settings, token counts, timestamps, source hashes, collection/schema identities and model revisions.
- Separate initialization, extraction, retrieval, reranking, synthesis, verification, pacing and retry timings. Refuse silent degraded retrieval or unintended model fallback in controlled comparisons.
- Track the controlled runner, analysis scripts, environment dependencies, selection manifest and aggregate-output schema.
- Audit question/answer leakage in every active retrieval collection. Reject evaluation stems, keys and answer explanations from the corpus.
- Before considering more graph changes, inspect linking correctness, negated/historical symptoms, candidate relevance and the effect of graph passages on synthesis using development data. A returned candidate count is not a correctness metric.
- Test feasible improvements on development data: lexical+dense retrieval, reranker ablations, scope gating and evidence-budget controls. Keep only choices supported by development evidence; avoid a broad architecture rewrite or fine-tuning simply to raise a paper score.
- If additional drug rules are implemented, develop and check them on a separate development set before the final freeze.
- Preserve the current checkpoint, then commit/tag the final implementation, configuration, corpus manifest and protocol before the holdout is opened. No tuning after final test inspection. A later fix gets a new version and a new independent holdout.

### 3. Build independent safety and evidence challenges

Owner: independent case author plus qualified clinician/pharmacist reviewers. Deliverable: sealed cases and adjudicated labels.

- Aim for at least 100 new independently authored safety cases, with strata for positive warnings, clean negatives, negation, stopped medicines, uncertain/conflicting documentation, temporal changes, misspellings, lookalike names and out-of-scope inputs. Split by scenario/template family so superficial paraphrases do not cross development/test boundaries.
- Prefer two or three drugs if source acquisition, implementation and independent review are feasible. Otherwise retain one drug and explicitly limit all conclusions to that rule scope.
- Evaluate three layers separately: intended structured facts to safety gate; raw text through production clarification with a fixed proposed option; and full report generation with live source retrieval. Score omitted or inappropriate treatment suggestions rather than excluding cases where no option is generated.
- Compare LLM-only, lexical/regex, a stronger deterministic baseline, and the hybrid system for the same bounded warning task. Include an otherwise matched gate-disabled arm to test the incremental value of the gate.
- Add an independently labeled challenge, targeting roughly 100 claim/evidence/case triplets if review capacity allows. Include valid supported claims, genuine but irrelevant citations, contradicted statements, wrong patient facts, altered doses and missing prerequisites. Retain the separate integrity-tampering suite.
- Report false supported-decision rate, warning precision/recall, abstention correctness, useful supported coverage and risk versus coverage. An always-abstaining system must not appear successful merely because it never supports a false claim.
- Obtain labels without model outputs. Prefer two qualified reviewers, measure agreement and reconcile disagreements before calculating clinician-adjudicated metrics. A teammate supplies independence from debugging but does not replace clinical qualification. If review is unavailable, label results developer-authored and limit the paper accordingly.
- Group related claims/cases in uncertainty calculations; do not treat many near-identical claims from one scenario as independent patients.

### 4. Run new retrieval and diagnosis evaluations

Owner: independent question author/reviewer plus evaluation runner.

- Retrieval: target at least 50 independently phrased questions over an expanded, declared corpus, with questions and relevance labels created without seeing system rankings. Compare BM25, dense retrieval, and dense plus reranker. Use P@1, MRR, Recall@5 and nDCG with appropriate relevance labels, uncertainty and per-query results. Report incomplete relevance judgments honestly; do not claim complete recall from an incomplete judged pool. If independent labeling is not feasible, move existing retrieval probes to the supplement as engineering checks.
- Diagnosis: choose the feasible holdout source and eligibility rule before inference. Run LLM-only, text RAG and graph plus text once under matched model/settings, shared extraction where appropriate, balanced arm order and the same scoring procedure. Record any unequal evidence/token budgets. Keep failures in the primary denominator and report successful-output-only results only as secondary analyses.
- Prespecify synonym scoring or blinded clinical adjudication for open-ended answers. Do not add favorable aliases after looking at arm-level outcomes.
- Use Wilson intervals for per-arm proportions and exact McNemar for paired correctness, with paired difference intervals and multiplicity control where applicable. With a small holdout, present estimation and uncertainty rather than promising significance.
- Preserve all first-run outcomes and failures. Limit retries to the predefined transport policy; do not regenerate an answer to improve its score.

### 5. Revise the manuscript after the evaluation is locked

Owner: authors. Deliverable: revised manuscript with claims matched to evidence.

- Replace development-set headline claims with independent results when available. Put the 36/10/108-case pre/post numbers in a clearly labeled development or regression subsection/supplement.
- Replace “frozen challenge set” with “unchanged regression suite” when describing the post-fix safety rerun. A frozen fixture can still be used for regression; it is not an untouched validation set.
- Remove duplicated conclusion sentences. State the graph result plainly even if it remains negative.
- Delete or relocate paced end-to-end latency; retain separately defined retrieval-only timing only with its measurement conditions. Report new component/service timing without request pacing mixed in.
- Add substantive prior work on scientific claim verification, citation correctness/completeness, clinical RAG and abstention. Explain the implemented distinction and its evidence; adding citations alone does not create novelty.
- Add accurate funding, conflicts, author contributions, ethics/consent applicability, data/code availability and AI-assisted writing disclosures. Disclose use of ChatGPT/Codex, QuillBot and Grammarly as appropriate to actual use and journal policy; authors verify all claims and references. Detector scores are not evidence of authorship or scientific quality.
- Audit every numerical claim against the locked analysis outputs. Preserve author order and individual blocks, two-column working layout and full-width tables/figure, with a main-text target below nine pages. Prioritize independent evidence over repeated development tables; use a supplement for regression details.
- Before submission, reconcile the working layout with the chosen journal's actual author instructions. IJDDT's current instructions describe double-spaced submission text and surname/initial author formatting; a published two-column example is not automatically the submission template. Do not change author order without author agreement.

### 6. Verify release and journal fit

- Publish/release appropriate code, protocols, non-content case IDs, source/model hashes, privacy/rights-safe per-case scores, aggregate tables and analysis commands. Keep copyrighted text, credentials and local database archives out of the public artifact.
- From a fresh checkout, reproduce every reported aggregate using the released permissible outputs and scripts. Verify the exact repository/commit or archival link as an unauthenticated reader. Keep links stable and do not claim public availability before this succeeds.
- Discuss journal fit with the guide before committing to submission. IJDDT describes a pharmaceutics/drug-delivery remit; generic diagnosis/Graph RAG is not automatically within that remit. More drugs alone do not establish fit or acceptance. If IJDDT remains the target, the medication/evidence evaluation must be a real substantive contribution rather than a framing change.

## Priority and completion criteria

1. Highest priority: independent safety/evidence labels and evaluation, honest development/holdout separation, reproducible runner and model/source logging.
2. Next: independent retrieval, feasible paired diagnosis holdout, controlled component ablations.
3. Then: rewrite, declarations, reference audit, release verification and final layout.

Ready for submission consideration means the protocol and implementation were frozen before the final tests; case independence and label provenance are documented; all baselines and failures are reported; the central claim has a direct experiment; and a reader can access the promised reproducibility material. A negative result can satisfy these conditions. A higher accuracy number alone cannot.

## Sources and audit inputs

- Current manuscript export: `paper/revisions/20261029/updated_paper_two_column_20261030.docx`.
- Saved diagnosis cases and revised outputs: `evaluation/runs/medqa-us-diagnosis-v1/cases.json`, `evaluation/runs/improvements-20261027-medqa/case_results.jsonl`, corresponding metrics and manifest. These are local ignored artifacts; no question text is reproduced here.
- Selection protocol: `evaluation/medqa_adapter.py`, `evaluation/medqa_selection.v1.json`; auxiliary reserved IDs: `evaluation/runs/qa-table5-v1-frozen/manifest.json`.
- Safety paths: `evaluation/run_med_safety.py`, `backend/agents/clarifier.py`, `evaluation/SAFETY_PROVENANCE_PROTOCOL.md`, `evaluation/SAFETY_LABEL_REVIEW.md`.
- Implementation/result history: local `git show 68e9b05`, `paper/RESULTS_IMPROVEMENTS_20261027.md`, `paper/QA_BENCHMARK_PARTIAL_RESULTS.md`.
- [TRIPOD-LLM reporting guideline](https://www.nature.com/articles/s41591-024-03425-5).
- [ALCE citation evaluation](https://aclanthology.org/2023.emnlp-main.398/).
- [SciFact scientific claim verification](https://aclanthology.org/2020.emnlp-main.609/).
- [Statistical testing in NLP](https://aclanthology.org/P18-1128/).
- [Gemini GenerateContent response metadata](https://ai.google.dev/api/generate-content#generatecontentresponse).
- [IJDDT scope](https://ijddt.com/) and [author instructions](https://ijddt.com/instructions/), checked 31 October 2026.
