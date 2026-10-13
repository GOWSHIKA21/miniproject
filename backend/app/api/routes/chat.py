from fastapi import APIRouter
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["RAG Chat"])

@router.post("/ask", response_model=ChatResponse)
def ask_patent_question(request: ChatRequest):
    """Answer a natural-language patent question grounded strictly on retrieved InPASS evidence."""
    return rag_service.answer_question(request)
