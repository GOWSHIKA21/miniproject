import os
import re
import uuid
import logging
from typing import Optional, Dict, Any, List
import numpy as np

try:
    from qdrant_client import QdrantClient, models
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from backend.app.config import settings

logger = logging.getLogger(__name__)


def mask_qdrant_url(url: Optional[str]) -> str:
    """Mask credentials or sensitive host identifiers in Qdrant URL."""
    if not url:
        return "[EMPTY]"
    return re.sub(r"://([^@]+)@", "://****@", url)


def normalize_qdrant_url(url: Optional[str]) -> Optional[str]:
    """Normalize Qdrant Cloud URL. Public cloud clusters terminate TLS on port 443."""
    if not url:
        return None
    cleaned = url.strip()
    if "cloud.qdrant.io:6333" in cleaned:
        cleaned = cleaned.replace(":6333", "")
    return cleaned


def patent_id_to_uuid(patent_id: str) -> str:
    """Generate a deterministic, stable UUIDv5 for Qdrant point ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"inpass.patent.{patent_id.strip()}"))


class QdrantDatabaseClient:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        timeout: float = 10.0
    ):
        raw_url = url or os.getenv("QDRANT_URL") or getattr(settings, "QDRANT_URL", None)
        self.url = normalize_qdrant_url(raw_url)
        self.api_key = api_key or os.getenv("QDRANT_API_KEY") or getattr(settings, "QDRANT_API_KEY", None)
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION") or getattr(settings, "QDRANT_COLLECTION", "patent_embeddings")
        self.timeout = float(timeout or getattr(settings, "QDRANT_TIMEOUT", 10.0))
        self.dimension = int(getattr(settings, "EMBEDDING_DIM", 384))

        self.client: Optional[Any] = None
        self.connected = False
        self._init_connection()

    def _init_connection(self):
        if not QDRANT_AVAILABLE:
            logger.info("qdrant-client package not available. Using local FAISS vector search fallback.")
            self.connected = False
            return

        if not self.url or str(self.url).strip() == "":
            logger.info("Qdrant Cloud URL is empty. Operating in local FAISS vector search fallback mode.")
            self.connected = False
            return

        if self.api_key and (self.api_key.startswith("http://") or self.api_key.startswith("https://")):
            logger.warning(
                "QDRANT_API_KEY appears to be set to a URL instead of a valid secret API key token. "
                "Operating in local FAISS fallback mode until valid API key is provided in .env."
            )
            self.connected = False
            return

        masked = mask_qdrant_url(self.url)
        try:
            self.client = QdrantClient(
                url=self.url,
                port=None,
                prefer_grpc=False,
                api_key=self.api_key if self.api_key else None,
                timeout=self.timeout
            )
            # Ping by listing collections
            self.client.get_collections()
            self.connected = True
            logger.info(f"Connected to Qdrant Cloud at {masked} (collection: '{self.collection_name}')")
            self._ensure_collection_internal()
        except Exception as e:
            logger.info(f"Qdrant Cloud connection failed at {masked} ({type(e).__name__}: {e}). Using FAISS fallback.")
            self.connected = False
            self.client = None

    def _ensure_collection_internal(self):
        """Silently verify or create collection if connected."""
        if not self.connected or not self.client:
            return
        try:
            exists = self.client.collection_exists(self.collection_name)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.dimension, distance=models.Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' (dim={self.dimension}, distance=Cosine)")
                self._create_payload_indexes()
        except Exception as e:
            logger.warning(f"Error checking/creating Qdrant collection: {e}")

    def _create_payload_indexes(self):
        """Index payload fields for efficient filtering in Qdrant Cloud."""
        if not self.connected or not self.client:
            return
        fields = [
            ("patent_id", models.PayloadSchemaType.KEYWORD),
            ("field_of_invention", models.PayloadSchemaType.KEYWORD),
            ("ipo_location", models.PayloadSchemaType.KEYWORD),
            ("application_type", models.PayloadSchemaType.KEYWORD),
            ("filing_date", models.PayloadSchemaType.KEYWORD),
            ("publication_date", models.PayloadSchemaType.KEYWORD),
        ]
        for field_name, field_schema in fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_schema
                )
            except Exception:
                pass

    def ensure_collection(self, collection_name: Optional[str] = None, dim: Optional[int] = None) -> bool:
        """Explicitly ensure the Qdrant Cloud collection is ready."""
        if not self.connected or not self.client:
            return False
        coll = collection_name or self.collection_name
        d = dim or self.dimension
        try:
            if not self.client.collection_exists(coll):
                self.client.create_collection(
                    collection_name=coll,
                    vectors_config=models.VectorParams(size=d, distance=models.Distance.COSINE)
                )
                self.collection_name = coll
                self._create_payload_indexes()
            return True
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection '{coll}': {e}")
            return False

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform cosine vector similarity search on Qdrant Cloud."""
        if not self.connected or not self.client:
            return []

        # Convert numpy vector to list of floats
        if isinstance(query_vector, np.ndarray):
            vec = query_vector.flatten().tolist()
        elif isinstance(query_vector, list):
            vec = query_vector
        else:
            return []

        qdrant_filter = None
        if filters:
            conditions = []
            if filters.get("field_of_invention") and str(filters["field_of_invention"]).upper() != "ALL":
                conditions.append(models.FieldCondition(
                    key="field_of_invention",
                    match=models.MatchValue(value=str(filters["field_of_invention"]).upper())
                ))
            if filters.get("ipo_location") and str(filters["ipo_location"]).upper() not in ("ALL", "ALL PATENT OFFICES"):
                conditions.append(models.FieldCondition(
                    key="ipo_location",
                    match=models.MatchValue(value=str(filters["ipo_location"]).title())
                ))
            if conditions:
                qdrant_filter = models.Filter(must=conditions)

        try:
            # Compatible with both query_points and search methods across qdrant-client versions
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=vec,
                    query_filter=qdrant_filter,
                    limit=top_k,
                    with_payload=True
                )
                points = response.points
            else:
                points = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=vec,
                    query_filter=qdrant_filter,
                    limit=top_k,
                    with_payload=True
                )

            results = []
            for rank, hit in enumerate(points, start=1):
                payload = hit.payload or {}
                p_id = payload.get("patent_id")
                if not p_id:
                    continue
                results.append({
                    "patent_id": p_id,
                    "score": float(hit.score),
                    "rank": rank,
                    "retriever": "qdrant_cloud",
                    "payload": payload
                })
            return results
        except Exception as e:
            logger.error(f"Qdrant Cloud search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get collection metrics and vector count."""
        if not self.connected or not self.client:
            return {
                "connected": False,
                "url": mask_qdrant_url(self.url),
                "collection": self.collection_name,
                "total_vectors": 0,
                "status": "offline_fallback"
            }
        try:
            info = self.client.get_collection(self.collection_name)
            count = getattr(info, "points_count", 0) or getattr(info, "vectors_count", 0) or 0
            return {
                "connected": True,
                "url": mask_qdrant_url(self.url),
                "collection": self.collection_name,
                "total_vectors": count,
                "dimension": self.dimension,
                "distance": "Cosine",
                "status": "connected"
            }
        except Exception as e:
            return {
                "connected": False,
                "url": mask_qdrant_url(self.url),
                "collection": self.collection_name,
                "error": str(e),
                "status": "error"
            }


qdrant_client = QdrantDatabaseClient()
