import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ok", "degraded")
    assert "version" in data

def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_patents"] > 0
    assert "field_counts" in data

def test_search_endpoint():
    payload = {
        "query": "battery anode lithium",
        "top_k": 5,
        "retrieval_method": "hybrid"
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    assert len(data["results"]) > 0
    first_res = data["results"][0]
    assert "patent" in first_res
    assert "score" in first_res
    assert "provenance" in first_res

def test_patent_details():
    # First search to get a valid ID
    search_resp = client.post("/api/search", json={"query": "container", "top_k": 1})
    results = search_resp.json()["results"]
    assert len(results) > 0
    pid = results[0]["patent"]["id"]

    response = client.get(f"/api/patents/{pid}")
    assert response.status_code == 200
    p_data = response.json()
    assert p_data["id"] == pid
    assert p_data["title"] is not None

def test_graph_endpoints():
    sample_resp = client.get("/api/graph/sample")
    assert sample_resp.status_code == 200
    graph_data = sample_resp.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert len(graph_data["nodes"]) > 0

def test_chat_ask():
    chat_payload = {
        "query": "What patents relate to surgical cutting instruments?",
        "history": []
    }
    response = client.post("/api/chat/ask", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "verification" in data
    assert len(data["retrieved_evidence"]) > 0

def test_direct_ask_alias():
    chat_payload = {
        "query": "What patents relate to surgical cutting instruments?",
        "history": []
    }
    response = client.post("/api/ask", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["retrieved_evidence"]) > 0

def test_patent_citations():
    search_resp = client.post("/api/search", json={"query": "battery", "top_k": 1})
    pid = search_resp.json()["results"][0]["patent"]["id"]
    response = client.get(f"/api/patents/{pid}/citations")
    assert response.status_code == 200
    data = response.json()
    assert data["patent_id"] == pid
    assert "citations" in data

