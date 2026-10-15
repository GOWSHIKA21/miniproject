import math
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
from backend.app.database.mongodb import mongo_client
from backend.app.services.patent_service import patent_service

logger = logging.getLogger(__name__)

class HybridRetrievalEngine:
    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf

    def _filters_to_dict(self, filters: Optional[SearchFilters]) -> Dict[str, Any]:
        if not filters:
            return {}
        return {
            "field_of_invention": filters.field_of_invention,
            "fields_of_invention": filters.fields_of_invention,
            "ipo_location": filters.ipo_location,
            "inventor": filters.inventor,
            "organization": filters.organization,
            "application_type": filters.application_type,
            "date_type": filters.date_type,
            "priority_date": filters.priority_date,
            "exact_date": filters.exact_date,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
            "status": filters.status
        }

    def _has_active_filters(self, filter_dict: Dict[str, Any]) -> bool:
        for k, v in filter_dict.items():
            if v is not None and v != "" and v != [] and str(v).upper() not in ("ALL", "ALL PATENT OFFICES"):
                return True
        return False

    def search(
        self,
        query: str = "",
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        page_size: int = 25,
        top_k: Optional[int] = None,
        sort_by: str = "relevance",
        retrieval_method: str = "hybrid"
    ) -> SearchResponse:
        """
        Execute hybrid retrieval or structured database search with RRF ranking,
        exact database-side counting, filtering, and server-side pagination.
        """
        effective_page_size = top_k if (top_k is not None and top_k > 0) else page_size
        filter_dict = self._filters_to_dict(filters)
        has_filters = self._has_active_filters(filter_dict)
        query_str = query.strip() if query else ""
        is_generic_query = not query_str or query_str.lower() in ("patent invention", "all", "*")

        # CASE 1: Pure structured filter browse or empty/generic query
        if is_generic_query:
            if mongo_client.connected:
                total, raw_docs = mongo_client.search_patents(
                    query_text="",
                    filters=filter_dict,
                    sort_by=sort_by,
                    page=page,
                    page_size=effective_page_size
                )
            else:
                total, raw_docs = patent_service.search_fallback(
                    query_text="",
                    filters=filter_dict,
                    sort_by=sort_by,
                    page=page,
                    page_size=effective_page_size
                )

            total_pages = math.ceil(total / effective_page_size) if total > 0 else 1
            results = []
            for raw in raw_docs:
                frontend_patent = patent_service.to_frontend_format(raw, relevance=1.0)
                results.append(SearchResultItem(
                    patent=frontend_patent,
                    score=1.0,
                    retrieval_method="database",
                    provenance=SearchProvenance(),
                    match_evidence="Metadata filter match"
                ))

            return SearchResponse(
                query=query_str,
                retrieval_method="database",
                total_found=total,
                total_matching=total,
                page=page,
                page_size=effective_page_size,
                total_pages=total_pages,
                results=results
            )

        # CASE 2: Substantive semantic/keyword text query
        candidates = {}  # pid -> {bm25_rank, vector_rank, bm25_score, vector_score, rrf_score}
        pool_size = max(500, effective_page_size * 20)

        # 1. BM25 Search
        if retrieval_method in ("hybrid", "bm25"):
            bm25_results = bm25_retriever.search(query_str, top_k=pool_size)
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

        # 2. Vector Search
        if retrieval_method in ("hybrid", "vector"):
            vector_results = faiss_retriever.search(query_str, top_k=pool_size)
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
                candidates[pid]["rrf_score"] += 1.2 / (self.k_rrf + rank)

        # If vector/keyword search found no candidates, fallback to DB text search
        if not candidates:
            if mongo_client.connected:
                total, raw_docs = mongo_client.search_patents(
                    query_text=query_str,
                    filters=filter_dict,
                    sort_by=sort_by,
                    page=page,
                    page_size=effective_page_size
                )
            else:
                total, raw_docs = patent_service.search_fallback(
                    query_text=query_str,
                    filters=filter_dict,
                    sort_by=sort_by,
                    page=page,
                    page_size=effective_page_size
                )

            total_pages = math.ceil(total / effective_page_size) if total > 0 else 1
            results = [
                SearchResultItem(
                    patent=patent_service.to_frontend_format(r, relevance=0.8),
                    score=0.8,
                    retrieval_method="text_match",
                    provenance=SearchProvenance(),
                    match_evidence="Text match on patent record"
                )
                for r in raw_docs
            ]

            return SearchResponse(
                query=query_str,
                retrieval_method=retrieval_method,
                total_found=total,
                total_matching=total,
                page=page,
                page_size=effective_page_size,
                total_pages=total_pages,
                results=results
            )

        # 3. Sort candidates by score
        if retrieval_method == "bm25":
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1].get("bm25_score", 0) or 0, reverse=True)
        elif retrieval_method == "vector":
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1].get("vector_score", 0) or 0, reverse=True)
        else:
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1]["rrf_score"], reverse=True)

        candidate_ids = [pid for pid, _ in sorted_candidates]
        records_map = patent_service.get_patents_batch(candidate_ids)

        # 4. Filter candidates
        filtered_candidates = []
        max_rrf = max((data["rrf_score"] for _, data in sorted_candidates), default=1.0) or 1.0

        for pid, data in sorted_candidates:
            raw = records_map.get(pid)
            if not raw:
                continue

            if has_filters:
                # Check field of invention
                techs = filter_dict.get("fields_of_invention") or ([filter_dict.get("field_of_invention")] if filter_dict.get("field_of_invention") else [])
                techs = [t for t in techs if t and str(t).upper() != "ALL"]
                if techs:
                    raw_field = str(raw.get("field_of_invention", "")).upper()
                    if not any(str(t).strip().upper() in raw_field for t in techs):
                        continue

                # Check patent office / IPO location
                office = filter_dict.get("ipo_location")
                if office and str(office).upper() not in ("ALL", "ALL PATENT OFFICES", ""):
                    raw_loc = str(raw.get("ipo_location", "")).upper()
                    if str(office).strip().upper() not in raw_loc:
                        continue

                # Check inventor
                inv = filter_dict.get("inventor")
                if inv and str(inv).strip():
                    inv_term = str(inv).strip().lower()
                    is_def_inv = any(tok in "government of india ipo record" for tok in inv_term.split())
                    raw_inv = str(raw.get("inventor", "") or "").lower()
                    raw_app = str(raw.get("applicant", "") or "").lower()
                    raw_title = str(raw.get("title", "") or "").lower()
                    if not is_def_inv and inv_term not in raw_inv and inv_term not in raw_app and inv_term not in raw_title:
                        continue

                # Check organisation
                org = filter_dict.get("organization")
                if org and str(org).strip():
                    org_term = str(org).strip().lower()
                    is_def_org = any(tok in org_term for tok in ["indian", "patent", "office", "ipo"])
                    raw_org = str(raw.get("organization", "") or raw.get("organisation", "") or "").lower()
                    raw_loc = str(raw.get("ipo_location", "") or "").lower()
                    raw_title = str(raw.get("title", "") or "").lower()
                    if not is_def_org and org_term not in raw_org and org_term not in raw_loc and org_term not in raw_title:
                        continue

                # Check date
                exact_date = filter_dict.get("exact_date")
                priority_date = filter_dict.get("priority_date")
                date_from = filter_dict.get("date_from")
                date_to = filter_dict.get("date_to")

                pub_d = str(raw.get("publication_date", "") or "")
                fil_d = str(raw.get("filing_date", "") or "")

                if exact_date:
                    if pub_d != exact_date and fil_d != exact_date:
                        continue
                elif priority_date:
                    if fil_d != priority_date and pub_d != priority_date:
                        continue
                else:
                    if date_from:
                        if (pub_d and pub_d < date_from) and (fil_d and fil_d < date_from):
                            continue
                    if date_to:
                        if (pub_d and pub_d > date_to) and (fil_d and fil_d > date_to):
                            continue

            filtered_candidates.append((pid, data, raw))

        # Check total count across database if filtered
        if has_filters and mongo_client.connected:
            db_total, _ = mongo_client.search_patents(query_text=query_str, filters=filter_dict, page_size=1)
            total_found = max(len(filtered_candidates), db_total)
        else:
            total_found = len(filtered_candidates)

        total_pages = math.ceil(total_found / effective_page_size) if total_found > 0 else 1

        # Slice for current page
        start_idx = max(0, (page - 1) * effective_page_size)
        end_idx = start_idx + effective_page_size
        page_slice = filtered_candidates[start_idx:end_idx]

        results = []
        for pid, data, raw in page_slice:
            if retrieval_method == "vector" and data["vector_score"] is not None:
                norm_score = max(0.0, min(1.0, float(data["vector_score"])))
            elif retrieval_method == "bm25" and data["bm25_score"] is not None:
                norm_score = min(1.0, float(data["bm25_score"]) / 25.0)
            else:
                norm_score = min(1.0, data["rrf_score"] / max_rrf)

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

        return SearchResponse(
            query=query_str,
            retrieval_method=retrieval_method,
            total_found=total_found,
            total_matching=total_found,
            page=page,
            page_size=effective_page_size,
            total_pages=total_pages,
            results=results
        )

hybrid_retrieval_engine = HybridRetrievalEngine()
