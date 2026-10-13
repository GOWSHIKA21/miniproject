import os
import json
import logging
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
from backend.app.config import settings
from backend.app.embeddings.embedding_model import get_embedding_model

logger = logging.getLogger(__name__)

class FAISSRetriever:
    def __init__(self, index_path: str = settings.FAISS_INDEX_PATH, id_map_path: str = settings.FAISS_ID_MAP_PATH):
        self.index_path = index_path
        self.id_map_path = id_map_path
        self.index: Optional[faiss.Index] = None
        self.index_to_patent_id: Dict[str, str] = {}
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.id_map_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.index_to_patent_id = data.get("index_to_patent_id", {})
                logger.info(f"Loaded FAISS index with {self.index.ntotal:,} vectors.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
        else:
            logger.warning(f"FAISS index files not found at {self.index_path}")

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Encode query and perform cosine similarity search on normalized index."""
        if not self.index or self.index.ntotal == 0:
            return []

        embed_model = get_embedding_model()
        query_vec = embed_model.encode([query])  # (1, 384) normalized

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
                "retriever": "vector"
            })
        return results

faiss_retriever = FAISSRetriever()
