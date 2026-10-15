from pydantic import BaseModel, Field
from typing import List, Optional
from backend.app.schemas.patent import PatentFrontendFormat

class SearchFilters(BaseModel):
    field_of_invention: Optional[str] = None
    fields_of_invention: Optional[List[str]] = None
    ipo_location: Optional[str] = None
    inventor: Optional[str] = None
    organization: Optional[str] = None
    application_type: Optional[str] = None
    date_type: Optional[str] = None
    priority_date: Optional[str] = None
    exact_date: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field("", description="Natural language search query or keywords")
    filters: Optional[SearchFilters] = None
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(25, ge=1, le=100, description="Number of results per page")
    top_k: Optional[int] = Field(None, ge=1, le=100, description="Alias for page_size")
    sort_by: Optional[str] = Field("relevance", description="Sort order: relevance, newest, oldest")
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
    total_matching: int = 0
    page: int = 1
    page_size: int = 25
    total_pages: int = 1
    results: List[SearchResultItem]
