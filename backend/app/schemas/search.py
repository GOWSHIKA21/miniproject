from pydantic import BaseModel, Field
from typing import List, Optional
from backend.app.schemas.patent import PatentFrontendFormat

class SearchFilters(BaseModel):
    field_of_invention: Optional[str] = None
    ipo_location: Optional[str] = None
    application_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query or keywords")
    filters: Optional[SearchFilters] = None
    top_k: int = Field(20, ge=1, le=100)
    retrieval_method: str = Field("hybrid", description="Retrieval engine mode: 'hybrid', 'vector', 'bm25'")

class SearchProvenance(BaseModel):
    bm25_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    rrf_score: Optional[float] = None
    similarity_score: Optional[float] = None

class SearchResultItem(BaseModel):
    patent: PatentFrontendFormat
    score: float
    retrieval_method: str
    provenance: Optional[SearchProvenance] = None
    match_evidence: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    retrieval_method: str
    total_found: int
    results: List[SearchResultItem]
