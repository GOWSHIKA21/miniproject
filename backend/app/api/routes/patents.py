from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from backend.app.schemas.patent import PatentFrontendFormat
from backend.app.services.patent_service import patent_service
from backend.app.graph.graph_queries import graph_engine

from backend.app.schemas.search import SearchResponse, SearchFilters
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine

router = APIRouter(prefix="/patents", tags=["Patents"])

@router.get("", response_model=SearchResponse)
def get_patents_list(
    q: Optional[str] = Query(None, description="Search query or keyword"),
    field: Optional[str] = Query(None, description="Technology domain"),
    office: Optional[str] = Query(None, description="Patent office branch"),
    inventor: Optional[str] = Query(None, description="Inventor name"),
    org: Optional[str] = Query(None, description="Organisation or applicant"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Records per page"),
    sort_by: str = Query("relevance", description="Sort order: relevance, newest, oldest")
):
    """Retrieve filtered, paginated Indian patent records directly with exact database counts."""
    filters = SearchFilters(
        field_of_invention=field,
        ipo_location=office,
        inventor=inventor,
        organization=org
    )
    return hybrid_retrieval_engine.search(
        query=q or "",
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by
    )

@router.get("/{patent_id:path}/related")
def get_related_patents(patent_id: str, limit: int = Query(6, ge=1, le=20)):
    """Fetch related patents through knowledge graph concept co-occurrence."""
    related = graph_engine.get_related_patents(patent_id, limit=limit)
    return {"patent_id": patent_id, "related": related}

@router.get("/{patent_id:path}/citations")
def get_patent_citations(patent_id: str):
    """Fetch citations for a patent. In the official InPASS tabular extract, external citations are not recorded."""
    patent = patent_service.get_patent_by_id(patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail=f"Patent '{patent_id}' not found in database.")
    return {
        "patent_id": patent_id,
        "title": patent.title,
        "citations": [],
        "citation_count": 0,
        "status": "No external forward/backward citation records recorded in the official InPASS granted applications extract"
    }

@router.get("/{patent_id:path}", response_model=PatentFrontendFormat)
def get_patent_details(patent_id: str):
    """Fetch full details for an individual Indian patent by application number."""
    patent = patent_service.get_patent_by_id(patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail=f"Patent '{patent_id}' not found in database.")
    return patent

