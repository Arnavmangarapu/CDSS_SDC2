from typing import List, Dict, Any
import math
import re
from backend.schemas.patient import PatientContext
from backend.config import settings
from backend.schemas.evidence import SourcePassage
from backend.services.telemetry import stage

class VectorRetriever:
    def __init__(self):
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
            self.client = QdrantClient(settings.QDRANT_URL)
            self.model = SentenceTransformer(settings.VECTOR_EMBEDDER_MODEL,
                                              revision=settings.VECTOR_EMBEDDER_REVISION,
                                              local_files_only=True)
            self.collection_name = settings.VECTOR_COLLECTION_TEXTBOOKS
            self.is_ready = True
            self.reranker = None
            if settings.VECTOR_RERANKER_MODEL:
                try:
                    from sentence_transformers import CrossEncoder
                    self.reranker = CrossEncoder(settings.VECTOR_RERANKER_MODEL, device="cpu",
                        revision=settings.VECTOR_RERANKER_REVISION,
                        local_files_only=True, max_length=512)
                except (ImportError, OSError, ValueError):
                    print("Cross-encoder unavailable locally; using dense ranking. Run ingestion.prepare_models.")
        except Exception as e:
            print(f"Failed to initialize VectorRetriever: {e}")
            self.is_ready = False

    def build_index(self, chunks: List[Dict[str, Any]]):
        """No-op. Indexing is now handled out-of-band by ingestion scripts into Qdrant."""
        pass

    def retrieve(self, context: PatientContext, top_k: int = 5) -> List[Dict[str, Any]]:
        self.last_error = None
        if not self.is_ready:
            self.last_error = "Vector retriever unavailable"
            return []

        base_query = context.expanded_query if context.expanded_query else context.raw_input
        query_parts = [base_query]
        query_parts.extend([s.text for s in context.symptoms])
        query = " ".join(query_parts)

        try:
            with stage("embedding"):
                query_vec = self.model.encode(query).tolist()
            with stage("vector_search"):
                search_result = self.client.query_points(
                    collection_name=self.collection_name, query=query_vec, limit=max(20, top_k)
                )
            results = []
            for hit in search_result.points:
                results.append({
                        "text": hit.payload.get("text", ""),
                        "metadata": {"source": hit.payload.get("source", ""),
                                     "dense_score": hit.score, "chunk_id": str(hit.id)},
                        "score": hit.score,
                    })
            reranker = getattr(self, "reranker", None)
            if reranker is not None and results:
                with stage("reranking"):
                    scores = reranker.predict([(query, item["text"]) for item in results], show_progress_bar=False)
                for item, score in zip(results, scores):
                    item["metadata"]["reranker_score"] = float(score)
                    item["score"] = 1 / (1 + math.exp(-max(-50, min(50, float(score)))))
                results.sort(key=lambda item: item["score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            self.last_error = type(e).__name__
            print(f"Vector search failed: {e}")
            return []

    def retrieve_authoritative(self, context: PatientContext, top_k: int = 5) -> tuple[list[SourcePassage], list[str]]:
        query = context.expanded_query or context.raw_input
        # A normal BP reading in an unrelated case is not a hypertension query.
        scoped = bool(re.search(r"\b(?:hypertension|hypertensive|high blood pressure|amlodipine|simvastatin)\b",
                                context.raw_input, re.I))
        scoped = scoped or any(r.systolic_mm_hg >= 140 or r.diastolic_mm_hg >= 90
                               for r in context.blood_pressure_readings)
        if not scoped:
            return [], []
        return self.retrieve_authoritative_query(query, top_k)

    def retrieve_authoritative_query(self, query: str, top_k: int = 5) -> tuple[list[SourcePassage], list[str]]:
        """Return only pinned, checksum-verified source passages; report every unavailable collection."""
        from ingestion.authoritative_sources import COLLECTIONS, build_passages, load_manifest

        if not self.is_ready:
            return [], ["Authoritative vector retrieval is unavailable"]
        try:
            manifest = load_manifest()
            active = {entry.document_id: entry for entry in manifest.sources if not entry.retired}
            verified_ids = {p.id for items in build_passages(manifest).values() for p, _ in items}
        except Exception as exc:
            return [], [f"Authoritative source manifest or snapshot unavailable: {exc}"]

        passages: list[SourcePassage] = []
        dense_scores = {}
        limitations: list[str] = []
        try:
            with stage("embedding"):
                vector = self.model.encode(query)
            vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        except Exception as exc:
            return [], [f"Authoritative query embedding unavailable: {exc}"]
        for kind, collection in COLLECTIONS.items():
            if not any(entry.source_type == kind for entry in active.values()):
                continue
            try:
                with stage("vector_search"):
                    hits = self.client.query_points(collection_name=collection, query=vector,
                                                    limit=top_k, with_payload=True).points
            except Exception as exc:
                limitations.append(f"{kind} collection unavailable: {exc}")
                continue
            if not hits:
                limitations.append(f"{kind} collection has no matching source passages")
            for hit in hits:
                try:
                    payload = hit.payload or {}
                    passage = SourcePassage.model_validate(payload["source_passage"])
                    entry = active[passage.document_id]
                    if (entry.source_type != kind or passage.document_version != entry.document_version
                            or payload.get("source_sha256") != entry.sha256
                            or passage.id not in verified_ids):
                        raise ValueError("source version or checksum does not match manifest")
                    passages.append(passage)
                    dense_scores[passage.id] = float(hit.score)
                except (KeyError, ValueError, TypeError) as exc:
                    limitations.append(f"Rejected invalid {kind} citation payload: {exc}")
        # Both collections use the same encoder. Never impose a source-type rank.
        reranker = getattr(self, "reranker", None)
        if reranker is not None and passages:
            with stage("reranking"):
                scores = reranker.predict([(query, passage.passage) for passage in passages], show_progress_bar=False)
            ordered = sorted(zip(scores, passages), key=lambda pair: (-float(pair[0]), pair[1].id))
            passages = [passage for _, passage in ordered]
        else:
            passages.sort(key=lambda passage: (-dense_scores[passage.id], passage.id))
        return passages, limitations
