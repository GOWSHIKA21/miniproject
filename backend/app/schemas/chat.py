from pydantic import BaseModel, Field
from typing import List, Optional
from backend.app.schemas.search import SearchResultItem

class ChatCitation(BaseModel):
    patent_id: str
    title: str
    field_of_invention: Optional[str] = None
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    verified: bool = True

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question about Indian patents")
    history: Optional[List[dict]] = None
    filters: Optional[dict] = None

class VerificationReport(BaseModel):
    total_citations_claimed: int
    citations_verified: int
    grounding_ratio: float
    all_citations_valid: bool
    unverified_citations: List[str] = []

class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: List[ChatCitation]
    retrieved_evidence: List[SearchResultItem]
    verification: VerificationReport
    llm_provider: str
    trace_id: Optional[str] = None
    debug_info: Optional[dict] = None
