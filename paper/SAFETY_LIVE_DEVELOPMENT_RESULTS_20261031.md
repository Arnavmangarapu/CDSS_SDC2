# Live medication-safety development comparison

Completed all 108 planned synthetic cases and all 432 case/arm records. This is a new model-inference experiment on reused developer-authored material, not an independent held-out clinical study. The first 33 cases and every failure were retained unchanged across an infrastructure interruption and bounded continuations.

| Arm | Warning precision | Warning recall | Useful supported-warning recall | Exact warning/support cases | Failed cases |
| --- | ---: | ---: | ---: | ---: | ---: |
| Deterministic extraction + rules | 72/72 (100.0%) | 72/72 (100.0%) | 48/48 (100.0%) | 108/108 (100.0%) | 0 |
| LLM-only warnings | 49/65 (75.4%) | 49/72 (68.1%) | 37/48 (77.1%) | 81/108 (75.0%) | 1 |
| Production extraction + rules | 69/69 (100.0%) | 69/72 (95.8%) | 45/48 (93.8%) | 106/108 (98.1%) | 2 |
| Same LLM warnings + rule filter | 46/46 (100.0%) | 46/72 (63.9%) | 34/48 (70.8%) | 83/108 (76.9%) | 3 |

## Meaning of the comparison

The hybrid produced more exact decisions than the LLM-only warning baseline on these fixtures, but did not improve on the strong deterministic baseline. The baseline already matched every expected case. The rule-filter ablation illustrates a coverage tradeoff: false supported warnings fell from 14/51 to 0/34, while useful supported recall fell from 37/48 to 34/48. Warning precision improved to 100%, but warning recall fell from 49/72 to 46/72. Removing unsupported emissions cannot recover omitted warnings.

All arms used a fixed proposed amlodipine option and supplied label passages. The LLM-only task predicts warning/support types; it is not the 36-case diagnosis baseline. Production clarification uses the unchanged LLM prompt and deterministic merging/linking. The filter reuses the same LLM warnings and the rule eligibility computed from that observed production context, without adding warnings. It requires an additional extraction call and is not an equal-compute competitor or general semantic verifier. No live source retrieval, free treatment generation, clinician workflow or patient outcome was tested.

## Failures and continuation

One production extraction request timed out. The execution environment later terminated the first process after 33 complete cases (exit 143); its next possible in-flight extraction was conservatively counted failed instead of regenerated. One LLM-only response was invalid. The filter inherits three dependency failures; those are not additional model requests. Under the frozen controlled policy, unavailable/invalid LLM extraction was counted failed rather than credited as the production deterministic fallback. These scores therefore should not be described as proof that the operational fallback returned an unsafe warning.

Administrative runner checkpoints added continuation and complete-case segmentation. Continuation verified unchanged clinical function/class ASTs, other implementation hashes, case/source/ontology hashes and runtime configuration. Original outputs remained intact. Protocols were frozen before each continuation, and the final matrix passed duplicate/completeness checks. No generated answer was repeated to improve a score.

## Extraction observations

- Raw current-medication name sets matched 106/108 planned cases; full medication name/status sets matched 76/108. These exact-name/status comparisons can penalize synonyms and include easy empty-set controls.
- Merged allergy status, medication-list status and current-medication sets each matched 106/108. All 106 completed production extractions matched these merged fields; the two controlled failed attempts remain failures in the primary denominator.
- All 124 emitted source phrases were copied literally from the input. This measures literal grounding of emitted spans, not semantic correctness or completeness; omitted statements are not in that denominator.
- The unchanged raw LLM schema does not request allergy-status or medication-list-status fields. No raw status accuracy is invented from their absence. Raw and merged outputs are preserved privately for audit.

## Reporting limits

All cases informed earlier development, labels lack independent clinical review, and drug/rule scope is narrow. Family/template dependence limits confidence-interval and paired-test interpretation. Case-level Wilson intervals and paired exact tests in the JSON are descriptive/exploratory, not clinical generalization evidence. The provider returned the string `gemini-3.5-flash-lite`; a returned alias is not independent proof of an immutable underlying model revision.

The externally reported base-paper QA outcomes are retained separately in `BASE_PAPER_COMPARISON_20261031.json`; different tasks/scoring prevent a head-to-head ranking. The old 255/300-attempt QA pilot was not pooled or silently resumed under changed code.

## Verification and remaining work

Offline regression suite: 95 passed, one live-LLM test deselected; live clinical API tests excluded. No production clinical prompts, rules or trained weights were changed for these comparisons. No database writes were made.

Independent case authorship, qualified clinical review, actual source-use confirmation, declarations deferred by the user and a verified public archive remain pending. A private source/aggregate review candidate is prepared; it does not make the repository public. Manuscript prose is processed through the authorized humanizer and then checked against the locked aggregate values.
