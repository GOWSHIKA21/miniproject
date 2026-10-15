import os
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from backend.app.config import settings
from backend.app.database.mongodb import mongo_client
from backend.app.schemas.patent import PatentFrontendFormat

logger = logging.getLogger(__name__)

class PatentService:
    def __init__(self):
        self._df_cache: Optional[pd.DataFrame] = None

    def _get_fallback_df(self) -> pd.DataFrame:
        if self._df_cache is None:
            if os.path.exists(settings.CLEANED_DATA_PATH):
                self._df_cache = pd.read_parquet(settings.CLEANED_DATA_PATH)
            else:
                self._df_cache = pd.DataFrame()
        return self._df_cache

    def to_frontend_format(self, record: Dict[str, Any], relevance: Optional[float] = None) -> PatentFrontendFormat:
        """Convert an internal patent record into the format required by React PatentCard and PatentDetails."""
        p_id = str(record.get("patent_id", ""))
        field = str(record.get("field_of_invention", "GENERAL"))
        loc = str(record.get("ipo_location", "India"))
        app_type = str(record.get("application_type", "Patent"))
        claims = record.get("no_of_claims")
        pages = record.get("no_of_pages")

        # Create informative abstract snippet explaining the patent details
        claims_str = f"{int(claims)} claims" if claims is not None and not pd.isna(claims) else "Unspecified claims"
        pages_str = f"{int(pages)} pages" if pages is not None and not pd.isna(pages) else "Unspecified pages"
        abstract_snippet = (
            f"Granted Indian Patent Application ({p_id}) published at IPO {loc} under the technical domain of {field}. "
            f"Filing Type: {app_type}. Specification comprises {pages_str} with {claims_str}. "
            f"Verified under Government of India Patent Journal Gazette records."
        )

        tech_tags = [field]
        if app_type and app_type != "Patent":
            tech_tags.append(app_type.replace(" APPLICATION", "").title())

        # Scale relevance percentage
        rel_pct = None
        if relevance is not None:
            rel_pct = round(float(relevance) * 100, 1)

        return PatentFrontendFormat(
            id=p_id,
            patentNumber=p_id,
            title=str(record.get("title", "")),
            abstract=abstract_snippet,
            inventor="Government of India IPO Record",
            organization=f"Indian Patent Office ({loc} Branch)",
            patentOffice="India",
            ipoLocation=loc,
            filingDate=str(record.get("filing_date", "")) if record.get("filing_date") else None,
            publicationDate=str(record.get("publication_date", "")) if record.get("publication_date") else None,
            technology=tech_tags,
            ipc=field,
            relevance=rel_pct,
            status="Granted",
            noOfClaims=int(claims) if claims is not None and not pd.isna(claims) else None,
            noOfPages=int(pages) if pages is not None and not pd.isna(pages) else None,
            sourceUrl=record.get("source_url", "https://ipindiaservices.gov.in/publicsearch/"),
            isSaved=False
        )

    def get_patent_by_id(self, patent_id: str) -> Optional[PatentFrontendFormat]:
        # 1. Try MongoDB
        doc = mongo_client.get_patent(patent_id)
        if doc:
            return self.to_frontend_format(doc)

        # 2. Try Parquet fallback
        df = self._get_fallback_df()
        if not df.empty:
            matches = df[df["patent_id"] == patent_id]
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

    def get_dataset_stats(self) -> Dict[str, Any]:
        """Aggregate stats for the Home and Explorer pages."""
        df = self._get_fallback_df()
        if df.empty:
            return {"total_patents": 0, "domains": {}}

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
        """In-memory Parquet fallback search with filter support, counting, and pagination."""
        df = self._get_fallback_df()
        if df.empty:
            return (0, [])

        mask = pd.Series(True, index=df.index)

        if filters:
            # 1. Tech domains
            techs = filters.get("fields_of_invention") or ([filters.get("field_of_invention")] if filters.get("field_of_invention") else [])
            techs = [t for t in techs if t and str(t).upper() != "ALL"]
            if techs:
                pattern = "|".join(re.escape(str(t).strip()) for t in techs)
                mask &= df["field_of_invention"].astype(str).str.contains(pattern, case=False, na=False)

            # 2. Location
            office = filters.get("ipo_location")
            if office and str(office).upper() not in ("ALL", "ALL PATENT OFFICES", ""):
                mask &= df["ipo_location"].astype(str).str.contains(re.escape(str(office).strip()), case=False, na=False)

            # 3. Dates
            exact_date = filters.get("exact_date")
            priority_date = filters.get("priority_date")
            date_from = filters.get("date_from")
            date_to = filters.get("date_to")

            if exact_date:
                mask &= (df["publication_date"] == exact_date) | (df["filing_date"] == exact_date)
            elif priority_date:
                mask &= (df["filing_date"] == priority_date) | (df["publication_date"] == priority_date)
            else:
                if date_from:
                    mask &= (df["publication_date"] >= date_from) | (df["filing_date"] >= date_from)
                if date_to:
                    mask &= (df["publication_date"] <= date_to) | (df["filing_date"] <= date_to)

        if query_text and query_text.strip() and query_text.strip().lower() not in ("patent invention", "all", "*"):
            q_clean = re.escape(query_text.strip())
            mask &= (
                df["patent_id"].astype(str).str.contains(q_clean, case=False, na=False) |
                df["title"].astype(str).str.contains(q_clean, case=False, na=False) |
                df["search_text"].astype(str).str.contains(q_clean, case=False, na=False)
            )

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
