import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.structured_query_service import structured_query_service

client = TestClient(app)

def test_intent_detection_location_counts():
    q1 = "In IPO_LOCATION, how many patents are there in Delhi?"
    a1 = structured_query_service.analyze_intent(q1)
    assert a1["is_structured"] is True
    assert a1["intent"] == "COUNT_LOCATION"
    assert a1["value"] == "Delhi"

    q2 = "How many patents have IPO_LOCATION Chennai?"
    a2 = structured_query_service.analyze_intent(q2)
    assert a2["is_structured"] is True
    assert a2["intent"] == "COUNT_LOCATION"
    assert a2["value"] == "Chennai"

    q3 = "Count patents for each IPO_LOCATION."
    a3 = structured_query_service.analyze_intent(q3)
    assert a3["is_structured"] is True
    assert a3["intent"] == "GROUP_BY_LOCATION"

    q4 = "Show the first 10 patents whose IPO_LOCATION is Delhi."
    a4 = structured_query_service.analyze_intent(q4)
    assert a4["is_structured"] is True
    assert a4["intent"] == "SHOW_FILTERED_PATENTS"
    assert a4["value"] == "Delhi"
    assert a4["limit"] == 10

def test_delhi_count_query_exactness():
    res = structured_query_service.execute_structured_query({
        "is_structured": True,
        "intent": "COUNT_LOCATION",
        "field": "ipo_location",
        "value": "Delhi"
    })
    assert res.total_count == 13186
    assert res.total_dataset_size == 33825
    assert len(res.sample_patents) > 0

def test_chennai_count_query_exactness():
    res = structured_query_service.execute_structured_query({
        "is_structured": True,
        "intent": "COUNT_LOCATION",
        "field": "ipo_location",
        "value": "Chennai"
    })
    assert res.total_count == 10251

def test_group_by_location_breakdown():
    res = structured_query_service.execute_structured_query({
        "is_structured": True,
        "intent": "GROUP_BY_LOCATION",
        "field": "ipo_location"
    })
    assert res.breakdown is not None
    assert res.breakdown["Delhi"] == 13186
    assert res.breakdown["Chennai"] == 10251
    assert res.breakdown["Kolkata"] == 6563
    assert res.breakdown["Mumbai"] == 3825

def test_api_chat_ask_structured_delhi_count():
    response = client.post("/api/chat/ask", json={
        "query": "In IPO_LOCATION, how many patents are there in Delhi?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "13,186" in data["answer"] or "13186" in data["answer"]
    assert len(data["citations"]) > 0
    assert len(data["retrieved_evidence"]) > 0

def test_api_chat_ask_show_first_10_delhi():
    response = client.post("/api/chat/ask", json={
        "query": "Show the first 10 patents whose IPO_LOCATION is Delhi."
    })
    assert response.status_code == 200
    data = response.json()
    assert "13,186" in data["answer"] or "13186" in data["answer"]
    assert len(data["citations"]) == 10
