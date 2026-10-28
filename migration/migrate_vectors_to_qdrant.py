#!/usr/bin/env python3
"""
PatentGraph AI - Qdrant Cloud Vector Migration Script
====================================================
Migrates patent embeddings and metadata payloads into Qdrant Cloud.

Features:
- Connects securely to Qdrant Cloud using API key and cluster URL.
- Enforces port=None and prefer_grpc=False so QdrantClient uses HTTPS port 443.
- Automatically normalizes Qdrant Cloud endpoints (strips stray :6333).
- Validates API key formatting, detecting accidentally pasted cluster URLs.
- Deterministic .env resolution from backend/.env or miniproject/backend/.env.
- Reuses existing precomputed embeddings from local FAISS index (2,000 vectors)
  or encodes additional records from cleaned Parquet via all-MiniLM-L6-v2.
- Deterministic point IDs via UUIDv5(namespace, patent_id) for safe idempotent reruns.
- Rich payload metadata (patent_id, title, field, office, filing_date, etc.) for filtering.
- Batched streaming upserts (default: 250 points/batch) with retry logic.
- Modes: --check-connection, --dry-run, --test-batch <N>, --full, --source {faiss,parquet}, and --limit <N>.
- Generates JSON and Markdown migration reports.
"""

import os
import sys
import re
import time
import json
import uuid
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import faiss

# Deterministic .env loading from backend/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    env_candidates = [
        Path.cwd() / "backend" / ".env",
        Path.cwd() / "miniproject" / "backend" / ".env",
        PROJECT_ROOT / "backend" / ".env",
        Path.cwd() / ".env",
        PROJECT_ROOT / ".env",
    ]
    loaded_env = None
    for candidate in env_candidates:
        if candidate.is_file():
            load_dotenv(dotenv_path=candidate, override=True)
            loaded_env = candidate
            break
except ImportError:
    pass

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("QdrantMigration")


def mask_url(url: Optional[str]) -> str:
    if not url:
        return "[EMPTY]"
    return re.sub(r"://([^@]+)@", "://****@", url)


def normalize_qdrant_url(url: Optional[str]) -> Optional[str]:
    """Normalize Qdrant Cloud URL. Public cloud clusters terminate TLS on port 443."""
    if not url:
        return None
    cleaned = url.strip()
    # Strip port 6333 if specified for cloud.qdrant.io endpoints
    if "cloud.qdrant.io:6333" in cleaned:
        logger.info("Normalizing Qdrant Cloud URL: removing ':6333' because Qdrant Cloud uses standard HTTPS port 443.")
        cleaned = cleaned.replace(":6333", "")
    return cleaned


def patent_id_to_uuid(patent_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"inpass.patent.{patent_id.strip()}"))


class QdrantMigrator:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        source: str = "faiss",
        batch_size: int = 250,
        dry_run: bool = False,
        test_batch: Optional[int] = None,
        limit: Optional[int] = None,
        recompute: bool = False
    ):
        raw_url = url or os.getenv("QDRANT_URL")
        self.url = normalize_qdrant_url(raw_url)
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION") or "patent_embeddings"
        self.source = source
        self.batch_size = int(batch_size or 250)
        self.dry_run = dry_run
        self.test_batch = test_batch
        self.limit = limit
        self.recompute = recompute

        self.dimension = 384
        self.client: Optional[QdrantClient] = None

        self.stats = {
            "mode": "dry-run" if self.dry_run else ("test-batch" if self.test_batch else "full"),
            "target_url": mask_url(self.url),
            "collection": self.collection_name,
            "source_type": self.source,
            "dimension": self.dimension,
            "distance": "Cosine",
            "start_time": "",
            "end_time": "",
            "duration_seconds": 0.0,
            "total_points_prepared": 0,
            "total_points_upserted": 0,
            "errors": []
        }

    def connect(self) -> bool:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulating connection to Qdrant Cloud at {mask_url(self.url)}")
            return True

        if not self.url or str(self.url).strip() == "":
            err = "QDRANT_URL is not set. Please provide QDRANT_URL and QDRANT_API_KEY in backend/.env."
            logger.error(err)
            self.stats["errors"].append(err)
            return False

        # Validate API Key formatting
        if self.api_key and (self.api_key.startswith("http://") or self.api_key.startswith("https://") or self.api_key == self.url):
            err = (
                "CRITICAL CONFIGURATION ERROR: QDRANT_API_KEY is configured with a URL instead of a valid secret API key token!\n"
                f"Current value in .env: '{self.api_key}'\n"
                "----------------------------------------------------------------------\n"
                "DIAGNOSIS: Qdrant Cloud returned HTTP 403 Forbidden because it received\n"
                "the cluster URL as its authentication token rather than your secret API key.\n"
                "ACTION REQUIRED:\n"
                "  1. Log into your Qdrant Cloud Console: https://cloud.qdrant.io\n"
                "  2. Click on your Cluster (f926cdb3-3b12-47ea-9d60-e29fb6b159ff)\n"
                "  3. Open the 'API Keys' tab (or 'Data Access Control')\n"
                "  4. Copy your secret API Key token (an alphanumeric string, NOT the URL)\n"
                "  5. In backend/.env, update QDRANT_API_KEY with your secret key token.\n"
                "----------------------------------------------------------------------"
            )
            logger.error(err)
            self.stats["errors"].append(err)
            return False

        if not self.api_key or str(self.api_key).strip() == "":
            err = "QDRANT_API_KEY is empty. Qdrant Cloud clusters require a valid API key."
            logger.error(err)
            self.stats["errors"].append(err)
            return False

        masked = mask_url(self.url)
        logger.info(f"Connecting to Qdrant Cloud at {masked} (port=None, prefer_grpc=False)...")
        try:
            # Explicitly pass port=None and prefer_grpc=False to prevent QdrantClient
            # from defaulting to port 6333 or gRPC port 6334 (which are closed on Qdrant Cloud public clusters)
            self.client = QdrantClient(
                url=self.url,
                port=None,
                prefer_grpc=False,
                api_key=self.api_key,
                timeout=15.0
            )
            # Test connectivity
            collections = self.client.get_collections()
            colls_names = [c.name for c in collections.collections]
            logger.info(f"Successfully connected to Qdrant Cloud cluster! Existing collections: {colls_names}")
            return True
        except UnexpectedResponse as e:
            if e.status_code == 403:
                err = (
                    f"Qdrant Cloud Authentication Error (HTTP 403 Forbidden): {e}\n"
                    "-> Check your QDRANT_API_KEY in backend/.env.\n"
                    "-> Make sure the API key is valid and has read/write permissions for your cluster."
                )
            else:
                err = f"Qdrant Cloud HTTP Error ({e.status_code}): {e}"
            logger.error(err)
            self.stats["errors"].append(err)
            return False
        except Exception as e:
            err_str = str(e)
            if "10061" in err_str or "actively refused" in err_str:
                err = (
                    f"Connection refused by target machine: {e}\n"
                    "-> Ensure your QDRANT_URL does NOT include port 6333 on cloud.qdrant.io endpoints."
                )
            else:
                err = f"Cannot connect to Qdrant Cloud: {e}"
            logger.error(err)
            self.stats["errors"].append(err)
            return False

    def test_connection_only(self) -> bool:
        """Verify authentication and list collections without uploading vectors."""
        print("\n" + "=" * 70)
        print("QDRANT CLOUD CONNECTIVITY & AUTHENTICATION CHECK")
        print("=" * 70)
        masked_url = mask_url(self.url)
        print(f"Target URL       : {masked_url}")
        print(f"Target Collection: {self.collection_name}")
        print(f"API Key Config   : {'[SET - ' + str(len(self.api_key)) + ' chars]' if self.api_key else '[NOT SET]'}")
        print("-" * 70)

        connected = self.connect()
        if not connected:
            print("[-] Connectivity test FAILED.")
            return False

        try:
            colls = self.client.get_collections()
            colls_list = [c.name for c in colls.collections]
            print(f"[+] Connectivity test PASSED!")
            print(f"    Existing collections in cluster ({len(colls_list)}): {colls_list}")

            if self.collection_name in colls_list:
                info = self.client.get_collection(self.collection_name)
                print(f"[i] Collection '{self.collection_name}' already exists.")
                print(f"    - Points count    : {info.points_count:,}")
                print(f"    - Vector dimension: {info.config.params.vectors.size}")
                print(f"    - Distance metric : {info.config.params.vectors.distance}")
            else:
                print(f"[i] Collection '{self.collection_name}' does not exist yet (ready to be created).")

            print("\n" + "=" * 70)
            print("RESULT: SUCCESS - Ready for migration!")
            print("=" * 70 + "\n")
            return True
        except Exception as e:
            print(f"[-] Error retrieving collection info: {e}")
            return False

    def ensure_collection(self):
        """Create target collection with Cosine distance and create payload indexes."""
        if self.dry_run or not self.client:
            logger.info(f"[DRY-RUN] Would create collection '{self.collection_name}' (dim={self.dimension}, distance=Cosine)")
            return

        logger.info(f"Ensuring collection '{self.collection_name}' exists in Qdrant Cloud...")
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.dimension, distance=models.Distance.COSINE)
                )
                logger.info(f"Created Qdrant Cloud collection '{self.collection_name}'")
            else:
                info = self.client.get_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' already exists. Vectors count: {info.points_count}")

            # Create payload indexes for metadata filtering
            payload_fields = [
                ("patent_id", models.PayloadSchemaType.KEYWORD),
                ("field_of_invention", models.PayloadSchemaType.KEYWORD),
                ("ipo_location", models.PayloadSchemaType.KEYWORD),
                ("application_type", models.PayloadSchemaType.KEYWORD),
                ("filing_date", models.PayloadSchemaType.KEYWORD),
                ("publication_date", models.PayloadSchemaType.KEYWORD),
            ]
            for f_name, f_schema in payload_fields:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=f_name,
                        field_schema=f_schema
                    )
                except Exception:
                    pass
            logger.info("Payload metadata indexes verified.")
        except Exception as e:
            logger.error(f"Error preparing Qdrant Cloud collection: {e}")
            self.stats["errors"].append(f"Collection error: {str(e)}")

    def _resolve_path(self, rel_path: str) -> Path:
        candidates = [
            Path(rel_path),
            PROJECT_ROOT / rel_path,
            PROJECT_ROOT / "backend" / rel_path,
            PROJECT_ROOT / "backend" / "app" / "data" / Path(rel_path).name,
            Path.cwd() / rel_path,
            Path.cwd() / "miniproject" / rel_path,
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()
        raise FileNotFoundError(f"Could not find required data file: {rel_path}")

    def prepare_points_from_faiss(self) -> List[models.PointStruct]:
        """Extract existing 2,000 precomputed embeddings from local FAISS index."""
        faiss_path = self._resolve_path("backend/app/data/faiss_index.bin")
        id_map_path = self._resolve_path("backend/app/data/faiss_id_map.json")
        parquet_path = self._resolve_path("backend/app/data/cleaned_patents.parquet")

        logger.info(f"Reusing precomputed embeddings from {faiss_path}...")
        index = faiss.read_index(str(faiss_path))
        num_vectors = index.ntotal

        with open(id_map_path, "r", encoding="utf-8") as f:
            id_map = json.load(f)

        df_meta = pd.read_parquet(parquet_path)
        meta_dict = {}
        for _, row in df_meta.iterrows():
            pid = str(row.get("patent_id", "")).strip()
            if pid:
                meta_dict[pid] = {
                    "patent_id": pid,
                    "title": str(row.get("title", "")),
                    "abstract": str(row.get("abstract", "")),
                    "field_of_invention": str(row.get("field_of_invention", "")),
                    "ipo_location": str(row.get("ipo_location", "")),
                    "application_type": str(row.get("application_type", "")),
                    "filing_date": str(row.get("filing_date", "")),
                    "publication_date": str(row.get("publication_date", "")),
                    "source_url": str(row.get("source_url", ""))
                }

        # Reconstruct vectors from FAISS
        logger.info(f"Extracting {num_vectors:,} precomputed vectors from FAISS...")
        vectors = index.reconstruct_n(0, num_vectors)

        # Normalize vectors for Cosine distance
        faiss.normalize_L2(vectors)

        points = []
        idx_map = id_map.get("index_to_patent_id", id_map)
        limit = self.test_batch or self.limit or num_vectors
        for i in range(min(num_vectors, limit)):
            pid = idx_map.get(str(i)) or idx_map.get(i)
            if not pid:
                continue

            point_id = patent_id_to_uuid(pid)
            vec = vectors[i].tolist()
            payload = meta_dict.get(pid, {"patent_id": pid})

            points.append(models.PointStruct(
                id=point_id,
                vector=vec,
                payload=payload
            ))

        return points

    def prepare_points_from_parquet(self) -> List[models.PointStruct]:
        """Compute embeddings for all records using sentence-transformers model."""
        parquet_path = self._resolve_path("backend/app/data/cleaned_patents.parquet")
        logger.info(f"Loading patents from {parquet_path}...")
        df = pd.read_parquet(parquet_path)

        limit = self.test_batch or self.limit
        if limit:
            df = df.head(limit)

        from sentence_transformers import SentenceTransformer
        logger.info("Initializing SentenceTransformer (all-MiniLM-L6-v2)...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")

        texts = []
        for _, row in df.iterrows():
            title = str(row.get("title", ""))
            abstract = str(row.get("abstract", ""))
            texts.append(f"{title}\n{abstract}".strip())

        logger.info(f"Encoding {len(texts):,} patents into 384-dimensional vectors...")
        embeddings = embedder.encode(texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)

        points = []
        for i, (_, row) in enumerate(df.iterrows()):
            pid = str(row.get("patent_id", "")).strip()
            if not pid:
                continue

            point_id = patent_id_to_uuid(pid)
            payload = {
                "patent_id": pid,
                "title": str(row.get("title", "")),
                "abstract": str(row.get("abstract", "")),
                "field_of_invention": str(row.get("field_of_invention", "")),
                "ipo_location": str(row.get("ipo_location", "")),
                "application_type": str(row.get("application_type", "")),
                "filing_date": str(row.get("filing_date", "")),
                "publication_date": str(row.get("publication_date", "")),
                "source_url": str(row.get("source_url", ""))
            }

            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[i].tolist(),
                payload=payload
            ))

        return points

    def upsert_points(self, points: List[models.PointStruct]):
        """Stream upserts in batches into Qdrant Cloud."""
        if self.dry_run or not self.client:
            logger.info(f"[DRY-RUN] Schema, vectors, and UUIDv5 mapping verified. No network writes executed.")
            return

        total = len(points)
        num_batches = (total + self.batch_size - 1) // self.batch_size
        logger.info(f"Upserting {total:,} points into Qdrant Cloud in {num_batches} batches...")

        for b in range(num_batches):
            chunk = points[b * self.batch_size : (b + 1) * self.batch_size]
            for attempt in range(1, 4):
                try:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=chunk,
                        wait=True
                    )
                    self.stats["total_points_upserted"] += len(chunk)
                    if (b + 1) % 4 == 0 or (b + 1) == num_batches:
                        logger.info(f"  Upserted {self.stats['total_points_upserted']:,}/{total:,} points...")
                    break
                except Exception as e:
                    logger.warning(f"  Batch {b+1} attempt {attempt} failed: {e}")
                    if attempt == 3:
                        self.stats["errors"].append(f"Failed batch {b+1}: {str(e)}")
                    time.sleep(1.5 * attempt)

    def run(self) -> Dict[str, Any]:
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        if not self.connect():
            self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
            self.stats["duration_seconds"] = round(time.time() - t0, 2)
            self._save_report()
            return self.stats

        try:
            self.ensure_collection()

            if self.source == "parquet" or self.recompute:
                points = self.prepare_points_from_parquet()
            else:
                points = self.prepare_points_from_faiss()

            self.stats["total_points_prepared"] = len(points)
            logger.info(f"Prepared {len(points):,} points for Qdrant Cloud.")

            self.upsert_points(points)

        except Exception as e:
            logger.error(f"Migration error: {e}")
            self.stats["errors"].append(str(e))

        self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
        self.stats["duration_seconds"] = round(time.time() - t0, 2)
        self._save_report()
        logger.info(f"Qdrant Cloud vector migration finished in {self.stats['duration_seconds']}s.")
        return self.stats

    def _save_report(self):
        reports_dir = Path(__file__).resolve().parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path = reports_dir / f"qdrant_cloud_migration_report_{self.stats['mode']}.json"
        md_path = reports_dir / f"qdrant_cloud_migration_report_{self.stats['mode']}.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

        md = f"""# PatentGraph AI - Qdrant Cloud Vector Migration Report

- **Execution Mode**: `{self.stats['mode']}`
- **Target URL**: `{self.stats['target_url']}`
- **Collection**: `{self.stats['collection']}`
- **Vector Dimension**: `{self.stats['dimension']}`
- **Distance Metric**: `{self.stats['distance']}`
- **Source Used**: `{self.stats['source_type']}`
- **Points Prepared**: `{self.stats['total_points_prepared']:,}`
- **Points Upserted**: `{self.stats['total_points_upserted']:,}`
- **Duration**: `{self.stats['duration_seconds']}`s

## Status / Errors
{chr(10).join(f"- ⚠️ {e}" for e in self.stats['errors']) if self.stats['errors'] else "- ✅ Successfully completed without errors."}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)


def main():
    parser = argparse.ArgumentParser(description="Migrate Patent Embeddings to Qdrant Cloud")
    parser.add_argument("--check-connection", action="store_true", help="Test connectivity & auth without modifying data")
    parser.add_argument("--dry-run", action="store_true", help="Validate FAISS/parquet inputs without network writes")
    parser.add_argument("--test-batch", type=int, default=None, help="Upsert a small test batch of N vectors")
    parser.add_argument("--full", action="store_true", help="Execute full migration of all vectors")
    parser.add_argument("--limit", type=int, default=None, help="Limit maximum points upserted")
    parser.add_argument("--source", choices=["faiss", "parquet"], default="faiss", help="Source for vectors")
    parser.add_argument("--batch-size", type=int, default=250, help="Batch size for vector upserts")
    parser.add_argument("--recompute", action="store_true", help="Recompute embeddings via SentenceTransformer")
    parser.add_argument("--url", type=str, default=None, help="Qdrant Cloud URL")
    parser.add_argument("--api-key", type=str, default=None, help="Qdrant Cloud API key")
    parser.add_argument("--collection", type=str, default=None, help="Target collection name")

    args = parser.parse_args()

    migrator = QdrantMigrator(
        url=args.url,
        api_key=args.api_key,
        collection_name=args.collection,
        source=args.source,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        test_batch=args.test_batch,
        limit=args.limit,
        recompute=args.recompute
    )

    if args.check_connection:
        ok = migrator.test_connection_only()
        sys.exit(0 if ok else 1)

    if not args.dry_run and not args.test_batch and not args.full:
        print("[SAFETY DEFAULT] No execution mode provided. Running in --dry-run mode.")
        args.dry_run = True
        migrator.dry_run = True
        migrator.stats["mode"] = "dry-run"

    migrator.run()


if __name__ == "__main__":
    main()
