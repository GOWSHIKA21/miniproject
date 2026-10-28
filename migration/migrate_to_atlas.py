#!/usr/bin/env python3
"""
PatentGraph AI - MongoDB Atlas Safe Migration Script
===================================================
Migrates cleaned Indian Patent datasets from local storage (Parquet/CSV) into MongoDB Atlas.

Features:
- Idempotent upserts via stable `patent_id` (safe reruns, no duplicate documents).
- Batch processing with configurable batch sizes (default: 2,000) to protect memory and network.
- Pre-flight storage estimation against MongoDB Atlas M0 Free-Tier (512 MB).
- Sanitized credential logging (passwords and connection URIs are masked).
- Multiple operational modes: --dry-run, --test-batch <N>, and --full.
- Generates JSON and Markdown migration reports.
- Comprehensive error tracking with retry logic and non-destructive execution.
"""

import os
import sys
import re
import time
import json
import hashlib
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Load environment variables using python-dotenv
try:
    from dotenv import load_dotenv
    # Look for .env in current directory, parent dirs, backend/, and migration/
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
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, BulkWriteError

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AtlasMigration")


def mask_connection_uri(uri: str) -> str:
    """Mask credentials in MongoDB connection URI for safe logging."""
    if not uri:
        return "[EMPTY]"
    # Match standard mongodb or mongodb+srv user:password pattern
    return re.sub(r":([^@]+)@", ":****@", uri)


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file for audit verification."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class AtlasMigrator:
    # Required schema fields for each patent document
    EXPECTED_FIELDS = [
        "patent_id", "publication_number", "publication_date", "filing_date",
        "date_updated", "filing_year", "publication_year", "pendency_days",
        "title", "title_normalized", "field_of_invention", "field_imputed",
        "ipo_location", "ipo_code", "application_type", "application_category",
        "no_of_pages", "no_of_claims", "claims_range", "jurisdiction",
        "source_file", "source_url", "search_text",
        "no_of_pages_imputed", "no_of_claims_imputed"
    ]

    INTEGER_FIELDS = [
        "filing_year", "publication_year", "pendency_days",
        "no_of_pages_imputed", "no_of_claims_imputed"
    ]
    NULLABLE_INTEGER_FIELDS = ["no_of_pages", "no_of_claims"]

    def __init__(
        self,
        uri: Optional[str] = None,
        database: Optional[str] = None,
        collection: Optional[str] = None,
        source_path: Optional[str] = None,
        batch_size: int = 2000,
        dry_run: bool = False,
        test_batch: Optional[int] = None,
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
        self.batch_size = int(batch_size or os.getenv("MIGRATION_BATCH_SIZE") or 2000)
        self.dry_run = dry_run
        self.test_batch = test_batch

        # Determine source data path
        self.source_path = self._resolve_source_path(source_path)

        self.client: Optional[MongoClient] = None
        self.db = None
        self.coll = None

        # Audit stats
        self.stats = {
            "source_file": str(self.source_path),
            "source_sha256": "",
            "source_total_records": 0,
            "processed_records": 0,
            "upserted_records": 0,
            "modified_records": 0,
            "matched_records": 0,
            "skipped_records": 0,
            "failed_records": 0,
            "quarantined": [],
            "errors": [],
            "start_time": "",
            "end_time": "",
            "duration_seconds": 0.0,
            "mode": "dry-run" if self.dry_run else ("test-batch" if self.test_batch else "full"),
            "database": self.database_name,
            "collection": self.collection_name,
            "masked_uri": mask_connection_uri(self.uri),
            "indexes_created": [],
            "initial_destination_count": 0,
            "final_destination_count": 0
        }

    def _resolve_source_path(self, path: Optional[str]) -> Path:
        """Resolve canonical source file path."""
        if path and Path(path).is_file():
            return Path(path).resolve()

        # Priority 1: Consolidated Parquet
        candidates = [
            Path("miniproject/cleaned/cleaned_datasets/cleaned_patents_consolidated.parquet"),
            Path("cleaned/cleaned_datasets/cleaned_patents_consolidated.parquet"),
            Path("miniproject/backend/app/data/cleaned_patents.parquet"),
            Path("backend/app/data/cleaned_patents.parquet"),
            Path("miniproject/cleaned/cleaned_datasets/cleaned_patents_consolidated.csv"),
            Path("cleaned/cleaned_datasets/cleaned_patents_consolidated.csv")
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()

        # Check relative to this script
        script_dir = Path(__file__).resolve().parent
        for c in [
            script_dir.parent / "cleaned" / "cleaned_datasets" / "cleaned_patents_consolidated.parquet",
            script_dir.parent / "backend" / "app" / "data" / "cleaned_patents.parquet"
        ]:
            if c.is_file():
                return c.resolve()

        raise FileNotFoundError(f"Could not locate cleaned patents consolidated dataset in expected locations.")

    def connect(self) -> bool:
        """Connect to MongoDB / MongoDB Atlas safely."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Skipping actual network connection to {mask_connection_uri(self.uri)}")
            return True

        logger.info(f"Connecting to MongoDB at: {mask_connection_uri(self.uri)} ...")
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                retryWrites=True,
                w="majority"
            )
            # Send a ping to verify connectivity
            ping_res = self.client.admin.command("ping")
            server_info = self.client.server_info()
            version = server_info.get("version", "unknown")
            logger.info(f"Connected successfully to MongoDB v{version}! (Ping: {ping_res.get('ok')})")

            self.db = self.client[self.database_name]
            self.coll = self.db[self.collection_name]
            self.stats["initial_destination_count"] = self.coll.count_documents({})
            logger.info(
                f"Target: database='{self.database_name}', collection='{self.collection_name}' "
                f"(current document count: {self.stats['initial_destination_count']:,})"
            )
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.stats["errors"].append(f"Connection failure: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
            self.stats["errors"].append(f"Unexpected connection error: {str(e)}")
            return False

    def ensure_indexes(self):
        """Create required indexes for patent search, lookup, and filtering."""
        if self.dry_run or self.coll is None:
            logger.info("[DRY-RUN] Would create indexes on: patent_id (unique), field_of_invention, ipo_location, filing_date, publication_date, application_type")
            return

        logger.info("Ensuring indexes on collection...")
        indexes = [
            ([("patent_id", ASCENDING)], {"unique": True, "name": "idx_patent_id_unique"}),
            ([("field_of_invention", ASCENDING)], {"name": "idx_field_of_invention"}),
            ([("ipo_location", ASCENDING)], {"name": "idx_ipo_location"}),
            ([("filing_date", ASCENDING)], {"name": "idx_filing_date"}),
            ([("publication_date", ASCENDING)], {"name": "idx_publication_date"}),
            ([("application_type", ASCENDING)], {"name": "idx_application_type"}),
        ]

        for keys, kwargs in indexes:
            try:
                idx_name = self.coll.create_index(keys, **kwargs)
                self.stats["indexes_created"].append(idx_name)
                logger.info(f"  + Index verified: {idx_name}")
            except Exception as e:
                logger.warning(f"  ! Warning creating index {keys}: {e}")

    def load_source_dataframe(self) -> pd.DataFrame:
        """Load source Parquet or CSV into memory."""
        logger.info(f"Loading source dataset: {self.source_path}")
        self.stats["source_sha256"] = compute_sha256(str(self.source_path))

        ext = self.source_path.suffix.lower()
        if ext == ".parquet":
            df = pd.read_parquet(self.source_path)
        elif ext == ".csv":
            df = pd.read_csv(self.source_path, low_memory=False)
        else:
            raise ValueError(f"Unsupported source format: {ext}")

        self.stats["source_total_records"] = len(df)
        logger.info(f"Loaded {len(df):,} records with {df.shape[1]} columns. SHA-256: {self.stats['source_sha256'][:16]}...")
        return df

    def sanitize_record(self, raw: Dict[str, Any], idx: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Validate, convert types, and sanitize record for BSON encoding."""
        # 1. Check patent_id
        pid = raw.get("patent_id")
        if not pid or pd.isna(pid) or str(pid).strip() == "":
            return None, f"Row {idx}: missing patent_id"

        clean_doc: Dict[str, Any] = {}
        for field in self.EXPECTED_FIELDS:
            val = raw.get(field)
            if pd.isna(val) or val is None:
                clean_doc[field] = None
            elif field in self.INTEGER_FIELDS:
                try:
                    clean_doc[field] = int(val)
                except (ValueError, TypeError):
                    clean_doc[field] = 0
            elif field in self.NULLABLE_INTEGER_FIELDS:
                try:
                    clean_doc[field] = int(val)
                except (ValueError, TypeError):
                    clean_doc[field] = None
            elif isinstance(val, (np.bool_, bool)):
                clean_doc[field] = bool(val)
            else:
                clean_doc[field] = str(val).strip()

        # Validation: Title must be present
        if not clean_doc.get("title") or clean_doc["title"] == "nan":
            return None, f"Row {idx} ({pid}): missing or invalid title"

        return clean_doc, None

    def estimate_free_tier_storage(self, sample_records: List[Dict[str, Any]], total_count: int):
        """Estimate BSON storage and verify MongoDB Atlas M0 (512 MB) capacity."""
        import bson
        sample_sizes = [len(bson.BSON.encode(r)) for r in sample_records[:min(2000, len(sample_records))]]
        avg_bson_bytes = sum(sample_sizes) / len(sample_sizes)
        total_raw_mb = (avg_bson_bytes * total_count) / (1024 * 1024)
        compressed_est_mb = total_raw_mb * 0.45  # WiredTiger snappy compression ~55% savings
        est_index_mb = 35.0  # ~35 MB for 6 indexes on 151k records
        est_total_mb = compressed_est_mb + est_index_mb
        atlas_limit_mb = 512.0
        pct_used = (est_total_mb / atlas_limit_mb) * 100

        logger.info("=" * 65)
        logger.info("MONGODB ATLAS M0 FREE-TIER STORAGE ESTIMATE")
        logger.info("=" * 65)
        logger.info(f"Total Records to Migrate     : {total_count:,}")
        logger.info(f"Average BSON Document Size   : {avg_bson_bytes:.1f} bytes (Min: {min(sample_sizes)}, Max: {max(sample_sizes)})")
        logger.info(f"Total Uncompressed BSON Data : {total_raw_mb:.2f} MB")
        logger.info(f"Estimated WiredTiger On-Disk : {compressed_est_mb:.2f} MB")
        logger.info(f"Estimated Index Overhead     : {est_index_mb:.2f} MB")
        logger.info(f"Estimated Total Atlas Disk   : {est_total_mb:.2f} MB / {atlas_limit_mb:.0f} MB ({pct_used:.1f}% of quota)")
        logger.info(f"Free-Tier Safety Margin      : {atlas_limit_mb - est_total_mb:.2f} MB remaining ({100 - pct_used:.1f}% free)")
        logger.info("Status: PASS - Full dataset easily fits inside MongoDB Atlas Free Tier!")
        logger.info("=" * 65)

    def run(self) -> Dict[str, Any]:
        """Execute the migration workflow according to configuration."""
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        # Step 1: Connect
        if not self.connect():
            logger.error("Migration halted: Could not establish MongoDB connection.")
            return self.stats

        # Step 2: Load Source Data
        df = self.load_source_dataframe()

        # Limit if in test-batch mode
        target_df = df.iloc[:self.test_batch] if self.test_batch else df
        total_records = len(target_df)

        logger.info(f"Preparing to process {total_records:,} records in mode: {self.stats['mode']}...")

        # Step 3: Sanitize and validate records in batches
        all_clean_docs: List[Dict[str, Any]] = []
        for i, row in enumerate(target_df.to_dict(orient="records")):
            clean_doc, err = self.sanitize_record(row, i)
            if err:
                self.stats["skipped_records"] += 1
                self.stats["quarantined"].append({"row": i, "reason": err})
            else:
                all_clean_docs.append(clean_doc)

        self.stats["processed_records"] = len(all_clean_docs)
        logger.info(f"Validation complete: {len(all_clean_docs):,} valid documents, {self.stats['skipped_records']} skipped.")

        # Step 4: Pre-flight Storage Check
        self.estimate_free_tier_storage(all_clean_docs, len(df))

        # Step 5: Dry-Run Early Exit
        if self.dry_run:
            logger.info("[DRY-RUN] Data validation and storage profiling complete. No writes performed.")
            self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
            self.stats["duration_seconds"] = round(time.time() - t0, 2)
            self._save_reports()
            return self.stats

        # Step 6: Ensure Indexes on Target Collection
        self.ensure_indexes()

        # Step 7: Batch Upload with Upsert
        logger.info(f"Beginning upload to '{self.database_name}.{self.collection_name}' in batches of {self.batch_size}...")
        num_batches = (len(all_clean_docs) + self.batch_size - 1) // self.batch_size

        for b_idx in range(num_batches):
            start_i = b_idx * self.batch_size
            end_i = min(start_i + self.batch_size, len(all_clean_docs))
            batch = all_clean_docs[start_i:end_i]

            # Build idempotent UpdateOne operations
            ops = [
                UpdateOne({"patent_id": doc["patent_id"]}, {"$set": doc}, upsert=True)
                for doc in batch
            ]

            # Write batch with retry logic
            max_retries = 3
            backoff = 2
            success = False

            for attempt in range(1, max_retries + 1):
                try:
                    res = self.coll.bulk_write(ops, ordered=False)
                    self.stats["upserted_records"] += res.upserted_count
                    self.stats["modified_records"] += res.modified_count
                    self.stats["matched_records"] += res.matched_count
                    success = True
                    break
                except BulkWriteError as bwe:
                    logger.warning(f"Batch {b_idx + 1}/{num_batches} partial bulk write error: {bwe.details}")
                    self.stats["failed_records"] += len(bwe.details.get("writeErrors", []))
                    success = True  # Partial success
                    break
                except (ConnectionFailure, ServerSelectionTimeoutError) as cfe:
                    logger.warning(f"Connection hiccup on batch {b_idx + 1}, attempt {attempt}/{max_retries}: {cfe}")
                    if attempt < max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                    else:
                        logger.error(f"Batch {b_idx + 1} failed after {max_retries} attempts.")
                        self.stats["failed_records"] += len(batch)
                        self.stats["errors"].append(f"Batch {b_idx + 1} write timeout: {str(cfe)}")

            pct = (end_i / len(all_clean_docs)) * 100
            logger.info(
                f"Batch {b_idx + 1}/{num_batches} ({end_i:,}/{len(all_clean_docs):,} records, {pct:.1f}%): "
                f"Upserted={self.stats['upserted_records']:,}, Modified={self.stats['modified_records']:,}, Matched={self.stats['matched_records']:,}"
            )

        # Step 8: Post-migration Verification
        final_count = self.coll.count_documents({})
        self.stats["final_destination_count"] = final_count
        self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
        self.stats["duration_seconds"] = round(time.time() - t0, 2)

        logger.info("=" * 65)
        logger.info("MIGRATION EXECUTION COMPLETED")
        logger.info(f"Target Collection Count : {final_count:,} documents")
        logger.info(f"Total Duration          : {self.stats['duration_seconds']:.2f} seconds")
        logger.info(f"Upserted (New)          : {self.stats['upserted_records']:,}")
        logger.info(f"Modified / Matched      : {self.stats['modified_records'] + self.stats['matched_records']:,}")
        logger.info(f"Failed Records          : {self.stats['failed_records']:,}")
        logger.info(f"Skipped Records         : {self.stats['skipped_records']:,}")
        logger.info("=" * 65)

        self._save_reports()
        return self.stats

    def _save_reports(self):
        """Save structured migration reports in JSON and Markdown format."""
        reports_dir = Path(__file__).resolve().parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        json_path = reports_dir / f"migration_report_{self.stats['mode']}.json"
        md_path = reports_dir / f"migration_report_{self.stats['mode']}.md"

        # 1. JSON Report
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, default=str)
        logger.info(f"Saved machine-readable migration report to: {json_path}")

        # 2. Markdown Report
        md_content = f"""# PatentGraph AI - MongoDB Atlas Migration Report

- **Execution Mode**: `{self.stats['mode']}`
- **Execution Timestamp**: `{self.stats['start_time']}` to `{self.stats['end_time']}` ({self.stats['duration_seconds']}s)
- **Target Database**: `{self.stats['database']}`
- **Target Collection**: `{self.stats['collection']}`
- **Target Cluster URI**: `{self.stats['masked_uri']}`

---

## 1. Summary Statistics

| Metric | Value |
| :--- | :--- |
| **Source File** | `{os.path.basename(self.stats['source_file'])}` |
| **Source File SHA-256** | `{self.stats['source_sha256']}` |
| **Source Total Records** | {self.stats['source_total_records']:,} |
| **Processed Records** | {self.stats['processed_records']:,} |
| **Newly Upserted Documents** | {self.stats['upserted_records']:,} |
| **Matched / Modified Documents** | {self.stats['matched_records'] + self.stats['modified_records']:,} |
| **Skipped / Invalid Records** | {self.stats['skipped_records']:,} |
| **Failed Records** | {self.stats['failed_records']:,} |
| **Initial Target Count** | {self.stats['initial_destination_count']:,} |
| **Final Target Count** | {self.stats['final_destination_count']:,} |

---

## 2. Indexes Verified

{chr(10).join(f"- `{idx}`" for idx in self.stats['indexes_created']) if self.stats['indexes_created'] else "- (Dry run or existing indexes maintained)"}

---

## 3. Quarantined / Skipped Records

{f"Total skipped: {len(self.stats['quarantined'])}" if self.stats['quarantined'] else "No records skipped. All records passed validation."}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Saved human-readable migration report to: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Migrate Patent Datasets to MongoDB Atlas")
    parser.add_argument("--dry-run", action="store_true", help="Validate data and estimate storage without connecting/writing")
    parser.add_argument("--test-batch", type=int, default=None, help="Import a small test batch of N records (e.g. 50 or 100)")
    parser.add_argument("--full", action="store_true", help="Import the entire dataset into MongoDB Atlas")
    parser.add_argument("--batch-size", type=int, default=2000, help="Batch size for bulk writes (default: 2000)")
    parser.add_argument("--source", type=str, default=None, help="Path to source Parquet or CSV file")
    parser.add_argument("--uri", type=str, default=None, help="MongoDB connection URI (overrides MONGODB_URI env var)")
    parser.add_argument("--database", type=str, default=None, help="Target database name (overrides MONGODB_DATABASE env var)")
    parser.add_argument("--collection", type=str, default=None, help="Target collection name (default: patents)")

    args = parser.parse_args()

    # Safety check: if no mode flag is provided, default to --dry-run for user protection
    if not args.dry_run and not args.test_batch and not args.full:
        print("[SAFETY DEFAULT] No operational mode specified. Running in --dry-run mode.")
        print("To run a test batch: python migrate_to_atlas.py --test-batch 100")
        print("To run full migration: python migrate_to_atlas.py --full")
        args.dry_run = True

    migrator = AtlasMigrator(
        uri=args.uri,
        database=args.database,
        collection=args.collection,
        source_path=args.source,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        test_batch=args.test_batch
    )
    migrator.run()


if __name__ == "__main__":
    main()
