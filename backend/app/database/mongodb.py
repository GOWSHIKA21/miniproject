import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(
        self,
        uri: str = settings.MONGODB_URI,
        db_name: str = settings.MONGODB_DB_NAME,
        collection_name: str = settings.MONGODB_COLLECTION
    ):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[MongoClient] = None
        self.db = None
        self.connected = False
        self._init_connection()

    def _init_connection(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2500)
            # Force server check
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.connected = True
            logger.info(f"Connected successfully to MongoDB at {self.uri}, database '{self.db_name}', collection '{self.collection_name}'")
            self._ensure_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(f"MongoDB connection failed at {self.uri} ({e}). Operating in memory/Parquet fallback mode.")
            self.connected = False
            self.client = None
            self.db = None

    def _ensure_indexes(self):
        if not self.connected or self.db is None:
            return
        try:
            coll = self.db[self.collection_name]
            coll.create_index([("patent_id", ASCENDING)], unique=True)
            coll.create_index([("field_of_invention", ASCENDING)])
            coll.create_index([("ipo_location", ASCENDING)])
            coll.create_index([("filing_date", ASCENDING)])
            coll.create_index([("publication_date", ASCENDING)])
            logger.info(f"MongoDB indexes verified on collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error ensuring indexes on '{self.collection_name}': {e}")

    def insert_patents_from_parquet(
        self,
        parquet_path: Optional[str] = None,
        collection_name: Optional[str] = None,
        batch_size: int = 5000
    ) -> int:
        """Batch load cleaned patents from Parquet into MongoDB using upserts to prevent duplicates."""
        if not self.connected or self.db is None:
            logger.warning("MongoDB not connected. Skipping DB population.")
            return 0

        target_coll_name = collection_name or self.collection_name
        target_parquet = parquet_path or settings.CLEANED_DATA_PATH

        if not os.path.exists(target_parquet):
            raise FileNotFoundError(f"Parquet file not found at {target_parquet}")

        coll = self.db[target_coll_name]
        coll.create_index([("patent_id", ASCENDING)], unique=True)

        logger.info(f"Reading cleaned patents from {target_parquet} for MongoDB collection '{target_coll_name}'...")
        df = pd.read_parquet(target_parquet)
        records = df.to_dict(orient="records")
        total = len(records)
        existing_count = coll.count_documents({})

        if existing_count == total:
            logger.info(f"MongoDB collection '{target_coll_name}' already contains all {existing_count:,} documents. Skipping reload.")
            return existing_count

        logger.info(f"Importing {total:,} records into '{target_coll_name}' in batches of {batch_size} (existing: {existing_count:,})...")
        from pymongo import UpdateOne
        
        inserted = 0
        for i in range(0, total, batch_size):
            chunk = records[i:i + batch_size]
            operations = [
                UpdateOne({"patent_id": doc["patent_id"]}, {"$set": doc}, upsert=True)
                for doc in chunk
            ]
            res = coll.bulk_write(operations, ordered=False)
            inserted += len(chunk)
            logger.info(f"Processed {inserted:,}/{total:,} records (upserted: {res.upserted_count}, modified: {res.modified_count})...")

        final_count = coll.count_documents({})
        logger.info(f"Completed loading patents into MongoDB '{target_coll_name}'. Final count: {final_count:,} documents.")
        return final_count

    def get_patent(self, patent_id: str) -> Optional[Dict[str, Any]]:
        if self.connected and self.db is not None:
            try:
                doc = self.db[self.collection_name].find_one({"patent_id": patent_id}, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                logger.error(f"MongoDB get_patent error for '{patent_id}': {e}")
        return None

    def build_mongo_query(self, filters: Optional[Dict[str, Any]] = None, query_text: Optional[str] = None) -> Dict[str, Any]:
        conditions = []

        if filters:
            # 1. Technology Domain
            techs = filters.get("fields_of_invention") or ([filters.get("field_of_invention")] if filters.get("field_of_invention") else [])
            techs = [t for t in techs if t and str(t).upper() != "ALL"]
            if techs:
                regex_pattern = "^(" + "|".join(re.escape(str(t).strip()) for t in techs) + ")"
                conditions.append({"field_of_invention": {"$regex": regex_pattern, "$options": "i"}})

            # 2. Patent Office
            office = filters.get("ipo_location")
            if office and str(office).upper() not in ("ALL", "ALL PATENT OFFICES", ""):
                conditions.append({"ipo_location": {"$regex": "^" + re.escape(str(office).strip()), "$options": "i"}})

            # 3. Application Type
            app_type = filters.get("application_type")
            if app_type and str(app_type).upper() not in ("ALL", ""):
                conditions.append({"application_type": {"$regex": re.escape(str(app_type).strip()), "$options": "i"}})

            # 4. Inventor Filter
            inv = filters.get("inventor")
            if inv and str(inv).strip():
                inv_clean = str(inv).strip()
                is_default_inv = any(tok in "government of india ipo record" for tok in inv_clean.lower().split())
                inv_conds = [
                    {"inventor": {"$regex": re.escape(inv_clean), "$options": "i"}},
                    {"applicant": {"$regex": re.escape(inv_clean), "$options": "i"}},
                    {"inventors": {"$elemMatch": {"$regex": re.escape(inv_clean), "$options": "i"}}},
                    {"applicants": {"$elemMatch": {"$regex": re.escape(inv_clean), "$options": "i"}}},
                    {"search_text": {"$regex": re.escape(inv_clean), "$options": "i"}},
                    {"title": {"$regex": re.escape(inv_clean), "$options": "i"}}
                ]
                if is_default_inv:
                    inv_conds.append({"inventor": {"$exists": False}})
                    inv_conds.append({"inventor": None})
                conditions.append({"$or": inv_conds})

            # 5. Organisation / Applicant Filter
            org = filters.get("organization")
            if org and str(org).strip():
                org_clean = str(org).strip()
                is_default_org = any(tok in org_clean.lower() for tok in ["indian", "patent", "office", "ipo"])
                org_conds = [
                    {"organization": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"organisation": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"applicant": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"assignee": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"applicants": {"$elemMatch": {"$regex": re.escape(org_clean), "$options": "i"}}},
                    {"assignees": {"$elemMatch": {"$regex": re.escape(org_clean), "$options": "i"}}},
                    {"ipo_location": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"search_text": {"$regex": re.escape(org_clean), "$options": "i"}},
                    {"title": {"$regex": re.escape(org_clean), "$options": "i"}}
                ]
                if is_default_org:
                    org_conds.append({"organization": {"$exists": False}})
                    org_conds.append({"organization": None})
                conditions.append({"$or": org_conds})

            # 6. Date Filter
            exact_date = filters.get("exact_date")
            priority_date = filters.get("priority_date")
            date_from = filters.get("date_from")
            date_to = filters.get("date_to")

            if exact_date:
                conditions.append({"$or": [
                    {"publication_date": exact_date},
                    {"filing_date": exact_date}
                ]})
            elif priority_date:
                conditions.append({"$or": [
                    {"filing_date": priority_date},
                    {"publication_date": priority_date}
                ]})
            else:
                if date_from and date_to:
                    conditions.append({"$or": [
                        {"publication_date": {"$gte": date_from, "$lte": date_to}},
                        {"filing_date": {"$gte": date_from, "$lte": date_to}}
                    ]})
                elif date_from:
                    conditions.append({"$or": [
                        {"publication_date": {"$gte": date_from}},
                        {"filing_date": {"$gte": date_from}}
                    ]})
                elif date_to:
                    conditions.append({"$or": [
                        {"publication_date": {"$lte": date_to}},
                        {"filing_date": {"$lte": date_to}}
                    ]})

            # 7. Status Filter
            status = filters.get("status")
            if status and str(status).upper() not in ("ALL", ""):
                conditions.append({"status": {"$regex": "^" + re.escape(str(status).strip()), "$options": "i"}})

        # Text Query
        if query_text and query_text.strip() and query_text.strip().lower() not in ("patent invention", "all", "*"):
            q_clean = query_text.strip()
            tokens = [re.escape(tok) for tok in q_clean.split() if len(tok) > 1]
            if tokens:
                title_regex = "|".join(tokens)
                conditions.append({"$or": [
                    {"patent_id": {"$regex": re.escape(q_clean), "$options": "i"}},
                    {"title": {"$regex": title_regex, "$options": "i"}},
                    {"search_text": {"$regex": title_regex, "$options": "i"}}
                ]})

        if not conditions:
            return {}
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def search_patents(
        self,
        query_text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Perform database-level filtering, exact counting, sorting, and server-side pagination."""
        if not self.connected or self.db is None:
            return (0, [])

        try:
            coll = self.db[self.collection_name]
            mongo_query = self.build_mongo_query(filters=filters, query_text=query_text)

            total = coll.count_documents(mongo_query)
            if total == 0:
                return (0, [])

            # Determine sorting
            if sort_by == "newest":
                sort_order = [("filing_date", DESCENDING), ("publication_date", DESCENDING)]
            elif sort_by == "oldest":
                sort_order = [("filing_date", ASCENDING), ("publication_date", ASCENDING)]
            else:
                sort_order = [("publication_date", DESCENDING), ("_id", ASCENDING)]

            skip_n = max(0, (page - 1) * page_size)
            cursor = coll.find(mongo_query, {"_id": 0}).sort(sort_order).skip(skip_n).limit(page_size)
            return (total, list(cursor))
        except Exception as e:
            logger.error(f"MongoDB search_patents error: {e}")
            return (0, [])

    def search_metadata(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        _, docs = self.search_patents(filters=filters, page_size=limit)
        return docs

    def get_stats(self) -> Dict[str, Any]:
        if self.connected and self.db is not None:
            try:
                coll = self.db[self.collection_name]
                total = coll.count_documents({})
                return {
                    "total_patents": total,
                    "status": "connected",
                    "database": self.db_name,
                    "collection": self.collection_name,
                    "uri": self.uri
                }
            except Exception as e:
                logger.error(f"MongoDB get_stats error: {e}")
                return {"total_patents": 0, "status": f"error: {e}"}
        return {"total_patents": 0, "status": "fallback_mode"}

mongo_client = MongoDBClient()
