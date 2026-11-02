# 08 — Testing, evaluation, and results

[Documentation index](README.md) · [Previous: API and UI](07_API_AND_FRONTEND.md) · [Next: limitations](09_LIMITATIONS_AND_FUTURE_WORK.md)

## 1. Testing and research evaluation are different

A software test checks a defined behavior, such as rejecting a wrong source ID. A research evaluation measures a system on a particular labeled task. Neither automatically establishes that the application is appropriate for patient care.

This repository has useful regression tests and multiple exploratory experiments. Its readiness records still say that independent case authorship, qualified clinical review, and fresh held-out clinical evaluation remain pending.

## 2. Offline checks

From the repository root with dependencies installed:

```bash
PYTHONPATH=. python -m pytest -q tests --ignore=tests/test_api.py -k 'not test_clarifier'
```

This excludes the unmocked API test file and the unmocked `test_clarifier` in `test_services.py`. The selected tests use synthetic fixtures and mocks rather than deliberately calling providers or rebuilding databases. The check result for this documentation task is recorded in the final delivery message; historical counts in `paper/` belong to their dated checkpoints.

For a simple API-process check, without invoking analysis:

```bash
PYTHONPATH=. python -m pytest -q tests/test_api.py::test_health_endpoint
```

The full suite includes tests that invoke the real pipeline and may use local databases and external providers:

```bash
PYTHONPATH=. python -m pytest -q tests backend/tests
```

Only run that broader command when its dependencies and provider calls are intended. The legacy live diagnosis assertion expects a particular disease string; it is not an independent clinical correctness test.

## 3. Test areas

| Test area | Examples of behavior checked |
| --- | --- |
| Patient context | Explicit/unknown/conflicting states, quoted facts, retry anchoring |
| Claim synthesis | Required conditions, rejected IDs, evidence-role separation |
| Claim verifier | Pinned identity matching, unsupported scope, conservative status |
| Evidence contracts | Source identity derivation, report reference validity |
| Authoritative sources | Manifest constraints, parsing, indexing behavior with fixtures |
| Provider fallback | Timeout, invalid JSON, provider errors, schema validation |
| Model improvements | Global graph IDs, typed linking, chunk overlap, schema transport |
| Report presentation | Grouped claims, medication facts, uncertainty visibility |
| Frontend assets | Cache headers and expected presentation contracts |
| Evaluation | Denominators, replay, review labels, metrics, protocol integrity |

A passing regression test means the tested behavior still holds. It does not mean every language variation, drug, or clinical situation has been tested.

## 4. Basic three-arm analysis experiment

[evaluation/run.py](../evaluation/run.py) reuses the production route function and swaps retrieval:

| Arm | Information supplied |
| --- | --- |
| `llm_only` | Patient context and model synthesis; no graph/text retrieval |
| `text_rag` | Textbooks and scoped pinned source passages |
| `graph_text` | Same text retrieval plus Neo4j candidate retrieval |

Clarification is shared per case. Arm order rotates. Web discovery and DrugCentral are excluded in this comparison. Adaptive retries default to zero for evaluation, unlike the production route's two-retry budget.

Example live experiment and replay, using fresh paths:

```bash
python -m evaluation.run --output evaluation/runs/documented-study
python -m evaluation.run --replay evaluation/runs/documented-study/case_results.jsonl --output evaluation/runs/documented-study-replay
```

Replay rescoring avoids new model calls, but the runner still needs its matching case file and pinned snapshots. For a nondefault dataset, provide the same `--cases` file to both commands.

## 5. Output artifacts

| Artifact | Purpose |
| --- | --- |
| `run_manifest.json` | Dataset/source/code/configuration provenance and run settings |
| `case_results.partial.jsonl` | Incrementally saved live records |
| `case_results.jsonl` | Complete case/arm records, reports, trace, and timing |
| `metrics.json` | Counts, denominators, available/unavailable metrics |
| `case_errors.jsonl` | Failed cases, misses, citation issues, and labeled errors |
| `review_packet_blinded.jsonl` | Reviewable claims without system arm/status labels |
| `review_index_private.jsonl` | Private mapping between review items and system outputs |
| `review_disagreements.jsonl` | Reviewer disagreements that remain unresolved |

The matrix validator requires exactly one record per planned case and mode. New runs refuse existing output directories. Raw cases, reports, and keys stay under ignored run paths; preserve them locally for audit without adding them to a public documentation commit.

## 6. Metrics in simple English

| Metric | Meaning and limitation |
| --- | --- |
| Top-1 agreement | First diagnosis matches a normalized reference alias |
| Top-3 agreement | A reference alias appears among the first three candidates |
| Citation identity validity | Cited metadata/text matches the pinned corpus; not semantic support |
| Warning precision | Correct expected warnings divided by emitted warnings |
| Warning recall | Detected expected warnings divided by expected warning opportunities |
| Useful supported coverage | Supportable decisions actually returned as supported |
| False supported-decision fraction | Incorrect supported decisions among the declared opportunities/outputs |
| Abstention | Claim or decision left unverified where the protocol defines it |
| Precision@k | Direct-answer passages in the first k, divided by k |
| Recall@k | Judged direct-answer passages retrieved in the first k, divided by all judged relevant passages |
| Hit@k | Whether at least one directly relevant passage appears in the first k |
| MRR | Average reciprocal rank of the first directly relevant passage |
| nDCG | Ranking quality that rewards higher relevance near the top |
| Latency | Measured wall time for a declared stage or end-to-end task |

Diagnosis alias agreement can penalize a medically equivalent synonym. Warning opportunities are not always independent cases. Retrieval recall only covers the judged corpus, not all medical literature. Each experiment must state its denominator.

The current diagnosis scorer's primary metrics include all planned cases: failures and empty answers count incorrect. Completed-output-only results are secondary. Earlier saved snapshots may use earlier policies and must be read with their own definitions.

## 7. Dated diagnosis results

These are separate experiments; do not merge them into one accuracy claim.

| Experiment | LLM only top-1 | Text RAG top-1 | Graph + text top-1 | Interpretation |
| --- | --- | --- | --- | --- |
| 7 October six-case synthetic fixtures | 1/6 | 4/6 | 5/6 | Reference diagnoses were stated in the case text; recognition check |
| 12 October four-condition pilot | 10/12 | 9/12 | 10/12 | Author-built diagnosis-withheld cases; no independent standard |
| 13 October MedQA vignette pilot | 19/36 | 12/36 | 14/36 | Public exam subset; provider mismatch and zero graph candidates |
| 27 October repaired development run, summarized again on 31 October | 18/36 | 19/36 | 17/36 | Reused development cases and combined repairs; no fresh holdout |

Sources: [six-case snapshot](../paper/RESULTS_SNAPSHOT.json), [four-condition snapshot](../paper/MULTIDISEASE_PILOT_RESULTS.json), [original MedQA snapshot](../paper/MEDQA_EXAM_PILOT_RESULTS.json), [repair report](../paper/RESULTS_IMPROVEMENTS_20261027.md), and paired development analysis (`paper/PAIRED_DEVELOPMENT_RESULTS_20261031.json`, local checkpoint).

The 31 October paired analysis is a rescoring/statistical analysis of development records, not another independent model experiment. Its pairwise Holm-adjusted p-values are 1.0. This does not prove equivalence; it also does not repair development-set reuse.

The repaired graph produced candidates in 33/36 end-to-end cases, compared with none in the older exam run. Increased candidate coverage does not establish better candidate correctness or diagnosis accuracy. In the repaired run, text-only top-1 agreement was higher than graph-plus-text agreement.

## 8. Retrieval and provenance checks

Ten known-passage retrieval probes were written from the same 26-passage source corpus. Historical Precision@1 was 0.600 and repaired Precision@1 was 0.900; MRR@10 changed from 0.667 to 0.925. Reranking also increased measured retrieval time. See [the probe snapshot](../paper/RETRIEVAL_PROBE_RESULTS.json) for the original protocol and [the repair report](../paper/RESULTS_IMPROVEMENTS_20261027.md) for the later results.

These probes measure known-source engineering behavior. They are not independently authored clinical retrieval questions. The current merged ranking differs from the original five-guidelines-before-five-labels order.

The provenance challenge accepted 26/26 valid controls and rejected 132/132 constructed invalid checks. [Its snapshot](../paper/PROVENANCE_TAMPER_RESULTS.json) reports the corruption types and counts. This supports the tested identity checks, not a claim of universal tamper resistance or semantic verification.

## 9. Medication-safety experiments

The original 108 developer-labeled synthetic cases supply a fixed proposed amlodipine option and label passages. They isolate extraction/rules; they do not test live retrieval or free treatment generation. Original deterministic text extraction warning recall was 68/72; after the unknown-allergy phrase repair it was 72/72. These are development/regression results.

The separate 31 October live comparison completed 108 cases and 432 arm records:

| Arm | Warning precision | Warning recall | Exact warning/support cases | Failed cases |
| --- | --- | --- | --- | --- |
| Deterministic extraction + rules | 72/72 | 72/72 | 108/108 | 0 |
| LLM-only warnings | 49/65 | 49/72 | 81/108 | 1 |
| Production extraction + rules | 69/69 | 69/72 | 106/108 | 2 |
| Same LLM warnings + rule filter | 46/46 | 46/72 | 83/108 | 3 |

Source: live safety report (`paper/SAFETY_LIVE_DEVELOPMENT_RESULTS_20261031.md`, local checkpoint) and aggregate JSON (`paper/SAFETY_LIVE_DEVELOPMENT_RESULTS_20261031.json`, local checkpoint).

The deterministic baseline already matched every expected case. The hybrid did not beat it. Filtering improved precision while losing recall: removing unsupported warnings cannot recover omitted warnings. Controlled extraction failures stayed failed rather than receiving credit for operational fallback.

## 10. Separate three-dataset QA pilot

The QA adapter experiment planned 50 questions from each of MedQA, PubMedQA, and MedBullets, in two arms: 300 case/arm attempts. Its saved state remains **255/300 attempts**, with 45 missing after a daily provider quota stop.

The CDSS arm adds report generation and an answer-selection adapter; the baseline uses direct answer selection. Their inference budgets differ. This task differs from open-ended diagnosis and from narrow warning checks.

[The partial-results report](../paper/QA_BENCHMARK_PARTIAL_RESULTS.md) records all attempted denominators and failures. [The protocol](../evaluation/QA_BENCHMARK_PROTOCOL.md) gives its original continuation commands. Retain exact code/protocol consistency before any continuation; do not silently resume old results under changed clinical code. This documentation task does not complete or rerun the pilot.

## 11. Independent evaluation workflow

The newer tooling supports exposure exclusions, corpus audits, frozen protocols, single-provider controlled runs, baseline comparisons, and blinded review. See the full protocol (`evaluation/INDEPENDENT_EVALUATION_PROTOCOL.md`, local checkpoint).

The intended sequence is:

1. Register previously exposed material and manual exclusions.
2. Obtain independently authored cases and qualified labels.
3. Develop and select settings on separate development material.
4. Audit corpus leakage and record data/model/code identities.
5. Freeze the protocol before inference.
6. Run controlled comparisons with failures retained.
7. Collect blinded clinical ratings and preserve disagreements.
8. Report paired results, uncertainty, useful coverage, and limitations.

Implemented tools include `holdout`, `audit_corpus`, `freeze`, `controlled`, `safety_v2`, `claim_challenge`, `retrieval_baselines`, and `paired_statistics`. Their existence does not mean an independent study has been completed.

## 12. Timing, cost, and statistical caution

Timing stages are nested. Do not add extraction wall time to all its nested HTTP/model stages and call the sum end-to-end time. Older paced runs include waiting and cannot be quoted as unqualified inference-speed benchmarks. Gemini traces can record returned model version, response ID, and token-count metadata, but full cross-provider cost accounting is not implemented.

Wilson intervals, paired bootstrap intervals, exact McNemar tests, and Holm correction help describe specific comparisons. They do not remove template dependence, selection bias, provider alias changes, public-test contamination, or the lack of clinical reviewers.

The defensible conclusion is that the project has inspectable engineering behavior and documented development results. Clinical accuracy, general semantic support, prescribing safety, and patient benefit remain unestablished.
