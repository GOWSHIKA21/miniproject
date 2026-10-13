from pydantic import BaseModel, Field
from typing import List, Optional

class PatentBase(BaseModel):
    patent_id: str = Field(..., description="Canonical patent application number e.g. 10/DEL/2010")
    publication_number: Optional[str] = Field(None, description="Publication journal number e.g. 01/2016")
    title: str = Field(..., description="Title of the invention")
    field_of_invention: Optional[str] = Field(None, description="Technical field category e.g. CHEMISTRY, ELECTRICAL")
    ipo_location: Optional[str] = Field(None, description="IPO branch office e.g. Delhi, Chennai, Mumbai, Kolkata")
    application_type: Optional[str] = Field(None, description="Type of patent application e.g. PCT NATIONAL PHASE")
    filing_date: Optional[str] = Field(None, description="Filing date in YYYY-MM-DD format")
    publication_date: Optional[str] = Field(None, description="Publication date in YYYY-MM-DD format")
    no_of_claims: Optional[int] = Field(None, description="Number of claims")
    no_of_pages: Optional[int] = Field(None, description="Number of pages")
    jurisdiction: str = Field("India", description="Patent jurisdiction")
    source_url: Optional[str] = Field(None, description="Official portal verification URL")
    abstract: Optional[str] = Field(None, description="Patent abstract or enriched technical summary")

class PatentFrontendFormat(BaseModel):
    """Schema matching the existing frontend's expectation in PatentCard and PatentDetails."""
    id: str
    patentNumber: str
    title: str
    abstract: str
    inventor: str = "Government of India IPO Record"
    organization: str = "Indian Patent Office"
    patentOffice: str = "India"
    ipoLocation: Optional[str] = None
    filingDate: Optional[str] = None
    publicationDate: Optional[str] = None
    technology: List[str] = []
    ipc: Optional[str] = None
    relevance: Optional[float] = None
    status: str = "Granted"
    noOfClaims: Optional[int] = None
    noOfPages: Optional[int] = None
    sourceUrl: Optional[str] = None
    isSaved: bool = False

class PatentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    patents: List[PatentFrontendFormat]
