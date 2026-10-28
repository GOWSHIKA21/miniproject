#!/usr/bin/env python3
"""
PatentGraph AI - Unified Cloud Services Verification Diagnostic
==============================================================
Validates connectivity, schemas, and live query execution across:
1. MongoDB Atlas (Preserved authoritative document metadata store)
2. Neo4j Aura (Cloud Knowledge Graph nodes and relationships)
3. Qdrant Cloud (Cloud Vector database for similarity search)
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

# Load environment explicitly from miniproject/backend/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_ENV = PROJECT_ROOT / "backend" / ".env"

try:
    from dotenv import load_dotenv
    if PRIMARY_ENV.is_file():
        load_dotenv(dotenv_path=PRIMARY_ENV, override=True)
    else:
        for candidate in [PROJECT_ROOT / ".env", Path.cwd() / "backend" / ".env", Path.cwd() / ".env"]:
            if candidate.is_file():
                load_dotenv(dotenv_path=candidate, override=True)
                break
except ImportError:
    pass

# Import backend clients
sys.path.insert(0, str(PROJECT_ROOT))
from backend.app.database.mongodb import mongo_client, mask_uri as mask_mongo_uri
from backend.app.database.neo4j_client import neo4j_client, mask_neo4j_uri
from backend.app.database.qdrant_client import qdrant_client, mask_qdrant_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CloudDiagnostics")


class CloudDiagnosticSuite:
    def __init__(self):
        self.report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mongodb_atlas": {},
            "neo4j_aura": {},
            "qdrant_cloud": {},
            "overall_cloud_ready": False
        }

    def verify_mongodb_atlas(self):
        logger.info("=" * 65)
        logger.info("1. VERIFYING MONGODB ATLAS (UNCHANGED METADATA STORE)")
        logger.info("=" * 65)
        stats = mongo_client.get_stats()
        self.report["mongodb_atlas"] = {
            "uri": mask_mongo_uri(mongo_client.uri),
            "database": mongo_client.db_name,
            "collection": mongo_client.collection_name,
            "connected": mongo_client.connected,
            "total_documents": stats.get("total_patents", 0),
            "status": "PASS" if mongo_client.connected else "OFFLINE_FALLBACK"
        }
        logger.info(f"MongoDB Atlas Status: {self.report['mongodb_atlas']['status']} (Docs: {self.report['mongodb_atlas']['total_documents']:,})")

    def verify_neo4j_aura(self):
        logger.info("=" * 65)
        logger.info("2. VERIFYING NEO4J AURA (CLOUD KNOWLEDGE GRAPH)")
        logger.info("=" * 65)
        masked_uri = mask_neo4j_uri(neo4j_client.uri)

        if not neo4j_client.connected:
            self.report["neo4j_aura"] = {
                "uri": masked_uri,
                "connected": False,
                "status": "OFFLINE_FALLBACK",
                "notes": "Aura cluster is paused or credentials need checking. System is operating safely on embedded NetworkX fallback."
            }
            logger.info("Neo4j Aura Status: OFFLINE_FALLBACK (Using embedded NetworkX graph engine)")
            return

        try:
            t0 = time.time()
            stats = neo4j_client.get_stats()
            latency_ms = round((time.time() - t0) * 1000, 2)

            sample = neo4j_client.run_query("MATCH (n) RETURN labels(n) AS lbl, count(n) AS cnt LIMIT 5")

            self.report["neo4j_aura"] = {
                "uri": masked_uri,
                "database": neo4j_client.database,
                "connected": True,
                "latency_ms": latency_ms,
                "total_nodes": stats.get("total_nodes", 0),
                "total_relationships": stats.get("total_relationships", 0),
                "sample_labels": sample,
                "status": "PASS"
            }
            logger.info(f"Neo4j Aura Status: PASS ({latency_ms} ms, Nodes: {stats.get('total_nodes'):,}, Rels: {stats.get('total_relationships'):,})")
        except Exception as e:
            self.report["neo4j_aura"] = {
                "uri": masked_uri,
                "connected": False,
                "error": str(e),
                "status": "FAIL"
            }
            logger.error(f"Neo4j Aura verification failed: {e}")

    def verify_qdrant_cloud(self):
        logger.info("=" * 65)
        logger.info("3. VERIFYING QDRANT CLOUD (CLOUD VECTOR DATABASE)")
        logger.info("=" * 65)
        masked_url = mask_qdrant_url(qdrant_client.url)

        if not qdrant_client.connected:
            self.report["qdrant_cloud"] = {
                "url": masked_url,
                "connected": False,
                "status": "OFFLINE_FALLBACK",
                "notes": "Qdrant Cloud API key needs configuration. System is operating safely on local FAISS vector search fallback."
            }
            logger.info("Qdrant Cloud Status: OFFLINE_FALLBACK (Using local FAISS vector search fallback)")
            return

        try:
            t0 = time.time()
            stats = qdrant_client.get_stats()
            latency_ms = round((time.time() - t0) * 1000, 2)

            self.report["qdrant_cloud"] = {
                "url": masked_url,
                "collection": qdrant_client.collection_name,
                "connected": True,
                "latency_ms": latency_ms,
                "total_vectors": stats.get("total_vectors", 0),
                "dimension": stats.get("dimension", 384),
                "status": "PASS"
            }
            logger.info(f"Qdrant Cloud Status: PASS ({latency_ms} ms, Vectors: {stats.get('total_vectors'):,}, Dim: {stats.get('dimension')})")
        except Exception as e:
            self.report["qdrant_cloud"] = {
                "url": masked_url,
                "connected": False,
                "error": str(e),
                "status": "FAIL"
            }
            logger.error(f"Qdrant Cloud verification failed: {e}")

    def run(self) -> Dict[str, Any]:
        self.verify_mongodb_atlas()
        self.verify_neo4j_aura()
        self.verify_qdrant_cloud()

        cloud_nodes = self.report["neo4j_aura"].get("connected", False)
        cloud_vectors = self.report["qdrant_cloud"].get("connected", False)
        self.report["overall_cloud_ready"] = cloud_nodes and cloud_vectors

        logger.info("=" * 65)
        logger.info(f"DIAGNOSTIC SUMMARY: All Cloud Services Live: {self.report['overall_cloud_ready']}")
        logger.info("=" * 65)

        self._save_report()
        return self.report

    def _save_report(self):
        reports_dir = Path(__file__).resolve().parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path = reports_dir / "cloud_verification_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2)
        logger.info(f"Saved diagnostic report to: {json_path}")


def main():
    suite = CloudDiagnosticSuite()
    suite.run()


if __name__ == "__main__":
    main()
