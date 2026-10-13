import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

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
    MONGODB_DB_NAME: str = "patentgraph_db"
    MONGODB_COLLECTION: str = "patents"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Embedding and Paths
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    DATA_DIR: str = "backend/app/data"
    CLEANED_DATA_PATH: str = "backend/app/data/cleaned_patents.parquet"
    FAISS_INDEX_PATH: str = "backend/app/data/faiss_index.bin"
    BM25_INDEX_PATH: str = "backend/app/data/bm25_index.pkl"
    GRAPH_STORE_PATH: str = "backend/app/data/knowledge_graph.pkl"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

settings = Settings()
