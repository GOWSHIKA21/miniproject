#!/usr/bin/env python3
"""
PatentGraph AI - Neo4j Aura Graph Migration Script
=================================================
Migrates Indian Patent Knowledge Graph nodes and relationships into Neo4j Aura.

Features:
- Dual-transport connection: Neo4j Bolt Driver (Port 7687) with seamless fallback
  to Neo4j Aura official Query API (HTTPS Port 443) for firewall resilience.
- Connects securely with verified TLS using certifi bundle.
- Masks credentials and URIs in logs and generated reports.
- Idempotent ingestion using parameterized Cypher and MERGE (safe reruns).
- Creates uniqueness constraints and B-Tree indexes.
- Batch processing (default: 2,000 items/batch) via UNWIND $batch AS row.
- Operational modes: --dry-run, --test-batch <N>, --full, and --limit <N>.
- Generates structured Markdown and JSON migration reports.
"""

import os
import sys
import re
import time
import json
import base64
import ssl
import urllib.request
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

import certifi
import pandas as pd

# Configure CA bundle for verified TLS before loading drivers
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

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

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AuraMigration")


def mask_uri(uri: str) -> str:
    if not uri:
        return "[EMPTY]"
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:****@", uri)


class AuraMigrator:
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        graph_dir: Optional[str] = None,
        batch_size: int = 2000,
        dry_run: bool = False,
        test_batch: Optional[int] = None,
        limit_patents: Optional[int] = None,
        skip_edges: bool = False
    ):
        self.uri = uri or os.getenv("NEO4J_URI") or "neo4j+s://f53f0d18.databases.neo4j.io"
        self.username = (
            username
            or os.getenv("NEO4J_USERNAME")
            or os.getenv("NEO4J_USER")
            or "f53f0d18"
        )
        self.password = password or os.getenv("NEO4J_PASSWORD") or ""
        self.database = database or os.getenv("NEO4J_DATABASE") or self.username or "f53f0d18"
        self.batch_size = int(batch_size or 2000)
        self.dry_run = dry_run
        self.test_batch = test_batch
        self.limit_patents = limit_patents
        self.skip_edges = skip_edges

        parsed = urlparse(self.uri)
        self.host = parsed.hostname or self.uri.replace("neo4j+s://", "").replace("bolt+s://", "").split(":")[0]

        self.graph_dir = self._resolve_graph_dir(graph_dir)
        self.driver: Optional[Driver] = None
        self.use_http = False
        self.http_headers: Dict[str, str] = {}
        self.ssl_ctx: Optional[ssl.SSLContext] = None

        self.stats = {
            "mode": "dry-run" if self.dry_run else ("test-batch" if self.test_batch else "full"),
            "target_uri": mask_uri(self.uri),
            "target_database": self.database,
            "username": self.username,
            "transport": "dry-run" if self.dry_run else "pending",
            "start_time": "",
            "end_time": "",
            "duration_seconds": 0.0,
            "nodes_ingested": {},
            "relationships_ingested": {},
            "constraints_created": [],
            "errors": []
        }

    def _resolve_graph_dir(self, path: Optional[str]) -> Path:
        candidates = [
            Path(path) if path else None,
            Path("miniproject/cleaned/graph"),
            Path("cleaned/graph"),
            PROJECT_ROOT / "cleaned" / "graph"
        ]
        for c in candidates:
            if c and c.is_dir():
                return c.resolve()
        raise FileNotFoundError("Could not locate cleaned/graph directory containing prepared graph CSVs.")

    def _init_http_client(self):
        auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.http_headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    def _test_http_query_api(self) -> bool:
        """Test authentication and query execution over HTTPS port 443."""
        self._init_http_client()
        url = f"https://{self.host}/db/{self.database}/query/v2"
        body = json.dumps({"statement": "RETURN 1 AS status"}).encode()
        try:
            req = urllib.request.Request(url, data=body, headers=self.http_headers)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=10) as resp:
                return resp.status in (200, 202)
        except Exception as e:
            logger.debug(f"HTTP Query API probe failed: {e}")
            return False

    def connect(self) -> bool:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulating connection to {mask_uri(self.uri)}")
            return True

        masked = mask_uri(self.uri)
        logger.info(f"Connecting to Neo4j Aura at {masked} (database: '{self.database}', user: '{self.username}')...")

        if not self.password or self.password.strip() == "":
            err = "NEO4J_PASSWORD is empty. Please set your Neo4j Aura password in backend/.env."
            logger.error(err)
            self.stats["errors"].append(err)
            return False

        # Attempt 1: Try Bolt driver on Port 7687
        try:
            logger.info("Attempting Bolt connection (Port 7687)...")
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                connection_timeout=6.0,
                max_connection_lifetime=300,
                keep_alive=True
            )
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j Aura via Bolt Driver (Port 7687)!")
            self.stats["transport"] = "Bolt (Port 7687)"
            self.use_http = False
            return True
        except AuthError as e:
            err = f"Neo4j Aura Authentication Failure: {e}"
            logger.error(err)
            self.stats["errors"].append(str(e))
            return False
        except Exception as e:
            logger.info(f"Bolt port 7687 unavailable ({type(e).__name__}). Falling back to HTTPS Query API (Port 443)...")
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
                self.driver = None

        # Attempt 2: Fallback to official Aura Query API on HTTPS Port 443 (firewall resilient)
        if self._test_http_query_api():
            logger.info("Successfully connected to Neo4j Aura via HTTPS Query API (Port 443 - Firewall Resilient)!")
            self.stats["transport"] = "HTTPS Query API (Port 443)"
            self.use_http = True
            return True
        else:
            err = (
                "Cannot connect to Neo4j Aura on port 7687 or port 443.\n"
                "-> Check your instance status and credentials in backend/.env."
            )
            logger.error(err)
            self.stats["errors"].append(err)
            return False

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
            self.driver = None

    def _execute_cypher(self, statement: str, parameters: Optional[Dict[str, Any]] = None):
        """Execute Cypher query using either Bolt driver or HTTPS Query API."""
        if self.dry_run:
            return

        if not self.use_http and self.driver:
            with self.driver.session(database=self.database) as session:
                session.run(statement, parameters or {})
            return

        # Execute via HTTPS Query API (port 443)
        url = f"https://{self.host}/db/{self.database}/query/v2"
        payload: Dict[str, Any] = {"statement": statement}
        if parameters:
            payload["parameters"] = parameters
        body = json.dumps(payload).encode()

        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(url, data=body, headers=self.http_headers)
                with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=20) as resp:
                    if resp.status in (200, 202):
                        return
            except urllib.error.HTTPError as e:
                err_content = e.read().decode()
                if attempt == 3:
                    logger.error(f"HTTP Cypher error ({e.code}): {err_content}")
                    raise
                time.sleep(1.0 * attempt)
            except Exception as e:
                if attempt == 3:
                    logger.error(f"Query API error: {e}")
                    raise
                time.sleep(1.0 * attempt)

    def ensure_constraints_and_indexes(self):
        """Create required uniqueness constraints and indexes on Aura."""
        if self.dry_run:
            logger.info("[DRY-RUN] Would create uniqueness constraints on: (Patent.id), (Field.id), (Location.id), (ApplicationType.id), (Concept.id)")
            return

        constraints = [
            ("patent_id_unique", "CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE"),
            ("field_id_unique", "CREATE CONSTRAINT field_id_unique IF NOT EXISTS FOR (f:Field) REQUIRE f.id IS UNIQUE"),
            ("location_id_unique", "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE"),
            ("type_id_unique", "CREATE CONSTRAINT type_id_unique IF NOT EXISTS FOR (t:ApplicationType) REQUIRE t.id IS UNIQUE"),
            ("concept_id_unique", "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE"),
            ("patent_field_idx", "CREATE INDEX patent_field_idx IF NOT EXISTS FOR (p:Patent) ON (p.field)"),
            ("patent_filing_idx", "CREATE INDEX patent_filing_idx IF NOT EXISTS FOR (p:Patent) ON (p.filing_date)")
        ]

        logger.info(f"Ensuring constraints and indexes on Neo4j Aura (via {self.stats['transport']})...")
        for name, query in constraints:
            try:
                self._execute_cypher(query)
                self.stats["constraints_created"].append(name)
                logger.info(f"  + Verified constraint/index: {name}")
            except Exception as e:
                logger.warning(f"  ! Note on constraint {name}: {e}")

    def ingest_nodes(self):
        """Ingest all node types from prepared CSVs."""
        node_configs = [
            {
                "file": "nodes_fields.csv",
                "label": "Field",
                "id_col": "id:ID(Field-ID)",
                "query": """
                UNWIND $batch AS row
                MERGE (f:Field {id: row.id})
                SET f.name = row.field_name,
                    f.patent_count = toInteger(row.patent_count)
                """
            },
            {
                "file": "nodes_locations.csv",
                "label": "Location",
                "id_col": "id:ID(Location-ID)",
                "query": """
                UNWIND $batch AS row
                MERGE (l:Location {id: row.id})
                SET l.city = row.city,
                    l.office_code = row.office_code,
                    l.patent_count = toInteger(row.patent_count)
                """
            },
            {
                "file": "nodes_application_types.csv",
                "label": "ApplicationType",
                "id_col": "id:ID(Type-ID)",
                "query": """
                UNWIND $batch AS row
                MERGE (t:ApplicationType {id: row.id})
                SET t.name = row.type_name,
                    t.category = row.category,
                    t.patent_count = toInteger(row.patent_count)
                """
            },
            {
                "file": "nodes_concepts.csv",
                "label": "Concept",
                "id_col": "id:ID(Concept-ID)",
                "query": """
                UNWIND $batch AS row
                MERGE (c:Concept {id: row.id})
                SET c.name = row.concept_name,
                    c.patent_count = toInteger(row.patent_count)
                """
            },
            {
                "file": "nodes_patents.csv",
                "label": "Patent",
                "id_col": "id:ID(Patent-ID)",
                "query": """
                UNWIND $batch AS row
                MERGE (p:Patent {id: row.id})
                SET p.title = row.title,
                    p.field = row.field_of_invention,
                    p.location = row.ipo_location,
                    p.application_type = row.application_type,
                    p.filing_date = row.filing_date,
                    p.publication_date = row.publication_date,
                    p.pendency_days = toInteger(row.pendency_days),
                    p.no_of_claims = toInteger(row.no_of_claims),
                    p.no_of_pages = toInteger(row.no_of_pages),
                    p.source_url = row.source_url
                """
            }
        ]

        # Use batch_size of 500 when on HTTP transport for lower payload latency
        eff_batch_size = min(self.batch_size, 500) if self.use_http else self.batch_size

        for cfg in node_configs:
            csv_path = self.graph_dir / cfg["file"]
            if not csv_path.is_file():
                logger.warning(f"File not found: {csv_path}, skipping.")
                continue

            df = pd.read_csv(csv_path, low_memory=False)
            df = df.rename(columns={cfg["id_col"]: "id"})

            # Limit records if requested
            if cfg["label"] == "Patent":
                if self.test_batch:
                    df = df.head(self.test_batch)
                elif self.limit_patents:
                    df = df.head(self.limit_patents)

            records = df.to_dict(orient="records")
            total = len(records)
            logger.info(f"Ingesting {total:,} ({cfg['label']}) nodes from {cfg['file']}...")

            # Clean nulls
            for r in records:
                for k, v in r.items():
                    if pd.isna(v):
                        r[k] = None

            num_batches = (total + eff_batch_size - 1) // eff_batch_size
            for b in range(num_batches):
                chunk = records[b * eff_batch_size : (b + 1) * eff_batch_size]
                self._execute_cypher(cfg["query"], {"batch": chunk})
                if (b + 1) % 5 == 0 or (b + 1) == num_batches:
                    logger.info(f"  [{cfg['label']}] Ingested {min((b + 1) * eff_batch_size, total):,}/{total:,} nodes...")

            self.stats["nodes_ingested"][cfg["label"]] = total

    def ingest_relationships(self):
        """Ingest all relationship types from prepared CSVs."""
        if self.skip_edges:
            logger.info("Skipping relationships as --skip-edges is set.")
            return

        edge_configs = [
            {
                "file": "edges_classified_in.csv",
                "rel": "CLASSIFIED_IN",
                "start_col": ":START_ID(Patent-ID)",
                "end_col": ":END_ID(Field-ID)",
                "query": """
                UNWIND $batch AS row
                MATCH (p:Patent {id: row.start_id})
                MATCH (f:Field {id: row.end_id})
                MERGE (p)-[:CLASSIFIED_IN]->(f)
                """
            },
            {
                "file": "edges_filed_at.csv",
                "rel": "FILED_AT",
                "start_col": ":START_ID(Patent-ID)",
                "end_col": ":END_ID(Location-ID)",
                "query": """
                UNWIND $batch AS row
                MATCH (p:Patent {id: row.start_id})
                MATCH (l:Location {id: row.end_id})
                MERGE (p)-[:FILED_AT]->(l)
                """
            },
            {
                "file": "edges_type_of.csv",
                "rel": "TYPE_OF",
                "start_col": ":START_ID(Patent-ID)",
                "end_col": ":END_ID(Type-ID)",
                "query": """
                UNWIND $batch AS row
                MATCH (p:Patent {id: row.start_id})
                MATCH (t:ApplicationType {id: row.end_id})
                MERGE (p)-[:TYPE_OF]->(t)
                """
            },
            {
                "file": "edges_relates_to.csv",
                "rel": "RELATES_TO",
                "start_col": ":START_ID(Patent-ID)",
                "end_col": ":END_ID(Concept-ID)",
                "query": """
                UNWIND $batch AS row
                MATCH (p:Patent {id: row.start_id})
                MATCH (c:Concept {id: row.end_id})
                MERGE (p)-[:RELATES_TO]->(c)
                """
            },
            {
                "file": "edges_co_occurs_with.csv",
                "rel": "CO_OCCURS_WITH",
                "start_col": ":START_ID(Concept-ID)",
                "end_col": ":END_ID(Field-ID)",
                "query": """
                UNWIND $batch AS row
                MATCH (c:Concept {id: row.start_id})
                MATCH (f:Field {id: row.end_id})
                MERGE (c)-[r:CO_OCCURS_WITH]->(f)
                SET r.weight = toInteger(row.weight)
                """
            }
        ]

        eff_batch_size = min(self.batch_size, 500) if self.use_http else self.batch_size

        for cfg in edge_configs:
            csv_path = self.graph_dir / cfg["file"]
            if not csv_path.is_file():
                logger.warning(f"File not found: {csv_path}, skipping.")
                continue

            df = pd.read_csv(csv_path, low_memory=False)
            df = df.rename(columns={cfg["start_col"]: "start_id", cfg["end_col"]: "end_id"})

            if self.test_batch:
                df = df.head(self.test_batch * 2)

            records = df.to_dict(orient="records")
            total = len(records)
            logger.info(f"Ingesting {total:,} [:{cfg['rel']}] edges from {cfg['file']}...")

            num_batches = (total + eff_batch_size - 1) // eff_batch_size
            for b in range(num_batches):
                chunk = records[b * eff_batch_size : (b + 1) * eff_batch_size]
                self._execute_cypher(cfg["query"], {"batch": chunk})
                if (b + 1) % 5 == 0 or (b + 1) == num_batches:
                    logger.info(f"  [:{cfg['rel']}] Ingested {min((b + 1) * eff_batch_size, total):,}/{total:,} edges...")

            self.stats["relationships_ingested"][cfg["rel"]] = total

    def run(self) -> Dict[str, Any]:
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        if not self.connect():
            self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
            self.stats["duration_seconds"] = round(time.time() - t0, 2)
            self._save_report()
            return self.stats

        try:
            self.ensure_constraints_and_indexes()
            self.ingest_nodes()
            self.ingest_relationships()
        finally:
            self.close()

        self.stats["end_time"] = datetime.now(timezone.utc).isoformat()
        self.stats["duration_seconds"] = round(time.time() - t0, 2)
        self._save_report()
        logger.info(f"Neo4j Aura migration completed in {self.stats['duration_seconds']}s.")
        return self.stats

    def _save_report(self):
        reports_dir = Path(__file__).resolve().parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path = reports_dir / f"neo4j_aura_migration_report_{self.stats['mode']}.json"
        md_path = reports_dir / f"neo4j_aura_migration_report_{self.stats['mode']}.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

        md = f"""# PatentGraph AI - Neo4j Aura Migration Report

- **Execution Mode**: `{self.stats['mode']}`
- **Cluster URI**: `{self.stats['target_uri']}`
- **Database**: `{self.stats['target_database']}`
- **Username**: `{self.stats['username']}`
- **Transport**: `{self.stats['transport']}`
- **Duration**: `{self.stats['duration_seconds']}`s

## Nodes Ingested
{chr(10).join(f"- **{k}**: {v:,}" for k, v in self.stats['nodes_ingested'].items()) if self.stats['nodes_ingested'] else "- None"}

## Relationships Ingested
{chr(10).join(f"- **{k}**: {v:,}" for k, v in self.stats['relationships_ingested'].items()) if self.stats['relationships_ingested'] else "- None"}

## Constraints & Indexes
{chr(10).join(f"- `{c}`" for c in self.stats['constraints_created']) if self.stats['constraints_created'] else "- (Dry run or already verified)"}

## Status / Errors
{chr(10).join(f"- ⚠️ {e}" for e in self.stats['errors']) if self.stats['errors'] else "- ✅ Successfully completed without errors."}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)


def main():
    parser = argparse.ArgumentParser(description="Migrate Knowledge Graph to Neo4j Aura")
    parser.add_argument("--dry-run", action="store_true", help="Validate CSV inputs and Cypher without network calls")
    parser.add_argument("--test-batch", type=int, default=None, help="Import a small test batch of N nodes/edges")
    parser.add_argument("--full", action="store_true", help="Execute full ingestion")
    parser.add_argument("--limit", type=int, default=None, help="Limit maximum patents ingested")
    parser.add_argument("--skip-edges", action="store_true", help="Ingest nodes only without edges")
    parser.add_argument("--batch-size", type=int, default=2000, help="Batch size for Cypher UNWIND transactions")
    parser.add_argument("--uri", type=str, default=None, help="Neo4j Aura URI")
    parser.add_argument("--username", type=str, default=None, help="Neo4j username")
    parser.add_argument("--password", type=str, default=None, help="Neo4j password")
    parser.add_argument("--database", type=str, default=None, help="Neo4j database name")

    args = parser.parse_args()

    if not args.dry_run and not args.test_batch and not args.full:
        print("[SAFETY DEFAULT] No execution mode provided. Running in --dry-run mode.")
        args.dry_run = True

    migrator = AuraMigrator(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        test_batch=args.test_batch,
        limit_patents=args.limit,
        skip_edges=args.skip_edges
    )
    migrator.run()


if __name__ == "__main__":
    main()
