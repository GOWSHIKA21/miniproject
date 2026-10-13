from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from backend.app.schemas.patent import PatentFrontendFormat
from backend.app.services.patent_service import patent_service
from backend.app.graph.graph_queries import graph_engine

router = APIRouter(prefix="/patents", tags=["Patents"])

@router.get("/{patent_id:path}/related")
def get_related_patents(patent_id: str, limit: int = Query(6, ge=1, le=20)):
    """Fetch related patents through knowledge graph concept co-occurrence."""
    related = graph_engine.get_related_patents(patent_id, limit=limit)
    return {"patent_id": patent_id, "related": related}

@router.get("/{patent_id:path}", response_model=PatentFrontendFormat)
def get_patent_details(patent_id: str):
    """Fetch full details for an individual Indian patent by application number."""
    patent = patent_service.get_patent_by_id(patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail=f"Patent '{patent_id}' not found in database.")
    return patent
