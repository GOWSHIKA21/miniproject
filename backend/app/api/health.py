import os
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.database.mongodb import mongo_client
from backend.app.database.neo4j_client import neo4j_client, mask_neo4j_uri
from backend.app.database.qdrant_client import qdrant_client
from backend.app.retrieval.vector_search import faiss_retriever
from backend.app.retrieval.keyword_search import bm25_retriever
from backend.app.graph.graph_queries import graph_engine
from backend.app.services.rag_service import rag_service

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health_status():
    """Health check endpoint to verify backend service readiness and database connectivity."""
    mongo_status = mongo_client.get_stats()
    qdrant_status = qdrant_client.get_stats()
    neo4j_status = neo4j_client.get_stats()
    
    faiss_ready = faiss_retriever.index is not None
    faiss_count = faiss_retriever.index.ntotal if faiss_ready else 0
    
    bm25_ready = bm25_retriever.bm25 is not None
    bm25_count = len(bm25_retriever.patent_ids) if bm25_ready else 0
    
    graph_ready = graph_engine.G is not None
    graph_nodes = graph_engine.G.number_of_nodes() if graph_ready else 0
    graph_edges = graph_engine.G.number_of_edges() if graph_ready else 0

    vector_ready = qdrant_client.connected or faiss_ready

    return {
        "status": "healthy" if (mongo_client.connected and vector_ready and bm25_ready) else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "review_dataset": {
            "years": [2016, 2017, 2018],
            "dataset_path": settings.CLEANED_DATA_PATH
        },
        "components": {
            "mongodb_atlas": {
                "connected": mongo_client.connected,
                "database": mongo_client.db_name,
                "collection": mongo_client.collection_name,
                "total_documents": mongo_status.get("total_patents", 0)
            },
            "neo4j_aura": {
                "connected": neo4j_client.connected,
                "uri": mask_neo4j_uri(neo4j_client.uri),
                "database": neo4j_client.database,
                "active_engine": "Neo4j Aura Cloud" if neo4j_client.connected else "Embedded NetworkX MultiDiGraph (Offline Fallback)",
                "total_nodes": neo4j_status.get("total_nodes", 0) if neo4j_client.connected else graph_nodes,
                "total_relationships": neo4j_status.get("total_relationships", 0) if neo4j_client.connected else graph_edges
            },
            "qdrant_cloud": {
                "connected": qdrant_client.connected,
                "url": qdrant_status.get("url"),
                "collection": qdrant_status.get("collection"),
                "active_engine": "Qdrant Cloud Vector Database" if qdrant_client.connected else "Local FAISS IndexFlatIP (Offline Fallback)",
                "total_vectors": qdrant_status.get("total_vectors", 0) if qdrant_client.connected else faiss_count
            },
            "knowledge_graph_fallback": {
                "loaded": graph_ready,
                "nodes": graph_nodes,
                "edges": graph_edges,
                "file": settings.GRAPH_STORE_PATH
            },
            "faiss_vector_index_fallback": {
                "ready": faiss_ready,
                "total_vectors": faiss_count,
                "dimension": settings.EMBEDDING_DIM,
                "model": settings.EMBEDDING_MODEL_NAME,
                "file": settings.FAISS_INDEX_PATH
            },
            "bm25_keyword_index": {
                "ready": bm25_ready,
                "total_documents": bm25_count,
                "file": settings.BM25_INDEX_PATH
            },
            "rag_llm": {
                "configured_provider": settings.LLM_PROVIDER,
                "model": settings.GROQ_MODEL,
                "active_synthesizer": (
                    f"Groq Cloud Inference ({settings.GROQ_MODEL})" if rag_service.groq_client
                    else "Offline Evidence-Grounded Engine (Active until GROQ_API_KEY is provided in .env)"
                ),
                "groq_api_key_configured": bool(settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY"))
            }
        }
    }
