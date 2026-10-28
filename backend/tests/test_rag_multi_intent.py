import pytest
from backend.app.schemas.chat import ChatRequest
from backend.app.services.rag_service import rag_service

def test_specific_patent_inquiry():
    req = ChatRequest(query="Explain patent 10/DEL/2010 and its technical scope", history=[])
    res = rag_service.answer_question(req)
    assert res.answer is not None
    assert "10/DEL/2010" in res.answer
    assert len(res.citations) > 0
    # The target patent must be cited
    assert any(c.patent_id == "10/DEL/2010" for c in res.citations)

def test_patent_comparison():
    req = ChatRequest(query="Compare 10/DEL/2010 and 2049/DEL/2007", history=[])
    res = rag_service.answer_question(req)
    assert res.answer is not None
    assert "10/DEL/2010" in res.answer
    assert "2049/DEL/2007" in res.answer
    # Both patents should be in citations
    c_ids = [c.patent_id for c in res.citations]
    assert "10/DEL/2010" in c_ids
    assert "2049/DEL/2007" in c_ids

def test_conversational_followup():
    history = [
        {"role": "user", "content": "Show me patents related to agriculture and pharma."},
        {"role": "assistant", "content": "Here are two relevant records: 1. [10/DEL/2010] in pharma, and 2. [2049/DEL/2007] in agriculture."}
    ]
    req = ChatRequest(query="Explain the second patent in simple language", history=history)
    res = rag_service.answer_question(req)
    assert res.answer is not None
    assert "2049/DEL/2007" in res.answer
    c_ids = [c.patent_id for c in res.citations]
    assert "2049/DEL/2007" in c_ids
