from typing import List
from backend.schemas.patient import PatientContext, LinkedEntity
from backend.services.entity_linker import EntityLinker
from backend.services.llm_fallback import LLMFallback

class ClinicalClarifier:
    def __init__(self, entity_linker: EntityLinker):
        self.linker = entity_linker
        self.llm = LLMFallback()

    def process(self, raw_text: str) -> PatientContext:
        """
        Extracts patient context with Gemini, Cohere, Mistral, and OpenRouter fallbacks.
        """
        prompt = (
            "You are a medical data extraction system. Extract the clinical information from the following text into JSON.\n"
            "Output strictly valid JSON with the following structure. If a field is missing, use null or an empty list.\n\n"
            "{\n"
            '  "age": 45,\n'
            '  "sex": "male",\n'
            '  "safety_flags": ["chest pain", "shortness of breath"],\n'
            '  "symptoms": ["headache", "nausea"],\n'
            '  "conditions": ["type 2 diabetes", "hypertension"],\n'
            '  "medications": ["metformin", "lisinopril"]\n'
            "}\n\n"
            f"Clinical Text:\n{raw_text}"
        )
        
        def validate_extraction(data):
            for field in ("symptoms", "conditions", "medications", "safety_flags"):
                if not isinstance(data.get(field, []), list):
                    raise ValueError(f"{field} must be a list")
                if any(not isinstance(item, str) for item in data.get(field, [])):
                    raise ValueError(f"{field} must contain strings")

        parsed = self.llm.generate_json(
            prompt,
            "You are a clinical entity extractor. Output JSON only.",
            validate=validate_extraction,
        )

        # Hard fallback to prevent crashes if all 4 APIs go down or limits are exceeded
        if not parsed:
            print("WARNING: All Clarifier LLMs failed! Falling back to basic extraction.")
            parsed = {"age": None, "sex": None, "safety_flags": [], "symptoms": [], "conditions": [], "medications": []}
            
        # Parse extracted lists and link them
        age = parsed.get("age")
        sex = parsed.get("sex")
        safety_flags = parsed.get("safety_flags", [])
        
        symptoms = []
        for sym in parsed.get("symptoms", []):
            linked = self.linker.link(sym, "symptom")
            symptoms.append(linked)
            
        conditions = []
        for cond in parsed.get("conditions", []):
            linked = self.linker.link(cond, "condition")
            conditions.append(linked)
            
        medications = []
        for med in parsed.get("medications", []):
            linked = self.linker.link(med, "medication")
            medications.append(linked)

        return PatientContext(
            raw_input=raw_text,
            age=age,
            sex=sex,
            symptoms=symptoms,
            known_conditions=conditions,
            medications=medications,
            safety_flags=safety_flags
        )
