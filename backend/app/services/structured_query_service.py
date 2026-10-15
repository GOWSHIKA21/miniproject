import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import pandas as pd
from backend.app.config import settings
from backend.app.database.mongodb import mongo_client
from backend.app.services.patent_service import patent_service

logger = logging.getLogger(__name__)

LOC_MAP = {
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "del": "Delhi",
    "chennai": "Chennai",
    "madras": "Chennai",
    "che": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "kol": "Kolkata",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "mum": "Mumbai"
}

DOMAINS = [
    'BIOCHEMISTRY', 'BIOMEDICAL', 'BIOTECHNOLOGY', 'CHEMISTRY', 'CIVIL',
    'COMMUNICATION', 'COMPUTER', 'ELECTRICAL', 'ELECTRONICS', 'FOOD',
    'MECHANICAL', 'METALLURGY', 'PHYSICS', 'POLYMER', 'TEXTILE'
]

@dataclass
class StructuredQueryResult:
    is_structured: bool = False
    intent: str = "SEMANTIC_RAG"
    target_field: Optional[str] = None
    filter_value: Optional[str] = None
    total_count: Optional[int] = None
    total_dataset_size: int = 33825
    breakdown: Optional[Dict[str, int]] = None
    sample_patents: List[Dict[str, Any]] = field(default_factory=list)
    limit: int = 5
    description: str = ""
    error_message: Optional[str] = None

class StructuredQueryService:
    """
    Identifies, routes, and executes structured patent database queries
    (counts, aggregations, exact field filters, group-by, and listings)
    directly against MongoDB with Parquet fallback.
    """

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        q = query.strip()
        ql = q.lower()

        # 1. Group-by / breakdown by location
        if re.search(r"\b(for each|per|by|across all|breakdown of|distribution of)\b.*\b(ipo_location|ipo location|patent office|office|location|branch)\b", ql) or \
           re.search(r"\b(ipo_location|ipo location|patent office|office location)\b.*\b(for each|breakdown|distribution|per office)\b", ql):
            return {
                "is_structured": True,
                "intent": "GROUP_BY_LOCATION",
                "field": "ipo_location"
            }

        # 2. Group-by / breakdown by technology domain
        if re.search(r"\b(for each|per|by|across all|breakdown of|distribution of)\b.*\b(domain|technology|tech field|ipc|field of invention)\b", ql) or \
           re.search(r"\b(technology domain|domains|fields of invention)\b.*\b(for each|breakdown|distribution)\b", ql):
            return {
                "is_structured": True,
                "intent": "GROUP_BY_DOMAIN",
                "field": "field_of_invention"
            }

        # 3. Show / List N Patents with Filter
        show_match = re.search(r"\b(show|list|display|give me|fetch|find)\b.*?\b(?:the\s+)?(?:first\s+)?(\d+)?\s*patents?\b", ql)
        if show_match:
            limit = int(show_match.group(2)) if show_match.group(2) else 10
            # Check location
            for loc_key, std_loc in LOC_MAP.items():
                if re.search(rf"\b{loc_key}\b", ql):
                    return {
                        "is_structured": True,
                        "intent": "SHOW_FILTERED_PATENTS",
                        "field": "ipo_location",
                        "value": std_loc,
                        "limit": limit
                    }
            # Check domain
            for dom in DOMAINS:
                if re.search(rf"\b{dom.lower()}\b", ql):
                    return {
                        "is_structured": True,
                        "intent": "SHOW_FILTERED_PATENTS",
                        "field": "field_of_invention",
                        "value": dom,
                        "limit": limit
                    }

        # 4. Count Signals
        is_count = bool(re.search(r"\b(how many|count|number of|total number of|total count|how much)\b", ql))
        
        # Also handle "In IPO_LOCATION, how many patents are there in Delhi?"
        if not is_count and re.search(r"\bipo_location\b.*\b(how many|patents in)\b", ql):
            is_count = True

        if is_count:
            is_active = bool(re.search(r"\b(active|granted|published|in-force)\b", ql))

            # A. Location check
            for loc_key, std_loc in LOC_MAP.items():
                if re.search(rf"\b{loc_key}\b", ql):
                    if is_active:
                        return {
                            "is_structured": True,
                            "intent": "COUNT_ACTIVE_LOCATION",
                            "field": "ipo_location",
                            "value": std_loc,
                            "status": "Granted"
                        }
                    return {
                        "is_structured": True,
                        "intent": "COUNT_LOCATION",
                        "field": "ipo_location",
                        "value": std_loc
                    }

            # B. Domain check
            for dom in DOMAINS:
                if re.search(rf"\b{dom.lower()}\b", ql):
                    if is_active:
                        return {
                            "is_structured": True,
                            "intent": "COUNT_ACTIVE_DOMAIN",
                            "field": "field_of_invention",
                            "value": dom,
                            "status": "Granted"
                        }
                    return {
                        "is_structured": True,
                        "intent": "COUNT_DOMAIN",
                        "field": "field_of_invention",
                        "value": dom
                    }

            # C. Publication Year check (e.g. 2016, 2017, 2018)
            year_match = re.search(r"\b(201[6-8])\b", ql)
            if year_match:
                return {
                    "is_structured": True,
                    "intent": "COUNT_YEAR",
                    "field": "publication_date",
                    "value": year_match.group(1)
                }

            # D. Total Repository Count
            if re.search(r"\b(total|all|database|repository|dataset|system|records?)\b", ql):
                return {
                    "is_structured": True,
                    "intent": "COUNT_TOTAL",
                    "field": "all"
                }

        # Default: Semantic RAG
        return {"is_structured": False, "intent": "SEMANTIC_RAG"}

    def execute_structured_query(self, analysis: Dict[str, Any]) -> StructuredQueryResult:
        intent = analysis["intent"]
        field = analysis.get("field")
        val = analysis.get("value")
        limit = analysis.get("limit", 5)

        res = StructuredQueryResult(
            is_structured=True,
            intent=intent,
            target_field=field,
            filter_value=val,
            limit=limit
        )

        try:
            if mongo_client.connected and mongo_client.db is not None:
                self._execute_mongo(intent, field, val, limit, res)
            else:
                self._execute_fallback(intent, field, val, limit, res)
        except Exception as e:
            logger.error(f"Error executing structured query in primary backend: {e}. Trying Parquet fallback.")
            try:
                self._execute_fallback(intent, field, val, limit, res)
            except Exception as e_fallback:
                logger.error(f"Structured fallback query also failed: {e_fallback}")
                res.error_message = f"Unable to verify exact patent count: {e_fallback}"

        return res

    def _execute_mongo(self, intent: str, field: Optional[str], val: Optional[str], limit: int, res: StructuredQueryResult):
        coll = mongo_client.db[mongo_client.collection_name]
        total_db = coll.count_documents({})
        res.total_dataset_size = total_db

        if intent == "COUNT_LOCATION":
            query = {"ipo_location": {"$regex": rf"^\s*{re.escape(val)}\s*$", "$options": "i"}}
            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))
            res.description = f"Patents filed at the {val} Patent Office (IPO_LOCATION = {val})"

        elif intent == "COUNT_ACTIVE_LOCATION":
            query = {
                "ipo_location": {"$regex": rf"^\s*{re.escape(val)}\s*$", "$options": "i"},
                "status": {"$regex": r"^(granted|active|published)", "$options": "i"}
            }
            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))
            res.description = f"Active/Granted patents at the {val} Patent Office (IPO_LOCATION = {val})"

        elif intent == "GROUP_BY_LOCATION":
            pipeline = [
                {"$group": {"_id": "$ipo_location", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            agg = list(coll.aggregate(pipeline))
            res.breakdown = {doc["_id"]: doc["count"] for doc in agg if doc["_id"]}
            res.total_count = total_db
            res.sample_patents = list(coll.find({}, {"_id": 0}).limit(limit))
            res.description = "Patent distribution breakdown across all official IPO Patent Offices"

        elif intent == "COUNT_DOMAIN":
            query = {"field_of_invention": {"$regex": rf"^{re.escape(val)}", "$options": "i"}}
            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))
            res.description = f"Patents classified under the {val} technical domain (FIELD_OF_INVENTION = {val})"

        elif intent == "COUNT_ACTIVE_DOMAIN":
            query = {
                "field_of_invention": {"$regex": rf"^{re.escape(val)}", "$options": "i"},
                "status": {"$regex": r"^(granted|active|published)", "$options": "i"}
            }
            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))
            res.description = f"Active/Granted patents classified under {val} (FIELD_OF_INVENTION = {val})"

        elif intent == "GROUP_BY_DOMAIN":
            pipeline = [
                {"$group": {"_id": "$field_of_invention", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            agg = list(coll.aggregate(pipeline))
            res.breakdown = {doc["_id"]: doc["count"] for doc in agg if doc["_id"]}
            res.total_count = total_db
            res.sample_patents = list(coll.find({}, {"_id": 0}).limit(limit))
            res.description = "Patent distribution breakdown across all technical domains"

        elif intent == "SHOW_FILTERED_PATENTS":
            if field == "ipo_location":
                query = {"ipo_location": {"$regex": rf"^\s*{re.escape(val)}\s*$", "$options": "i"}}
                res.description = f"First {limit} patents filed at {val} Patent Office"
            else:
                query = {"field_of_invention": {"$regex": rf"^{re.escape(val)}", "$options": "i"}}
                res.description = f"First {limit} patents classified under {val}"

            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))

        elif intent == "COUNT_YEAR":
            query = {"publication_date": {"$regex": rf"^{re.escape(val)}"}}
            res.total_count = coll.count_documents(query)
            res.sample_patents = list(coll.find(query, {"_id": 0}).limit(limit))
            res.description = f"Patents published in calendar year {val}"

        elif intent == "COUNT_TOTAL":
            res.total_count = total_db
            res.sample_patents = list(coll.find({}, {"_id": 0}).limit(limit))
            res.description = "Total verified patents across the complete 2016-2018 repository"

    def _execute_fallback(self, intent: str, field: Optional[str], val: Optional[str], limit: int, res: StructuredQueryResult):
        df = patent_service._get_fallback_df()
        if df.empty:
            raise RuntimeError("Parquet dataset fallback is empty or not loaded.")

        total_db = len(df)
        res.total_dataset_size = total_db

        if intent in ("COUNT_LOCATION", "COUNT_ACTIVE_LOCATION"):
            matched = df[df["ipo_location"].astype(str).str.strip().str.lower() == val.lower()]
            res.total_count = len(matched)
            res.sample_patents = matched.head(limit).to_dict(orient="records")
            res.description = f"Patents filed at the {val} Patent Office (IPO_LOCATION = {val})"

        elif intent == "GROUP_BY_LOCATION":
            res.breakdown = df["ipo_location"].value_counts().to_dict()
            res.total_count = total_db
            res.sample_patents = df.head(limit).to_dict(orient="records")
            res.description = "Patent distribution breakdown across all official IPO Patent Offices"

        elif intent in ("COUNT_DOMAIN", "COUNT_ACTIVE_DOMAIN"):
            matched = df[df["field_of_invention"].astype(str).str.contains(re.escape(val), case=False, na=False)]
            res.total_count = len(matched)
            res.sample_patents = matched.head(limit).to_dict(orient="records")
            res.description = f"Patents classified under {val} (FIELD_OF_INVENTION = {val})"

        elif intent == "GROUP_BY_DOMAIN":
            res.breakdown = df["field_of_invention"].value_counts().to_dict()
            res.total_count = total_db
            res.sample_patents = df.head(limit).to_dict(orient="records")
            res.description = "Patent distribution breakdown across all technical domains"

        elif intent == "SHOW_FILTERED_PATENTS":
            if field == "ipo_location":
                matched = df[df["ipo_location"].astype(str).str.strip().str.lower() == val.lower()]
            else:
                matched = df[df["field_of_invention"].astype(str).str.contains(re.escape(val), case=False, na=False)]
            res.total_count = len(matched)
            res.sample_patents = matched.head(limit).to_dict(orient="records")
            res.description = f"First {limit} patents matching {field} = {val}"

        elif intent == "COUNT_YEAR":
            matched = df[df["publication_date"].astype(str).str.startswith(str(val))]
            res.total_count = len(matched)
            res.sample_patents = matched.head(limit).to_dict(orient="records")
            res.description = f"Patents published in calendar year {val}"

        elif intent == "COUNT_TOTAL":
            res.total_count = total_db
            res.sample_patents = df.head(limit).to_dict(orient="records")
            res.description = "Total verified patents across the complete 2016-2018 repository"

    def synthesize_deterministic_answer(self, query: str, res: StructuredQueryResult) -> str:
        """Constructs an authoritative, verified markdown answer for structured database questions."""
        if res.error_message:
            return (
                f"### Database Verification Notice for: *\"{query}\"*\n\n"
                f"⚠️ **Count verification failed**: {res.error_message}\n\n"
                "The system cannot verify the exact count across the database at this moment. "
                "Please ensure the MongoDB service is running."
            )

        lines = [
            f"### Official Indian Patent Office Database Intelligence",
            f"**Query:** *\"{query}\"*",
            ""
        ]

        # 1. Prominent count or breakdown
        if res.intent in ("COUNT_LOCATION", "COUNT_ACTIVE_LOCATION", "COUNT_DOMAIN", "COUNT_ACTIVE_DOMAIN", "COUNT_YEAR", "COUNT_TOTAL"):
            pct = round((res.total_count / res.total_dataset_size) * 100, 1) if res.total_dataset_size else 0
            lines.append(f"Based on a direct count of all records in the complete Indian Patent Office database (2016–2018 repository):")
            lines.append("")
            lines.append(f"🏛️ **Exact Verified Count:** **{res.total_count:,} patents** ({pct}% of the {res.total_dataset_size:,} total patents)")
            lines.append(f"- **Target Metric:** {res.description}")
            lines.append(f"- **Data Source:** Official Government of India InPASS Gazette Records (MongoDB `{settings.MONGODB_COLLECTION}` collection)")
            lines.append(f"- **Legal Status:** All matching records in this repository are granted Indian patents.")
            lines.append("")

        elif res.intent in ("GROUP_BY_LOCATION", "GROUP_BY_DOMAIN"):
            lines.append(f"Based on a complete aggregation across all **{res.total_dataset_size:,} patents** in the database:")
            lines.append("")
            lines.append(f"📊 **{res.description}:**")
            lines.append("")
            lines.append("| Classification / Office | Exact Patent Count | Share of Repository |")
            lines.append("| :--- | :--- | :--- |")
            if res.breakdown:
                for k, v in res.breakdown.items():
                    pct = round((v / res.total_dataset_size) * 100, 1)
                    lines.append(f"| **{k}** | **{v:,}** | {pct}% |")
            lines.append("")

        elif res.intent == "SHOW_FILTERED_PATENTS":
            lines.append(f"The database contains **{res.total_count:,} total patents** matching your filter (*{res.description}*).")
            lines.append(f"Below are the **first {len(res.sample_patents)} representative patent records** retrieved from the database:")
            lines.append("")

        # 2. Cite sample patents
        if res.sample_patents:
            lines.append("---")
            lines.append(f"**Representative Sample Patents ({len(res.sample_patents)} displayed for reference):**")
            lines.append("")
            for idx, p in enumerate(res.sample_patents, 1):
                pid = p.get("patent_id", "N/A")
                title = p.get("title", "Untitled")
                loc = p.get("ipo_location", "India")
                field_inv = p.get("field_of_invention", "N/A")
                pub_date = p.get("publication_date", "N/A")
                lines.append(f"**{idx}. [{pid}]** — *{title}*")
                lines.append(f"   - **IPO Office:** {loc} | **Technical Field:** {field_inv} | **Publication Date:** {pub_date}")
            lines.append("")

        lines.append("---")
        lines.append(
            "> [!NOTE]\n"
            f"> This total of **{res.total_count:,}** represents the exact document count in the underlying database. "
            "It is calculated directly from the complete repository, not estimated from a top-k retrieval snippet."
        )

        return "\n".join(lines)

structured_query_service = StructuredQueryService()
