from fastapi import APIRouter
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("", response_model=SearchResponse)
def execute_search(request: SearchRequest):
    """Execute hybrid BM25 + FAISS vector search or database filter search with pagination."""
    return hybrid_retrieval_engine.search(
        query=request.query,
        filters=request.filters,
        page=request.page,
        page_size=request.page_size,
        top_k=request.top_k,
        sort_by=request.sort_by or "relevance",
        retrieval_method=request.retrieval_method
    )
