# Research improvement plan after the second assessment

Prepared 31 October 2026. Planning only: this step does not change application code, the manuscript or the live Google Doc, start paid inference, publish a release, or contact an editor. Current implementation checkpoint: `49b69ae`; prior rollback checkpoint: `39d532b`.

## Main decision

Prioritize a fair medication-safety comparison and testing the deployed extraction path. Another diagnosis accuracy run alone will not establish the proposed provenance/uncertainty contribution. First test whether the bounded hybrid system adds useful supported decisions beyond a strong deterministic baseline and an LLM given the same source access. If it does not, report that result and reconsider whether the contribution is sufficient for a research article. Do not keep tuning against a final test until the result looks favorable.

The candidate contribution is an auditable workflow that separates source integrity, documented patient facts, bounded medication rules and abstention. It is not a general clinical semantic verifier, and its novelty remains to be established against existing clinical verification systems.

## Assessment of all ten suggestions

| Point | Decision | Planned action |
| --- | --- | --- |
| 1 Development data | Agree on the central weakness; qualify the mandatory 100-vignette target | New independent safety/evidence material is the priority. Diagnosis is secondary. The prior audit found only 51 candidates under the existing diagnosis eligibility; manual exposure remains unknown. Broaden eligibility or choose another source before viewing new outcomes if seeking 100 or more. A sample-size target is not a power analysis. |
| 2 Before/after claims | Agree | Replace “development gains” and percentage-point improvement framing with recovery after defect repair. Put historical runs in an engineering/regression subsection or supplement. Compare functioning methods under matched settings for the scientific result. Do not attribute every old text-RAG failure to the incompatible literature embeddings; that collection was excluded. |
| 3 Weak lexical comparator | Agree that it cannot establish an advantage | Retain only as an optional sanity baseline. The stronger deterministic comparator is already present and matches the old perfect safety score. Add the missing same-task LLM-only and deployed hybrid results. |
| 4 Untested LLM extraction | Agree | The new harness supports production clarification, but that is not an executed result. Run it and separately score raw LLM extraction, the merged production context and downstream warning decisions. |
| 5 Outdated introduction | Agree | Rewrite the last introduction paragraph around implemented provenance checks, preservation of missing/conflicting information, bounded medication decisions and the comparative evaluation. Describe graph retrieval in the architecture, without making graph superiority the contribution. |
| 6 Availability and reuse notes | Agree that these need factual resolution | Verify a rights-safe public artifact and actual source acquisition/reuse basis. Do not merely delete the caveats and assert compliance/public availability. |
| 7 Declarations | Agree for submission; retain the user's current deferral | Funding, conflicts, institutional ethics determination and author contributions require author facts. Prepare an accurate AI-assistance disclosure from the recorded Codex/ChatGPT, Grammarly, QuillBot and ZeroGPT use; leave all declarations out until the user resumes this work. |
| 8 Clinical verification prior work | Agree | Read and compare MedRAGChecker, CRITIC-RAG and MedRAG/MIRAGE, alongside ALCE and SciFact. Discuss differences in task, verifier, human labels, source access and inference budget. Citations alone do not establish novelty. |
| 9 McNemar prose | Agree; low effort | Use a compact paired-results table with discordant counts, paired difference/interval, raw exact p and Holm-adjusted p. Keep the development/exploratory label. Remove duplicated prose to preserve the eight-page target. |
| 10 IJDDT fit | Partly agree | A medication-safety title can accurately describe the study if that is its central evaluated task. Adding drug terminology cannot establish journal fit. A presubmission scope inquiry is reasonable if IJDDT is mandatory; draft it for author review, do not send it without authorization. |

## Work sequence and completion gates

### A Establish the question and prior-work gap

Owner: implementation author with guide.

1. Make a comparison matrix for the directly related work. MedRAGChecker combines textual NLI with KG compatibility for claim-level biomedical verification; our pinned identity checks and bounded rules do not implement that capability. CRITIC-RAG uses a verifier throughout retrieval/generation; distinguish it from post-generation rule checks. MedRAG/MIRAGE informs matched retrieval evaluation.
2. Prespecify the main question: does the hybrid reduce incorrectly supported medication warnings while preserving useful supported warnings compared with deterministic rules and an LLM given the same case, proposal and passages?
3. Define primary comparison(s), false-support and useful-recall endpoints, handling of missing outputs, source/rule scope and scenario-family dependence before evaluation. Keep general semantic verification and diagnosis as separate tasks.
4. Use a working disease-neutral title such as **Evidence Provenance and Uncertainty Handling for Medication Safety in a Clinical Review Prototype**, provided medication safety becomes the main evaluated task. Avoid a title that implies validated prescribing safety.

Gate: a defensible task-specific contribution and comparison, rather than a promise to obtain higher accuracy.

### B Run the missing development comparisons now

Owner: implementation work. Independent case authorship is not needed to run further tests honestly labeled development.

Use the existing 108 cases as an explicit pilot under a frozen development protocol. Run all cases, preserve first outcomes and failures, and retain the requested and returned model versions.

| Arm or measurement | What it isolates |
| --- | --- |
| Strong deterministic extraction plus existing rules | Necessary practical comparator; already perfect on the reused cases |
| LLM-only medication warning decisions | Same raw case, fixed proposed option and supplied label passages; not the 18/36 diagnosis baseline |
| Production LLM clarification plus deterministic merging and rules | The actual deployed extraction path with a fixed proposed option |
| Matched gate-disabled control | Gate enabled/disabled on identical saved generation, extracted context and source inputs; isolates gate effects without new generation differences |
| Full report generation with retrieval | A separate end-to-end task; includes omitted/unsupported options and needs independent clinical assessment |

Add field-level extraction reporting for allergy state, relevant active/stopped medication status and explicit prerequisites. Retain raw extraction and merged production context in private evaluation records so the deterministic merge cannot hide LLM extraction errors. Then report downstream warning precision/recall, false support, useful supported recall, unknown-status handling and failed cases. A low false-support fraction accompanied by near-zero useful coverage is not success.

The existing live harness supports LLM-only, production hybrid and full-report arms; raw-field extraction scoring and the matched gate-disabled analysis still need implementation. Do not describe planned instrumentation as an already executed experiment.

Gate: complete comparable development outputs, reviewed error categories and a decision about whether further model/rule changes are warranted. If the hybrid provides no benefit over rules, retain that finding. Any resulting fixes remain development work and precede the final freeze.

### C Resolve source and release questions before locking the new study

Owner: implementation author plus corresponding author for rights/access decisions.

- Local `git ls-tree` confirms that historical commit `68e9b05` includes aggregate result files under `paper/`, including diagnosis, retrieval, medication-safety and provenance summaries. This does not prove that the remote contains or publicly exposes the commit. The GitHub connector returned 404 again for both repository and commit on 31 October 2026; a private/inaccessible or moved repository cannot be distinguished from a missing one by that response alone.
- Prepare a minimal release with executable harnesses, frozen protocols, permissible case IDs/boolean outcomes, aggregate tables, environment/model/source hashes and analysis commands. Verify every promised URL without sign-in and reproduce aggregates from the released artifact. Do not change repository visibility or release private content merely to remove a manuscript note. An archival release is another option after author approval.
- The MedQA paper states that its textbook release is subject to a research-use-only license agreement. Record the actual acquisition route and agreement applicable to the local files; repository licensing is not automatically textbook redistribution permission. Keep books and copied passages out of the public release. If the intended use cannot be supported, replace the corpus with suitable material and rerun every affected retrieval/generation experiment under a new corpus version. Historical outputs can remain labeled historical; they must not be presented as results of the replacement corpus.

Gate: verified availability statement and documented source-use basis, or a transparently limited release with affected experiments revised. No unsupported rights statement.

### D Prepare independent evaluation and freeze after development

Owner: a case author who did not develop the fixes, plus qualified clinical reviewers. The user currently has neither available.

- Safety: target at least 100 new cases across prespecified scenario families, including ordinary supported/negative controls and challenging negation, uncertainty, timing and similar-name cases. Do not construct only cases chosen to favor our rules. Avoid family overlap with development. Separate case writing from clinical label validation; a teammate alone does not establish clinical correctness. Prefer two qualified reviewers, preserve agreement/disagreements and reconcile before outcome scoring. More drugs require separately developed and reviewed rules first.
- Retrieval: target at least 50 independently written queries and reviewed relevance grades without showing rankings to annotators. Use BM25, dense and reranked dense on the same declared corpus. Preserve incomplete judgments rather than claiming complete recall. If independent annotation remains unavailable, keep the ten old probes as supplementary engineering checks.
- Diagnosis: use the feasible genuinely unused remainder or preregister a broader task/selection rule for 100 or more eligible vignettes. The old rule leaves 51 candidates, not 100. Keep open-ended diagnosis distinct from multiple-choice QA and disclose possible provider pretraining exposure. A teammate is not required to rewrite an established examination benchmark.
- Claim support: if making claims about general passage entailment or patient applicability, obtain an independently labeled challenge directly measuring them. Medication-rule success cannot validate arbitrary clinical claim support.
- Select sample size using the primary endpoint, desired precision and plausible paired discordance, not a universal 100-case threshold. Report residual imprecision if resources constrain the study.
- After all development fixes, commit a new implementation and freeze code, prompts, requested model, corpus, labels, selection rule and scoring. Run each arm once under matched access/settings, retain failures, report intervals and paired tests. Later fixes require a new version and a new untouched final set.

Gate: independent material/review documented and protocol frozen before final inference. Until then, all new reused-case runs remain development evidence. AI-generated paraphrases cannot fill the independent-author/reviewer gap.

### E Revise the manuscript after the results are available

Owner: authors with writing assistance.

1. Put independent primary safety/evidence outcomes first. Move defect-repair history and old probes to a compact development subsection or supplement. Preserve negative results and scope limits.
2. Align introduction, abstract, title, methods and conclusion around the actual central experiment. Add the clinical verification comparison matrix and explain the remaining novelty and limitations.
3. Add the compact paired-results table; shorten repeated narrative to preserve the eight-page working layout. Preserve author blocks and full-width tables/figure.
4. Replace unresolved availability/reuse notes only after the underlying facts are resolved. Add factual declarations when the user supplies or authorizes them; do not invent ethics exemption, funding status or contributions.
5. Process revised manuscript prose through the authorized humanizer before insertion, then verify scientific meaning, numbers and references. Detector scores do not establish authorship or originality. Disclose actual writing assistance according to the chosen journal's policy.
6. If IJDDT is mandatory, prepare a scope inquiry explaining the medication task, bounded drug coverage, real evidence and limitations. Await scope guidance before final journal packaging. The journal describes a pharmaceutics/drug-delivery remit; its author instructions also request double-spaced text and margins, so the preferred two-column working paper should not automatically be treated as its submission template.

## Priority order

1. Prior-work gap and same-task LLM/production-extraction development comparison.
2. Source-use and reproducibility release resolution.
3. Independent safety/evidence material and review, then final freeze and evaluation.
4. Secondary diagnosis/retrieval studies as feasible.
5. Evidence-led manuscript rewrite, declarations and journal-specific submission preparation.

## Added base-paper comparison workstream

Added at the user's request after the initial plan. The archived base paper is **An Adaptive Multi-Agent LLM-Based Clinical Decision Support System Integrating Biomedical RAG and Web Intelligence**, IEEE Access (2025), DOI [10.1109/ACCESS.2025.3613340](https://doi.org/10.1109/ACCESS.2025.3613340). Its Table 5 was checked visually on PDF page 12 (printed page 167401).

| Dataset | Base paper correct/evaluated | Reported accuracy | Evaluation distinction |
| --- | ---: | ---: | --- |
| MedQA | 47/50 | 94% | Five-option exact answer matching |
| PubMedQA | 44/50 | 88% | Free-text correctness using the paper's semantic-similarity rule |
| MedBullets | 42/50 | 84% | Free-text correctness using the paper's semantic-similarity rule |

The paper describes a cosine-similarity threshold of 0.80 for its free-text scoring and up to three iterations in the main evaluation. Do not substitute the separate iteration experiment's 94.7% for Table 5's 47/50 result, or treat repeated micro precision/recall/F1 numbers as independent outcomes. A matching dataset name or sample count does not establish a matched question selection or evaluation.

Use two explicitly different comparisons:

1. **External reported results and protocol comparison.** Include the published counts above with source, task, dataset selection, sample size, scoring method, backbone, evidence access and iteration/inference budget. Add our results only in separately labeled rows with the same metadata. Missing comparable outcomes remain unavailable. The current 36-case open-ended diagnosis agreement and 108-case medication-rule results cannot be ranked against these QA percentages. Do not calculate a cross-paper improvement percentage or McNemar test on unpaired results.
2. **Matched experimental comparison, if feasible.** Obtain the original selected IDs, prompts, scorer, settings and executable implementation or enough documented detail. Run both systems on the same independently reserved questions with matched model/source access and a declared inference budget. If exact reproduction is impossible, identify a reimplementation as such and state deviations. Report clinical QA, medication safety, provenance integrity and claim support as separate tasks. The original QA paper does not supply a comparable medication-rule outcome merely because it is a CDSS.

The repository already has a related adapted three-dataset QA pilot in `evaluation/QA_BENCHMARK_PROTOCOL.md` and `paper/QA_BENCHMARK_PARTIAL_RESULTS.md`. It contains **255/300 planned arm attempts**, with **45 missing**, and unequal inference budgets between direct LLM and CDSS-plus-answer-selector arms. Its PubMedQA protocol is question-plus-abstract yes/no/maybe exact classification, different from the base paper's free-text semantic rule. It is not a reproduction and must not appear as a completed base-paper comparison. Audit the historical frozen implementation/configuration before resuming; preserve earlier failures. If the current version differs, restore the original snapshot for a genuine continuation or define a new experiment and do not pool versions. Completing the pilot would still leave the cross-paper protocol mismatch.

Place a concise external comparison and limitations in related work/discussion, with detailed protocol differences and historical pilot results in the supplement to protect the eight-page target. Keep the matched deterministic/LLM/hybrid medication comparison as the priority: adding published QA scores cannot replace the central safety experiment or independent review. Revised manuscript prose still goes through the authorized humanizer and factual checks before insertion.

If no independent author/reviewer becomes available, complete A–C and publish only engineering/development conclusions where an appropriate venue permits. Do not label that route as independently validated clinical research. More cosmetic rewriting or model tuning cannot substitute for the missing evidence.

## Verified reference leads

- [MedRAGChecker](https://aclanthology.org/2026.findings-emnlp.399/): biomedical claim-level NLI and KG compatibility.
- [CRITIC-RAG](https://pubmed.ncbi.nlm.nih.gov/42139130/): verifier-enhanced medical RAG; full-text methods must be read before a detailed implementation comparison.
- [MedRAG and MIRAGE](https://aclanthology.org/2024.findings-acl.372/): medical RAG component evaluation.
- [MedQA original paper](https://arxiv.org/html/2009.13081), document-collection section: research-use-only textbook agreement.
- [IJDDT journal remit](https://ijddt.com/) and [author instructions](https://ijddt.com/instructions/).

Local audit inputs: final retained manuscript `paper/revisions/20261031/updated_paper_20261031.docx`, `evaluation/safety_v2.py`, `evaluation/INDEPENDENT_EVALUATION_PROTOCOL.md`, existing aggregate results and local Git tree at `68e9b05`.
