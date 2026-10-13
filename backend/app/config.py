from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PatentGraph AI - Indian Patent Intelligence"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "patentgraph_db"
    MONGODB_COLLECTION: str = "patents"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Embedding & Retrieval
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    FAISS_INDEX_PATH: str = "backend/app/data/faiss_index.bin"
    FAISS_ID_MAP_PATH: str = "backend/app/data/faiss_id_map.json"
    BM25_INDEX_PATH: str = "backend/app/data/bm25_index.pkl"
    GRAPH_STORE_PATH: str = "backend/app/data/knowledge_graph.pkl"
    CLEANED_DATA_PATH: str = "backend/app/data/cleaned_patents.parquet"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # gemini, openai, local, mock
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # RAG parameters
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.25
    RAG_MAX_CONTEXT_TOKENS: int = 2000

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
