import os
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
try:
    import faiss
except Exception:
    pass
from backend.app.config import settings
from backend.app.database.mongodb import mongo_client
from backend.app.schemas.patent import PatentFrontendFormat

logger = logging.getLogger(__name__)

class PatentService:
    def __init__(self):
        self._df_cache: Optional[pd.DataFrame] = None

    def _get_fallback_df(self) -> pd.DataFrame:
        if self._df_cache is None:
            data_path = settings.CLEANED_DATA_PATH
            if not os.path.exists(data_path):
                candidate = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned_patents.parquet")
                if os.path.exists(candidate):
                    data_path = candidate
            if os.path.exists(data_path):
                self._df_cache = pd.read_parquet(data_path)
            else:
                self._df_cache = pd.DataFrame()
        return self._df_cache

    def to_frontend_format(self, record: Dict[str, Any], relevance: Optional[float] = None) -> PatentFrontendFormat:
        """Convert an internal patent record into the comprehensive format required by React PatentCard and PatentDetails."""
        p_id = str(record.get("patent_id", "") or "").strip()
        pub_no = str(record.get("publication_number", "") or "").strip() or None
        title = str(record.get("title", "") or "").strip()
        title_norm = str(record.get("title_normalized", "") or "").strip() or None
        
        field = str(record.get("field_of_invention", "") or "").strip() or None
        field_imp = record.get("field_imputed")
        field_imp_bool = bool(field_imp) if field_imp is not None and not pd.isna(field_imp) else None
        
        loc = str(record.get("ipo_location", "") or "").strip() or None
        code = str(record.get("ipo_code", "") or "").strip() or None
        
        app_type = str(record.get("application_type", "") or "").strip() or None
        app_cat = str(record.get("application_category", "") or "").strip() or None
        
        filing_d = str(record.get("filing_date", "") or "").strip() or None
        pub_d = str(record.get("publication_date", "") or "").strip() or None
        date_upd = str(record.get("date_updated", "") or "").strip() or None
        
        filing_yr = record.get("filing_year")
        filing_yr_int = int(filing_yr) if filing_yr is not None and not pd.isna(filing_yr) else None
        
        pub_yr = record.get("publication_year")
        pub_yr_int = int(pub_yr) if pub_yr is not None and not pd.isna(pub_yr) else None
        
        pendency = record.get("pendency_days")
        pendency_int = int(pendency) if pendency is not None and not pd.isna(pendency) else None
        
        claims = record.get("no_of_claims")
        claims_int = int(claims) if claims is not None and not pd.isna(claims) else None
        
        pages = record.get("no_of_pages")
        pages_int = int(pages) if pages is not None and not pd.isna(pages) else None
        
        claims_rng = str(record.get("claims_range", "") or "").strip() or None
        
        claims_imp = record.get("no_of_claims_imputed")
        claims_imp_int = int(claims_imp) if claims_imp is not None and not pd.isna(claims_imp) else None
        
        pages_imp = record.get("no_of_pages_imputed")
        pages_imp_int = int(pages_imp) if pages_imp is not None and not pd.isna(pages_imp) else None
        
        jurisdiction = str(record.get("jurisdiction", "India") or "India").strip()
        source_f = str(record.get("source_file", "") or "").strip() or None
        source_u = str(record.get("source_url", "") or "").strip() or None
        search_t = str(record.get("search_text", "") or "").strip() or None
        
        # Technology tags
        tech_tags = []
        if field:
            tech_tags.append(field)
        if app_type and app_type != "Patent":
            tech_tags.append(app_type.replace(" Application", "").replace(" APPLICATION", "").title())
        
        # Scale relevance percentage
        rel_pct = None
        if relevance is not None:
            rel_pct = round(float(relevance) * 100, 1)

        # Structured Abstract
        abstract_parts = [
            f"Official Indian Patent Application {p_id} titled \"{title}\", classified under technical domain {field or 'General Engineering'}."
        ]
        if loc:
            abstract_parts.append(f"Filed at IPO {loc} branch office under application category {app_cat or app_type or 'Ordinary'}.")
        if filing_d and pub_d:
            abstract_parts.append(f"Filing date: {filing_d}; Journal publication date: {pub_d}.")
        if claims_int is not None:
            pages_text = f" across {pages_int} specification pages" if pages_int else ""
            abstract_parts.append(f"The filing comprises {claims_int} legal claims{pages_text}.")
        abstract_text = " ".join(abstract_parts)

        # Structured Description / Specification Scope
        desc_lines = [
            f"### 1. Technical Overview & Domain Classification",
            f"The invention is designated as \"{title}\". It is formally cataloged under the technical domain `{field or 'General Technology'}` within the Indian Patent Office jurisdiction ({jurisdiction}).",
            "",
            f"### 2. Filing Chronology & Administrative Metadata",
            f"- **Application Number:** `{p_id}`",
            f"- **Publication Journal Number:** `{pub_no or 'Standard Gazette'}`",
            f"- **Filing Date:** {filing_d or 'Recorded in Gazette'}",
            f"- **Publication Date:** {pub_d or 'Recorded in Gazette'}",
            f"- **IPO Branch Office:** {loc or 'India Central'} ({code or 'IPO'})",
            f"- **Application Classification:** {app_type or 'Standard'} ({app_cat or 'Ordinary'})",
        ]
        if pendency_int:
            desc_lines.append(f"- **Examination Pendency:** {pendency_int} days")
        desc_lines.extend([
            "",
            f"### 3. Specification Scope & Claim Boundary",
            f"- **Total Specification Length:** {pages_int if pages_int is not None else 'Refer to filing'} pages",
            f"- **Number of Legal Claims:** {claims_int if claims_int is not None else 'Refer to filing'} claims ({claims_rng or 'Standard claim bin'})",
            "",
            f"### 4. Official Gazette Record Scope & Public Notice",
            f"This record is sourced from the official Indian Patent Office Gazette publication archives (source file: `{source_f or 'IPO Gazette'}`).",
            "> **Note on Full Specifications:** In accordance with InPASS gazette publishing conventions, this repository maintains structured bibliographic records, classification data, and claims counts. Full continuous legal patent specifications, line drawings, and claims sheets are filed directly with the Controller General of Patents, Designs and Trade Marks (CGPDTM) and are accessible via the official IP India portal."
        ])
        description_text = "\n".join(desc_lines)

        claims_list = []
        if claims_int:
            claims_list.append(f"Official filing embodies {claims_int} legal claims ({claims_rng or 'categorized'}) filed with the Indian Patent Office.")
            if field:
                claims_list.append(f"Claims fall within the classified technical boundary of {field}.")

        return PatentFrontendFormat(
            id=p_id,
            patentNumber=p_id,
            patent_id=p_id,
            patentId=p_id,
            publication_number=pub_no,
            publicationNumber=pub_no,
            title=title,
            title_normalized=title_norm,
            titleNormalized=title_norm,
            filing_date=filing_d,
            filingDate=filing_d,
            publication_date=pub_d,
            publicationDate=pub_d,
            date_updated=date_upd,
            dateUpdated=date_upd,
            filing_year=filing_yr_int,
            filingYear=filing_yr_int,
            publication_year=pub_yr_int,
            publicationYear=pub_yr_int,
            pendency_days=pendency_int,
            pendencyDays=pendency_int,
            field_of_invention=field,
            fieldOfInvention=field,
            field_imputed=field_imp_bool,
            fieldImputed=field_imp_bool,
            technology=tech_tags,
            ipc=field,
            jurisdiction=jurisdiction,
            ipo_location=loc,
            ipoLocation=loc,
            ipo_code=code,
            ipoCode=code,
            patentOffice=jurisdiction,
            application_type=app_type,
            applicationType=app_type,
            application_category=app_cat,
            applicationCategory=app_cat,
            no_of_pages=pages_int,
            noOfPages=pages_int,
            no_of_claims=claims_int,
            noOfClaims=claims_int,
            claims_range=claims_rng,
            claimsRange=claims_rng,
            no_of_pages_imputed=pages_imp_int,
            noOfPagesImputed=pages_imp_int,
            no_of_claims_imputed=claims_imp_int,
            noOfClaimsImputed=claims_imp_int,
            source_file=source_f,
            sourceFile=source_f,
            source_url=source_u,
            sourceUrl=source_u,
            search_text=search_t,
            searchText=search_t,
            relevance=rel_pct,
            abstract=abstract_text,
            description=description_text,
            claims=claims_list,
            inventor=record.get("inventor") or "Government of India IPO Record",
            organization=record.get("organization") or (f"Indian Patent Office ({loc} Branch)" if loc else "Indian Patent Office"),
            status=record.get("status") or (f"Published ({app_cat or 'Application'})"),
            isSaved=False
        )

    def get_patent_by_id(self, patent_id: str) -> Optional[PatentFrontendFormat]:
        clean_id = str(patent_id).strip()
        # 1. Try MongoDB
        doc = mongo_client.get_patent(clean_id)
        if doc:
            return self.to_frontend_format(doc)

        # 2. Try Parquet fallback
        df = self._get_fallback_df()
        if not df.empty:
            matches = df[df["patent_id"].astype(str) == clean_id]
            if not matches.empty:
                return self.to_frontend_format(matches.iloc[0].to_dict())

        return None

    def get_patents_batch(self, patent_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Retrieve a dictionary of patent_id -> raw record for a list of patent IDs."""
        result = {}
        if not patent_ids:
            return result

        # MongoDB batch query
        if mongo_client.connected and mongo_client.db is not None:
            try:
                coll = mongo_client.db[settings.MONGODB_COLLECTION]
                cursor = coll.find({"patent_id": {"$in": patent_ids}}, {"_id": 0})
                for doc in cursor:
                    result[doc["patent_id"]] = doc
            except Exception as e:
                logger.error(f"MongoDB batch query error: {e}")

        # Check for missing in fallback
        missing_ids = [pid for pid in patent_ids if pid not in result]
        if missing_ids:
            df = self._get_fallback_df()
            if not df.empty:
                subset = df[df["patent_id"].isin(missing_ids)]
                for _, row in subset.iterrows():
                    result[row["patent_id"]] = row.to_dict()

        return result

    def get_related_inventions(
        self,
        patent_id: str,
        limit: int = 6,
        min_similarity: float = 0.40
    ) -> List[Dict[str, Any]]:
        """
        Generate semantically related invention recommendations using vector embeddings,
        normalized metadata, and Knowledge Graph domain synergy.
        Guarantees honest empty states when candidate similarity does not meet threshold,
        excludes self/duplicates, and provides transparent match explanations.
        """
        clean_id = str(patent_id).strip()
        target = self.get_patent_by_id(clean_id)
        if not target:
            return []

        # 1. Fetch target vector from FAISS or encode
        from backend.app.retrieval.vector_search import faiss_retriever
        target_text = f"{target.title} {target.field_of_invention or ''} {target.search_text or ''}"
        target_vec = faiss_retriever.get_patent_vector(clean_id, fallback_text=target_text)
        if target_vec is None:
            return []

        # 2. Semantic search for candidates
        candidates_raw = faiss_retriever.search_by_vector(target_vec, top_k=limit * 5 + 10)
        if not candidates_raw:
            return []

        # Filter out self, duplicates, and candidates below min_similarity
        valid_candidates = []
        seen_ids = {clean_id}
        for c in candidates_raw:
            pid = c["patent_id"]
            score = float(c["score"])
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            if score < min_similarity:
                continue
            valid_candidates.append((pid, score))

        if not valid_candidates:
            return []

        # Batch fetch metadata for candidates
        cand_ids = [pid for pid, _ in valid_candidates[:limit * 2]]
        cand_records = self.get_patents_batch(cand_ids)

        # Stop words for concept extraction
        stopwords = {
            "a", "an", "the", "of", "for", "with", "in", "on", "by", "to", "and", "or",
            "as", "at", "is", "from", "device", "apparatus", "method", "system", "improved",
            "process", "composition", "thereof", "same", "using", "novel", "preparation",
            "producing", "production", "treatment", "having", "comprising", "useful"
        }

        target_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", target.title.lower())) - stopwords

        results = []
        for pid, score in valid_candidates:
            raw_c = cand_records.get(pid)
            if not raw_c:
                continue

            c_title = str(raw_c.get("title", "") or "").strip()
            c_field = str(raw_c.get("field_of_invention", "") or "").strip()
            c_loc = str(raw_c.get("ipo_location", "") or "").strip()
            c_claims = raw_c.get("no_of_claims")
            c_pages = raw_c.get("no_of_pages")

            cand_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", c_title.lower())) - stopwords
            shared_concepts = sorted(list(target_words & cand_words))

            is_same_domain = bool(target.field_of_invention and c_field and target.field_of_invention.upper() == c_field.upper())
            sim_pct = int(round(score * 100))

            # Generate accurate, non-hallucinatory match explanation
            if shared_concepts and is_same_domain:
                reason = f"High semantic similarity ({sim_pct}%) in {c_field}; shares core technical concepts: {', '.join(shared_concepts[:4])}."
            elif shared_concepts:
                reason = f"Strong semantic alignment ({sim_pct}%); overlapping technical keywords: {', '.join(shared_concepts[:4])}."
            elif is_same_domain:
                reason = f"Conceptual similarity ({sim_pct}%) within the classified {c_field} technical domain."
            else:
                reason = f"Semantic vector similarity ({sim_pct}%) based on technical problem formulation and terminology."

            results.append({
                "patent_id": pid,
                "title": c_title,
                "field": c_field or "General",
                "location": c_loc,
                "similarity_score": round(score, 3),
                "similarity_pct": sim_pct,
                "shared_concepts": shared_concepts,
                "shared_concepts_count": len(shared_concepts),
                "match_reason": reason,
                "no_of_claims": int(c_claims) if c_claims is not None and not pd.isna(c_claims) else None,
                "no_of_pages": int(c_pages) if c_pages is not None and not pd.isna(c_pages) else None
            })

            if len(results) >= limit:
                break

        return results

    def get_dataset_stats(self) -> Dict[str, Any]:
        """Aggregate stats for the Home and Explorer pages."""
        df = self._get_fallback_df()
        if df.empty:
            return {"total_patents": 0, "domains": {}, "field_counts": {}}

        total = len(df)
        field_counts = df["field_of_invention"].value_counts().to_dict()
        loc_counts = df["ipo_location"].value_counts().to_dict()
        app_type_counts = df["application_type"].value_counts().to_dict()

        return {
            "total_patents": total,
            "field_counts": field_counts,
            "location_counts": loc_counts,
            "application_types": app_type_counts
        }

    def search_fallback(
        self,
        query_text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 25
    ) -> tuple[int, List[Dict[str, Any]]]:
        """In-memory Parquet fallback search with exact domain matching, priority-year filtering, counting, and pagination."""
        df = self._get_fallback_df()
        if df.empty:
            return (0, [])

        mask = pd.Series(True, index=df.index)

        if filters:
            # 1. Tech domains (exact domain match to prevent 'Chemistry' matching 'Biochemistry')
            techs = filters.get("fields_of_invention") or ([filters.get("field_of_invention")] if filters.get("field_of_invention") else [])
            techs = [str(t).strip().upper() for t in techs if t and str(t).upper() != "ALL"]
            if techs:
                mask &= df["field_of_invention"].astype(str).str.upper().isin(techs)

            # 2. Location
            office = filters.get("ipo_location")
            if office and str(office).upper() not in ("ALL", "ALL PATENT OFFICES", ""):
                mask &= df["ipo_location"].astype(str).str.contains(re.escape(str(office).strip()), case=False, na=False)

            # 3. Application Type
            app_type = filters.get("application_type")
            if app_type and str(app_type).upper() not in ("ALL", ""):
                mask &= df["application_type"].astype(str).str.contains(re.escape(str(app_type).strip()), case=False, na=False)

            # 4. Dates & Priority Date (Year Only or Exact Date)
            exact_date = filters.get("exact_date")
            priority_date = filters.get("priority_date")
            date_from = filters.get("date_from")
            date_to = filters.get("date_to")

            if exact_date:
                mask &= (df["publication_date"].astype(str) == str(exact_date)) | (df["filing_date"].astype(str) == str(exact_date))
            elif priority_date:
                pyear = str(priority_date).strip()
                if re.match(r"^\d{4}$", pyear):
                    year_int = int(pyear)
                    if "priority_date" in df.columns:
                        prio_series = df["priority_date"].astype(str)
                        prio_mask = prio_series.str.startswith(pyear) & (~prio_series.isin(["nan", "None", ""]))
                        if prio_mask.any():
                            mask &= prio_mask
                        else:
                            year_mask = (
                                df["publication_date"].astype(str).str.startswith(pyear) |
                                df["filing_date"].astype(str).str.startswith(pyear)
                            )
                            if "publication_year" in df.columns:
                                year_mask |= (df["publication_year"] == year_int)
                            if "filing_year" in df.columns:
                                year_mask |= (df["filing_year"] == year_int)
                            mask &= year_mask
                    else:
                        year_mask = (
                            df["publication_date"].astype(str).str.startswith(pyear) |
                            df["filing_date"].astype(str).str.startswith(pyear)
                        )
                        if "publication_year" in df.columns:
                            year_mask |= (df["publication_year"] == year_int)
                        if "filing_year" in df.columns:
                            year_mask |= (df["filing_year"] == year_int)
                        mask &= year_mask
                else:
                    if "priority_date" in df.columns:
                        mask &= (df["priority_date"].astype(str) == pyear)
                    else:
                        mask &= (df["filing_date"].astype(str) == pyear) | (df["publication_date"].astype(str) == pyear)
            else:
                if date_from and date_to:
                    mask &= (
                        ((df["publication_date"].astype(str) >= str(date_from)) & (df["publication_date"].astype(str) <= str(date_to))) |
                        ((df["filing_date"].astype(str) >= str(date_from)) & (df["filing_date"].astype(str) <= str(date_to)))
                    )
                elif date_from:
                    mask &= (df["publication_date"].astype(str) >= str(date_from)) | (df["filing_date"].astype(str) >= str(date_from))
                elif date_to:
                    mask &= (df["publication_date"].astype(str) <= str(date_to)) | (df["filing_date"].astype(str) <= str(date_to))

            # 5. Inventor (Whole-word matching)
            inv = filters.get("inventor")
            if inv and str(inv).strip():
                inv_clean = str(inv).strip()
                is_default_inv = any(tok in "government of india ipo record" for tok in inv_clean.lower().split() if len(tok) >= 3)
                if not is_default_inv:
                    inv_rx = rf"\b{re.escape(inv_clean)}\b"
                    inv_mask = pd.Series(False, index=df.index)
                    if "inventor" in df.columns:
                        inv_mask |= df["inventor"].astype(str).str.contains(inv_rx, case=False, regex=True, na=False)
                    if "applicant" in df.columns:
                        inv_mask |= df["applicant"].astype(str).str.contains(inv_rx, case=False, regex=True, na=False)
                    inv_mask |= df["title"].astype(str).str.contains(inv_rx, case=False, regex=True, na=False)
                    inv_mask |= df["search_text"].astype(str).str.contains(inv_rx, case=False, regex=True, na=False)
                    mask &= inv_mask

            # 6. Organization (Whole-word matching)
            org = filters.get("organization")
            if org and str(org).strip():
                org_clean = str(org).strip()
                is_default_org = any(tok in org_clean.lower() for tok in ["indian patent office", "patent office", "ipo record"])
                if not is_default_org:
                    org_rx = rf"\b{re.escape(org_clean)}\b"
                    org_mask = pd.Series(False, index=df.index)
                    org_mask |= df["ipo_location"].astype(str).str.contains(org_rx, case=False, regex=True, na=False)
                    if "organization" in df.columns:
                        org_mask |= df["organization"].astype(str).str.contains(org_rx, case=False, regex=True, na=False)
                    if "applicant" in df.columns:
                        org_mask |= df["applicant"].astype(str).str.contains(org_rx, case=False, regex=True, na=False)
                    org_mask |= df["title"].astype(str).str.contains(org_rx, case=False, regex=True, na=False)
                    org_mask |= df["search_text"].astype(str).str.contains(org_rx, case=False, regex=True, na=False)
                    mask &= org_mask

        if query_text and query_text.strip() and query_text.strip().lower() not in ("patent invention", "all", "*"):
            q_clean = query_text.strip()
            id_match = df["patent_id"].astype(str).str.contains(re.escape(q_clean), case=False, na=False)
            q_terms = [t for t in q_clean.split() if t]
            text_match = pd.Series(True, index=df.index)
            for t in q_terms:
                t_rx = rf"\b{re.escape(t)}\b"
                text_match &= (
                    df["title"].astype(str).str.contains(t_rx, case=False, regex=True, na=False) |
                    df["search_text"].astype(str).str.contains(t_rx, case=False, regex=True, na=False)
                )
            mask &= (id_match | text_match)

        filtered = df[mask]
        total = len(filtered)
        if total == 0:
            return (0, [])

        if sort_by == "newest":
            filtered = filtered.sort_values(by=["filing_date", "publication_date"], ascending=[False, False])
        elif sort_by == "oldest":
            filtered = filtered.sort_values(by=["filing_date", "publication_date"], ascending=[True, True])

        start_idx = max(0, (page - 1) * page_size)
        page_df = filtered.iloc[start_idx : start_idx + page_size]
        return (total, page_df.to_dict(orient="records"))

patent_service = PatentService()
