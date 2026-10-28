import os
import logging
from typing import List, Union
import numpy as np

# Ensure offline mode is enabled if local weights exist to avoid network retry hangs
from pathlib import Path
_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
if _hf_cache.exists() and any(_hf_cache.glob("models--sentence-transformers*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer
from backend.app.config import settings

logger = logging.getLogger(__name__)

class PatentEmbeddingModel:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        logger.info(f"Loading Sentence Transformer model: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(model_name)
        if hasattr(self.model, "get_embedding_dimension"):
            self.dimension = self.model.get_embedding_dimension()
        else:
            self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model loaded. Dimension: {self.dimension}")

    def encode(self, texts: Union[str, List[str]], batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
        """Encode text or list of texts to normalized numpy embedding vectors."""
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings.astype(np.float32)

# Lazy singleton
_embedding_model_instance = None

def get_embedding_model() -> PatentEmbeddingModel:
    global _embedding_model_instance
    if _embedding_model_instance is None:
        _embedding_model_instance = PatentEmbeddingModel()
    return _embedding_model_instance
