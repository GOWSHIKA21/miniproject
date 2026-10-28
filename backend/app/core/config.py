import os
from pathlib import Path
from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically enable offline HuggingFace Hub / Transformers if local weights are present
_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
if _hf_cache.exists() and any(_hf_cache.glob("models--sentence-transformers*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_backend_dir = Path(__file__).resolve().parent.parent.parent
_env_paths = [
    str(_backend_dir / ".env"),
    str(_backend_dir.parent / ".env"),
    ".env",
    "backend/.env"
]

def _resolve_data_path(rel_subpath: str) -> str:
    """Safely resolve data file paths regardless of the current working directory."""
    if os.path.exists(rel_subpath):
        return os.path.abspath(rel_subpath)
    candidate_app = str((_backend_dir / "app" / "data" / Path(rel_subpath).name).resolve())
    if os.path.exists(candidate_app):
        return candidate_app
    clean_sub = rel_subpath.replace("backend/", "").replace("backend\\", "")
    candidate_backend = str((_backend_dir / clean_sub).resolve())
    if os.path.exists(candidate_backend):
        return candidate_backend
    return rel_subpath

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_paths, extra="allow")

    PROJECT_NAME: str = "PatentGraph AI - Indian Patent Intelligence"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Frontend Development Origin
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Database & Storage
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "patentgraph_db"
    MONGODB_DB_NAME: str = "patentgraph_db"
    MONGODB_COLLECTION: str = "patents"

    # Neo4j Graph Database (Local or Neo4j Aura)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"

    # Qdrant Cloud Vector Database
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "patent_embeddings"
    QDRANT_TIMEOUT: float = 10.0

    # Embedding and Paths (Pre-configured to verified 2016-2018 InPASS assets)
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    DATA_DIR: str = _resolve_data_path("backend/app/data")
    CLEANED_DATA_PATH: str = _resolve_data_path("backend/app/data/cleaned_patents_2016_2018.parquet")
    FAISS_INDEX_PATH: str = _resolve_data_path("backend/app/data/faiss_index_2016_2018.bin")
    FAISS_ID_MAP_PATH: str = _resolve_data_path("backend/app/data/faiss_id_map_2016_2018.json")
    BM25_INDEX_PATH: str = _resolve_data_path("backend/app/data/bm25_index_2016_2018.pkl")
    GRAPH_STORE_PATH: str = _resolve_data_path("backend/app/data/knowledge_graph_2016_2018.pkl")

    # Groq LLM Settings
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # RAG Settings
    RAG_TOP_K: int = 10
    RAG_SIMILARITY_THRESHOLD: float = 0.25
    RAG_MAX_CONTEXT_TOKENS: int = 3000
    RAG_ENABLE_DEBUG_LOGGING: bool = False

    @model_validator(mode="after")
    def resolve_path_fields(self):
        for field in ["DATA_DIR", "CLEANED_DATA_PATH", "FAISS_INDEX_PATH", "FAISS_ID_MAP_PATH", "BM25_INDEX_PATH", "GRAPH_STORE_PATH"]:
            val = getattr(self, field, None)
            if val and isinstance(val, str):
                setattr(self, field, _resolve_data_path(val))
        return self

settings = Settings()
