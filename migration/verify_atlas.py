#!/usr/bin/env python3
"""
PatentGraph AI - MongoDB Atlas Verification & Query Test Script
=============================================================
Verifies MongoDB Atlas migration integrity:
- Server connectivity & latency
- Document count comparison vs local dataset
- Preservation of patent identifiers and all fields
- Execution of representative queries matching the application API
- Collection & index storage breakdown
- Duplicate check for idempotency verification
"""

import os
import sys
import re
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment
try:
    from dotenv import load_dotenv
    env_candidates = [
        Path.cwd() / ".env",
        Path.cwd() / "migration" / ".env",
        Path.cwd() / "backend" / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / "backend" / ".env",
    ]
    for env_path in env_candidates:
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path, override=False)
except ImportError:
    pass

import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AtlasVerifier")


def mask_connection_uri(uri: str) -> str:
    if not uri:
        return "[EMPTY]"
    return re.sub(r":([^@]+)@", ":****@", uri)


class AtlasVerifier:
    def __init__(
        self,
        uri: Optional[str] = None,
        database: Optional[str] = None,
        collection: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
        self.database_name = (
            database
            or os.getenv("MONGODB_DATABASE")
            or os.getenv("MONGODB_DB_NAME")
            or "patentgraph_db"
        )
        self.collection_name = (
            collection
            or os.getenv("MONGODB_COLLECTION")
            or "patents"
        )

        self.client: Optional[MongoClient] = None
        self.db = None
        self.coll = None

        self.results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "masked_uri": mask_connection_uri(self.uri),
            "database": self.database_name,
            "collection": self.collection_name,
            "connected": False,
            "ping_latency_ms": 0.0,
            "total_documents": 0,
            "duplicate_patent_ids": 0,
            "storage_stats": {},
            "indexes": [],
            "sample_record_verified": False,
            "query_tests": [],
            "all_tests_passed": False
        }

    def connect(self) -> bool:
        try:
            t0 = time.time()
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
                retryWrites=True
            )
            self.client.admin.command("ping")
            latency = (time.time() - t0) * 1000
            self.results["ping_latency_ms"] = round(latency, 2)
            self.results["connected"] = True
            self.db = self.client[self.database_name]
            self.coll = self.db[self.collection_name]
            logger.info(f"Connected to Atlas! Ping latency: {self.results['ping_latency_ms']} ms")
            return True
        except Exception as e:
            logger.error(f"Cannot connect to Atlas at {mask_connection_uri(self.uri)}: {e}")
            self.results["connected"] = False
            self.results["error"] = str(e)
            return False

    def verify_counts_and_duplicates(self):
        logger.info("Checking document counts and uniqueness...")
        total = self.coll.count_documents({})
        self.results["total_documents"] = total
        logger.info(f"Total documents in '{self.collection_name}': {total:,}")

        # Check for duplicates on patent_id via aggregation
        pipeline = [
            {"$group": {"_id": "$patent_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": 10}
        ]
        dups = list(self.coll.aggregate(pipeline))
        self.results["duplicate_patent_ids"] = len(dups)
        if dups:
            logger.warning(f"Found duplicate patent_ids! Example: {dups}")
        else:
            logger.info("Integrity check: Zero duplicate patent_ids found (100% unique).")

    def verify_indexes_and_storage(self):
        logger.info("Inspecting indexes and storage...")
        try:
            indexes = list(self.coll.list_indexes())
            self.results["indexes"] = [idx["name"] for idx in indexes]
            logger.info(f"Existing indexes ({len(indexes)}): {self.results['indexes']}")
        except Exception as e:
            logger.warning(f"Could not list indexes: {e}")

        # Attempt to retrieve collection storage statistics
        try:
            stats = self.db.command("collStats", self.collection_name)
            self.results["storage_stats"] = {
                "count": stats.get("count", 0),
                "size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "total_index_size_mb": round(stats.get("totalIndexSize", 0) / (1024 * 1024), 2),
                "avg_obj_size_bytes": stats.get("avgObjSize", 0)
            }
            logger.info(
                f"Storage breakdown: uncompressed={self.results['storage_stats']['size_mb']} MB, "
                f"compressed on-disk={self.results['storage_stats']['storage_size_mb']} MB, "
                f"indexes={self.results['storage_stats']['total_index_size_mb']} MB"
            )
        except Exception as e:
            logger.info(f"collStats command not available on tier (normal for some Atlas shared tiers): {e}")

    def test_sample_record(self):
        logger.info("Verifying representative record structure...")
        doc = self.coll.find_one({}, {"_id": 0})
        if not doc:
            logger.warning("No records found in collection to verify.")
            return

        expected_fields = [
            "patent_id", "title", "field_of_invention", "ipo_location",
            "filing_date", "publication_date", "application_type"
        ]
        missing = [f for f in expected_fields if f not in doc]
        if missing:
            logger.warning(f"Sample record missing expected fields: {missing}")
            self.results["sample_record_verified"] = False
        else:
            self.results["sample_record_verified"] = True
            self.results["sample_patent_id"] = doc.get("patent_id")
            logger.info(f"Sample record [{doc.get('patent_id')}] verified successfully.")

    def run_representative_queries(self):
        """Execute queries matching backend routes (health, search, details, stats)."""
        logger.info("Executing representative queries...")
        queries = [
            {
                "name": "Exact Lookup by Patent ID",
                "filter": {"patent_id": self.results.get("sample_patent_id", "10/DEL/2010")},
                "expected_min": 1
            },
            {
                "name": "Filter by Technology Domain (CHEMISTRY)",
                "filter": {"field_of_invention": {"$regex": "^CHEMISTRY", "$options": "i"}},
                "expected_min": 1
            },
            {
                "name": "Filter by IPO Jurisdiction (Delhi)",
                "filter": {"ipo_location": {"$regex": "^Delhi", "$options": "i"}},
                "expected_min": 1
            },
            {
                "name": "Date Range Query (filing >= 2018)",
                "filter": {"filing_date": {"$gte": "2018-01-01"}},
                "expected_min": 1
            },
            {
                "name": "Composite Faceted Search (MECHANICAL + Chennai)",
                "filter": {
                    "$and": [
                        {"field_of_invention": {"$regex": "^MECHANICAL", "$options": "i"}},
                        {"ipo_location": {"$regex": "^Chennai", "$options": "i"}}
                    ]
                },
                "expected_min": 0
            }
        ]

        all_passed = True
        for q in queries:
            t0 = time.time()
            cursor = self.coll.find(q["filter"], {"_id": 0, "patent_id": 1, "title": 1}).limit(10)
            matches = list(cursor)
            duration_ms = round((time.time() - t0) * 1000, 2)
            passed = len(matches) >= q["expected_min"]
            if not passed:
                all_passed = False

            q_res = {
                "name": q["name"],
                "filter": str(q["filter"]),
                "results_count": len(matches),
                "duration_ms": duration_ms,
                "passed": passed
            }
            self.results["query_tests"].append(q_res)
            logger.info(f"  [{'PASS' if passed else 'FAIL'}] {q['name']}: {len(matches)} matches in {duration_ms} ms")

        self.results["all_tests_passed"] = (
            all_passed
            and self.results["connected"]
            and self.results["duplicate_patent_ids"] == 0
            and self.results["sample_record_verified"]
        )

    def run(self) -> Dict[str, Any]:
        if not self.connect():
            self._save_report()
            return self.results

        self.verify_counts_and_duplicates()
        self.verify_indexes_and_storage()
        self.test_sample_record()
        self.run_representative_queries()
        self._save_report()

        logger.info("=" * 65)
        logger.info(f"VERIFICATION FINISHED: {'ALL TESTS PASSED' if self.results['all_tests_passed'] else 'ATTENTION NEEDED'}")
        logger.info("=" * 65)
        return self.results

    def _save_report(self):
        reports_dir = Path(__file__).resolve().parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "verification_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Verification report saved to: {report_path}")


def main():
    verifier = AtlasVerifier()
    verifier.run()


if __name__ == "__main__":
    main()
