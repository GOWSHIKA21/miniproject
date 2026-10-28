from pydantic import BaseModel, Field
from typing import List, Optional

class PatentBase(BaseModel):
    patent_id: str = Field(..., description="Canonical patent application number e.g. 10/DEL/2010")
    publication_number: Optional[str] = Field(None, description="Publication journal number e.g. 01/2016")
    title: str = Field(..., description="Title of the invention")
    title_normalized: Optional[str] = Field(None, description="Normalized title")
    field_of_invention: Optional[str] = Field(None, description="Technical field category e.g. CHEMISTRY, ELECTRICAL")
    field_imputed: Optional[bool] = Field(None, description="Whether field was imputed")
    ipo_location: Optional[str] = Field(None, description="IPO branch office e.g. Delhi, Chennai, Mumbai, Kolkata")
    ipo_code: Optional[str] = Field(None, description="IPO office code e.g. DEL, CHE, KOL, MUM")
    application_type: Optional[str] = Field(None, description="Type of patent application e.g. PCT National Phase")
    application_category: Optional[str] = Field(None, description="Application category e.g. Ordinary, Convention, PCT")
    filing_date: Optional[str] = Field(None, description="Filing date in YYYY-MM-DD format")
    publication_date: Optional[str] = Field(None, description="Publication date in YYYY-MM-DD format")
    date_updated: Optional[str] = Field(None, description="Last record update date")
    filing_year: Optional[int] = Field(None, description="Filing year")
    publication_year: Optional[int] = Field(None, description="Publication year")
    pendency_days: Optional[int] = Field(None, description="Pendency duration in days")
    no_of_claims: Optional[int] = Field(None, description="Number of claims")
    no_of_pages: Optional[int] = Field(None, description="Number of pages")
    claims_range: Optional[str] = Field(None, description="Claims range bin e.g. 16-30 claims")
    jurisdiction: str = Field("India", description="Patent jurisdiction")
    source_file: Optional[str] = Field(None, description="Source gazette CSV file name")
    source_url: Optional[str] = Field(None, description="Official portal verification URL")
    search_text: Optional[str] = Field(None, description="Full structured search text")
    no_of_pages_imputed: Optional[int] = Field(None, description="Imputed pages count")
    no_of_claims_imputed: Optional[int] = Field(None, description="Imputed claims count")
    abstract: Optional[str] = Field(None, description="Patent abstract or concise metadata summary")
    description: Optional[str] = Field(None, description="Structured technical scope and description")

class PatentFrontendFormat(BaseModel):
    """
    Comprehensive schema matching frontend expectations in PatentCard and PatentDetails,
    providing all dataset fields in both camelCase and snake_case for complete compatibility.
    """
    id: str
    patentNumber: str
    patent_id: Optional[str] = None
    patentId: Optional[str] = None
    publication_number: Optional[str] = None
    publicationNumber: Optional[str] = None
    
    title: str
    title_normalized: Optional[str] = None
    titleNormalized: Optional[str] = None
    
    filing_date: Optional[str] = None
    filingDate: Optional[str] = None
    publication_date: Optional[str] = None
    publicationDate: Optional[str] = None
    date_updated: Optional[str] = None
    dateUpdated: Optional[str] = None
    filing_year: Optional[int] = None
    filingYear: Optional[int] = None
    publication_year: Optional[int] = None
    publicationYear: Optional[int] = None
    pendency_days: Optional[int] = None
    pendencyDays: Optional[int] = None
    
    field_of_invention: Optional[str] = None
    fieldOfInvention: Optional[str] = None
    field_imputed: Optional[bool] = None
    fieldImputed: Optional[bool] = None
    technology: List[str] = []
    ipc: Optional[str] = None
    
    jurisdiction: str = "India"
    ipo_location: Optional[str] = None
    ipoLocation: Optional[str] = None
    ipo_code: Optional[str] = None
    ipoCode: Optional[str] = None
    patentOffice: str = "India"
    
    application_type: Optional[str] = None
    applicationType: Optional[str] = None
    application_category: Optional[str] = None
    applicationCategory: Optional[str] = None
    
    no_of_pages: Optional[int] = None
    noOfPages: Optional[int] = None
    no_of_claims: Optional[int] = None
    noOfClaims: Optional[int] = None
    claims_range: Optional[str] = None
    claimsRange: Optional[str] = None
    no_of_pages_imputed: Optional[int] = None
    noOfPagesImputed: Optional[int] = None
    no_of_claims_imputed: Optional[int] = None
    noOfClaimsImputed: Optional[int] = None
    
    source_file: Optional[str] = None
    sourceFile: Optional[str] = None
    source_url: Optional[str] = None
    sourceUrl: Optional[str] = None
    search_text: Optional[str] = None
    searchText: Optional[str] = None
    
    relevance: Optional[float] = None
    abstract: Optional[str] = None
    description: Optional[str] = None
    claims: Optional[List[str]] = None
    inventor: Optional[str] = None
    organization: Optional[str] = None
    status: Optional[str] = None
    isSaved: bool = False

class PatentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    patents: List[PatentFrontendFormat]
