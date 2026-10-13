import logging
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, Driver
from backend.app.config import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri: str = settings.NEO4J_URI, user: str = settings.NEO4J_USER, password: str = settings.NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None
        self.connected = False
        self._init_connection()

    def _init_connection(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password), connection_timeout=2)
            self.driver.verify_connectivity()
            self.connected = True
            logger.info(f"Connected to Neo4j successfully at {self.uri}")
        except Exception as e:
            logger.info(f"Neo4j instance not reachable at {self.uri} ({e}). Using embedded Graph Engine.")
            self.connected = False
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.connected or not self.driver:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return []

neo4j_client = Neo4jClient()
