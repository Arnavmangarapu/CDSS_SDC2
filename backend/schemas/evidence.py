from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class EvidenceItem(BaseModel):
    id: str
    source_type: str
    source_name: str
    title: Optional[str] = None
    text: str
    score: float = 0.0
    metadata: Dict[str, Any] = {}
    supports: List[str] = []
    contradicts: List[str] = []
