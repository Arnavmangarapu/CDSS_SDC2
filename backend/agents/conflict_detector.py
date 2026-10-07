from typing import List, Dict, Any
from backend.schemas.patient import PatientContext
from backend.schemas.retrieval import OrchestratorResult
from backend.schemas.evidence import EvidenceItem

class ConflictDetector:
    def detect(
        self, 
        context: PatientContext, 
        retrieval_result: OrchestratorResult, 
        ranked_evidence: List[EvidenceItem]
    ) -> List[Dict[str, Any]]:
        """
        Detects contradictions (contraindications, drug-drug interactions, missing symptoms).
        Returns a list of conflict dictionaries with severity.
        """
        conflicts = []
        
        # 1. Check Drug Contraindications from Graph Results
        for contra in retrieval_result.graph_results.contraindications:
            drug = contra.get("drug")
            disease = contra.get("disease")
            # If the disease is one of the top candidates, we flag it
            candidate_names = [d.get("name") for d in retrieval_result.graph_results.candidate_diseases]
            if disease in candidate_names:
                conflicts.append({
                    "type": "contraindication",
                    "severity": "high",
                    "description": f"Current medication '{drug}' is contraindicated for candidate disease '{disease}'."
                })
        
        # 2. Check Drug-Drug Interactions
        for interaction in retrieval_result.graph_results.drug_interactions:
            conflicts.append({
                "type": "drug_interaction",
                "severity": "high",
                "description": f"Potential drug interaction between {interaction.get('drug_a')} and {interaction.get('drug_b')}."
            })
            
        # 3. Weak Evidence Check
        if retrieval_result.graph_results.candidate_diseases and not ranked_evidence:
            conflicts.append({
                "type": "weak_evidence",
                "severity": "medium",
                "description": "Candidates generated but no strong evidence found to support them."
            })
            
        # 4. Critical Missing Information
        if not context.age or not context.sex:
            conflicts.append({
                "type": "missing_info",
                "severity": "low",
                "description": "Demographic information (age/sex) is incomplete."
            })
            
        return conflicts
