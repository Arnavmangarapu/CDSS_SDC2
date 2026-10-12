# Step 8 evaluation

For the proposed multi-condition benchmark, staged implementation, metric definitions, and paper reporting, see [MULTI_DISEASE_EVALUATION_PLAN.md](MULTI_DISEASE_EVALUATION_PLAN.md). The plan has not been executed.

This is a reproducible **engineering evaluation on six hand-authored synthetic cases**, not a clinical validation set. Every reference diagnosis is stated in its case text. Top-k results measure recognition on these fixtures, not diagnostic performance on patients. The cases live outside the indexed textbook and pinned source corpus. The runner also checks that no case text appears verbatim in a pinned passage.

## Run

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

## Artifacts and interpretation

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

## Source and design limits

The pinned corpus covers NICE NG136 recommendations for adult hypertension (England; snapshot updated 2026-02-26) and one DailyMed amlodipine label (United States; effective 2026-01-01). The source manifest records URLs, checksums, license notes, and sections. The two source jurisdictions differ. The medication rules cover only amlodipine sensitivity and its simvastatin interaction; other contraindications and interactions are untested. The synthetic set is tiny, contains mostly known hypertension, and includes a pregnancy and GERD boundary case. It has no clinician-selected differential diagnoses, real-world prevalence, complex missingness, prospective workflow, or patient outcomes. Independent clinician review of the source choices, case labels, claim support, and treatment safety remains pending.
