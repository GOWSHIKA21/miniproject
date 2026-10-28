import os
import json
import logging
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
from backend.app.config import settings
from backend.app.embeddings.embedding_model import get_embedding_model
from backend.app.database.qdrant_client import qdrant_client

logger = logging.getLogger(__name__)


class CloudVectorRetriever:
    """
    Hybrid Vector Retriever:
    1. Primary: Qdrant Cloud (high-performance cloud vector database with payload filtering).
    2. Fallback: Local FAISS IndexFlatIP (fast in-memory CPU similarity search).
    """
    def __init__(self, index_path: str = settings.FAISS_INDEX_PATH, id_map_path: str = settings.FAISS_ID_MAP_PATH):
        self.index_path = index_path
        self.id_map_path = id_map_path
        self.index: Optional[faiss.Index] = None
        self.index_to_patent_id: Dict[str, str] = {}
        self._load_local_faiss()

    def _load_local_faiss(self):
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.id_map_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.index_to_patent_id = data.get("index_to_patent_id", {})
                logger.info(f"Loaded local FAISS index with {self.index.ntotal:,} vectors (dim={self.index.d}).")
            except Exception as e:
                logger.error(f"Error loading local FAISS index: {e}")
        else:
            logger.warning(f"Local FAISS index files not found at {self.index_path}")

    def search(self, query: str, top_k: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Encode query and perform cosine similarity search via Qdrant Cloud or FAISS fallback."""
        embed_model = get_embedding_model()
        query_vec = embed_model.encode([query])  # (1, 384) unit-normalized

        # 1. Primary: Qdrant Cloud
        if qdrant_client.connected:
            try:
                qdrant_results = qdrant_client.search(query_vec, top_k=top_k, filters=filters)
                if qdrant_results:
                    return qdrant_results
            except Exception as e:
                logger.warning(f"Qdrant Cloud search failed ({e}). Falling back to local FAISS.")

        # 2. Resilient Fallback: Local FAISS Index
        if not self.index or self.index.ntotal == 0:
            return []

        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for rank, (score, idx) in enumerate(zip(distances[0], indices[0]), start=1):
            if idx < 0:
                continue
            patent_id = self.index_to_patent_id.get(str(idx))
            if not patent_id:
                continue
            results.append({
                "patent_id": patent_id,
                "score": float(score),
                "rank": rank,
                "retriever": "vector_faiss"
            })
        return results


# Backward compatibility singleton aliases
vector_retriever = CloudVectorRetriever()
faiss_retriever = vector_retriever
