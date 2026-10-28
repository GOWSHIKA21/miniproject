import math
import logging
import re
from typing import List, Dict, Any, Optional

from backend.app.schemas.search import (
    SearchFilters,
    SearchResultItem,
    SearchProvenance,
    SearchResponse
)
from backend.app.retrieval.keyword_search import bm25_retriever
from backend.app.retrieval.vector_search import faiss_retriever
from backend.app.services.patent_service import patent_service
from backend.app.database.mongodb import mongo_client
from backend.app.retrieval.query_expander import (
    clean_nl_query,
    detect_exact_identifier,
    get_expanded_search_query
)

logger = logging.getLogger(__name__)


class HybridRetrievalEngine:
    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf

    def _filters_to_dict(self, filters: Optional[SearchFilters]) -> Dict[str, Any]:
        if not filters:
            return {}
        d = {}
        if filters.field_of_invention:
            d["field_of_invention"] = filters.field_of_invention
        if filters.fields_of_invention:
            d["fields_of_invention"] = filters.fields_of_invention
        if filters.ipo_location:
            d["ipo_location"] = filters.ipo_location
        if filters.inventor:
            d["inventor"] = filters.inventor
        if filters.organization:
            d["organization"] = filters.organization
        if filters.date_from:
            d["date_from"] = filters.date_from
        if filters.date_to:
            d["date_to"] = filters.date_to
        if filters.exact_date:
            d["exact_date"] = filters.exact_date
        if filters.priority_date:
            d["priority_date"] = filters.priority_date
        if filters.application_type:
            d["application_type"] = filters.application_type
        return d

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

        # Check for exact patent ID or publication number match
        exact_id_info = detect_exact_identifier(query_str)
        exact_match_patent = None
        if exact_id_info:
            id_type, id_val = exact_id_info
            if id_type == "patent_id":
                exact_p = patent_service.get_patent_by_id(id_val)
                if exact_p:
                    exact_match_patent = exact_p
            elif id_type == "publication_number":
                # Look up in DB by publication number
                df = patent_service._get_fallback_df()
                if not df.empty and "publication_number" in df.columns:
                    pub_matches = df[df["publication_number"].astype(str).str.strip() == id_val]
                    if not pub_matches.empty:
                        exact_p = patent_service.to_frontend_format(pub_matches.iloc[0].to_dict())
                        exact_match_patent = exact_p

        cleaned_core = clean_nl_query(query_str)
        expanded_query = get_expanded_search_query(query_str)

        # 1. BM25 Search (search expanded query for domain synonym recall)
        if retrieval_method in ("hybrid", "bm25"):
            bm25_results = bm25_retriever.search(expanded_query, top_k=pool_size)
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

        # 2. Vector Search (run on core query)
        if retrieval_method in ("hybrid", "vector"):
            vector_results = faiss_retriever.search(cleaned_core, top_k=pool_size)
            for item in vector_results:
                pid = item["patent_id"]
                rank = item["rank"]
                v_score = float(item["score"])
                # Discard noise below calibrated baseline (0.28)
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

        # Promote exact identifier match to Rank #1
        if exact_match_patent:
            eid = exact_match_patent.patent_id or exact_match_patent.id
            candidates[eid] = {
                "bm25_rank": 1,
                "bm25_score": 99.0,
                "vector_rank": 1,
                "vector_score": 1.0,
                "rrf_score": 999.0
            }

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

        # Batch fetch patent records for candidate metadata and title boosting
        candidate_pids = list(candidates.keys())
        records_map = patent_service.get_patents_batch(candidate_pids)

        # Exact title and phrase match boost
        q_norm = query_str.lower().strip()
        for pid, data in candidates.items():
            raw = records_map.get(pid)
            if raw:
                raw_title = str(raw.get("title", "") or "").lower().strip()
                if q_norm == raw_title:
                    data["rrf_score"] += 10.0
                elif len(q_norm) > 8 and q_norm in raw_title:
                    data["rrf_score"] += 3.0

        # 3. Sort candidates by RRF score
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        )

        # Normalize score baseline
        max_rrf = sorted_candidates[0][1]["rrf_score"] if sorted_candidates else 1.0

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

                # Check inventor (Whole-word matching)
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

                # Check organisation
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
            if data["rrf_score"] >= 900.0:
                norm_score = 1.0
                match_evidence = "Exact patent identifier match"
            elif retrieval_method == "vector" and data["vector_score"] is not None:
                norm_score = max(0.0, min(1.0, float(data["vector_score"])))
                match_evidence = f"Semantic vector match (Rank #{data['vector_rank']})"
            elif retrieval_method == "bm25" and data["bm25_score"] is not None:
                norm_score = min(1.0, float(data["bm25_score"]) / 25.0)
                match_evidence = f"Keyword match (Rank #{data['bm25_rank']})"
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
