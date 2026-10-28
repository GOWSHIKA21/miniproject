import re
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
            num_bm25 = len(bm25_results) if retrieval_method in ("hybrid", "bm25") else 0
            for item in vector_results:
                pid = item["patent_id"]
                rank = item["rank"]
                v_score = float(item["score"])
                # Discard ambient vector noise (< 0.38) when keyword search returned 0 hits
                if num_bm25 == 0 and v_score < 0.38:
                    continue
                if v_score < 0.28:
                    continue
                if pid not in candidates:
                    candidates[pid] = {
                        "bm25_rank": None,
                        "bm25_score": None,
                        "vector_rank": rank,
                        "vector_score": v_score,
                        "rrf_score": 0.0
                    }
                else:
                    candidates[pid]["vector_rank"] = rank
                    candidates[pid]["vector_score"] = v_score
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
            results = []
            for raw in raw_docs:
                frontend_patent = patent_service.to_frontend_format(raw, relevance=0.85)
                results.append(SearchResultItem(
                    patent=frontend_patent,
                    score=0.85,
                    retrieval_method="fallback_text",
                    provenance=SearchProvenance(),
                    match_evidence="Text and metadata match"
                ))

            return SearchResponse(
                query=query_str,
                retrieval_method="fallback_text",
                total_found=total,
                total_matching=total,
                page=page,
                page_size=effective_page_size,
                total_pages=total_pages,
                results=results
            )

        # 3. Sort candidates by RRF score
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        )

        # Normalize score baseline
        max_rrf = sorted_candidates[0][1]["rrf_score"] if sorted_candidates else 1.0

        # Retrieve raw patent records in batch for candidate filtering
        candidate_pids = [pid for pid, _ in sorted_candidates]
        records_map = patent_service.get_patents_batch(candidate_pids)

        # 4. Filter candidates
        filtered_candidates = []
        for pid, data in sorted_candidates:
            raw = records_map.get(pid)
            if not raw:
                continue

            if has_filters:
                # Check field of invention (exact domain match)
                techs = filter_dict.get("fields_of_invention") or ([filter_dict.get("field_of_invention")] if filter_dict.get("field_of_invention") else [])
                techs = [t for t in techs if t and str(t).upper() != "ALL"]
                if techs:
                    raw_field = str(raw.get("field_of_invention", "")).strip().upper()
                    tech_set = {str(t).strip().upper() for t in techs}
                    if raw_field not in tech_set:
                        continue

                # Check patent office / IPO location
                office = filter_dict.get("ipo_location")
                if office and str(office).upper() not in ("ALL", "ALL PATENT OFFICES", ""):
                    raw_loc = str(raw.get("ipo_location", "")).upper()
                    if str(office).strip().upper() not in raw_loc:
                        continue

                # Check inventor (Whole-word matching to avoid false positives like 'tata' in 'rotatable')
                inv = filter_dict.get("inventor")
                if inv and str(inv).strip():
                    inv_term = str(inv).strip()
                    is_def_inv = any(tok in "government of india ipo record" for tok in inv_term.lower().split() if len(tok) >= 3)
                    if not is_def_inv:
                        inv_rx = re.compile(rf"\b{re.escape(inv_term)}\b", re.IGNORECASE)
                        raw_inv = str(raw.get("inventor", "") or "")
                        raw_app = str(raw.get("applicant", "") or "")
                        raw_title = str(raw.get("title", "") or "")
                        raw_st = str(raw.get("search_text", "") or "")
                        has_inv = (
                            bool(inv_rx.search(raw_inv)) or
                            bool(inv_rx.search(raw_app)) or
                            bool(inv_rx.search(raw_title)) or
                            bool(inv_rx.search(raw_st))
                        )
                        if not has_inv:
                            continue

                # Check organisation (Whole-word matching across org, app, ipo_location, title, and search_text)
                org = filter_dict.get("organization")
                if org and str(org).strip():
                    org_term = str(org).strip()
                    is_def_org = any(tok in org_term.lower() for tok in ["indian patent office", "patent office", "ipo record"])
                    if not is_def_org:
                        org_rx = re.compile(rf"\b{re.escape(org_term)}\b", re.IGNORECASE)
                        raw_org = str(raw.get("organization", "") or raw.get("organisation", "") or "")
                        raw_app = str(raw.get("applicant", "") or "")
                        raw_loc = str(raw.get("ipo_location", "") or "")
                        raw_title = str(raw.get("title", "") or "")
                        raw_st = str(raw.get("search_text", "") or "")
                        has_org = (
                            bool(org_rx.search(raw_org)) or
                            bool(org_rx.search(raw_app)) or
                            bool(org_rx.search(raw_loc)) or
                            bool(org_rx.search(raw_title)) or
                            bool(org_rx.search(raw_st))
                        )
                        if not has_org:
                            continue

                # Check date & priority date
                exact_date = filter_dict.get("exact_date")
                priority_date = filter_dict.get("priority_date")
                date_from = filter_dict.get("date_from")
                date_to = filter_dict.get("date_to")

                pub_d = str(raw.get("publication_date", "") or "")
                fil_d = str(raw.get("filing_date", "") or "")

                if exact_date:
                    if pub_d != str(exact_date) and fil_d != str(exact_date):
                        continue
                elif priority_date:
                    pyear = str(priority_date).strip()
                    raw_prio = str(raw.get("priority_date", "") or "").strip()
                    raw_prio_yr = raw.get("priority_year")
                    if re.match(r"^\d{4}$", pyear):
                        year_int = int(pyear)
                        matched = False
                        if raw_prio and raw_prio.startswith(pyear) and raw_prio not in ("nan", "None", ""):
                            matched = True
                        elif raw_prio_yr == year_int:
                            matched = True
                        elif pub_d.startswith(pyear) or fil_d.startswith(pyear):
                            matched = True
                        elif raw.get("publication_year") == year_int or raw.get("filing_year") == year_int:
                            matched = True
                        if not matched:
                            continue
                    else:
                        if fil_d != pyear and pub_d != pyear and raw_prio != pyear:
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
        if has_filters:
            if mongo_client.connected:
                db_total, _ = mongo_client.search_patents(query_text=query_str, filters=filter_dict, page_size=1)
                total_found = max(len(filtered_candidates), db_total)
            else:
                db_total, _ = patent_service.search_fallback(query_text=query_str, filters=filter_dict, page_size=1)
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
