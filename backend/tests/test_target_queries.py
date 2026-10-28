import pytest
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine

TARGET_QUERIES = [
    ("Agriculture", 5),
    ("Farming", 5),
    ("Crop cultivation", 3),
    ("Agricultural machinery", 3),
    ("Irrigation systems", 3),
    ("Plant disease detection", 3),
    ("Renewable energy", 5),
    ("Machine learning", 3),
    ("10/DEL/2010", 1),
    ("01/2016", 1),
    ("CONTROLLED ENVIRONMENT AGRICULTURE OR HYDROPONICS AGRICULTURE", 1),
    ("Which patents relate to solar powered irrigation systems?", 1)
]

@pytest.mark.parametrize("query,min_expected", TARGET_QUERIES)
def test_target_search_queries(query, min_expected):
    res = hybrid_retrieval_engine.search(query, page_size=10)
    assert res.total_found >= min_expected, f"Query '{query}' returned {res.total_found} < {min_expected}"
    assert len(res.results) > 0, f"Query '{query}' had empty results slice"
    
    # Test specific expectations
    if query == "10/DEL/2010":
        # Must be rank 1
        top = res.results[0].patent
        assert "10/DEL/2010" in (top.patent_id or top.patentNumber)
        assert res.results[0].score == 1.0

    if query == "CONTROLLED ENVIRONMENT AGRICULTURE OR HYDROPONICS AGRICULTURE":
        # Must match title in top 3
        top_titles = [r.patent.title.upper() for r in res.results[:3]]
        assert any("CONTROLLED ENVIRONMENT AGRICULTURE" in t for t in top_titles)
