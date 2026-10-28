import pytest
try:
    import faiss
except Exception:
    pass
from backend.app.services.patent_service import patent_service

def test_related_inventions_semantic_accuracy():
    # 1. Agriculture patent
    agri_rel = patent_service.get_related_inventions("2049/DEL/2007", limit=5, min_similarity=0.40)
    assert len(agri_rel) > 0
    agri_pids = [r["patent_id"] for r in agri_rel]
    assert "2049/DEL/2007" not in agri_pids  # Self must be excluded
    for r in agri_rel:
        assert r["similarity_score"] >= 0.40
        assert r["similarity_pct"] >= 40
        assert "match_reason" in r
        assert len(r["match_reason"]) > 10

    # 2. Pharma patent
    pharma_rel = patent_service.get_related_inventions("10/DEL/2010", limit=5, min_similarity=0.40)
    assert len(pharma_rel) > 0
    pharma_pids = [r["patent_id"] for r in pharma_rel]
    assert "10/DEL/2010" not in pharma_pids  # Self must be excluded
    for r in pharma_rel:
        assert r["similarity_score"] >= 0.40
        assert r["similarity_pct"] >= 40
        assert "match_reason" in r

    # 3. Recommendations must change across different domains (Agriculture vs Pharma)
    assert set(agri_pids) != set(pharma_pids)
    overlap = set(agri_pids).intersection(set(pharma_pids))
    assert len(overlap) == 0  # Zero overlap between agriculture and pharma recommendations

def test_related_inventions_empty_state():
    # Query with impossible similarity threshold (0.999) must return empty list honestly
    rel = patent_service.get_related_inventions("2049/DEL/2007", limit=5, min_similarity=0.999)
    assert rel == []

    # Non-existent patent must return empty list
    rel_nonexistent = patent_service.get_related_inventions("NON_EXISTENT_ID_99999", limit=5)
    assert rel_nonexistent == []
