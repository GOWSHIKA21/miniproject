import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

class TestSearchFiltersAndExplorer:
    # -------------------------------------------------------------
    # Test 1: Individual filters
    # -------------------------------------------------------------
    def test_filter_technology_domain_chemistry(self):
        payload = {
            "query": "",
            "filters": {"field_of_invention": "Chemistry"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 11059, f"Expected 11,059 Chemistry patents, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert "CHEMISTRY" in item["patent"]["ipc"].upper()

    def test_filter_patent_office_delhi(self):
        payload = {
            "query": "",
            "filters": {"ipo_location": "Delhi"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 13186, f"Expected 13,186 Delhi patents, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert "Delhi" in item["patent"]["ipoLocation"]

    def test_filter_data_filter_exact_date(self):
        payload = {
            "query": "",
            "filters": {"exact_date": "2016-01-01"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 140, f"Expected 140 patents for 2016-01-01, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            p = item["patent"]
            assert p["publicationDate"] == "2016-01-01" or p["filingDate"] == "2016-01-01"

    def test_filter_data_filter_date_range(self):
        payload = {
            "query": "",
            "filters": {"date_from": "2017-01-01", "date_to": "2017-01-31"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 802, f"Expected 802 patents for Jan 2017, got {data['total_found']}"

    def test_filter_inventor(self):
        # Testing synthetic/schema inventor filter
        payload = {
            "query": "",
            "filters": {"inventor": "Government"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 33825
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert "Government" in item["patent"]["inventor"]

    def test_filter_organisation(self):
        payload = {
            "query": "",
            "filters": {"organization": "Delhi"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 13186
        assert len(data["results"]) == 25

    # -------------------------------------------------------------
    # Test 2: Combined filters
    # -------------------------------------------------------------
    def test_combined_filters_chemistry_and_delhi(self):
        payload = {
            "query": "",
            "filters": {
                "field_of_invention": "Chemistry",
                "ipo_location": "Delhi",
                "organization": "Delhi"
            },
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 5216, f"Expected 5,216 Chemistry + Delhi patents, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert "CHEMISTRY" in item["patent"]["ipc"].upper()
            assert "Delhi" in item["patent"]["ipoLocation"]

    # -------------------------------------------------------------
    # Test 3: Technology Explorer navigation & pagination
    # -------------------------------------------------------------
    def test_technology_explorer_count_parity(self):
        # 1. Stats endpoint (used by Explorer page)
        stats_resp = client.get("/api/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        chemistry_explorer_count = stats["field_counts"]["CHEMISTRY"]
        assert chemistry_explorer_count == 11059

        # 2. Search endpoint for Chemistry
        search_resp = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Chemistry"},
            "page": 1,
            "page_size": 25
        })
        assert search_resp.status_code == 200
        search_data = search_resp.json()

        # 3. Confirm parity
        assert search_data["total_found"] == chemistry_explorer_count == 11059
        assert search_data["total_matching"] == 11059
        assert search_data["page"] == 1
        assert search_data["page_size"] == 25
        assert search_data["total_pages"] == 443
        assert len(search_data["results"]) == 25

        # 4. Navigate to Page 2
        page2_resp = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Chemistry"},
            "page": 2,
            "page_size": 25
        })
        assert page2_resp.status_code == 200
        page2_data = page2_resp.json()
        assert page2_data["total_found"] == 11059
        assert page2_data["page"] == 2
        assert len(page2_data["results"]) == 25

        # 5. Verify different records on page 1 vs page 2
        p1_ids = [r["patent"]["id"] for r in search_data["results"]]
        p2_ids = [r["patent"]["id"] for r in page2_data["results"]]
        assert set(p1_ids).isdisjoint(set(p2_ids)), "Page 1 and Page 2 should not share patent IDs!"

    def test_direct_get_patents_endpoint(self):
        resp = client.get("/api/patents?field=Chemistry&page=1&page_size=25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 11059
        assert len(data["results"]) == 25
        assert data["results"][0]["patent"]["ipc"] == "CHEMISTRY"

    # -------------------------------------------------------------
    # Test 4: Edge cases
    # -------------------------------------------------------------
    def test_no_matching_patents(self):
        payload = {
            "query": "",
            "filters": {"field_of_invention": "NON_EXISTENT_DOMAIN_XYZ"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0
        assert data["total_pages"] == 1
        assert data["results"] == []

    def test_empty_filters(self):
        payload = {
            "query": "",
            "filters": {},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 33825
        assert len(data["results"]) == 25

    def test_switching_technology_domains(self):
        # Electrical
        resp_elec = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Electrical"},
            "page": 1,
            "page_size": 25
        })
        assert resp_elec.status_code == 200
        data_elec = resp_elec.json()
        assert data_elec["total_found"] > 0
        assert all("ELECTRICAL" in r["patent"]["ipc"].upper() for r in data_elec["results"])

        # Mechanical
        resp_mech = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Mechanical"},
            "page": 1,
            "page_size": 25
        })
        assert resp_mech.status_code == 200
        data_mech = resp_mech.json()
        assert data_mech["total_found"] > 0
        assert all("MECHANICAL" in r["patent"]["ipc"].upper() for r in data_mech["results"])
