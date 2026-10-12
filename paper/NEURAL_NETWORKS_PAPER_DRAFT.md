# Title

**Evidence-linked Graph-RAG for clinician review of differential diagnoses and conditional treatment claims: system design and a synthetic feasibility study**

*Working manuscript draft, 12 October 2026. The headings follow the template supplied by the project owner. Formatting, word limits, declarations, and article type still require checking against the selected journal's current author instructions. This draft reports engineering feasibility, not clinical validation.*

# Author names and affiliations

**Author 1:** [Full legal name], [Department], [Institution], [City], [Country].

**Author 2:** [Full legal name], [Department], [Institution], [City], [Country], if applicable.

**Corresponding author:** [Name and institutional email].
**ORCID identifiers and author contributions:** [Supply for each actual contributor before submission].

These fields are intentionally open. Repository ownership or Git commits do not establish manuscript authorship or affiliation.

# Abstract

Clinical decision support generated with retrieval-augmented language models can present plausible claims with citations whose clinical relevance has not been established. We developed an evidence-linked Graph-RAG prototype that separates candidate evidence from versioned guideline and drug-label passages and exposes the verification status of individual diagnosis, investigation, treatment, and medication-warning claims. A free-text case is converted into structured patient facts and missingness; graph and text retrieval generate candidates; a language model proposes claims; and a separate gate checks citation identity against SHA-256-pinned local source snapshots and applies two narrow amlodipine-label warning rules. We evaluated six hand-authored safety and boundary fixtures and a separate 12-case, four-condition synthetic diagnostic pilot, each in language-model-only, text-RAG, and graph-plus-text modes. All 54 case–mode analyses completed across the two recorded runs. In the six-case set, exact alias matching to diagnoses already explicit in the input gave top-1 counts of 1/6, 4/6, and 5/6. In the pilot, which withheld the diagnosis names, exact matches to provisional author-intended labels were 10/12, 9/12, and 10/12. The graph arm retrieved zero disease candidates in all 12 pilot cases; two pilot cases used different synthesis providers across modes. Pilot citation identities matched for 30/30 text-RAG and 26/26 graph-plus-text uses, but clinical support was not adjudicated. The historical six-case set missed an unknown-allergy warning in all three modes. The work demonstrates a traceable claim-review workflow within a limited adult-hypertension *authoritative-source* domain. It does not establish diagnostic accuracy, safe prescribing, a graph-retrieval benefit, calibrated probabilities, or patient benefit.

# Keywords

Clinical decision support; retrieval-augmented generation; biomedical knowledge graph; claim-level provenance; source verification; medication safety; synthetic evaluation.

# 1. Introduction

Clinical decision support systems can help organize case information and surface relevant knowledge for a clinician to examine. For a system that produces a differential diagnosis or a treatment option, the central requirement is that the reviewer can tell what was stated by the patient, what was retrieved, what was generated, and what remains unverified. A citation alone cannot answer whether a source applies to a particular patient or jurisdiction. This distinction matters especially for medication choices, where allergy status, current medicines, dose, pregnancy, and other missing facts can change the interpretation of a guideline or label.

Retrieval-augmented generation (RAG) combines a language model with external documents, while biomedical knowledge graphs encode relations among diseases, phenotypes, and drugs [1,2]. These methods can make candidate generation more informed, but the retrieved text or relation still has to be checked for identity, scope, and clinical meaning. A graph edge is not a prescription rule; a search snippet is not a guideline; and an authentic passage may support a general statement while being insufficient for a patient-specific recommendation. We therefore treat the movement from retrieved evidence to a clinical claim as a distinct system boundary.

The objective of this project is to implement a **clinician-facing, evidence-linked review prototype** that makes that boundary visible. The input is one free-text case; the output is a structured report with ranked differential candidates, possible investigations, conditional treatment considerations, medication warnings, source passages, and unresolved checks. The model may propose claims, but a separate verifier decides whether the cited passage matches a pinned source snapshot. General generated claims remain `unverified`; only narrowly defined amlodipine-label warnings can become `supported` when explicit patient facts and the exact label passage are present. The system is not intended to make an autonomous diagnosis or prescribe medicine.

The main technical contribution is an implemented claim-provenance contract rather than a new neural-network architecture. `ClinicalClaim` objects carry type, text, conditions, missing checks, evidence IDs, status, and an unverified reason. A versioned source manifest anchors the citable corpus, and a verification gate separates authentic passage identity from semantic or patient-specific support. A third contribution is a reproducible evaluation harness that records three retrieval modes, denominators, source and prompt hashes, provider traces, case-level errors, and a blinded packet for later clinician review. The claim that these features improve clinical decisions remains untested.

This paper reports two engineering evaluations: the original six-case safety/boundary set with explicit diagnoses, and a 12-case synthetic pilot across four author-intended conditions with diagnosis names withheld. Their questions are whether the pipeline executes in each mode, whether emitted source IDs match pinned passages, how exact label matches vary by condition, and which failures remain visible. Neither set has independently adjudicated clinical labels or a representative sampling frame; the reported counts are not clinical diagnostic-accuracy or safety estimates. The rest of the paper positions the design, describes the pipeline and frozen fixtures, reports the recorded results, and identifies the evidence required for later clinical evaluation.

# 2. Related Work / Literature Review

## 2.1. Retrieval-augmented generation and biomedical graph retrieval

Lewis and colleagues introduced RAG as a way to combine parametric generation with retrieved nonparametric memory for knowledge-intensive language tasks [1]. That result motivates retrieval as a source of context, but it does not imply that a retrieved passage clinically entails a generated answer. The present project uses retrieval for candidate generation and keeps a distinct verification stage; it does not claim to improve the underlying RAG algorithm.

Biomedical knowledge graphs connect heterogeneous entities and can reveal paths that are less obvious in a flat text search. PrimeKG is an example of an integrated graph for precision-medicine research [2]. In this prototype, graph relations stored in Neo4j provide possible disease and drug signals for the report. They are never sufficient by themselves to mark a treatment claim `supported`. This separation is central to the system's claim hierarchy: graph relations and textbook hits are *candidate context*, while versioned publisher passages are *citable sources* whose meaning still needs review.

## 2.2. Clinical terminology and evidence sources

The pipeline uses local Human Phenotype Ontology and Mondo files to normalize selected phenotypes and disease terms [6,7]. DrugCentral files contribute drug-name and target associations [8]. These resources help retrieval find related concepts, but a successful mapping is not a validated patient observation. The graph importer expects a PrimeKG-shaped CSV; the text importer reads a limited excerpt of one MedQA textbook file [2,9]. These data choices describe the current implementation, not a comprehensive clinical knowledge base.

For treatment and medicine-related citations, the current pinned corpus is deliberately smaller: selected recommendations from NICE NG136 on adult hypertension and one DailyMed structured product label for amlodipine [3,4]. These sources have different publishers and jurisdictions. The NICE document is a guideline for England; DailyMed hosts a United States drug label from a named labeler. Neither should be described as a universal “WHO/NCBI standard.” Their identity, date, section, population, and conditions must be carried with any proposed claim.

## 2.3. Evaluation and reporting context

The DECIDE-AI reporting guideline addresses *early-stage live clinical evaluation* of AI-based decision support [5]. Its emphasis on intended use, users, workflow, and safety is relevant to future work, but this study has no clinicians or patients in a live setting. We therefore report it as an offline engineering study with synthetic fixtures and explicit unavailable metrics. We do not treat a literature link, model self-rating, or citation count as a substitute for independent clinical adjudication.

# 3. Methodology / Proposed Method

## 3.1. Task definition and trust boundary

Let `x` be the free-text case, `c` the extracted patient context, `G` the retrieved graph candidates, `T` the textbook and pinned-source passages, and `R` the final report. The application first derives `c` from `x`; retrieval uses `c` to obtain `G` and `T`; a fusion model proposes a set of claims `C`; and a separate verification stage checks each claim's cited source IDs and any implemented safety rule. The result is `R = report(c, G, T, verify(C, T))`. This notation describes the implemented execution order, not a learned or calibrated clinical inference model. In particular, `verify` does not infer general textual entailment.

```mermaid
flowchart LR
    A[Free-text case] --> B[Patient facts, unknowns, ontology links]
    B --> C[Neo4j graph candidates]
    B --> D[Qdrant textbook and pinned passages]
    B --> E[DrugCentral and optional web leads]
    C --> F[Evidence ranking and conflict signals]
    D --> F
    E --> F
    F --> G[LLM claim proposals]
    H[Source manifest and SHA-256-checked local snapshots] --> I[Claim verification]
    G --> I
    D --> I
    I --> J[Structured clinician review report]
```

**Figure 1.** Runtime pipeline and trust boundary. Graph, textbook, DrugCentral, and web results can inform proposals. Only manifest-pinned guideline or label passages are eligible for citation-identity checks. The complete system, ingestion, and evaluation diagrams are in [ARCHITECTURE_DIAGRAM.md](../ARCHITECTURE_DIAGRAM.md).

## 3.2. Patient-context extraction

`ClinicalClarifier` parses the case into age, sex, symptoms, known conditions, current medicines, allergy statements, and missing information. A fact-extraction pass checks important statements against the original case text, while `OntologyParser` and `EntityLinker` normalize selected terms using local HPO, Mondo, and drug-name resources. `PatientContext` carries explicit `known`, `unknown`, or `conflicting` states for safety-critical fields such as allergy and medication list. The later safety rules use only explicitly extracted medication and allergy statements. This design aims to prevent an unstated dose or missing allergy history from being treated as a reassuring negative.

Extraction still remains fallible. The recorded unknown-allergy case shows that the phrase “His allergy history was not supplied” was misinterpreted by the extraction path, causing the expected missingness warning to disappear. This failure is not repaired by better downstream retrieval. Accordingly, the report preserves missing checks and is intended for clinician verification of the patient context itself.

## 3.3. Multi-source candidate retrieval and ranking

`RetrievalOrchestrator` queries a Neo4j biomedical graph, Qdrant textbook vectors, and separate Qdrant collections for pinned NICE and DailyMed passages. The normal application path can also use local DrugCentral associations and optional Serper discovery. `OrchestratorResult` retains these channels separately. `EvidenceRanker` orders candidates heuristically, and `ConflictDetector` flags possible graph contraindications or interactions as `unverified` leads. No heuristic evidence rank is interpreted as a diagnostic probability or an authorization to recommend treatment.

The local deployment matters to interpretation. `populate_neo4j.py` defaults to the first 50,000 rows of `datasets/kg.csv`, and `populate_qdrant.py` indexes only the first 150,000 characters of one MedQA English textbook file. The full graph and textbook corpora are not in the public repository. A null or sparse result can reflect local data coverage or a service outage as well as clinical irrelevance. Optional web snippets and DrugCentral target relations cannot become verified citations in the current claim gate.

## 3.4. Claim proposal, schema, and report assembly

`ClinicalFusion` proposes ranked diagnoses and typed diagnosis, investigation, and conditional-treatment claims from the patient context and retrieval results. `claim_synthesis.py` normalizes evidence IDs and rejects invented or non-authoritative citation IDs. Each new model-generated claim begins with `status=unverified`. A claim stores its text, target condition, prerequisites, missing checks, source IDs separated into supporting/conflicting/unverified buckets, and a reason when not verified. The `ClinicalReport` schema rejects duplicate claim IDs, unresolved included citation IDs, and mismatched claim-group references.

`ReportGenerator` then groups claims under differential entries and medication safety, includes the exact source passages and verification failures, and renders a case summary and limitations. The API still contains legacy `ranked_diagnoses` and `overall_confidence` fields. The latter is a retry heuristic, **not** a calibrated probability; the current browser review hides it. In the normal request path, an adaptive retry can run up to two additional analyses, while preserving the original case text as the extraction anchor. The evaluation disabled retries to keep comparisons bounded.

## 3.5. Pinned-source and safety verification

`sources/hypertension/manifest.json` records document IDs, version dates, URLs, sections, jurisdictions, local snapshot paths, and SHA-256 hashes. The current manifest pins NICE NG136 recommendations updated 26 February 2026 and one amlodipine SPL label effective January 2026 [3,4]. The ingestion parser yields 17 selected NICE passages and 9 label passages in the current local snapshot. A passage ID incorporates document identity, version, section, span, and text hash. Fetching or verifying a changed snapshot fails until a human reviews the new document and updates the manifest.

`ClaimVerifier` reloads the pinned snapshots, checks their bytes and version, and accepts a retrieved `SourcePassage` as trusted only when its ID, full metadata, and text equal the locally reconstructed passage. It rejects missing or mismatched citations and some obvious source/claim-scope mismatches, including use of a treatment section to establish a diagnosis or use of the adult guideline for a pregnant treatment case. Even after an exact identity match, it leaves general diagnosis, investigation, and treatment claims `unverified`, because it does not perform a validated patient-specific entailment test.

`ConflictDetector.detect_medication_safety` applies two narrow rules to explicitly stated amlodipine exposure or proposals. First, a reported amlodipine allergy can produce a source-backed warning and conflict with an amlodipine option if the label's contraindication passage is present. Second, current amlodipine plus simvastatin can produce a source-backed interaction-review warning if the relevant label passage is present; the system does not invent the patient's simvastatin dose. The DailyMed label describes known amlodipine sensitivity as a contraindication and a simvastatin daily-dose limit with amlodipine [4]. Unknown allergy or medication-list states generate unresolved warnings rather than safety clearance. These rules cover only the named drug and label sections; they do not constitute a complete drug-interaction engine.

## 3.6. Provider fallback and data boundaries

`LLMFallback` tries configured providers in order when one is unavailable; the selected provider and model are recorded per analysis when trace information is available. This improves engineering continuity but makes comparisons difficult when different arms use different synthesis models. The `openrouter/free` route can change its underlying model, so even a matched route name is not enough to recover the exact model version. Prompts, source hashes, and configured model IDs are recorded in the evaluation manifest; output reproducibility remains conditional on provider availability.

The prototype runs locally but may send case text to configured external language-model services and selected terms to optional web search. It has no deployment-grade authentication, audit logging, privacy governance, or clinical sign-off process. Only synthetic or appropriately de-identified cases should be used in demonstrations. This paper reports no processing of real patient records.

# 4. Experimental Setup / Dataset

## 4.1. Frozen synthetic cases

The evaluation dataset is `evaluation/cases.v1.json`, version 1.0.0, with six hand-authored English cases. Five mention a documented hypertension diagnosis and one mentions documented gastroesophageal reflux disease. Four hypertension cases target amlodipine allergy, amlodipine–simvastatin co-medication, unknown allergy history, and a case without an identified warning. The remaining hypertension case includes pregnancy as a guideline-scope boundary. These cases are engineering fixtures, not clinician-selected or clinician-labeled encounters. The reference diagnosis is explicitly written in each input, and no prevalence, outcome, or differential gold standard is supplied.

| Case ID | Explicit case feature | Expected warning type | Purpose |
| --- | --- | --- | --- |
| `htn-amlodipine-allergy` | Known hypertension, current amlodipine, reported amlodipine allergy | `amlodipine_allergy` | Narrow label contraindication path |
| `htn-amlodipine-simvastatin` | Known hypertension, both named current medicines | `amlodipine_simvastatin` | Interaction-review path without an inferred dose |
| `htn-allergy-unknown` | Known hypertension, current amlodipine, allergy history not supplied | `allergy_status_unconfirmed` | Missingness and abstention |
| `htn-no-identified-warning` | Known hypertension, current amlodipine, no known allergies or other medicines | None | Warning-negative control |
| `htn-pregnancy-out-of-scope` | Documented hypertension during pregnancy | None | Adult-guideline treatment-scope boundary |
| `known-gerd-out-of-scope` | Documented gastroesophageal reflux disease | None | Clinical-domain boundary |

**Table 1.** Frozen synthetic fixture categories. The exact input text is in [cases.v1.json](../evaluation/cases.v1.json). The cases are stored outside ingestion paths; the runner also checks that no full case text appears verbatim in a pinned passage.

## 4.2. Compared configurations and run controls

The same production `/analyze` implementation was called for each case and mode, with only the retrieval layer substituted. `llm_only` removed graph, vector, authoritative-passage, DrugCentral, and web retrieval. `text_rag` used textbook-vector and pinned guideline/label passages. `graph_text` added Neo4j graph candidates to the same text retrieval. DrugCentral and web discovery were disabled in *all* arms so those changing channels could not favor one arm. The clarifier ran once per case and its `PatientContext` was reused across arms. Mode order rotated by case. The saved run used temperature zero and zero retries.

The captured local run was performed on 7 October 2026 and rescored without additional provider calls. Its manifest records dataset SHA-256 `65c62940…a47cdb5b7`, source-manifest SHA-256 `3ecb766b…cc7596d4667`, source document versions, prompt hashes, Git SHA, dirty-worktree flag, fallback order, provider trace, and command. The aggregate counters reproduced in this draft are also saved in [RESULTS_SNAPSHOT.json](RESULTS_SNAPSHOT.json). Case-level generated runs are ignored by Git. The public code and fixture file support inspection, but exact end-to-end replay needs the retained source snapshots, local indexes, and providers that produced the original output.

## 4.3. Measures and analysis plan

For each successful case, *top-1* and *top-3 alias match* ask whether an output diagnosis exactly matches any normalized reference alias at rank 1 or within the first three ranks. Normalization lowercases and removes punctuation; it is not semantic equivalence. Because the alias appears in the input, this is a recognition and ranking check, not diagnostic accuracy. *Citation identity validity* is the number of claim citation uses resolving to an included passage identical to the pinned reconstructed passage divided by all emitted claim citation uses. If no IDs are emitted, the value is unavailable, not zero. Neither metric adjudicates the truth or clinical applicability of a claim.

The *expected warning-type recall* is the number of fixture-labeled warning types emitted divided by three expected types across the set. *Supported-label-warning recall* uses only the two amlodipine-label warning fixtures and requires `verification_status=supported`. The *label-warning false-positive case rate* counts the three cases with no expected warning when either label-warning type appears. *Claim abstention* counts claims whose status is `unverified` divided by all emitted claims. These are transparent counts with denominators, not calibrated probabilities; no confidence intervals or significance tests are reported for six fixtures.

Claim-support accuracy, unsupported-supported-claim rate, and unsafe-treatment-option rate were specified in the scorer but had no independently adjudicated labels and are reported as **unavailable**. The harness can produce a blinded claim packet without mode or system status, plus a private index. Its review protocol requires two qualified reviewers to judge support and option safety independently against the cited section, document date, patient facts, population, and conditions. Disagreements remain unresolved until documented reconciliation; no such adjudication was performed for this run.

## 4.4. Four-condition diagnostic pilot

Before running the pilot, we versioned [`cases.multidisease-pilot.v1.json`](../evaluation/cases.multidisease-pilot.v1.json) with three adult outpatient presentations each for hypertension, chronic asthma, type 2 diabetes, and gastro-oesophageal reflux/dyspepsia. The case text withholds each reference diagnosis name; its intended label is stored only in the evaluation file and is never passed to `/analyze`. The author designed typical synthetic patterns using public [NICE NG136](https://www.nice.org.uk/guidance/ng136/chapter/Recommendations), [NICE NG245](https://www.nice.org.uk/guidance/ng245/chapter/Recommendations), [WHO HbA1c diagnostic guidance](https://www.who.int/publications/i/item/use-of-glycated-haemoglobin-%28-hba1c%29-in-diagnosis-of-diabetes-mellitus), and [NICE CG184](https://www.nice.org.uk/guidance/cg184/chapter/Recommendations) as context [3,10–12]. These documents were **not** added to the application's pinned source corpus, except for the already pinned NG136 sections. The intended labels were not independently clinician reviewed, and three deliberately clear examples per condition do not sample real diagnostic ambiguity.

The pilot reused the three modes, production analysis path, once-per-case clarification, rotating mode order, zero retries, and local services. The prespecified engineering endpoint was exact normalized match of a ranked diagnosis to an author-listed alias at rank 1 or within ranks 1–3, with case-level attempted/completed denominators and per-condition counts. We computed descriptive Wilson 95% binomial intervals for those small case proportions, not confidence intervals for real-world accuracy. A failure to complete remained in the attempted count. We also recorded provider/model identity, citation identity, claim abstention, graph-candidate counts, and latency. No positive medication-warning cases or independently labeled relevant passages were included, so warning sensitivity and retrieval Hit@k/Recall@k are unavailable in this pilot. The run was replay-scored from its saved case results; the metric JSON was byte-identical.

# 5. Results and Discussion

## 5.1. Engineering results

All 18 case–mode runs completed. The saved aggregate counters are shown in Table 2. Fractions are reported as counts because the small, hand-authored set does not support clinical performance inference. The citation denominator is the number of *citation uses*, not the number of distinct source documents or clinically correct claims.

| Measure | LLM only | Text RAG | Graph + text |
| --- | ---: | ---: | ---: |
| Completed cases | 6/6 | 6/6 | 6/6 |
| Explicit diagnosis alias at rank 1 | 1/6 | 4/6 | 5/6 |
| Explicit diagnosis alias within top 3 | 1/6 | 4/6 | 6/6 |
| Pinned citation identity matched | No IDs emitted | 13/13 | 17/17 |
| Expected warning type emitted | 2/3 | 2/3 | 2/3 |
| Label warning emitted as `supported` | 0/2 | 1/2 | 1/2 |
| Claims marked `unverified` | 14/14 | 11/12 | 17/18 |
| Clinician-adjudicated claim support or option safety | Unavailable | Unavailable | Unavailable |

**Table 2.** Results from the saved 7 October 2026 local run, rescored with the current metric code. The table establishes execution and source-ID behavior on these fixtures only. Graph and text retrieval did not create a clinically verified general treatment claim.

The ranking counts suggest different output behavior across modes but cannot isolate a retrieval effect. Provider traces matched across all arms for only three cases, differed for two, and were unknown for one. In addition, `openrouter/free` does not pin its underlying model. The graph-plus-text arm therefore cannot be credited with a causal diagnostic improvement from these counts. The amlodipine-allergy case also shows a limitation of exact aliases: graph plus text ranked “amlodipine hypersensitivity” above “hypertension,” so rank 1 was counted as a miss even though the safety issue was surfaced.

The citation check reached 13/13 and 17/17 in the two retrieval arms. That means every emitted claim citation ID in those arms matched the pinned passage identity used by the scorer. It does not mean the associated claim was clinically supported. A valid label paragraph can be linked to an inappropriate option, and a genuine guideline recommendation may depend on conditions absent from the case. The high abstention counts, 11/12 and 17/18, reflect the deliberately conservative verifier and two narrow supported-warning exceptions. A system that abstains frequently has not thereby been shown safe; the unreviewed treatment proposals and missed warnings still matter.

## 5.2. Four-condition diagnostic pilot results

All 36 pilot case–mode analyses completed on 12 October 2026. Table 3 reports **exact alias matches to provisional, author-intended synthetic labels**, not clinician-adjudicated diagnoses. Each condition contributes only three cases. Rank-3 counts equalled rank-1 counts in all conditions and modes; outputs often contained only one ranked diagnosis.

| Intended condition | LLM only rank 1 | Text RAG rank 1 | Graph + text rank 1 |
| --- | ---: | ---: | ---: |
| Hypertension | 1/3 | 2/3 | 3/3 |
| Chronic asthma | 3/3 | 2/3 | 2/3 |
| Type 2 diabetes | 3/3 | 3/3 | 2/3 |
| GORD-like presentation | 3/3 | 2/3 | 3/3 |
| **All pilot cases** | **10/12** | **9/12** | **10/12** |

**Table 3.** Three prespecified, diagnosis-withheld synthetic cases per condition. The descriptive Wilson 95% intervals are 0.55–0.95 for 10/12 and 0.47–0.91 for 9/12. At the condition level, 3/3 has an interval of 0.44–1.00, 2/3 of 0.21–0.94, and 1/3 of 0.06–0.79. These wide intervals describe sampling variation **within this constructed pilot** and do not quantify population diagnostic performance. The case-level outputs and exact denominators are preserved in [MULTIDISEASE_PILOT_RESULTS.json](MULTIDISEASE_PILOT_RESULTS.json).

The ranking measure is intentionally strict: “Stage 2 Hypertension” did not match the alias “hypertension,” while “Reversible airflow obstruction” was not counted as “asthma.” One text-RAG GORD case and one graph-plus-text diabetes case returned an empty ranked list despite a completed report. The exact-match counts therefore also reflect output wording and empty-list behavior; they cannot grade a clinically acceptable differential. No clinician adjudicated whether the author-intended diagnosis was the only or best answer. In particular, an elevated HbA1c establishes hyperglycaemia under a stated diagnostic rule, but does not independently establish the diabetes *subtype*; the intended type 2 label in these vignettes remains provisional.

The graph-plus-text mode returned **zero graph disease candidates in all 12 cases**. A read-only audit of the local Neo4j state found 14,467 nodes, 649,815 edges, and zero edges whose relationship type contained `phenotype`, the relation filter used by the current graph disease query. The graph arm therefore supplied no observed disease-candidate signal in this pilot. Synthesis providers matched across all three arms for 10 cases and differed for two: one text-RAG arm used `openrouter/free`, and one graph-plus-text arm used Cohere after fallbacks. The mode differences in Table 3 cannot be interpreted as a graph effect; provider fallback and ordinary model variability remain possible explanations.

The two retrieval modes returned 120 authoritative candidate passages each across the 12 cases, but the only pinned corpus was hypertension guideline sections and an amlodipine label. Citation **identity** matched 30/30 uses in text RAG and 26/26 in graph plus text. All pilot claims remained `unverified` (41/41 LLM only, 34/34 text RAG, 22/22 graph plus text); no clinician judged semantic support or patient applicability. No positive warning opportunities were designed into this diagnostic pilot, so warning recall, unsafe-option rate, and claim-support precision are **unavailable**, not zero. The current code also lacks independently labeled relevant passage ranks for retrieval Hit@k or Recall@k. The repository's 51 automated engineering tests passed after the pilot changes; those checks do not substitute for clinical review.

## 5.3. Failure analysis

The clearest recorded safety-relevant failure was the unknown-allergy case. The case says that allergy history was not supplied, yet extraction treated “his” as an allergy mention. The expected `allergy_status_unconfirmed` warning was missed in all three modes. This is an upstream patient-context error: citation pinning, graph retrieval, and label rules all operate on the context they receive. The failure identifies missingness extraction and input confirmation as priorities before any clinical study.

The warning-type measure was 2/3 in every mode. The two named label-warning categories appeared as expected in the relevant cases, but only one of the two was emitted with `supported` status in each retrieval arm. This difference reflects the exact-passage and explicit-fact gate, not proof that the other case was clinically safe or unsafe. The saved scorer found zero label-warning false-positive cases among the three warning-negative fixtures. With only three such cases and two implemented warning rules, that count cannot establish specificity or comprehensive medication safety.

The pregnancy and reflux fixtures probe domain boundaries, but they do not constitute a robust out-of-distribution evaluation. The pregnancy case has a documented hypertension diagnosis while the pinned NICE treatment scope excludes pregnancy; the reflux case has a documented diagnosis outside the hypertension source set. Their inclusion shows that the pipeline can be exercised on boundary inputs, but no clinician judged whether every proposed investigation or treatment was appropriately suppressed. A future study needs many independently selected boundary cases and a prespecified failure-to-abstain metric.

## 5.4. Interpretation, limitations, and implications

The evidence-supported conclusion is that the software implements an inspectable claim and source-provenance workflow and that one saved synthetic run exercised it without process failures. The verification boundary is narrower than clinical claim validation: it checks publisher snapshot identity, explicit scope mismatches, and two rule-backed warnings; it does not reason exhaustively over guideline eligibility, all drug interactions, or all patient attributes. A clinician must still inspect the case facts, source date, exact passage, population, and treatment conditions.

Several limitations prevent a clinical-effectiveness claim. Both fixture sets are small, synthetic, and selected by the developers. Diagnoses are explicit in the first set and withheld but only author-labeled in the second. The second set has no independent clinician review or negative/mimic reference standard. Authoritative sources span two jurisdictions and cover only hypertension and amlodipine; source choice and case labels lack independent clinical review; raw publisher snapshots and large external datasets are excluded from Git. The local graph lacked the phenotype relations required for disease retrieval in the pilot, and the graph/text indexes are not version-pinned or comprehensive. Provider fallback confounds the three-arm comparison. The interface has no validated workflow study, and the application lacks clinical deployment controls for identifiable patient data. There are no physician ratings, treatment-safety adjudications, prospective outcomes, or calibrated risk estimates.

The next research stage is a controlled offline study with frozen provider models and retrieval indexes, independently selected cases, clinician-reviewed source selection, and two blinded adjudicators per claim. Primary outcomes should distinguish diagnosis ranking, claim support, missing critical warnings, unsafe treatment suggestions, abstention appropriateness, and clinician review time. Only after acceptable offline results and deployment governance would a live clinician-facing study be defensible; DECIDE-AI can guide reporting of that later stage [5]. The present manuscript is therefore a methods and feasibility draft, not a claim of patient benefit.

# 6. Conclusion

We implemented a Graph-RAG clinical decision support prototype that records patient-context uncertainty, separates candidate retrieval from citable publisher passages, and exposes claim-level verification status for clinician review. The six-case engineering set completed all 18 analyses, and a separate four-condition diagnostic pilot completed all 36 analyses with exact author-label matches of 10/12, 9/12, and 10/12 across the three modes. The graph retrieved no disease candidates in the pilot, while the earlier set missed an unknown-allergy warning. Pinned citation identities matched in the retrieval arms of both studies, but their clinical support was not adjudicated. Independent clinical review, source expansion, and broader controlled evaluation are required before diagnostic, prescribing-safety, graph-benefit, or outcome claims can be made.

# Acknowledgements – if applicable

No acknowledgements are asserted in this draft. Before submission, the actual contributors should name any qualifying assistance and confirm that each named person agrees to be acknowledged. The [research-paper-writing skill](https://github.com/Master-cai/Research-Paper-Writing-Skills), adapted from [Peng Sida's public notes](https://github.com/pengsida/learning_research), informed the draft's section flow and claim–evidence review; it is not a coauthor or evidence source for clinical results.

# References

1. Lewis P, Perez E, Piktus A, et al. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). *Advances in Neural Information Processing Systems*. 2020;33.
2. Chandak P, Huang K, Zitnik M. [Building a knowledge graph to enable precision medicine](https://doi.org/10.1038/s41597-023-01960-3). *Scientific Data*. 2023;10:67.
3. National Institute for Health and Care Excellence. [Hypertension in adults: diagnosis and management (NG136), recommendations](https://www.nice.org.uk/guidance/ng136/chapter/Recommendations). Project-pinned recommendations snapshot updated 26 February 2026; England jurisdiction. The exact selected sections and checksum are in [the source manifest](../sources/hypertension/manifest.json).
4. National Library of Medicine, DailyMed. [Amlodipine besylate tablets structured product label, set ID 0c5784b9-5542-144f-e063-6394a90a7ebc](https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=0c5784b9-5542-144f-e063-6394a90a7ebc). Label version 2; January 2026; United States jurisdiction.
5. Vasey B, Nagendran M, Campbell B, et al. [Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI](https://doi.org/10.1038/s41591-022-01772-9). *Nature Medicine*. 2022;28:924–933.
6. Köhler S, Gargano M, Matentzoglu N, et al. [The Human Phenotype Ontology in 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7778952/). *Nucleic Acids Research*. 2021;49(D1):D1207–D1217.
7. Monarch Initiative. [Mondo Disease Ontology: project and downloads](https://mondo.monarchinitiative.org/pages/download/). Local ontology file used for normalization; no specific Mondo release is asserted for the saved run.
8. DrugCentral. [Downloadable drug data](https://www.drugcentral.org/download). Local drug-name and drug-target files used for candidate signals; disabled in the three-arm evaluation.
9. Jin D, Pan E, Oufattole N, et al. [What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams](https://arxiv.org/abs/2009.13081). 2020. The prototype indexes a limited local textbook excerpt; it does not evaluate on MedQA examination questions.
10. British Thoracic Society, National Institute for Health and Care Excellence, Scottish Intercollegiate Guidelines Network. [Asthma: diagnosis, monitoring and chronic asthma management, NG245](https://www.nice.org.uk/guidance/ng245/chapter/Recommendations). Context for author-built pilot cases; **not** pinned as an application source.
11. World Health Organization. [Use of glycated haemoglobin (HbA1c) in diagnosis of diabetes mellitus](https://www.who.int/publications/i/item/use-of-glycated-haemoglobin-%28-hba1c%29-in-diagnosis-of-diabetes-mellitus). Context for author-built pilot cases; **not** pinned as an application source.
12. National Institute for Health and Care Excellence. [Gastro-oesophageal reflux disease and dyspepsia in adults: investigation and management, CG184](https://www.nice.org.uk/guidance/cg184/chapter/Recommendations). Context for author-built pilot cases; **not** pinned as an application source.

# Supplementary material – if applicable

## S1. Reproducibility and artifact map

The public repository contains the [analysis API](../backend/api/routes.py), [claim verifier](../backend/services/claim_verifier.py), [clinical report schema](../backend/schemas/report.py), [source manifest](../sources/hypertension/manifest.json), [six-case fixtures](../evaluation/cases.v1.json), [four-condition pilot cases](../evaluation/cases.multidisease-pilot.v1.json), [evaluation runner and metric definitions](../evaluation/README.md), [six-case aggregate snapshot](RESULTS_SNAPSHOT.json), [pilot aggregate and per-case rank-1 snapshot](MULTIDISEASE_PILOT_RESULTS.json), and [detailed architecture figure](../ARCHITECTURE_DIAGRAM.md). Full report JSONL files are under ignored `evaluation/runs/` on the development machine; they are not part of the GitHub repository. Exact recreation needs matching publisher snapshots, local Neo4j and Qdrant contents, and provider/model behavior, which is partly unresolved for `openrouter/free`.

The saved run manifest reports dataset SHA-256 `65c6294006062bd79d5ab5c9f95fc5ccb238975d72ec75df36b89d4a47cdb5b7`, source-manifest SHA-256 `3ecb766b7dd00f233f50a8dcf481bfd0135d95add924ca3b852cbca7596d4667`, original Git SHA `02e4d343714efda0668088a5236ed917782ab01d`, and `git_worktree_dirty=true`. These are provenance identifiers for the historical run, not a guarantee of bit-for-bit reproduction from the current checkout. The aggregate snapshot was checked against the locally saved metric file before this draft was prepared.

The 12 October 2026 pilot manifest records dataset SHA-256 `0588cbe7cd4b2851215c2253805b2ce64c5c1193e579544fa9332ccefc42ebca`, the same source-manifest SHA-256, and evaluation-code Git SHA `a9134a2a0983c23726def88e3049e8c12ad77168`. It flagged a dirty working tree because an unrelated, untracked `paper/figures/` directory existed; the tracked pilot case and scoring files were committed before the run. [MULTIDISEASE_PILOT_RESULTS.json](MULTIDISEASE_PILOT_RESULTS.json) records the full run-file hashes, 36 rank-1 strings, provider selections, denominators, and graph audit. Replay of the captured JSONL produced byte-identical `metrics.json`. The local graph database was audited after the run but its index is not itself version-pinned in Git.

## S2. Claim–evidence alignment audit

| Major statement | Direct evidence available now | Manuscript status |
| --- | --- | --- |
| The code creates typed claims and tracks source IDs, missing checks, and status | `ClinicalClaim` and `ClinicalReport` schemas; API and verifier implementations | Supported as an implementation description |
| All 18 synthetic analyses completed | Saved 6-case × 3-mode metric counters | Supported for the recorded engineering run |
| All 36 four-condition pilot analyses completed | Saved 12-case × 3-mode result files and replayed counters | Supported for this synthetic pilot only |
| Graph retrieval improved diagnosis | Zero graph disease candidates; no phenotype relation edges; two provider mismatches | **Not claimed** |
| Emitted pinned citation IDs matched local passage identity in retrieval arms | 13/13 and 17/17 citation-use counters | Supported for identity only; no semantic entailment claimed |
| A missing-allergy warning was missed | `htn-allergy-unknown` case-level errors in all three arms | Supported observed failure |
| Graph retrieval improves diagnosis or treatment safety | Provider-confounded synthetic comparison; no clinician labels | **Not claimed** |
| The system is ready for clinical use | No clinical review, governance, or prospective study | **Not claimed** |

## S3. Declarations and pre-submission checks

**Ethics and participants:** The reported evaluation uses only hand-authored synthetic fixtures and no patient or clinician-participant study. No institutional ethics-exemption determination is asserted. **Data and code availability:** Code, case definitions, manifest, and aggregate counters are linked above; external datasets, local indexes, publisher snapshots, credentials, and raw generated runs are not distributed. **Funding and competing interests:** To be completed by the actual authors; none are inferred. **Authorship:** Names, affiliations, corresponding author, ORCID IDs, and contributions remain to be supplied.

Before submission, reviewers should verify five open dimensions from the [research-paper-writing skill](https://github.com/Master-cai/Research-Paper-Writing-Skills): contribution relative to comparable CDSS literature; prose and method reproducibility; experimental strength under stable model identity; evaluation completeness with independent clinician labels; and method soundness under realistic missingness and source-scope conditions. The most material gaps are two small developer-authored datasets, the allergy-extraction failure, absent phenotype graph retrieval in the pilot, lack of independently adjudicated claim support and option safety, and provider-confounded mode comparisons. These require new evidence; wording alone cannot resolve them.
