# Frozen three-dataset QA pilot

This experiment responds to the 50-question-per-dataset table in Öğdü et al.,
IEEE Access (2025), DOI 10.1109/ACCESS.2025.3613340. It measures our own adapted
system and does not reproduce that paper's system or exact question selection.

Before inference, SHA-256 ordering with seed `cdss-three-dataset-qa-v1` selects
50 items each from the local five-option MedQA US test split, MedBullets test
file, and the 500 official PubMedQA test IDs. Source hashes and selected IDs are
stored in the frozen manifest. No selection depends on model outputs. A fixed
requested Gemini Flash Lite model, temperature zero, no provider fallback, and
zero adaptive retries are used. Public-test training contamination is unknown.

The first execution stopped on HTTP 429 limits. Resume preserves every recorded
attempt (including failures) and executes only missing case/arm pairs. Transport
recovery waits for the provider cooldown and retries HTTP 429 up to three times;
it never retries a generated answer, changes the model, or replaces earlier
failed answers. Retain both original and resumed run manifests. A preceding
serialization smoke run stopped before a CDSS answer was recorded; it is not
part of the result matrix.

The current partial run stopped after 255/300 arm attempts when the provider
confirmed `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, limit 500.
Its saved metrics replay byte for byte. The status report is
`paper/QA_BENCHMARK_PARTIAL_RESULTS.md`; it is not the completed benchmark.
Forty-five arm attempts remain. After quota reset, continue without replacing
any earlier attempts:

```bash
python3 -u -m evaluation.run_qa_benchmark --prepared evaluation/runs/qa-table5-v1-frozen --resume-records evaluation/runs/qa-table5-v1-results-resumed/records.jsonl --output evaluation/runs/qa-table5-v1-completion
python3 -m evaluation.summarize_qa_benchmark --run evaluation/runs/qa-table5-v1-completion --output paper/QA_BENCHMARK_RESULTS
```

The runner now detects daily quota IDs and stops after preserving the failed
attempt, rather than treating a multi-hour reset as a minute-level rate limit.

Two arms alternate execution order per question:

- `llm_only`: original question and options directly to an answer selector.
- `cdss_qa_adapter`: original question (and PubMedQA abstract, where supplied)
  through the production clinical report pipeline, using graph, textbook, and
  pinned guideline/label retrieval, then the same answer selector with the
  report supplied as supplemental context. Web and DrugCentral are disabled.

The CDSS sees no multiple-choice options during patient-context extraction;
only the selector receives them. Gold labels, explanations, and PubMedQA
LONG_ANSWER are excluded from both inference inputs. PubMedQA supplies only
the abstract CONTEXTS and question, and uses standard yes/no/maybe exact scoring.
This differs from the IEEE paper's free-text semantic-similarity protocol.

The QA adapter is additional functionality and inference. A difference between
arms cannot isolate graph benefit, verification benefit, or compute-independent
improvement. The clinical pipeline is designed for patient cases; general
research questions may be outside its intended task. A question-answer match
cannot establish clinical safety or semantic verification accuracy.

Report correct/attempted, failures, accuracy with descriptive Wilson 95%
intervals, macro-F1, class support, and micro precision/recall/F1. For complete
valid single-label predictions, the micro measures equal accuracy. One-vs-rest
micro specificity is `1 - (1-accuracy)/(K-1)`; it is inflated by the number of
options. Invalid outputs are failures in the accuracy denominator; metrics
requiring valid single-label predictions are withheld. Interim runs are marked
incomplete and must not be presented as the planned full experiment.

Keep raw questions, keys and reports in ignored `evaluation/runs/`. Preserve
the frozen selection, prompts, source hashes, per-question provider and latency,
retrieval counts, and every failure. Reruns use new paths. Only aggregate results
and non-content selection metadata should be included in the manuscript/repo.

Commands from the repository root:

```bash
python3 -m evaluation.run_qa_benchmark --prepare-only --per-dataset 50 --output evaluation/runs/qa-table5-v1-frozen
python3 -u -m evaluation.run_qa_benchmark --prepared evaluation/runs/qa-table5-v1-frozen --output evaluation/runs/qa-table5-v1-results
python3 -m evaluation.run_qa_benchmark --prepared evaluation/runs/qa-table5-v1-frozen --replay evaluation/runs/qa-table5-v1-results/records.jsonl --output evaluation/runs/qa-table5-v1-replay
```

Published IEEE values (47/50 MedQA, 44/50 PubMedQA, 42/50 MedBullets) may be
shown as external reported results with a separate protocol column. They are
not paired baselines and do not support a superiority claim. Cite the original
MedQA and PubMedQA dataset papers and document MedBullets provenance.
