# Step 8 evaluation

For the proposed full multi-condition benchmark, staged implementation, metric definitions, and paper reporting, see [MULTI_DISEASE_EVALUATION_PLAN.md](MULTI_DISEASE_EVALUATION_PLAN.md). The synthetic pilot and the separate MedQA exam-vignette pilot are exploratory subsets of that broader plan.

## MedQA US test exam-vignette pilot (13 October 2026)

The local [MedQA](https://github.com/jind11/MedQA) USMLE `test.jsonl` file is an **exam question split**, not a patient-record dataset. The [adapter](medqa_adapter.py) requires SHA-256 `cfa75cbcc53c29b023752b0a395ff49d8202121041392735ae44771a5ec734a3` and scans its 1,273 rows. The frozen eligibility rule requires an exact terminal “most likely diagnosis?” prompt, a keyed answer equal to its answer option, at least 100 characters of vignette before that prompt, no literal answer in the vignette, and a recognized exam step. This yields 89 eligible cases: 27 Step 1 and 62 Step 2/3. Before seeing model outputs, SHA-256 sorting with seed `cdss-medqa-diagnosis-v1` selected 12 and 24 cases respectively. [The committed selection manifest](medqa_selection.v1.json) records the source hash, rules, counts, and zero-based source row indices. All 36 selected answer strings are distinct.

The adapter sends only the vignette stem to `/analyze`: answer choices, keyed answer, and terminal diagnosis question are withheld. The answer is available only to the scorer. It is a single exact normalized alias, so synonymous diagnoses can count as misses. This is **generative answer agreement** on a selected public examination subset, not multiple-choice accuracy, independent clinical diagnosis adjudication, or patient-case validation. The public test questions may also have appeared in provider training data; this cannot be ruled out. The pinned guideline and label corpus is limited to hypertension and amlodipine, so most selected questions are outside its supported source scope.

With the original MedQA test file in the documented local path, regenerate and run the frozen set:

```bash
python -m evaluation.medqa_adapter --output evaluation/runs/medqa-us-diagnosis-v1/cases.json
python -m evaluation.run --cases evaluation/runs/medqa-us-diagnosis-v1/cases.json --output evaluation/runs/medqa-us-diagnosis-v1-results --review-sample-size 1000
```

Use fresh output paths for reruns; both commands refuse to overwrite existing artifacts. Raw MedQA questions, derived vignette text, answer keys, and generated reports stay in ignored `evaluation/runs/`. Only the selection protocol, metadata, and aggregate result snapshot are committed. Warning sensitivity, retrieval Hit@k, claim-support accuracy, and unsafe-option rate cannot be estimated from these diagnosis answer keys.

## Four-condition synthetic diagnostic pilot (12 October 2026)

A **pilot subset** of that plan has now run on [12 author-built, diagnosis-withheld cases](cases.multidisease-pilot.v1.json): three each for hypertension, chronic asthma, type 2 diabetes, and GORD/dyspepsia. To rerun locally with the documented graph/vector services, pinned snapshots, and configured providers:

```bash
python -m evaluation.run --cases evaluation/cases.multidisease-pilot.v1.json --output evaluation/runs/new-multidisease-pilot --review-sample-size 1000
```

The 12 October run completed 36/36 analyses. Strict normalized exact-alias matches at rank 1 were 10/12 (LLM only), 9/12 (text RAG), and 10/12 (graph plus text); rank-3 counts were identical. [The versioned result snapshot](../paper/MULTIDISEASE_PILOT_RESULTS.json) provides disease-level counts, descriptive Wilson intervals, per-case rank-1 strings, provider traces, and hashes. The local graph returned zero disease candidates in all pilot cases; an audit found no phenotype-type relations for the current disease query. Two cases used different synthesis providers across modes, so differences between arms are not evidence of graph benefit. Citation identity matched 30/30 text-RAG and 26/26 graph-plus-text uses; semantic support was not adjudicated.

These cases have **provisional author-intended labels**, no clinician reference standard, no negative/mimic sample, and only three examples per condition. The application's pinned authoritative corpus still covers adult hypertension and one amlodipine label. The pilot contains no positive warning opportunities or independently labeled relevant passages, so warning sensitivity, retrieval Hit@k/Recall@k, claim-support precision, unsafe-option rate, and clinical diagnostic accuracy remain unavailable. The archived six-case fixture results below remain a separate safety/boundary engineering check.

## Historical six-case fixture evaluation

This is a reproducible **engineering evaluation on six hand-authored synthetic cases**, not a clinical validation set. Every reference diagnosis is stated in its case text. Top-k results measure recognition on these fixtures, not diagnostic performance on patients. The cases live outside the indexed textbook and pinned source corpus. The runner also checks that no case text appears verbatim in a pinned passage.

### Run

From the project root, with the documented Python dependencies and local Neo4j/Qdrant services configured:

```bash
python -m evaluation.run --output evaluation/runs/full-001
```

Each case is run through the same clarifier, fusion, verifier, safety detector, and report builder in three modes. `llm_only` removes graph and text retrieval; `text_rag` uses textbook vectors and pinned guideline/label passages; `graph_text` adds Neo4j graph retrieval to that text. Web discovery and DrugCentral are disabled in all modes so those changing sources cannot favor one arm. Case order is fixed; mode order rotates by case. The clarifier runs once per case and its context is reused in all three arms. The runner calls the existing `/analyze` implementation directly and does not change the production API.

The default retry count is zero to keep the comparison bounded. For a quick infrastructure check, use `--limit 1` with a distinct output path. A captured run can be rescored without provider calls:

```bash
python -m evaluation.run --replay evaluation/runs/full-001/case_results.jsonl --output evaluation/runs/full-001-rescore
```

The runner fails closed if the pinned source snapshots are missing or their checksums no longer match the manifest. A new run never overwrites an existing output directory. Generated runs are Git ignored; retain a run directory if reporting its numbers.

### Artifacts and interpretation

- `run_manifest.json`: dataset version/hash, source manifest hash and document dates, prompt hashes, configured model IDs, actual provider trace in each case result, Git commit and dirty state, run settings, and command. `openrouter/free` can change underlying models; the provider trace cannot resolve that model version.
- `metrics.json`: per-mode numerators, denominators, values, and reasons when a metric is unavailable. Failed runs are separate from successful-case metrics and appear in `failed_cases`.
- The metric file also flags cases where fallback selected different synthesis providers across modes. Those cases cannot support a clean retrieval-only comparison. A matching `openrouter/free` ID still does not guarantee the same underlying model.
- `case_results.jsonl`: per-case reports, retrieval, provider trace, and latency; may contain case details and must be handled as sensitive if real cases are ever used.
- `case_errors.jsonl`: diagnostic misses, missed or unexpected narrow warning types, bad citations, clinician-adjudicated unsupported claims or unsafe options, and run failures.
- `review_packet_blinded.jsonl`: shuffled claim text, case/context, and cited passages without mode or system status, for independent reviewers.
- `review_index_private.jsonl`: mapping from review IDs to mode and system status; do not give this to reviewers before adjudication.
- `review_disagreements.jsonl`: unresolved differences between reviewers.

Diagnostic top-1 and top-3 use exact normalized matches to the explicit reference aliases. Citation validity checks that each cited ID resolves to a passage whose full stored metadata and text match the pinned corpus. Warning sensitivity measures the three labeled fixture types (`amlodipine_allergy`, `amlodipine_simvastatin`, and `allergy_status_unconfirmed`); verified label-warning sensitivity uses the first two and requires `verification_status=supported`. False-positive rate counts warning-negative cases with either label warning. Claim abstention is the fraction marked `unverified`. Latency includes shared clarification plus each mode's analysis, and excludes process and model initialization.

Claim support accuracy, unsupported-claim rate, and unsafe-option rate remain **unavailable** until independent clinical adjudication. The scorer never infers those labels from the model's own status or from a citation. A citation can be valid while a claim is clinically false or inapplicable. For each sampled review item, collect two qualified reviewers' independent judgments in JSONL:

```json
{"review_id":"review_...","reviewer_id":"reviewer-a","support_label":"supported","option_safety_label":"uncertain"}
{"review_id":"review_...","reviewer_id":"reviewer-b","support_label":"supported","option_safety_label":"uncertain"}
```

Allowed support labels are `supported`, `unsupported`, and `uncertain`; option safety labels are `safe`, `unsafe`, and `uncertain`. For non-treatment claims use `uncertain` for option safety. Each reviewer should check cited source section, date, population, conditions, and patient facts, then record their answer independently. Unanimous two-reviewer items can be scored; disagreements are listed and excluded until a documented reconciliation. Use the resulting file with `--adjudications path/to/reviews.jsonl --replay ... --output ...`. Do not interpret synthetic fixture performance or provisional metrics as patient safety, calibrated probability, or outcome benefit.

### Source and design limits

The pinned corpus covers NICE NG136 recommendations for adult hypertension (England; snapshot updated 2026-02-26) and one DailyMed amlodipine label (United States; effective 2026-01-01). The source manifest records URLs, checksums, license notes, and sections. The two source jurisdictions differ. The medication rules cover only amlodipine sensitivity and its simvastatin interaction; other contraindications and interactions are untested. The synthetic set is tiny, contains mostly known hypertension, and includes a pregnancy and GERD boundary case. It has no clinician-selected differential diagnoses, real-world prevalence, complex missingness, prospective workflow, or patient outcomes. Independent clinician review of the source choices, case labels, claim support, and treatment safety remains pending.
