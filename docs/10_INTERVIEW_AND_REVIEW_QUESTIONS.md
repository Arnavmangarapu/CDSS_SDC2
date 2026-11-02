# 10 — Interview and review question bank

[Documentation index](README.md) · [Previous: limitations](09_LIMITATIONS_AND_FUTURE_WORK.md) · [Next: demo guide](11_DEMO_AND_EXPLANATION_GUIDE.md)

This bank contains **180 likely questions**, with short answers grounded in the repository. It covers project explanation, code review, algorithms, data, research, operations, and difficult scenarios. No finite list can predict every follow-up; use the answers as starting points and be ready to open the linked implementation guides.

## A. Project purpose and fundamentals — questions 1–15

### 1. What does this project do?

It turns a free-text synthetic clinical case into extracted context, differential candidates, conditional investigation/treatment claims, narrow medication warnings, and traceable source passages for review.

### 2. What problem are you trying to solve?

Generated clinical text can sound convincing without valid support. The project exposes patient facts, candidate evidence, exact citations, missing checks, and verification state separately.

### 3. What is the main contribution?

An evidence-linked claim workflow with explicit uncertainty, pinned-source identity checks, and narrow label-backed rules. It is not a general medical truth verifier.

### 4. Who is the intended user?

A clinician or researcher reviewing experimental output. The current application is a research prototype, not a validated patient-facing diagnostic or prescribing service.

### 5. What does CDSS mean?

Clinical Decision Support System. Here it means software that organizes candidate findings for review, rather than making autonomous clinical decisions.

### 6. What is RAG?

Retrieval-augmented generation: find relevant external information first, then provide it to a language model while asking it to generate an answer.

### 7. What makes this Graph-RAG?

It combines Neo4j biomedical relationships with text retrieval. Selected graph candidates and retrieved passages enter the proposal process.

### 8. Is this a graph neural network?

No. The implemented graph component uses Cypher queries and association counts. There is no trained graph neural network in the runtime path.

### 9. What does “multi-agent” mean here?

Named Python components divide extraction, ranking, fusion, checking, retry, and reporting. They run in one synchronous application rather than independent debating workers.

### 10. How is this different from asking an LLM directly?

It adds local retrieval, explicit facts and missingness, structured proposals, source identity checks, narrow safety rules, and inspectable report contracts.

### 11. Does the project diagnose diseases?

It proposes a differential. Its scores and outputs have not been validated as patient diagnoses.

### 12. Does it prescribe medication?

It presents conditional treatment proposals and a few warning conditions. It does not establish prescribing eligibility or issue a validated prescription.

### 13. What is the authoritative clinical scope?

Selected adult hypertension recommendations and one amlodipine label. Broader graph/textbook candidate generation does not expand the verifier's source scope.

### 14. What are the major technologies?

Python, FastAPI, Pydantic, Neo4j, Qdrant, Sentence Transformers, a cross-encoder, RapidFuzz, external model APIs, and a static HTML/CSS/JavaScript frontend.

### 15. What should you never claim from the current results?

Clinical validation, guaranteed medication safety, calibrated probabilities, universal semantic verification, or general superiority of Graph-RAG over an LLM.

## B. Architecture and control flow — questions 16–30

### 16. Where does an analysis start?

The browser sends `POST /analyze`; `backend/api/routes.py` coordinates the complete processing path.

### 17. What is the processing order?

Clarify, retrieve, rank, detect initial conflicts, propose claims, verify, apply medication rules, decide retries, then build the report. See [guide 03](03_END_TO_END_REQUEST_FLOW.md).

### 18. Why separate components?

It makes responsibilities, intermediate objects, failures, and tests easier to inspect. Deterministic verification can be reviewed separately from model generation.

### 19. Which components actually call a model?

The production clarifier and fusion component use `LLMFallback`. Ranking, claim identity checks, retry scoring, and report grouping are Python logic.

### 20. Are retrieval branches parallel?

No. The current orchestrator calls graph, textbook, authoritative, DrugCentral, and web retrieval sequentially despite the “fan-out” wording in its comment.

### 21. Why initialize services lazily?

Ontologies and models can be expensive to load. `get_pipeline()` initializes on first analysis and reuses objects, trading repeated loading for shared-state concerns.

### 22. What is stored in `pipeline_state`?

The clarifier, orchestrator, ranker, conflict detector, fusion, verifier, confidence evaluator, retry helper, and report builder for the process.

### 23. What is the concurrency risk?

Initialization has no lock, and shared LLM objects have mutable trace fields. Concurrent requests need isolated per-request metadata and a reviewed lifecycle.

### 24. What is `PatientContext`?

The typed intermediate patient representation: original input, linked entities, explicit status fields, observations, missing information, and safety flags.

### 25. Why keep retrieval sources in separate fields?

Graph associations, textbooks, drug targets, discovery snippets, and pinned passages have different trust roles. Separation prevents silently treating every hit as an authoritative citation.

### 26. What controls retries?

An uncalibrated score based on the first diagnosis score, high-severity conflicts, and missing-information counts. It is a control heuristic, not clinical confidence.

### 27. How many analysis attempts can the API make?

One initial attempt plus at most two adaptive retries, because the route constructs `AdaptiveRetry(max_retries=2)`.

### 28. Can retries invent new patient facts?

They should not. The route re-extracts the original case and keeps generated feedback only in the expanded retrieval query. Extraction can still be fallible.

### 29. Are reports merged across attempts?

No. The final report uses the final attempt's variables. Earlier attempts are not combined into a consensus report.

### 30. What is the most important trust boundary?

The transition from candidate evidence and model proposals to checked source-backed decisions. Exact provenance is necessary but insufficient for clinical support.

## C. Patient extraction and entity linking — questions 31–45

### 31. Why use both model extraction and deterministic rules?

The model handles varied language, while rules require selected safety facts to be anchored to input phrases and preserve unknown/conflicting states.

### 32. Which facts are extracted deterministically?

Specific medicine/allergy assertions, selected BP/lab patterns, pregnancy phrases, hypertension confirmation phrases, and demographics. Coverage is limited to implemented patterns.

### 33. What does a source phrase prove?

That the quoted text appears in the input. It does not prove the interpretation is correct, complete, current, or about the patient rather than someone else.

### 34. Why distinguish unknown allergies from no known allergies?

Missing history does not establish absence. The difference affects uncertainty warnings and prevents silent safety clearance.

### 35. How are conflicting histories represented?

Allergy and medication-list states can be `conflicting`; flags and missing checks request reconciliation. Current/stopped statements are retained.

### 36. How are stopped medicines handled?

They are stored as stopped statements. A conflicting current/stopped name is excluded from the clarifier's resolved current medicine list, with history marked conflicting.

### 37. Do all downstream fields use the same resolved medicine list?

No. Some safety/report code reads raw explicit current statements while also retaining list status. Review conflicting-history behavior rather than assuming perfect reconciliation everywhere.

### 38. What happens if all extraction providers fail?

The clarifier uses empty model hints and limited deterministic extraction. It cannot recover broad symptom/condition understanding from missing model output.

### 39. How does ontology linking work?

Normalize text, restrict to the appropriate vocabulary, try exact matching, then RapidFuzz `WRatio` with a default threshold of 85.

### 40. Why restrict matches by entity type?

A name can appear in multiple vocabularies. HPO for symptoms, MONDO for conditions, and DRUG for medicines/allergens reduces wrong-domain matches.

### 41. What happens when a phrase has no accepted match?

The phrase remains a `LinkedEntity` without a normalized concept ID. The system does not require every mention to map successfully.

### 42. Is linker confidence a disease probability?

No. It describes lexical match strength. An exact ontology name match does not establish a diagnosis.

### 43. Is negation fully handled?

No. Selected medicine/allergy patterns handle some negation. Generic symptom extraction and simple critical-keyword fallback are not a complete negation parser.

### 44. How are labs and BP handled?

Selected numerical patterns produce observations with source phrases. Missing units or measurement settings are flagged; general unit conversion and longitudinal interpretation are not implemented.

### 45. Give an extraction bug that was repaired.

“No allergy history was recorded” previously became an allergy mention. The repair keeps it unknown, with regression cases for missing and negated allergy history.

## D. Graph data and queries — questions 46–60

### 46. Which graph dataset is used?

A local PrimeKG CSV. The importer selects four clinical relation types rather than loading every relationship as a useful runtime signal.

### 47. What is the node label?

`ClinicalEntity`, with properties including global UID, raw ID, ontology ID, name, source, and type.

### 48. Why use the global PrimeKG index?

Raw vocabulary IDs can collide across sources or entity types. `PrimeKG:<index>` avoids incorrectly merging distinct nodes with the same raw ID.

### 49. Which relationships are imported?

Positive/negative phenotype–disease relations, drug contraindications, and drug indications. They map to four explicit Neo4j relationship names.

### 50. How are reverse edges deduplicated?

The importer canonicalizes direction, deduplicates endpoint pairs within batches, and uses `MERGE` so repeated rows do not create repeated stored relationships.

### 51. Does the importer read only the first 50,000 rows?

No. That describes older code. The current importer streams the full CSV in 100,000-row chunks and selects the declared relations.

### 52. What makes graph ingestion bounded?

Chunked CSV reads and transaction batches limit working memory and write size. It still needs substantial time and storage for the selected graph.

### 53. What indexes and constraints are created?

A unique `ClinicalEntity.uid` constraint and indexes on `name` and `ontology_id`, followed by an index-readiness wait.

### 54. How are graph diseases ranked?

By matched positive minus negative phenotype associations, then positive count and name. At least one positive association is required; at most ten candidates return.

### 55. What does a negative graph association mean?

The stored relation lowers that disease's association score when matched. It is not proof that the patient's narrative explicitly negated a symptom.

### 56. Does the graph perform multi-hop reasoning?

The current disease query uses direct phenotype–disease edges. It does not implement arbitrary multi-hop reasoning or causal inference.

### 57. How are graph contraindications used?

Current medicine names retrieve up to 100 associations. The initial detector flags concerns overlapping candidate diseases as unverified leads requiring authoritative checking.

### 58. Does an imported indication automatically produce treatment advice?

No. The runtime graph retriever does not use the indication edges to clear treatments. Import coverage and actual query use are separate.

### 59. Why might graph retrieval return nothing?

No symptoms, failed ontology linking, name/ID mismatch, missing relation coverage, or wrong schema. A zero result is not always a database outage.

### 60. Can a Neo4j outage always degrade gracefully?

No. Query exceptions are not fully caught by `GraphRetriever`; they can propagate and fail analysis. Vector retrieval has different degradation behavior.

## E. Text retrieval and models — questions 61–75

### 61. Why use Qdrant as well as Neo4j?

Neo4j searches explicit relationships; Qdrant searches similar passage vectors. They provide complementary candidate information.

### 62. What is the default textbook corpus?

Complete First Aid Step 1 and Pathoma files in the designated local MedQA textbook directory. Two full files do not mean complete medical coverage.

### 63. What is the active textbook collection?

`medical_textbooks_v2` by default, configurable through `VECTOR_COLLECTION_TEXTBOOKS`.

### 64. How is textbook text chunked?

150 words per chunk with 20-word overlap. It preserves the file's end but can split sentences.

### 65. Why overlap chunks?

To reduce context loss at boundaries. The tradeoffs are duplicated content, more points, and correlated retrieval results.

### 66. How are textbook point IDs assigned?

A deterministic UUID uses filename, document checksum, and chunk index. Identical inputs give stable point identities.

### 67. What encoder is configured?

`pritamdeka/S-PubMedBert-MS-MARCO` at a pinned revision, with 768-dimensional textbook vectors and cosine distance.

### 68. What is a cross-encoder doing here?

It reads a query and passage together to score relevance, reordering a smaller set of candidates after dense retrieval.

### 69. Why not cross-encode the whole library for every query?

Pairwise scoring is more expensive. Dense retrieval first narrows the candidates, then reranking improves their order at extra latency cost.

### 70. How many textbook hits are retrieved?

The default path fetches at least 20 dense candidates and returns five after optional reranking.

### 71. Are model downloads performed during analysis?

Runtime loading uses `local_files_only=True`. `ingestion.prepare_models` is the separate download step for the configured revisions.

### 72. What if the reranker is missing?

Supported local loading failures leave dense ranking active. This is a changed retrieval configuration and must be disclosed in comparisons.

### 73. Is a reranker sigmoid score a probability of truth?

No. It is a transformed relevance score, not calibrated diagnosis, entailment, or treatment safety.

### 74. Why exclude the old `medical_literature` collection?

Inspection found different vector dimensions and exam question/answer content. It was not a clean compatible textbook replacement for the frozen evaluations.

### 75. Does the textbook importer overwrite collections?

No. It refuses existing collections and manifest paths. Authoritative-source ingestion has different replacement behavior.

## F. Pinned sources and provenance — questions 76–90

### 76. What is in the source manifest?

Document identities, versions, dates, publisher URLs, selected sections, local paths, jurisdictions, reuse notes, retired state, and SHA-256 checksums.

### 77. Which publisher hosts are accepted?

The current manifest validator approves HTTPS NICE and DailyMed hosts. Adding another publisher requires reviewed code and source-process changes.

### 78. Why pin exact source bytes?

To detect silent document changes and reproduce the source version used in a run. A live URL alone cannot identify historical content.

### 79. What happens when a publisher updates its document?

`fetch` rejects a checksum mismatch. Review the new content, update/version the manifest, retain permitted snapshots, and rebuild the intended source index.

### 80. Does checksum matching prove medical correctness?

No. It proves equality to the pinned bytes within the trust model. It says nothing by itself about clinical truth, freshness, or source selection quality.

### 81. How does a SourcePassage ID work?

It hashes publisher, document ID/version, section, span, and passage-text hash, producing a stable `src_` identifier. See [guide 05](05_CLAIMS_VERIFICATION_AND_SAFETY.md).

### 82. Why compare full source objects as well as IDs?

Not every metadata field is in the ID recipe. Full equality also checks fields such as URL, jurisdiction, and dates against the pinned object.

### 83. What do passage offsets refer to?

Normalized extracted section text, not raw HTML bytes, document page numbers, or a clinical record's character positions.

### 84. How many passages are in the saved pinned corpus?

The saved snapshots contain 17 NICE passages and nine label chunks. The label count depends on the selected snapshot and parser output.

### 85. Are guidelines always returned before labels?

That was historical behavior. Current authoritative retrieval merges by reranker score or dense score, with stable ID tie-breaking.

### 86. Why have an authoritative scope filter?

The source corpus is narrow. Unrelated cases should not receive hypertension/amlodipine passages merely because a normal BP was mentioned.

### 87. Does a BP routing threshold diagnose hypertension?

No. It chooses whether to search this corpus. Diagnostic confirmation and applicability remain separate.

### 88. Does authoritative ingestion preserve its old collections?

It validates snapshots, then deletes/recreates the configured dedicated collections. Back up or choose new collection names when preserving previous indexes.

### 89. Why are raw source documents absent from Git?

They are retained locally under source-use constraints. Git contains metadata and hashes; reproduction also needs the exact permitted snapshots.

### 90. What if the manifest and local files are both maliciously changed?

Checksums alone cannot protect a compromised trust root. Protect and review manifests and source changes; the current gate assumes trusted local pinning metadata.

## G. Claims, verification, and rules — questions 91–105

### 91. What claim types exist?

Diagnosis, investigation, treatment, and medication warning. Model proposals use the first three; explicit rules create the implemented supported warning claims.

### 92. What do the three claim states mean?

`unverified` needs review, `supported` has the implemented source-backed rule support, and `conflicting` identifies a checked conflict such as amlodipine treatment with reported allergy.

### 93. Why do general claims remain unverified?

The gate does not establish broad semantic entailment and patient applicability. It deliberately avoids promoting a proposal just because a valid citation exists.

### 94. Can the model declare itself verified?

No. Proposal parsing/normalization starts generated claims unverified, and independent code determines later outcomes.

### 95. What happens to hallucinated citation IDs?

Normalization retains them as rejected IDs rather than active citations. Verification records failures/review reasons; they cannot become trusted evidence.

### 96. Why separate supporting and conflicting evidence?

A passage can argue against a proposal. Merging all citations into one list would hide that direction and encourage misleading support presentation.

### 97. What if one source is assigned incompatible roles?

Normalization removes it from those competing buckets and puts it into the unverified bucket with a reason.

### 98. What treatment constraints are enforced?

A named applicable condition, explicit conditions, missing checks, and rejection of selected imperative openings. These are structural safeguards, not complete clinical validation.

### 99. What are examples of source-scope mismatch checks?

Adult NICE guidance for a known child, pregnancy treatment exclusions, treatment sections used for diagnosis, and label passages missing the topic claimed.

### 100. What two label rules are implemented?

Reported amlodipine allergy with relevant exposure/proposal, and current simvastatin with amlodipine relevance. Both require the exact trusted label sections for support.

### 101. Can an allergy rule change a treatment claim?

Yes. Explicit amlodipine allergy plus the trusted contraindication passage can mark an amlodipine treatment proposal conflicting.

### 102. What happens if allergy history is unknown?

The medication path produces an unconfirmed-allergy concern when relevant. It does not invent an allergy or clear safety.

### 103. What happens if the expected label passage is not retrieved?

The rule cannot produce a supported warning from it. It records an unverified source gap or concern instead.

### 104. Can a supported interaction warning prescribe a dose?

No. It requests dose/interaction review against the label. The code does not establish the patient's actual dose or a complete prescribing plan.

### 105. What does the report schema guarantee?

Unique IDs, resolvable active citations, correctly typed claim groups, and required status evidence/reasons. It does not guarantee medically correct text.

## H. Language models and fallback — questions 106–120

### 106. What is the fallback order?

Gemini Flash Lite, Gemini Flash, Cohere, Mistral, OpenRouter. Providers without nonblank keys are skipped.

### 107. Where are requested model names defined?

In `backend/services/llm_fallback.py`. They are configured aliases, not proof of immutable upstream model weights or current account availability.

### 108. What makes a provider response usable?

Successful transport, parseable JSON object, and the supplied client validation callback. Valid JSON can still fail the required structure.

### 109. Which failures trigger another provider?

Supported request errors, invalid JSON, missing keys, wrong types, and validation failures. The adapter catches specific exception categories, not every possible failure.

### 110. Does the adapter remove Markdown JSON fences?

Yes, it strips common outer fences before parsing. That does not replace schema or clinical checks.

### 111. Why send a JSON Schema to Gemini?

To constrain synthesis structure at generation time. Independent client validators still check the resulting lists, claims, and conditions.

### 112. Why ignore reasoning-only response parts?

They may contain non-JSON analysis. Only response text parts intended as output should be concatenated into the JSON parser input.

### 113. What are the request timeouts?

The shared provider transport uses a 5-second connection and 35-second read timeout. Multiple provider attempts and analysis retries can multiply wall time.

### 114. What does temperature zero guarantee?

It requests low-variability generation. It does not guarantee repeatable outputs, immutable models, correctness, or identical infrastructure behavior.

### 115. What does synthesis failure return?

A zero-score synthesis-unavailable candidate, missing-information reason, and unverified graph candidate claims if graph names are available.

### 116. How is the actual provider recorded?

LLM objects keep selected provider/model metadata and expose `response_trace()`. Evaluation records those traces; the normal API does not expose a full provider-trace object.

### 117. What extra Gemini metadata is captured?

Returned model version, response ID, token-count metadata, and finish reasons when present. A returned alias still does not independently certify fixed weights.

### 118. Why is fallback a problem for experiments?

Different retrieval arms may end up using different providers. That confounds retrieval effects with model differences.

### 119. How do controlled runners address that?

They fix a requested model, disable fallback/adaptive retries where specified, preserve failures, and freeze relevant data/code/configuration. Upstream alias uncertainty remains.

### 120. Was an LLM fine-tuned for this project?

The inspected runtime uses pretrained retrieval models and external generation APIs. It contains no project-specific fine-tuning or weight-training pipeline.

## I. API, frontend, and report contracts — questions 121–135

### 121. What request does `/analyze` accept?

A JSON object with required string `case_text`. There is no declared maximum length or backend nonblank constraint.

### 122. What are the top-level response objects?

`patient_context`, `retrieval`, and `report`. See [guide 07](07_API_AND_FRONTEND.md) for their meaning and examples.

### 123. Does `/health` prove readiness?

No. It confirms the API process with fixed status data. It does not verify stores, model caches, source snapshots, or providers.

### 124. Is there a frontend framework?

No. Static HTML, CSS, and JavaScript are mounted under `/ui` by FastAPI. There is no npm frontend build step.

### 125. Why use same-origin API calls?

The UI and API are served by one application, so the browser posts to `/analyze` without a separate frontend/API origin configuration.

### 126. How is empty input handled?

The UI trims and rejects it. The API's plain string schema still accepts an empty string structurally.

### 127. What does the spinner mean?

Only that a request is pending. It is not live backend progress; the API returns one complete response without streaming.

### 128. How does the UI handle failures?

Request/network errors and rendering errors have separate messages. Rendering failure hides the partial report and asks for refresh/retry.

### 129. Why hide confidence percentages?

The scores are uncalibrated model/control values. Percentages could suggest diagnostic certainty that the system has not established.

### 130. Why retain legacy confidence fields in JSON?

For existing clients and retry compatibility. The report explicitly marks confidence as uncalibrated and provides richer claim structures.

### 131. How are claims associated with a diagnosis?

The report uses case-insensitive exact `applies_to` versus diagnosis-name matching. Synonyms can remain unassigned rather than automatically grouping.

### 132. How is generated text rendered?

Using `textContent` and text nodes, reducing HTML injection through model text. That is one safeguard, not complete application security.

### 133. Which citation links can be clicked?

Only HTTPS NICE and DailyMed host URLs pass the current UI allowlist. Others are shown as unavailable text.

### 134. Why set no-store cache headers on frontend assets?

To reduce stale scripts being paired with changed report markup after updates. It addresses a specific asset-version mismatch problem.

### 135. Is there report history or persistent patient storage?

The API implements neither. Logs, provider systems, and evaluation captures can still retain content, so absence of a patient database does not imply no persistence.

## J. Setup, operations, privacy, and scaling — questions 136–150

### 136. Why is a source clone insufficient to run everything?

Large datasets, exact publisher snapshots, models, populated Neo4j/Qdrant stores, and provider keys are separately required.

### 137. Where is configuration loaded from?

Environment settings and a repository-root `.env` through Pydantic settings. Keys are excluded from Git.

### 138. Do all path settings control runtime files?

No. The route and textbook importer construct some fixed repository-relative paths. Changing settings alone does not relocate those inputs.

### 139. What are the main service ports?

API 8000, Neo4j Bolt 7687/browser 7474, Qdrant HTTP 6333. The Qdrant helper also publishes 6334.

### 140. Are the Docker helpers production deployment scripts?

No. They expose development ports, use a default Neo4j password, and do not pin Qdrant's image. They do not containerize/harden the complete app.

### 141. What should you do if a container already exists?

Inspect and start the intended existing container. Avoid deleting volumes or launching another database pair on occupied ports.

### 142. Why back up stores separately from Git?

Git tracks code, not database volumes. Reproduction and rollback require data snapshots, image identities, collection configuration, and source/model hashes.

### 143. Is the application fully offline?

No. Retrieval models and databases can run locally, but configured LLM providers and optional Serper calls use external services.

### 144. What patient information can leave the process?

Case content in model prompts and symptom/condition terms in optional search. Console output and evaluation captures can also expose case-derived information.

### 145. Is authentication implemented?

No. There is no application login, authorization layer, rate limit, or governed clinical audit trail in the current implementation.

### 146. How would you improve concurrency?

Use explicit lifecycle management, isolated request traces, safe initialization, bounded work, and measured concurrency. This is proposed work, not existing behavior.

### 147. How would you reduce latency?

Measure stages first, then evaluate parallel independent retrieval, caching, context budgets, and bounded calls. Preserve source-version correctness and compare quality after changes.

### 148. Is cost per query known?

Not comprehensively. Some Gemini token metadata is captured, but complete provider-specific pricing, retries, initialization, and operating costs are not accounted for.

### 149. Are dependencies reproducibly locked?

No. `requirements.txt` is unpinned and one container image is unpinned. Record actual versions and build a lock/reproducible environment before strict replication claims.

### 150. What must change before handling real clinical records?

Independent validation, data governance, provider handling agreements, access controls, audit/retention policies, secure operations, and an appropriate reviewed clinical workflow. These remain future work.

## K. Testing, experiments, and metrics — questions 151–165

### 151. Which tests can run without deliberate live model calls?

The selected component suite excluding `tests/test_api.py` and unmocked `test_clarifier`. Use the command in [guide 08](08_TESTING_EVALUATION_AND_RESULTS.md).

### 152. Why not call the whole test suite an offline check?

Some API and clarifier tests invoke real services/providers. Their environment and expected model outputs are different from mocked deterministic regression checks.

### 153. What do the three diagnosis arms compare?

LLM-only, text retrieval, and graph-plus-text retrieval. They reuse clarification and the production analysis path while changing retrieval.

### 154. Why rotate arm order?

To reduce a fixed order's exposure to time-dependent rate limits or service conditions. It does not eliminate all provider/environment confounding.

### 155. Why disable web and DrugCentral in those comparisons?

To keep the declared retrieval arms controlled and avoid extra evidence channels favoring one arm.

### 156. What is top-k diagnosis agreement?

A normalized exact reference alias appears among the first k names. It is not independent patient diagnosis accuracy and may miss equivalent synonyms.

### 157. What does citation validity measure?

Exact source identity against pinned passages. It does not measure whether the citation semantically supports the statement or fits the patient.

### 158. Why report warning precision and recall together?

A filter can remove false warnings while missing useful ones. Always abstaining can look conservative but provides no supported coverage.

### 159. Why are the original six cases weak diagnostic evidence?

Their reference diagnoses are already stated in the input. They test recognition and boundary behavior, not diagnosis from an unknown case.

### 160. What were the repaired 36-case top-1 results?

18/36 LLM-only, 19/36 text RAG, and 17/36 graph-plus-text on reused development vignettes. They do not show graph superiority.

### 161. Did the live safety hybrid beat the deterministic baseline?

No. Exact cases were 106/108 for production extraction plus rules, versus 108/108 for deterministic extraction plus rules in the saved comparison.

### 162. Is the three-dataset QA pilot complete?

No. Saved results contain 255/300 planned arm attempts. Forty-five remained after a daily provider quota stop.

### 163. What does replay accomplish?

It rescoring saved outputs without fresh model answers. Matching metrics demonstrate scoring reproducibility, not that live generation will repeat identically.

### 164. How are failures counted in current primary diagnosis metrics?

All planned cases remain in the denominator; failed and empty outputs count incorrect. Completed-output-only scores are secondary.

### 165. What would make a stronger evaluation?

Fresh independent cases, qualified blinded labels, frozen protocols, strong baselines, fixed declared inference budgets, retained failures, and appropriate paired/family-level uncertainty analysis.

## L. Difficult reviewer scenarios and project defense — questions 166–180

### 166. A real guideline is cited for the wrong disease. What happens?

Some explicit scope checks flag it, and general claims still remain unverified. Exact provenance alone never makes the claim clinically supported.

### 167. The source ID is unchanged but the passage text is altered. What happens?

Normal source validation rejects an inconsistent derived ID; full object equality with pinned text adds another check. Mutated IDs do not bypass pinned membership.

### 168. A source is correct but stale. Can the gate detect clinical obsolescence?

Not automatically. It checks the pinned version. Source freshness requires an external review/update process.

### 169. A current medicine is mentioned alongside contradictory stopped history. Is safety resolved?

No. The status remains conflicting and requires reconciliation. Review downstream raw-current-statement use rather than treating the report as a resolved medication record.

### 170. An amlodipine label is available locally but no warning appears. Why?

The relevant exact section may not have been retrieved, facts may not satisfy the rule, or extraction may have failed. Local corpus presence is not end-to-end coverage.

### 171. The graph has more candidates after a repair. Has accuracy improved?

Not necessarily. Coverage and correctness are different. Check candidate relevance and paired end-task results on untouched data.

### 172. Why can RAG perform worse than LLM-only?

Irrelevant or misleading context, missing evidence, prompt truncation, graph mismatch, extraction errors, and model/provider variability can all reduce answer quality.

### 173. Would a second LLM verifier solve semantic support?

It would add another fallible model. A useful verifier needs independent labels, adversarial cases, calibration/coverage assessment, and a declared scope before support claims.

### 174. What ablations would you run next?

Hold extraction/model/cases fixed while comparing graph, corpus size, dense versus reranked text, prompt budget, and rule filtering. Prespecify outcomes and compute differences.

### 175. How would you add a new drug?

Review a versioned label, implement parsing and explicit rule scope, add fact requirements and boundary tests, then evaluate independently. Adding a drug name alone is insufficient.

### 176. How would you add a new disease?

Expand reviewed sources and retrieval scope, check ontology/graph coverage, define applicability rules and expected outputs, and obtain independent cases and labels.

### 177. What is the biggest current limitation?

General claim meaning and patient applicability are not automatically verified, while source/rule coverage is narrow and independent clinical validation is missing.

### 178. What exactly did you personally contribute?

Answer from actual work and history: files changed, decisions made, tests run, and measurements produced. Do not claim every repository component as personal authorship.

### 179. What would you change first with another month?

Choose a measurable scope: operational readiness and isolated traces, better fact extraction, or independently labeled retrieval/safety evaluation. Give an acceptance criterion instead of promising broad clinical deployment.

### 180. Why is this project still useful if most claims remain unverified?

It provides a concrete, auditable way to study evidence provenance, uncertainty, extraction, narrow rules, and failure modes. Its value must be assessed within that declared research scope.

## How to prepare beyond memorizing answers

For each area, practice a short explanation, open the relevant implementation, and trace one failure. Be able to distinguish implemented behavior, historical measurements, and proposed future work. Prepare to explain why a design was chosen, what it costs, how it was checked, and what evidence would change your conclusion.

For a project review, keep [the architecture](02_ARCHITECTURE_AND_CODE_MAP.md), [verification guide](05_CLAIMS_VERIFICATION_AND_SAFETY.md), [results guide](08_TESTING_EVALUATION_AND_RESULTS.md), and [demo guide](11_DEMO_AND_EXPLANATION_GUIDE.md) open alongside this bank.
