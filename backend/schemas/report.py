"""Legacy report fields plus claim-level provenance contracts."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .evidence import EvidenceItem, SourcePassage


ClaimType = Literal["diagnosis", "investigation", "treatment", "medication_warning"]
ClaimStatus = Literal["supported", "conflicting", "unverified"]


class ClinicalClaim(BaseModel):
    claim_id: str = Field(min_length=1)
    claim_type: ClaimType
    text: str = Field(min_length=1)
    status: ClaimStatus
    applies_to: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    missing_checks: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    unverified_evidence_ids: List[str] = Field(default_factory=list)
    rejected_evidence_ids: List[str] = Field(default_factory=list)
    unverified_reason: Optional[str] = None

    @field_validator("claim_id", "text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Claim ID and text must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def validate_status(self) -> "ClinicalClaim":
        if self.status == "supported" and not self.supporting_evidence_ids:
            raise ValueError("A supported claim needs supporting source IDs")
        if self.status == "conflicting" and not self.conflicting_evidence_ids:
            raise ValueError("A conflicting claim needs conflicting source IDs")
        if self.status == "unverified" and not (self.unverified_reason or "").strip():
            raise ValueError("An unverified claim needs a reason")
        all_ids = (
            self.supporting_evidence_ids
            + self.conflicting_evidence_ids
            + self.unverified_evidence_ids
        )
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("A source ID cannot appear more than once in a claim")
        return self


class DiagnosisCandidate(BaseModel):
    diagnosis: str
    confidence: float
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    recommended_tests: List[str] = Field(default_factory=list)
    treatment_considerations: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)


class ClinicalReport(BaseModel):
    disclaimer: str
    case_summary: str
    ranked_diagnoses: List[DiagnosisCandidate]
    missing_information: List[str]
    conflicts: List[Dict[str, Any]]
    overall_confidence: float
    limitations: List[str]
    references: List[EvidenceItem]
    claims: List[ClinicalClaim] = Field(default_factory=list)
    source_passages: List[SourcePassage] = Field(default_factory=list)
    confidence_calibrated: bool = False
    evidence_completeness: Dict[str, int] = Field(default_factory=dict)
    verification_failures: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_claim_provenance(self) -> "ClinicalReport":
        sources_by_id = {source.id: source for source in self.source_passages}
        if len(sources_by_id) != len(self.source_passages):
            raise ValueError("Source passage IDs must be unique")
        claim_ids = {claim.claim_id for claim in self.claims}
        if len(claim_ids) != len(self.claims):
            raise ValueError("Claim IDs must be unique")
        for claim in self.claims:
            cited_ids = (
                claim.supporting_evidence_ids
                + claim.conflicting_evidence_ids
                + claim.unverified_evidence_ids
            )
            missing = set(cited_ids) - sources_by_id.keys()
            if missing:
                raise ValueError(f"Claim {claim.claim_id} cites unavailable source passages")
            if claim.status == "supported" and all(
                sources_by_id[source_id].source_type == "graph_relation"
                for source_id in claim.supporting_evidence_ids
            ):
                raise ValueError(f"Claim {claim.claim_id} cannot be supported only by graph relations")
        return self
