# Independent evaluation workflow

Status on 31 October 2026: implementation ready for engineering checks; independent case author and clinical reviewer unavailable. No independent clinical evaluation has been completed. Funding, conflicts, ethics applicability and author contributions remain for the authors to confirm and are intentionally not invented.

## Study question and outcomes

The primary question is whether evidence and uncertainty handling reduces incorrect supported warnings while retaining useful supported decisions within the declared source/rule scope. Evaluate provenance integrity separately from semantic support, patient applicability, warning detection and diagnosis agreement. Graph coverage is a retrieval diagnostic, not a correctness outcome.

Primary safety/evidence endpoints are false supported-decision fraction, useful supported coverage and appropriate abstention. Always report recall and failed outputs; an always-abstaining system has zero useful support on supportable items. Secondary endpoints include exact case decisions, diagnostic top-1/top-3 agreement, retrieval P@1/MRR/Recall@5/nDCG and service timing. Event fractions are not independent patient estimates; case families need clustered analysis before inferential claims.

## Current evidence

- Original 36 diagnosis cases, ten retrieval probes and 108 safety cases are development/regression data. Preserve original outputs and subsequent repair runs.
- `paper/PAIRED_DEVELOPMENT_RESULTS_20261031.json` contains exact two-sided McNemar tests, Holm correction, descriptive paired bootstrap intervals and non-content per-case scores. It does not represent a new inference run.
- `paper/SAFETY_BASELINE_REGRESSION_20261031.json` compares a deliberately weak lexical baseline, the existing deterministic path and intended structured facts. The structured path is an oracle component check, not a fair raw-text competitor.
- There are 51 remaining candidates under the original MedQA diagnosis eligibility after the local exclusion audit, including exclusions for the separate QA pilot. Manual exposure and provider pretraining contamination are still unknown.
- The separate incomplete 255/300-attempt QA adapter experiment retains its own protocol, failures and unequal inference budgets. Do not blend it into this study.

## 1 Build the exclusion registry

Run before selecting any future holdout. Add artifacts from manual reviews and other computers as needed; a local scan cannot discover them automatically.

```bash
python -m evaluation.holdout registry \
  --input evaluation/runs \
  --input evaluation/medqa_selection.v1.json \
  --input evaluation/cases.v1.json \
  --input evaluation/cases.multidisease-pilot.v1.json \
  --output evaluation/runs/exclusions-v2/registry.json
python -m evaluation.holdout medqa \
  --registry evaluation/runs/exclusions-v2/registry.json \
  --source datasets/literature/MedQA/MedQA-USMLE/questions/US/test.jsonl \
  --count 50 --seed cdss-diagnosis-v2-prespecified \
  --output evaluation/runs/diagnosis-v2-candidates/cases.json
```

The selector refuses impossible sample sizes and retains the original diagnosis eligibility. A candidate file is reserved, not certified untouched. Complete the manual audit before classifying it as held out. For a larger sample, define a new eligibility protocol/source before inspecting outcomes; do not substitute MCQ scoring for open-ended diagnosis without declaring the task change.

## 2 Author and review new cases

An independent author should create at least 100 new safety cases with explicit `family_id`, avoiding template-family overlap with development. Prefer several drugs only after separately developing and reviewing their source/rule implementations. Current production label rules still cover one drug; the runner rejects unsupported warning labels rather than pretending multi-drug coverage.

Each safety case uses the version-1 fixture field schema: `case_id`, `family_id`, `case_text`, `stratum`, `structured_facts`, `expected_warning_types`, `expected_supported_warning_types`, `expected_treatment_conflict`. These fields are documented by `evaluation/med_safety_cases.v1.json`; old fixtures are examples of the format, not material to paraphrase into a supposedly independent holdout. Separate raw author material from blinded reviewer packets and labels. Preserve ambiguous examples and disagreements.

For semantic challenges, use `case_id`, `family_id`, `case_text`, `claim_type`, `claim_text`, and `cited_passages` (serialized `SourcePassage` objects). Include genuine-but-irrelevant citations, contradictions, wrong patient prerequisites, missing information and supported controls. Dataset envelope: `dataset_version`, `evidence_role`, `cases`.

```bash
python -m evaluation.claim_challenge prepare --cases LOCAL_CASES.json \
  --output evaluation/runs/claim-review-v2
```

Give reviewers only `review_packet.jsonl` and a separate copy of `ratings_blank.jsonl` each. Never give them the private index, developer labels, predictions or method names before rating. Record actual reviewer identity and qualifications. Required claim ratings are `support_label` (`supported`, `contradicted`, `insufficient`) and `applicability_label` (`applicable`, `not_applicable`, `unknown`). At least two independent reviewers must agree; preserve original disagreement records. A guide without relevant clinical expertise does not substitute for qualified clinical review.

For safety ratings, use each case ID with `reviewer_id`, `expected_warning_types` and `expected_supported_warning_types`. Reviewers must agree with final case labels before freezing. The freeze tool checks the supplied record structure and hashes, not the real-world authenticity of reviewer qualifications.

## 3 Freeze after development, before final evaluation

Develop fixes and choose models/prompts/ranking on development material only. Commit all implementation files. Write a protocol draft using `evaluation/protocol.draft.example.json` as a template; it is deliberately not ready to run as an independent clinical test.

```bash
python -m evaluation.freeze --cases LOCAL_CASES.json \
  --draft LOCAL_PROTOCOL_DRAFT.json --output evaluation/runs/study-v2/frozen.json
```

Before freezing a held-out protocol, run the read-only database preflight against the exact candidate file and set `corpus_audit_path` in the draft to its output:

```bash
python -m evaluation.audit_corpus --cases LOCAL_CASES.json \
  --output evaluation/runs/study-v2/corpus-audit.json
```

The freeze records the commit, code/data/source hashes and effective collection, embedder and reranker configuration. Clinical holdouts require manual exposure attestation, independent authorship and actual matching review records. For blinded claim ratings, also set `independent_review.private_index_path` to the private review index. Exam diagnosis holdouts use exam answer keys and must not be described as clinician-adjudicated patient diagnoses. Runtime validation refuses changed code, source manifests, cases or configuration. Held-out runs require the matching corpus audit; validation repeats its read-only Qdrant fingerprints and graph inventory. Qdrant hashes cover payloads and vectors; graph counts do not certify unchanged edge contents. Exact leakage checks cannot rule out paraphrases or model pretraining contamination. Publisher snapshots remain checksum-checked by the source loader.

## 4 Execute controlled experiments

Diagnosis:

```bash
python -m evaluation.controlled --cases LOCAL_CASES.json \
  --protocol evaluation/runs/study-v2/frozen.json \
  --output evaluation/runs/study-v2/diagnosis
```

This tracked runner replaces the ignored one-off wrapper. It fixes a single Gemini model, reuses extraction across three retrieval arms, rotates arm order, disables web/DrugCentral and adaptive retries, rejects missing retrievers/rerankers and records synthesis failures. Failed or empty answers remain incorrect in primary metrics. HTTP 429 transport recovery is limited; daily quota stops the experiment and preserves a partial journal. Never regenerate an answer to improve a score. Interrupted experiments remain incomplete and are not a full planned comparison.

Safety:

```bash
python -m evaluation.safety_v2 --cases evaluation/med_safety_cases.v1.json \
  --role regression --output evaluation/runs/safety-regression-new
python -m evaluation.safety_v2 --cases LOCAL_CASES.json --role held_out --live \
  --protocol evaluation/runs/study-v2/frozen.json \
  --output evaluation/runs/study-v2/safety
```

Offline modes are lexical, deterministic and structured oracle. Live modes add LLM-only with supplied label passages, production clarification followed by a fixed proposal/gate, and full report generation with graph/text retrieval. The full report arm disables web/DrugCentral for controlled scope. Fixed-proposal arms isolate fact extraction/gate behavior and do not test whether the model selects an appropriate treatment. Full-report treatment claims are retained for later clinical review, including omissions and inappropriate suggestions. Never omit a case because no relevant option was generated.

Claim component checks and reviewed scoring:

```bash
python -m evaluation.claim_challenge run --cases LOCAL_CASES.json \
  --output evaluation/runs/study-v2/claim-predictions
python -m evaluation.claim_challenge score --cases LOCAL_CASES.json \
  --predictions evaluation/runs/study-v2/claim-predictions/predictions.jsonl \
  --ratings COMPLETED_RATINGS.jsonl \
  --index evaluation/runs/claim-review-v2/private_index.jsonl \
  --output evaluation/runs/study-v2/claim-scores
```

The identity-only baseline deliberately confuses a genuine citation with support. The production gate's general semantic claims remain unverified. Its conservative abstention is not evidence of a useful semantic verifier; useful supported coverage is reported alongside false-support risk. The component runner supplies unknown patient facts rather than secretly inferring them; it is not the full production route. Metrics remain unavailable if review coverage is incomplete. A real semantic-support model would require separate development and independent evaluation before any deployment claim.

Retrieval:

Create at least 50 independently authored questions with a `query_id`, `family_id`, `query`, `grades` keyed by actual pinned source IDs, and `judgments_complete` boolean. Grade 0 is irrelevant, 1 related, 2 directly answering. A dataset envelope supplies `queries`, `annotation_status`, `evidence_role`. The new runner compares one shared pinned corpus using BM25, dense retrieval and reranking of the top 20 dense candidates. This is a distinct offline ranking protocol, not a replay of the old five-per-collection production probe.

```bash
python -m evaluation.retrieval_baselines --queries LOCAL_QUERIES.json \
  --methods bm25 dense dense_reranked --embedder-revision PINNED_40_HEX_COMMIT \
  --output evaluation/runs/study-v2/retrieval.json
```

Models must be cached; no download is performed. Incomplete judgments suppress recall/nDCG, and unjudged top-ranked items suppress precision/MRR rather than being silently called irrelevant. A headline aggregate is unavailable when any planned query lacks its required judgment. Held-out retrieval additionally requires a frozen protocol and matching independent grades. Do not replace clinical labels with model-generated judgments and call them independent review.

## 5 Interpret, release and revise

Report counts/denominators, Wilson intervals for case proportions, paired differences with descriptive case-bootstrap intervals, exact McNemar and Holm-adjusted exploratory comparisons. Do not treat nonsignificance as equivalence. Scenario/template families require clustered analysis; no independent-event intervals are supplied for correlated warning events. Prespecify one primary comparison if making confirmatory claims.

Returned `modelVersion`, response IDs and token counts are now captured for Gemini. Timing stages are nested wall times and must not be added. `http_service` excludes separately logged pacing/retry waits; extraction/retrieval/synthesis include nested stages. Original paced end-to-end timings remain historical artifacts and are not used as speed evidence.

Publish permissible scores, protocols, hashes and scripts without copyrighted stems, source books, keys, credentials, raw reviews or database archives. Verify the cited release/commit anonymously before claiming public access. The previous cited GitHub path returned 404 through the connector; public reproducibility remains unverified.

Revised manuscript prose must pass through the authorized humanizer, then numerical/meaning checks before insertion. Humanizer output and detector scores cannot validate research quality or authorship. Declarations remain pending author facts. Independent clinical results, multi-drug claims, journal acceptance and general semantic verification are not claimed by this implementation.
