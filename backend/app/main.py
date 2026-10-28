import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.routes import search, chat, patents, graph, stats
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import rag_service
from backend.app.database.mongodb import mongo_client
from backend.app.database.neo4j_client import neo4j_client
from backend.app.database.qdrant_client import qdrant_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PatentGraph AI backend services...")
    logger.info(f"MongoDB Status: {'Connected' if mongo_client.connected else 'Offline (Parquet fallback active)'}")
    logger.info(f"Neo4j Status: {'Connected' if neo4j_client.connected else 'Offline (Embedded NetworkX fallback active)'}")
    logger.info(f"Qdrant Status: {'Connected' if qdrant_client.connected else 'Offline (FAISS vector fallback active)'}")
    yield
    logger.info("Shutting down PatentGraph AI backend services...")
    neo4j_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Knowledge-Graph-Enhanced RAG API for Intelligent Querying of Indian Patent Databases",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(patents.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(stats.router, prefix="/api")

# Direct alias for /api/ask to support both /api/ask and /api/chat/ask
@app.post("/api/ask", response_model=ChatResponse, tags=["RAG Chat"])
def ask_direct_alias(request: ChatRequest):
    """Answer natural language patent question (direct alias to /api/chat/ask)."""
    return rag_service.answer_question(request)

@app.get("/")
def root():
    return {
        "message": "Welcome to PatentGraph AI API",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
