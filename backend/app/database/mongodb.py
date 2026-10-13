import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self, uri: str = settings.MONGODB_URI, db_name: str = settings.MONGODB_DB_NAME):
        self.uri = uri
        self.db_name = db_name
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
            logger.info(f"Connected successfully to MongoDB at {self.uri}, database '{self.db_name}'")
            self._ensure_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(f"MongoDB connection failed ({e}). Operating in memory/Parquet fallback mode.")
            self.connected = False
            self.client = None
            self.db = None

    def _ensure_indexes(self):
        if not self.connected or self.db is None:
            return
        try:
            coll = self.db[settings.MONGODB_COLLECTION]
            coll.create_index([("patent_id", ASCENDING)], unique=True)
            coll.create_index([("field_of_invention", ASCENDING)])
            coll.create_index([("ipo_location", ASCENDING)])
            coll.create_index([("filing_date", ASCENDING)])
            coll.create_index([("publication_date", ASCENDING)])
            logger.info("MongoDB indexes verified on 'patent_id', 'field_of_invention', etc.")
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")

    def insert_patents_from_parquet(self, parquet_path: str, batch_size: int = 5000) -> int:
        """Batch load cleaned patents from Parquet into MongoDB."""
        if not self.connected or self.db is None:
            logger.warning("MongoDB not connected. Skipping DB population.")
            return 0

        coll = self.db[settings.MONGODB_COLLECTION]
        existing_count = coll.count_documents({})
        if existing_count > 0:
            logger.info(f"MongoDB collection already contains {existing_count:,} documents. Skipping reload.")
            return existing_count

        logger.info(f"Loading cleaned patents from {parquet_path} into MongoDB in batches of {batch_size}...")
        df = pd.read_parquet(parquet_path)
        records = df.to_dict(orient="records")
        total = len(records)

        inserted = 0
        for i in range(0, total, batch_size):
            chunk = records[i:i + batch_size]
            coll.insert_many(chunk, ordered=False)
            inserted += len(chunk)
            logger.info(f"Inserted {inserted:,}/{total:,} records into MongoDB...")

        logger.info(f"Completed loading {inserted:,} patents into MongoDB.")
        return inserted

    def get_patent(self, patent_id: str) -> Optional[Dict[str, Any]]:
        if self.connected and self.db is not None:
            doc = self.db[settings.MONGODB_COLLECTION].find_one({"patent_id": patent_id}, {"_id": 0})
            if doc:
                return doc
        return None

    def search_metadata(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        if self.connected and self.db is not None:
            mongo_query = {}
            if filters.get("field_of_invention"):
                mongo_query["field_of_invention"] = filters["field_of_invention"]
            if filters.get("ipo_location"):
                mongo_query["ipo_location"] = filters["ipo_location"]
            if filters.get("application_type"):
                mongo_query["application_type"] = filters["application_type"]
            if filters.get("date_from"):
                mongo_query["filing_date"] = {"$gte": filters["date_from"]}
            if filters.get("date_to"):
                mongo_query.setdefault("filing_date", {})["$lte"] = filters["date_to"]
            
            cursor = self.db[settings.MONGODB_COLLECTION].find(mongo_query, {"_id": 0}).limit(limit)
            return list(cursor)
        return []

    def get_stats(self) -> Dict[str, Any]:
        if self.connected and self.db is not None:
            coll = self.db[settings.MONGODB_COLLECTION]
            total = coll.count_documents({})
            return {"total_patents": total, "status": "connected"}
        return {"total_patents": 0, "status": "fallback_mode"}

mongo_client = MongoDBClient()
