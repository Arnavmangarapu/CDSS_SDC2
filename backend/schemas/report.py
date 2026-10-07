from pydantic import BaseModel
from typing import List, Dict, Any
from .evidence import EvidenceItem

class DiagnosisCandidate(BaseModel):
    diagnosis: str
    confidence: float
    supporting_evidence_ids: List[str]
    conflicting_evidence_ids: List[str] = []
    recommended_tests: List[str] = []
    treatment_considerations: List[str] = []
    safety_notes: List[str] = []

class ClinicalReport(BaseModel):
    disclaimer: str
    case_summary: str
    ranked_diagnoses: List[DiagnosisCandidate]
    missing_information: List[str]
    conflicts: List[Dict[str, Any]]
    overall_confidence: float
    limitations: List[str]
    references: List[EvidenceItem]
