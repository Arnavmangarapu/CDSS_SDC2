from typing import List, Dict, Any, Tuple
from backend.schemas.patient import PatientContext
from backend.schemas.retrieval import OrchestratorResult
from backend.schemas.evidence import EvidenceItem
from backend.schemas.report import DiagnosisCandidate
from backend.services.llm_fallback import LLMFallback

class ClinicalFusion:
    def __init__(self):
        self.llm = LLMFallback()

    def fuse(
        self, 
        context: PatientContext, 
        retrieval_result: OrchestratorResult, 
        ranked_evidence: List[EvidenceItem],
        conflicts: List[Dict[str, Any]]
    ) -> Tuple[List[DiagnosisCandidate], List[str], List[str]]:
        
        prompt = self._build_prompt(context, retrieval_result, ranked_evidence, conflicts)
        
        def validate_fusion(data):
            if not isinstance(data.get("diagnoses"), list):
                raise ValueError("diagnoses must be a list")
            if not isinstance(data.get("missing_information", []), list):
                raise ValueError("missing_information must be a list")
            if not isinstance(data.get("recommended_investigations", []), list):
                raise ValueError("recommended_investigations must be a list")
            for diagnosis in data["diagnoses"]:
                DiagnosisCandidate(**diagnosis)

        parsed = self.llm.generate_json(
            prompt,
            "You are an expert clinical decision support system AI. Output strictly valid JSON.",
            validate=validate_fusion,
        )

        if not parsed:
            print("WARNING: All LLM Fusion attempts failed! Falling back to raw graph dump to prevent crash.")
            
            # Absolute fallback that dumps graph traversal results into a dummy diagnosis so the UI doesn't break
            graph_diseases = []
            if retrieval_result.graph_results and retrieval_result.graph_results.candidate_diseases:
                graph_diseases = [d["name"] for d in retrieval_result.graph_results.candidate_diseases]

            fallback_diagnosis = DiagnosisCandidate(
                diagnosis="LLM Synthesis Failed - Raw Graph Entities Found: " + ", ".join(graph_diseases[:5]) if graph_diseases else "LLM Synthesis Failed",
                confidence=0.0,
                supporting_evidence_ids=[],
                conflicting_evidence_ids=[],
                recommended_tests=[],
                treatment_considerations=[],
                safety_notes=["The AI synthesis engines failed (API limits). Showing raw graph entities."]
            )
            return [fallback_diagnosis], ["Missing LLM Context"], ["Run API troubleshooting"]

        diagnoses = [DiagnosisCandidate(**d) for d in parsed.get("diagnoses", [])]
        if context.hypertension_scope and context.missing_information:
            for diagnosis in diagnoses:
                if diagnosis.treatment_considerations:
                    diagnosis.treatment_considerations = []
                    diagnosis.safety_notes.append(
                        "Treatment options withheld pending clinician confirmation of: "
                        + "; ".join(context.missing_information)
                    )
        missing = parsed.get("missing_information", [])
        inv = parsed.get("recommended_investigations", [])
        
        return diagnoses, missing, inv

    def _build_prompt(self, context, retrieval_result, ranked_evidence, conflicts):
        prompt = "Synthesize the following clinical case and retrieved evidence into a differential diagnosis.\n\n"
        
        prompt += "### Patient Context\n"
        prompt += f"Raw Input: {context.raw_input}\n"
        prompt += f"Symptoms: {[s.normalized_name or s.text for s in context.symptoms]}\n"
        prompt += f"Conditions: {[s.normalized_name or s.text for s in context.known_conditions]}\n"
        prompt += f"Current medications: {[s.normalized_name or s.text for s in context.medications]}\n"
        prompt += f"Medication list status: {context.medication_list_status}\n"
        prompt += f"Allergy status: {context.allergy_status}; reported allergies: {[s.text for s in context.allergies]}\n"
        prompt += f"Blood pressure readings: {[reading.model_dump() for reading in context.blood_pressure_readings]}\n"
        prompt += f"Hypertension explicitly confirmed: {context.hypertension_confirmed}\n"
        prompt += f"Pregnancy status: {context.pregnancy_status}\n"
        prompt += f"Reported labs: {context.labs}\n"
        prompt += f"Missing patient information: {context.missing_information}\n\n"
        
        prompt += "### Retrieved Evidence (Graph, Vector & Web)\n"
        for ev in ranked_evidence[:10]:  # Limit to top 10
            prompt += f"- [{ev.id}] {ev.title}: {ev.text[:200]}...\n"
            
        prompt += "\n### Required Output Format (Strict JSON)\n"
        prompt += "{\n"
        prompt += '  "diagnoses": [\n'
        prompt += '    {\n'
        prompt += '      "diagnosis": "Disease Name",\n'
        prompt += '      "confidence": 0.95,\n'
        prompt += '      "supporting_evidence_ids": ["ev-1", "ev-2"],\n'
        prompt += '      "conflicting_evidence_ids": [],\n'
        prompt += '      "recommended_tests": ["Test A"],\n'
        prompt += '      "treatment_considerations": ["Treatment A"],\n'
        prompt += '      "safety_notes": []\n'
        prompt += '    }\n'
        prompt += '  ],\n'
        prompt += '  "missing_information": ["Patient age not provided"],\n'
        prompt += '  "recommended_investigations": ["Referral"]\n'
        prompt += "}\n"
        return prompt
