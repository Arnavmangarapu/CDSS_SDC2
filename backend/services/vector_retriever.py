import os
from typing import List, Dict, Any
from backend.schemas.patient import PatientContext
from backend.config import settings

class VectorRetriever:
    def __init__(self):
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
            self.client = QdrantClient(settings.QDRANT_URL)
            self.model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')
            self.collection_name = settings.VECTOR_COLLECTION_TEXTBOOKS
            self.is_ready = True
        except Exception as e:
            print(f"Failed to initialize VectorRetriever: {e}")
            self.is_ready = False

    def build_index(self, chunks: List[Dict[str, Any]]):
        """No-op. Indexing is now handled out-of-band by ingestion scripts into Qdrant."""
        pass

    def retrieve(self, context: PatientContext, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.is_ready:
            return []

        base_query = context.expanded_query if context.expanded_query else context.raw_input
        query_parts = [base_query]
        query_parts.extend([s.text for s in context.symptoms])
        query = " ".join(query_parts)

        try:
            query_vec = self.model.encode(query).tolist()
            
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=top_k
            )
            
            results = []
            for hit in search_result.points:
                if hit.score > 0.4: # Minimal threshold for semantic match
                    results.append({
                        "text": hit.payload.get("text", ""),
                        "metadata": {"source": hit.payload.get("source", "")},
                        "score": hit.score
                    })
            return results
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
