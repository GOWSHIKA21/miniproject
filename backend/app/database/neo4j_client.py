import os
import re
import json
import base64
import ssl
import urllib.request
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import certifi

# Configure CA bundle for verified TLS with Neo4j Aura
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from neo4j import GraphDatabase, Driver
from backend.app.config import settings

logger = logging.getLogger(__name__)


def mask_neo4j_uri(uri: str) -> str:
    """Mask credentials and sensitive segments in Neo4j connection URI."""
    if not uri:
        return "[EMPTY]"
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:****@", uri)


class Neo4jClient:
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        self.uri = uri or os.getenv("NEO4J_URI") or settings.NEO4J_URI
        self.user = (
            user
            or os.getenv("NEO4J_USERNAME")
            or os.getenv("NEO4J_USER")
            or getattr(settings, "NEO4J_USERNAME", None)
            or settings.NEO4J_USER
        )
        self.password = password or os.getenv("NEO4J_PASSWORD") or settings.NEO4J_PASSWORD
        self.database = database or os.getenv("NEO4J_DATABASE") or getattr(settings, "NEO4J_DATABASE", self.user)

        parsed = urlparse(self.uri)
        self.host = parsed.hostname or self.uri.replace("neo4j+s://", "").replace("bolt+s://", "").split(":")[0]

        self.driver: Optional[Driver] = None
        self.use_http = False
        self.http_headers: Dict[str, str] = {}
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        self.connected = False
        self._init_connection()

    def _init_http(self):
        auth = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        self.http_headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    def _test_http_api(self) -> bool:
        self._init_http()
        url = f"https://{self.host}/db/{self.database}/query/v2"
        body = json.dumps({"statement": "RETURN 1 AS status"}).encode()
        try:
            req = urllib.request.Request(url, data=body, headers=self.http_headers)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=6) as resp:
                return resp.status in (200, 202)
        except Exception:
            return False

    def _init_connection(self):
        if not self.uri or self.uri.strip() == "":
            logger.info("Neo4j URI is empty. Using embedded NetworkX Graph Engine fallback.")
            self.connected = False
            return

        masked = mask_neo4j_uri(self.uri)
        # Attempt 1: Try Bolt driver on Port 7687
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                connection_timeout=5.0,
                max_connection_lifetime=300,
                keep_alive=True
            )
            self.driver.verify_connectivity()
            self.connected = True
            self.use_http = False
            logger.info(f"Connected to Neo4j successfully via Bolt at {masked} (database: '{self.database}')")
            return
        except Exception as e:
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
                self.driver = None

        # Attempt 2: Fallback to HTTPS Query API on Port 443 (firewall resilient)
        if self.host not in ("localhost", "127.0.0.1") and self._test_http_api():
            self.connected = True
            self.use_http = True
            logger.info(f"Connected to Neo4j Aura via HTTPS Query API (Port 443) at {masked} (database: '{self.database}')")
        else:
            logger.info(f"Neo4j instance not reachable at {masked}. Using embedded NetworkX Graph Engine.")
            self.connected = False

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
            self.driver = None
        self.connected = False

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read/write Cypher query with parameterization."""
        if not self.connected:
            return []

        if not self.use_http and self.driver:
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Error executing Neo4j query via Bolt: {e}")
                return []

        # Execute via HTTPS Query API (port 443)
        url = f"https://{self.host}/db/{self.database}/query/v2"
        payload: Dict[str, Any] = {"statement": query}
        if parameters:
            payload["parameters"] = parameters
        body = json.dumps(payload).encode()

        try:
            req = urllib.request.Request(url, data=body, headers=self.http_headers)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                fields = data.get("data", {}).get("fields", [])
                values = data.get("data", {}).get("values", [])
                return [dict(zip(fields, row)) for row in values]
        except Exception as e:
            logger.error(f"Error executing Neo4j query via HTTPS Query API: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Fetch node, relationship and label counts."""
        if not self.connected:
            return {"status": "disconnected"}

        nodes_res = self.run_query("MATCH (n) RETURN count(n) AS total_nodes")
        rels_res = self.run_query("MATCH ()-[r]->() RETURN count(r) AS total_relationships")

        total_nodes = nodes_res[0].get("total_nodes", 0) if nodes_res else 0
        total_rels = rels_res[0].get("total_relationships", 0) if rels_res else 0

        return {
            "status": "connected",
            "transport": "HTTPS Query API (Port 443)" if self.use_http else "Bolt (Port 7687)",
            "database": self.database,
            "total_nodes": total_nodes,
            "total_relationships": total_rels
        }


# Singleton client
neo4j_client = Neo4jClient()
