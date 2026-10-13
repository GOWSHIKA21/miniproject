import logging
from typing import List, Dict, Any, Optional
from backend.app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchProvenance,
    SearchFilters
)
from backend.app.retrieval.keyword_search import bm25_retriever
from backend.app.retrieval.vector_search import faiss_retriever
from backend.app.services.patent_service import patent_service

logger = logging.getLogger(__name__)

class HybridRetrievalEngine:
    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf

    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 20,
        retrieval_method: str = "hybrid"
    ) -> SearchResponse:
        """Execute hybrid or individual retrieval with RRF merging, metadata filtering, and provenance tracking."""
        candidates = {}  # patent_id -> {rrf_score, bm25_rank, vector_rank, vector_score, bm25_score}

        # 1. Execute BM25 search
        bm25_results = []
        if retrieval_method in ("hybrid", "bm25"):
            bm25_results = bm25_retriever.search(query, top_k=top_k * 3)
            for item in bm25_results:
                pid = item["patent_id"]
                rank = item["rank"]
                candidates.setdefault(pid, {
                    "bm25_rank": rank,
                    "bm25_score": item["score"],
                    "vector_rank": None,
                    "vector_score": None,
                    "rrf_score": 0.0
                })
                candidates[pid]["rrf_score"] += 1.0 / (self.k_rrf + rank)

        # 2. Execute Vector search
        vector_results = []
        if retrieval_method in ("hybrid", "vector"):
            vector_results = faiss_retriever.search(query, top_k=top_k * 3)
            for item in vector_results:
                pid = item["patent_id"]
                rank = item["rank"]
                candidates.setdefault(pid, {
                    "bm25_rank": None,
                    "bm25_score": None,
                    "vector_rank": rank,
                    "vector_score": item["score"],
                    "rrf_score": 0.0
                })
                # Vector weight multiplier 1.2
                candidates[pid]["rrf_score"] += 1.2 / (self.k_rrf + rank)

        if not candidates:
            return SearchResponse(
                query=query,
                retrieval_method=retrieval_method,
                total_found=0,
                results=[]
            )

        # 3. Sort candidates by score
        if retrieval_method == "bm25":
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1].get("bm25_score", 0) or 0, reverse=True)
        elif retrieval_method == "vector":
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1].get("vector_score", 0) or 0, reverse=True)
        else:
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1]["rrf_score"], reverse=True)

        candidate_ids = [pid for pid, _ in sorted_candidates[:top_k * 3]]
        
        # 4. Fetch patent metadata in batch
        records_map = patent_service.get_patents_batch(candidate_ids)

        # 5. Apply metadata filters and format results
        results = []
        max_rrf = max((data["rrf_score"] for _, data in sorted_candidates), default=1.0) or 1.0

        for pid, data in sorted_candidates:
            raw = records_map.get(pid)
            if not raw:
                continue

            # Filtering
            if filters:
                if filters.field_of_invention and filters.field_of_invention != "All":
                    raw_field = str(raw.get("field_of_invention", "")).upper()
                    if filters.field_of_invention.upper() not in raw_field:
                        continue
                if filters.ipo_location and filters.ipo_location != "All":
                    raw_loc = str(raw.get("ipo_location", "")).upper()
                    if filters.ipo_location.upper() not in raw_loc:
                        continue
                if filters.application_type and filters.application_type != "All":
                    raw_app = str(raw.get("application_type", "")).upper()
                    if filters.application_type.upper() not in raw_app:
                        continue
                if filters.date_from and raw.get("filing_date"):
                    if str(raw["filing_date"]) < filters.date_from:
                        continue
                if filters.date_to and raw.get("filing_date"):
                    if str(raw["filing_date"]) > filters.date_to:
                        continue

            # Normalized score (0.0 to 1.0)
            if retrieval_method == "vector" and data["vector_score"] is not None:
                norm_score = max(0.0, min(1.0, float(data["vector_score"])))
            elif retrieval_method == "bm25" and data["bm25_score"] is not None:
                norm_score = min(1.0, float(data["bm25_score"]) / 25.0)
            else:
                norm_score = min(1.0, data["rrf_score"] / max_rrf)

            # Match evidence
            evidence_parts = []
            if data["vector_rank"] is not None:
                evidence_parts.append(f"Semantic vector match (Rank #{data['vector_rank']})")
            if data["bm25_rank"] is not None:
                evidence_parts.append(f"Keyword match (Rank #{data['bm25_rank']})")
            match_evidence = " & ".join(evidence_parts) if evidence_parts else "Metadata filter match"

            frontend_patent = patent_service.to_frontend_format(raw, relevance=norm_score)

            provenance = SearchProvenance(
                bm25_rank=data["bm25_rank"],
                vector_rank=data["vector_rank"],
                rrf_score=round(data["rrf_score"], 4),
                similarity_score=round(data["vector_score"], 4) if data["vector_score"] is not None else None
            )

            results.append(SearchResultItem(
                patent=frontend_patent,
                score=round(norm_score, 4),
                retrieval_method=retrieval_method,
                provenance=provenance,
                match_evidence=match_evidence
            ))

            if len(results) >= top_k:
                break

        return SearchResponse(
            query=query,
            retrieval_method=retrieval_method,
            total_found=len(results),
            results=results
        )

hybrid_retrieval_engine = HybridRetrievalEngine()
