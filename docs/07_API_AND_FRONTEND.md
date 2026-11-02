# 07 — API and frontend

[Documentation index](README.md) · [Previous: setup](06_SETUP_CONFIGURATION_AND_OPERATIONS.md) · [Next: testing and results](08_TESTING_EVALUATION_AND_RESULTS.md)

## 1. HTTP surface

| Method and path | Purpose | Important behavior |
| --- | --- | --- |
| `GET /health` | API liveness | Returns fixed status; does not initialize/test all services |
| `POST /analyze` | Analyze one free-text case | Synchronous complete-report response |
| `GET /ui/` | Browser application | Static HTML/CSS/JS served by FastAPI |
| `GET /docs` | FastAPI's default interactive API page | Generated from the declared API schema |
| `GET /openapi.json` | OpenAPI description | Request schema is typed; nested analysis response has no explicit response model |

There are no implemented login, patient CRUD, chat-history, asynchronous-job, or report-download API endpoints. The root `/` is not configured as a UI redirect.

## 2. Analyze request

```http
POST /analyze
Content-Type: application/json
```

```json
{"case_text":"A 57-year-old woman with confirmed hypertension currently takes amlodipine. She has no known drug allergies."}
```

`case_text` is the only declared request field. It is a required string. The backend currently accepts an empty string structurally, has no maximum input size validator, and does not return a custom error for every downstream dependency failure.

The UI trims and blocks blank submissions, but clients can call the API directly. Browser checks are not a substitute for backend validation.

## 3. Top-level response

Illustrative response outline, with variable lists abbreviated as empty arrays:

```json
{
  "patient_context": {
    "raw_input": "Synthetic case text",
    "age": 57,
    "sex": "female",
    "symptoms": [],
    "known_conditions": [],
    "medications": [],
    "medication_statements": [],
    "medication_list_status": "unknown",
    "allergies": [],
    "allergy_status": "unknown",
    "blood_pressure_readings": [],
    "pregnancy_status": "unknown",
    "hypertension_confirmed": null,
    "hypertension_scope": false,
    "missing_information": [],
    "safety_flags": []
  },
  "retrieval": {
    "graph_candidates": 0,
    "vector_items": 0,
    "drug_safety_matches": 0,
    "authoritative_passages": 0
  },
  "report": {
    "disclaimer": "Research and educational output; clinician review required.",
    "case_summary": "Illustrative summary.",
    "ranked_diagnoses": [],
    "missing_information": [],
    "conflicts": [],
    "overall_confidence": 0.0,
    "limitations": [],
    "references": [],
    "claims": [],
    "source_passages": [],
    "confidence_calibrated": false,
    "evidence_completeness": {},
    "verification_failures": [],
    "differential": [],
    "unassigned_diagnostic_claim_ids": [],
    "investigation_claim_ids": [],
    "treatment_claim_ids": [],
    "medication_safety": {
      "current_medications": [],
      "medication_list_status": "unknown",
      "allergies": [],
      "allergy_status": "unknown",
      "findings": [],
      "warning_claim_ids": []
    }
  }
}
```

This outline is not a model result for the earlier case and omits additional default patient fields. See [patient.py](../backend/schemas/patient.py) and [report.py](../backend/schemas/report.py) for the complete contracts.

## 4. Meaning of retrieval counters

`graph_candidates` counts candidate diseases, not graph edges. `vector_items` counts returned textbook items. `drug_safety_matches` counts drug records with targets, not verified interactions. `authoritative_passages` counts returned source passages, not supported claims.

These are counts from the final attempt. They do not summarize all retries or measure relevance, safety, or correctness.

## 5. Example claim

This illustrative unverified treatment object has no invented source ID:

```json
{
  "claim_id": "illustrative-claim",
  "claim_type": "treatment",
  "text": "A conditional option could be discussed after diagnosis and prerequisites are confirmed.",
  "status": "unverified",
  "applies_to": "Hypertension",
  "conditions": ["Diagnosis or condition confirmed: Hypertension"],
  "missing_checks": ["Current medication list not supplied"],
  "supporting_evidence_ids": [],
  "conflicting_evidence_ids": [],
  "unverified_evidence_ids": [],
  "rejected_evidence_ids": [],
  "unverified_reason": "No cited source passage; patient applicability requires review"
}
```

Runtime normalized claim IDs usually start with `claim_`. Source IDs must resolve to included `SourcePassage` objects with real matching content. Do not create placeholder source IDs and present them as valid citations.

## 6. Report grouping

`report.differential` lists ranked candidate names and related diagnosis/investigation/treatment claim IDs. General investigation and treatment sections have their own type-specific ID lists. Diagnostic claims that do not match a differential name appear in `unassigned_diagnostic_claim_ids`.

The matching rule is exact text after case folding. “Hypertension” and “High blood pressure” need not group together. The schema validates referenced claim types, but does not solve this name-equivalence issue.

`references` contains general retrieval evidence. `source_passages` contains the exact passage objects used to resolve claim citations. A legacy evidence UUID is not interchangeable with a source ID.

## 7. Frontend files

| File | Responsibility |
| --- | --- |
| [index.html](../frontend/index.html) | Input form, result containers, review headings |
| [style.css](../frontend/style.css) | Page layout, cards, badges, and loading/error presentation |
| [app.js](../frontend/app.js) | Submit handler, response parsing, claim/source mapping, report rendering |

There is no npm install step or generated frontend bundle. The browser loads the static files directly from the FastAPI mount.

## 8. Submit and error behavior

On submit, the UI disables the button and shows a spinner. After the request finishes, it restores the button in `finally`. An unsuccessful HTTP response or network failure shows a generic analysis-failed message.

Rendering has a separate error boundary. If JSON arrives but rendering fails, the UI hides the report and asks the user to refresh/retry. This avoids showing a partly rendered result as complete.

There is no request cancellation button, browser request timeout, streaming output, saved history, or automatic backend readiness check. Long backend fallback/retry sequences can leave the spinner visible for some time.

## 9. What the UI displays

The patient panel shows age, sex, allergy status, and medication-list status. The missing-information section remains separate. Differential cards show associated diagnosis claims; investigation and treatment claims have their own sections.

Claim state labels are:

| API state | UI text |
| --- | --- |
| `supported` | Supported finding |
| `conflicting` | Conflicting |
| `unverified` | Needs verification |

For treatment proposals that are not supported, a caution explains that the proposal is not a cleared treatment. Proposed supporting citations are labeled differently from verified-source citations. Each source row includes a dated section link, document ID/version, jurisdiction, and expandable passage text.

The overview counts supported, conflicting, and unverified claims. It explicitly says these counts are not diagnostic probabilities. Legacy diagnosis confidence and overall confidence fields remain in JSON for compatibility but are not displayed as percentages.

## 10. Medication safety display

The UI distinguishes unknown history, conflicting history, explicit no-current-medicine history, and no-known-allergy history. It says that no known allergies is not a safety clearance.

It removes duplicate finding text when the same content already appears as a warning claim. If no finding is present, it states that the limited check has not established medication safety. Absence of a detected warning must not become a green “safe” result.

## 11. Rendering and citation controls

Generated text is placed with `textContent` or text nodes rather than injected as HTML. Source links are enabled only for HTTPS URLs on `www.nice.org.uk` or `dailymed.nlm.nih.gov`; other or invalid URLs display as unavailable text. New tabs use `noopener noreferrer`.

These are useful UI safeguards within the current design. They do not implement authentication, authorization, complete security hardening, or proof that linked text supports the claim.

`FreshFrontendFiles` sets `Cache-Control: no-store, max-age=0` on static responses. This reduces mismatches between recently changed report markup and stale scripts.

## 12. Extending the contract

When adding a field, update the relevant schema, report builder, renderer, and meaningful regression checks together. For a new claim type, also update grouping validation and UI handling. For a new source publisher, review manifest validation, parsing, runtime trust checks, citation rendering policy, and evidence scope together.

Avoid adding a “supported” badge solely because a new document URL exists. The verification meaning must remain consistent across backend and frontend.
