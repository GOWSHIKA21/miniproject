from fastapi import APIRouter
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("", response_model=SearchResponse)
def execute_search(request: SearchRequest):
    """Execute hybrid BM25 + FAISS vector search with optional metadata filters."""
    return hybrid_retrieval_engine.search(
        query=request.query,
        filters=request.filters,
        top_k=request.top_k,
        retrieval_method=request.retrieval_method
    )
