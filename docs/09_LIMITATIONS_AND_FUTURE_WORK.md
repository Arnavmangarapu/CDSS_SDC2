# 09 — Limitations and future work

[Documentation index](README.md) · [Previous: testing and results](08_TESTING_EVALUATION_AND_RESULTS.md) · [Next: interview questions](10_INTERVIEW_AND_REVIEW_QUESTIONS.md)

## 1. Current status

This is an evidence-linked clinical decision support research prototype. Its implemented strengths are inspectable stages, typed claims, exact source provenance, explicit missingness, narrow label rules, and reproducible evaluation artifacts.

Its scope and evidence do not justify claims of validated diagnosis, safe prescribing, broad medical verification, or patient benefit. The limitations below describe actual code and saved study status, rather than hypothetical promises.

## 2. Clinical and evidence limits

| Limit | Practical consequence |
| --- | --- |
| Two pinned source documents | Most clinical topics lack an authoritative source path |
| One label and two narrow rules | No general medication interaction or safety engine |
| No general semantic verification | Valid source identity can coexist with an unsupported claim |
| Partial applicability checks | Population, treatment eligibility, and setting still require review |
| Different source jurisdictions | England guidance and a United States label cannot be treated as one universal policy |
| Pending independent source review | Selection itself is not clinically adjudicated |
| No automatic freshness review | A pinned source can become outdated while its checksum remains correct |
| Broad graph/textbook candidates | Candidate breadth can exceed the verifier's narrow scope |

A useful extension needs more than adding documents. It needs source selection rules, version handling, appropriate clinical labels, clear applicability conditions, and evidence that users interpret the resulting states correctly.

## 3. Extraction limits

Safety-fact extraction combines regex rules with quoted model hints. It handles specific current/stopped medication cues, allergy phrases, selected measurements, and unknown/conflicting states. It does not implement a complete clinical natural-language parser.

Important gaps include complex negation, historical timelines, family history, experiencer identification, abbreviations, spelling variation, multiword drug names, medicine dose reconciliation, lab unit normalization, and contradictory observations across time. The symptom keyword fallback can also pick up words in a negated sentence.

Age and sex use simple text matching. Pregnancy and hypertension confirmation use narrow phrases. A source quote shows where text came from; it does not prove the interpretation is right. Future extraction work should evaluate semantic correctness and omitted facts, not just whether emitted spans were copied.

## 4. Retrieval and ranking limits

The graph query uses selected one-edge associations. It is not a causal model or a calibrated disease probability. An absent graph candidate may reflect vocabulary mismatch, source coverage, schema issues, or an unrelated query.

The textbook corpus defaults to two complete books, not a complete medical library. Fixed word chunks can split sentences. Dense similarity, sigmoid reranker scores, graph association scores, and DrugCentral heuristic scores are not directly comparable clinical evidence strengths.

`EvidenceRanker` applies simple heuristics and can boost vector scores beyond one. The fusion prompt has a bounded evidence budget, so relevant content can be omitted. Authoritative retrieval can retrieve the wrong section even when the desired rule exists in the local corpus. A source identity check cannot recover a passage never retrieved.

The optional web scanner currently collects snippets that are not separately consumed by the ranker/fusion prompt. General drug interactions are not returned by the graph retriever. These hooks should be described as partial functionality, not complete evidence integration.

## 5. Model and control-flow limits

External providers can change availability, aliases, rate limits, or outputs. Temperature zero does not ensure bit-for-bit repeatability. OpenRouter's free route does not identify an immutable underlying model through the configured alias.

Fallback improves availability but confounds a retrieval comparison if arms use different providers. Strict controlled runners address part of this problem; they still cannot prove that an upstream alias never changed.

The retry heuristic is arbitrary and uncalibrated. Re-running extraction or retrieval cannot obtain missing real patient facts. Retries increase latency and calls, and the final report does not aggregate all attempts. A future workflow could request clarification from a user, but the current API is a single-case single-response interface.

## 6. API and operational limits

The request handler and retriever calls are synchronous. Database and model objects are shared in a process-wide dictionary; initialization has no lock. Mutable provider trace state is not designed as a robust concurrent audit record. There is no complete service shutdown lifecycle for closing every resource.

The API lacks authentication, authorization, application rate limiting, explicit case-length limits, governed audit records, and a documented retention policy. Health is liveness rather than dependency readiness. Neo4j errors can propagate while vector failures can degrade, so outage behavior is not uniform.

The development server enables reload and broad binding. Database helper scripts publish development ports and include a default Neo4j password; Qdrant's image is unpinned. These scripts are a convenience, not a production deployment definition.

## 7. Privacy and data handling

Local Neo4j and Qdrant do not make the system fully offline. Model prompts contain case content, optional search uses derived symptom/condition terms, and some console messages include case-derived feedback. There is no implemented privacy-governance layer for identifiable patient data.

The project does not deliberately save a clinical record history through its API, but evaluation captures and logs can contain inputs and reports. “No patient database” is not the same as “no data can persist anywhere.” Demonstrations should use synthetic cases.

## 8. Evaluation limits

The six-case fixtures expose their reference diagnosis in the case text. The four-condition pilot is small and author-labeled. The selected 36 MedQA vignettes are public exam material and were reused for development. Known-passage retrieval probes are derived from the same small source corpus. The 108 safety cases are reused developer-authored templates.

The live safety comparison did not beat its deterministic baseline. A rule-filtered arm improves precision at a recall cost. The QA adapter pilot remains incomplete and uses unequal inference budgets. Several historical comparisons had provider mismatches or broken graph coverage.

Independent clinical support labels, patient applicability judgments, fresh held-out evaluation, and workflow outcomes are absent. Exact answer matches, citation checks, and synthetic warnings cannot substitute for them.

## 9. Proposed improvement sequence

These are future steps, not features completed by this documentation task.

### Stage A: make the current implementation easier to operate

- Align runtime input paths with configuration.
- Add explicit startup/shutdown and dependency readiness.
- Remove shared mutable per-request trace state.
- Define consistent dependency-failure responses and bounded request handling.
- Lock package and container versions and record an environment inventory.

Success would mean a fresh authorized environment can run the declared setup and expose clear readiness/failure states without relying on undocumented local data.

### Stage B: improve extraction and retrieval on separate development data

- Review negation, chronology, drug names, dose statements, and units.
- Measure extraction omissions and errors using independently labeled fields.
- Create independently judged graph/text retrieval questions.
- Compare dense, lexical, and reranked retrieval with fixed inputs.
- Track retrieval relevance separately from final answer agreement.

Success would mean improvements on predefined development tasks, followed by confirmation on untouched material rather than repeatedly tuning the same cases.

### Stage C: expand clinical evidence deliberately

- Review additional source documents and jurisdictions.
- Add source-specific parsers and version/update procedures.
- Implement explicit rule scope and clinical prerequisites.
- Add supported and adversarial tests for each new rule.
- Keep general semantic support distinct from deterministic source-backed decisions.

Success would mean declared, reviewed coverage for each added condition/drug. It would not mean every medical statement becomes automatically verifiable.

### Stage D: perform independent evaluation

- Use independent authorship, matching reviewer records, and exposure exclusions.
- Freeze tasks, primary comparisons, code, prompts, data, and configuration.
- Compare strong deterministic and model baselines under declared compute budgets.
- Retain failed attempts and report useful coverage as well as false support.
- Use appropriate case/family-level analysis and publish permissible artifacts.

Success would mean independently reviewed evidence for a narrow stated task. A clinical deployment claim would need additional governance, validation, and operational work beyond this research plan.

## 10. Claims to use in a presentation

| Accurate statement | Evidence needed before making a stronger claim |
| --- | --- |
| “The gate checks exact pinned source identity.” | Broader attacks and trust-model analysis for universal tamper-resistance claims |
| “The code has two amlodipine label rules.” | Reviewed multi-drug rules and held-out cases for general medication safety |
| “The report exposes uncertainty and missing facts.” | Human-factors studies for better clinician decisions |
| “Retrieval repairs improved some development metrics.” | Fresh controlled comparisons for general performance benefit |
| “The pipeline uses graph and text retrieval.” | Component ablations for a causal graph-benefit claim |
| “Most generated claims remain unverified.” | A reviewed semantic verifier and useful-coverage evidence for automatic clinical support claims |

Being clear about these boundaries makes the project easier to assess and gives future work concrete acceptance criteria.
