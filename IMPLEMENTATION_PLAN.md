# Evidence-linked CDSS implementation plan

Updated: 2026-10-07. This is the active implementation and progress record for this checkout.

## Goal and boundary

Keep the current pipeline: clinical clarifier → retrieval orchestrator → evidence ranker → conflict detector → clinical fusion → confidence evaluator → report. Add curated guideline and drug-label evidence to retrieval, then a small claim-verification gate between fusion and confidence. The output should present conditional options for clinician review, with exact sources and explicit unknowns. Do not claim that the prototype is clinically validated or that a medicine is safe merely because a source is linked.

The first implementation should cover one defined clinical area and a versioned source set. Preserve the existing `/health` and `/analyze` API behavior while adding the new report fields.

## Git checkpoints and progress

| Step | Status | Git checkpoint | Completion gate |
| --- | --- | --- | --- |
| 0. Save the current prototype | Complete | `pre-claim-verification` (`e00a737`) | Baseline source committed; credentials, datasets, virtual environment, and large references excluded. |
| 1. Replace stale handoff documents | Complete | `implementation-plan-v1` | This plan and README are current; obsolete handoff files removed. |
| 2. Define evidence and claim contracts | Complete | `claim-step-2-contracts` | Stable source IDs, source spans, claim status, and backward-compatible API models tested. |
| 3. Curate and ingest authoritative sources | Complete (technical; clinician review pending) | `claim-step-3-sources` | Adult hypertension sources indexed with pinned checksums, exact sections, and validated retrieval. |
| 4. Extract patient context and unknowns | Complete | `claim-step-4-context` | Allergies, current medicines, blood pressure, selected labs, and missingness survive extraction, retry, and report. |
| 5. Produce source-linked diagnostic and treatment claims | Complete | `claim-step-5-claims` | Fusion returns conditional claim proposals with exact candidate source IDs; all remain unverified until Step 6. |
| 6. Verify claims and medication warnings | Pending | `claim-step-6-verification` | Citation IDs and source spans resolve; applicable warnings are checked; missing safety data causes abstention. |
| 7. Expose the report in API and UI | Pending | `claim-step-7-report` | The clinician can inspect each claim, condition, warning, and exact reference. |
| 8. Evaluate and document limitations | Pending | `claim-step-8-evaluation` | Reproducible claim, safety, and diagnostic metrics with baselines and error review. |

Work on the `claim-verification` branch; `main` remains at the pre-claim-verification prototype. For each future step: update its row and the progress log below, run that step's checks, make one focused Git commit, and add the named tag. Record any known limitation before marking the step complete. Keep `.env`, source documents with licensing restrictions, dataset dumps, and generated database files out of Git. Do not modify ignored source data in a way that would need Git for recovery; store hashes and ingestion instructions in the tracked manifest.

Inspect the old version with `git show pre-claim-verification:<path>` or `git switch --detach pre-claim-verification` in a separate checkout. To undo a completed step on the working branch, use `git revert <commit>` after reviewing dependent steps. `git log --oneline --decorate` shows the checkpoints.

## Step 2 — Evidence and claim contracts

Extend `backend/schemas/evidence.py`, `retrieval.py`, and `report.py` before changing generation logic.

- Give each source passage a stable ID derived from document ID, version, section, and span. Stop using a fresh runtime UUID as the only citation identity.
- Keep source organization, document title, document ID, publication/update date, URL, jurisdiction, section, and a short verifiable passage. Label the source as guideline, drug label, study, graph relation, or other.
- Represent each diagnosis, investigation, treatment option, and warning as a typed claim with `claim_id`, text, conditions, source IDs, and status: `supported`, `conflicting`, or `unverified`. Record why a claim is unverified. A graph edge is a candidate-generation signal unless its source supports the clinical claim.
- Preserve current fields while adding new ones so existing API clients continue to parse reports.

**Gate:** schema validation, serialization, stable-ID tests, and a fixture proving missing provenance cannot be labeled `supported`.

## Step 3 — Source curation and retrieval

Use the existing retrieval orchestrator and Qdrant path. Add separate collections or source filters for guidelines and drug labels; keep the existing Neo4j graph and textbook collection. The initial corpus should be deliberately narrow and reviewed by a clinician or domain expert.

- Track a source manifest with owner/publisher, URL, jurisdiction, version/date, license or reuse terms, local checksum, clinical scope, and retirement status. Prefer original guideline recommendations and official prescribing information. NCBI is a host/index; record the actual document author and publisher.
- Chunk by recommendation or label section so the cited span remains intelligible. Store metadata with every Qdrant point. Do not index evaluation answer keys.
- Treat Serper results as discovery leads. Retrieve and validate the original document before its content can become report evidence; a search snippet cannot support a claim.
- Make failed or stale source retrieval visible as `unverified`, rather than silently replacing it with general LLM knowledge.

**Gate:** repeatable ingestion, checksum verification, exact source retrieval for known questions, and tests that reject snippets or missing metadata as citation evidence.

## Step 4 — Patient context and missingness

`PatientContext` already has allergies, vitals, and labs, but the clarifier currently does not populate most of them. Extend its extraction and validation without changing the API entry point.

- Distinguish `no known allergy` from `allergy information not supplied`. Preserve the original phrase and extraction certainty for clinically important facts.
- Capture current medicines and the observations required by the selected clinical area. Do not infer a normal result from absent input.
- Surface missing information that would change a treatment or safety check. Leave the corresponding option conditional or withheld.

**Gate:** fixtures for explicit allergy, explicit no-known-allergy, unknown allergy, conflicting medication statements, and missing observations.

## Step 5 — Claim-linked synthesis

Have `ClinicalFusion` consume normalized evidence and emit the Step 2 claim structure. A treatment option must name the diagnosis or condition under which it applies. Keep investigations and medication options separate from diagnoses.

- Require citation IDs for source-backed statements and identify claims without adequate evidence as `unverified`.
- Keep supporting, conflicting, and unverified evidence distinct; do not hide contradictory findings.
- Avoid imperative fields such as `medicines_to_use`. Use `treatment_options_if_confirmed` and list prerequisites or missing checks.
- Remove the report generator's current generic treatment sentence, which is added without a source.

**Gate:** structured-output fixtures cover valid, malformed, contradictory, and citation-free model responses; provider fallback still works.

## Step 6 — Claim verification and safety

Insert a small validator after fusion and before confidence/report. It checks source identity and applicability independently of the model that wrote the claim. Expand the existing conflict detector for medication safety rather than replacing it.

- Check that each referenced ID resolves to the cited document version and passage; verify that the passage is about the stated population, intervention, and outcome. Use explicit rules for facts that can be checked deterministically; send ambiguous support for clinician review rather than declaring it verified.
- Check allergies, current-medication interactions, contraindications, and patient-specific prerequisites against appropriate labels or guidelines. DrugCentral target associations alone do not prove a contraindication or a treatment recommendation.
- If a required patient fact or source is absent, emit a warning or abstain. Never convert `unknown` to `safe`.
- Do not display the current confidence score as a calibrated probability. Assess evidence completeness and verification failures separately; show a percentage only after calibration is measured.

**Gate:** negative tests for wrong citation, wrong population, outdated version, allergy conflict, missing allergy status, and missing source; manually review a sample of positive claims.

## Step 7 — API, report, and UI

Extend `ClinicalReport` and `/analyze` with case summary, ranked differential, claim-linked evidence, conditional investigations and treatments, medication safety, and limitations. Retain existing response fields during migration. In the UI, make each citation open the exact source URL and show its section/date beside the claim.

**Gate:** API contract tests, a representative clinician-readable report, and checks that warnings and unknowns remain visible in the UI.

## Step 8 — Evaluation before publication claims

Freeze a test set that is separate from indexed sources. Compare at least LLM-only, text-RAG, and the proposed graph-plus-text approach. Report diagnostic top-k performance alongside citation validity, claim support accuracy, unsupported-claim rate, medication warning sensitivity, unsafe-option rate, abstention rate, and latency. Have qualified clinicians review a blinded sample and document disagreements. Include failure cases and source dates. This supports a claim about evidence-linked decision support; clinical safety or outcome benefit needs stronger validation.

**Gate:** one reproducible command generates metrics and case-level errors, with dataset version, model/version, prompts, source manifest hash, and run settings recorded.

## Progress log

- 2026-10-07 — Step 0 complete. Initialized Git and saved the current prototype as `e00a737` / `pre-claim-verification`. Moved credentials from a loose Markdown note and source literal into ignored `.env` before the first commit; Serper still reads the same active key. Focused LLM fallback tests: 2 passed. Broader clinical evaluation has not been established.
- 2026-10-07 — Step 1 complete on `claim-verification`. Created this plan, updated README, and removed obsolete handoff notes and old logs. No claim-verification feature has been implemented yet.
- 2026-10-07 — Step 2 complete. Added versioned source-passage IDs, typed clinical claims, source links in retrieval/report schemas, and structural provenance checks. Existing report fields still parse. Six focused tests pass. The existing FastAPI `TestClient` health test hangs in this environment and was stopped after 15 seconds; no full API test was claimed. Source-to-claim semantic verification remains Step 6.
- 2026-10-07 — Step 3 technical implementation complete. Pinned NICE NG136 recommendations (England; snapshot dated 2026-02-26) and a DailyMed amlodipine SPL label (United States; effective 2026-01-01) in a versioned manifest with source scope, reuse terms, jurisdiction, retirement flag, and SHA-256. Raw snapshots are ignored by Git. The official downloads replayed with identical checksums. Section parsing yielded 17 recommendation passages and 9 label passages; both dedicated collections were populated in the running Qdrant service. Real-model queries returned NICE Recommendation 1.4.35 and the DailyMed contraindications section for known questions. Retriever rejects incomplete or forged payloads, checks local snapshots and indexed versions against the manifest, and returns limitations when retrieval fails. Serper snippets remain separate discovery data. Focused tests passed; a broader existing clarifier test still fails when all external LLM providers are unreachable, unrelated to this step. Independent clinician review of source choice and applicability is pending. NICE and DailyMed cover different jurisdictions; retrieval yields candidate passages only, and later claim verification must check jurisdiction, population, and patient applicability before showing a supported recommendation.
- 2026-10-07 — Step 4 complete. Added explicit allergy and medication states, source phrases and extraction certainty, blood pressure readings with measurement setting, pregnancy and documented hypertension status, selected lab results, and missingness to `PatientContext`. The clarifier accepts model hints only when anchored to the original case and conservatively extracts common explicit statements when providers fail. Conflicting medication statements do not become a current medicine; unknown allergy or absent observations are not treated as normal. The retry path reprocesses the original case, and patient missingness reaches the final report. Hypertension treatment suggestions are withheld when required patient facts are missing. Nineteen focused tests passed, including a direct route test that forces a retry. Extraction rules cover common English phrasing only; ambiguous statements remain unknown for clinician confirmation. Lab units are retained when stated and flagged when absent. Patient-specific treatment eligibility and source-to-claim verification remain Steps 5–6, so this is not a clinical safety validation.
- 2026-10-07 — Step 5 complete. Fusion now requests separate diagnostic, investigation, and `treatment_options_if_confirmed` proposals. Treatment proposals require an applicable condition and explicit prerequisites; patient missingness is copied into their pending checks. Only IDs from the retrieved authoritative passages can remain in citation buckets. Unknown, graph-only, and web-snippet IDs are recorded as rejected; an ID assigned incompatible evidence roles moves to the unverified bucket. Claims retain candidate supporting and conflicting IDs but all have `status=unverified` until independent semantic and patient-applicability verification in Step 6. The report carries claims and exact source passages through `/analyze`; legacy diagnosis fields remain, while uncited free-text medicine and investigation suggestions and the report generator's generic treatment sentence are removed. Twenty-six focused tests passed, covering valid, malformed, contradictory, citation-free, fallback, and route output cases. The current UI does not display these claims yet (Step 7), and source presence is not proof of clinical support or safety.
