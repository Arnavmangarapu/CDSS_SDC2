from typing import List, Dict, Any
from backend.schemas.patient import PatientContext
from backend.schemas.evidence import EvidenceItem
from backend.schemas.report import ClinicalReport, DiagnosisCandidate

class ReportGenerator:
    def generate(
        self, 
        context: PatientContext, 
        diagnoses: List[DiagnosisCandidate], 
        evidence: List[EvidenceItem], 
        conflicts: List[Dict[str, Any]], 
        missing_info: List[str],
        confidence: float,
        limitations: List[str]
    ) -> ClinicalReport:
        """
        Constructs the final Clinical Report.
        """
        disclaimer = (
            "WARNING: This is a research/educational decision-support output and MUST NOT be used "
            "as a medical diagnosis. A licensed clinician must review all findings."
        )
        
        # Build case summary
        age_str = f"{context.age}-year-old " if context.age else "Patient "
        sex_str = f"{context.sex} " if context.sex else ""
        symptoms = [s.text for s in context.symptoms]
        summary = f"{age_str}{sex_str}presenting with {', '.join(symptoms) if symptoms else 'unspecified symptoms'}."
        
        # Add safety note to diagnoses based on conflicts
        for d in diagnoses:
            d.treatment_considerations.append(f"The evidence supports considering {d.diagnosis} as part of the differential diagnosis.")
            for c in conflicts:
                if d.diagnosis in c.get("description", ""):
                    d.safety_notes.append(f"SAFETY WARNING: {c.get('description')}")
        
        # Default limitations
        report_limitations = limitations.copy()
        report_limitations.append("The system relies on local automated extraction and may miss nuances in the clinical text.")
        
        return ClinicalReport(
            disclaimer=disclaimer,
            case_summary=summary,
            ranked_diagnoses=diagnoses,
            missing_information=missing_info,
            conflicts=conflicts,
            overall_confidence=confidence,
            limitations=report_limitations,
            references=evidence
        )
