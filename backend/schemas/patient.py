from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class LinkedEntity(BaseModel):
    text: str
    normalized_name: Optional[str] = None
    entity_type: str
    ontology_id: Optional[str] = None
    ontology_source: Optional[str] = None
    confidence: float = 0.0
    candidates: List[Dict[str, Any]] = []

class PatientContext(BaseModel):
    raw_input: str
    expanded_query: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    symptoms: List[LinkedEntity] = []
    known_conditions: List[LinkedEntity] = []
    medications: List[LinkedEntity] = []
    allergies: List[LinkedEntity] = []
    vitals: Dict[str, Any] = {}
    labs: List[Dict[str, Any]] = []
    missing_information: List[str] = []
    safety_flags: List[str] = []
