import os
import pickle
import logging
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from backend.app.config import settings

logger = logging.getLogger(__name__)

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in text.split() if len(w) > 1]

class BM25Retriever:
    def __init__(self, index_path: str = settings.BM25_INDEX_PATH):
        self.index_path = index_path
        self.bm25: BM25Okapi = None
        self.patent_ids: List[str] = []
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data["bm25"]
                    self.patent_ids = data["patent_ids"]
                logger.info(f"Loaded BM25 index with {len(self.patent_ids):,} documents.")
            except Exception as e:
                logger.error(f"Failed to load BM25 index from {self.index_path}: {e}")
        else:
            logger.warning(f"BM25 index not found at {self.index_path}")

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Run BM25 keyword search and return ranked list of patent IDs and scores."""
        if not self.bm25 or not self.patent_ids:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(top_indices, start=1):
            score = float(scores[idx])
            if score <= 0.0:
                continue
            results.append({
                "patent_id": self.patent_ids[idx],
                "score": score,
                "rank": rank,
                "retriever": "bm25"
            })
        return results

bm25_retriever = BM25Retriever()
