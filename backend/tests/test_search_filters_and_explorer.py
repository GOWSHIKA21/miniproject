import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

class TestSearchFiltersAndExplorer:
    # -------------------------------------------------------------
    # Test 1: Priority Date Filter (Year Only: 2016–2023)
    # -------------------------------------------------------------
    def test_filter_priority_year_2018(self):
        payload = {
            "query": "",
            "filters": {"priority_date": "2018"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 21240, f"Expected 21,240 patents for priority year 2018, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            p = item["patent"]
            fil = str(p.get("filingDate") or "")
            pub = str(p.get("publicationDate") or "")
            assert "2018" in fil or "2018" in pub, f"Patent {p['id']} does not match year 2018: fil={fil}, pub={pub}"

    def test_filter_priority_year_2020(self):
        payload = {
            "query": "",
            "filters": {"priority_date": "2020"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 28380, f"Expected 28,380 patents for priority year 2020, got {data['total_found']}"

    def test_filter_priority_year_non_existent(self):
        payload = {
            "query": "",
            "filters": {"priority_date": "1900"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0
        assert data["results"] == []

    # -------------------------------------------------------------
    # Test 2: Technology Domain Filters (Exact Matching)
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
        assert data["total_found"] == 38871, f"Expected 38,871 Chemistry patents, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert item["patent"]["ipc"].upper() == "CHEMISTRY"

    def test_filter_technology_domain_biochemistry(self):
        payload = {
            "query": "",
            "filters": {"field_of_invention": "Biochemistry"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 2055, f"Expected 2,055 Biochemistry patents, got {data['total_found']}"
        for item in data["results"]:
            assert item["patent"]["ipc"].upper() == "BIOCHEMISTRY"

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
        assert data["total_found"] == 57345, f"Expected 57,345 Delhi patents, got {data['total_found']}"
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
        assert data["total_found"] == 167, f"Expected 167 patents for 2016-01-01, got {data['total_found']}"
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
        assert data["total_found"] == 1642, f"Expected 1,642 patents for Jan 2017, got {data['total_found']}"

    # -------------------------------------------------------------
    # Test 3: Combined filters
    # -------------------------------------------------------------
    def test_combined_filters_chemistry_and_delhi(self):
        payload = {
            "query": "",
            "filters": {
                "field_of_invention": "Chemistry",
                "ipo_location": "Delhi"
            },
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 18231, f"Expected 18,231 Chemistry + Delhi patents, got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert item["patent"]["ipc"].upper() == "CHEMISTRY"
            assert "Delhi" in item["patent"]["ipoLocation"]

    # -------------------------------------------------------------
    # Test 4: Technology Explorer stats and parity
    # -------------------------------------------------------------
    def test_technology_explorer_count_parity(self):
        stats_resp = client.get("/api/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert "field_counts" in stats
        chemistry_explorer_count = stats["field_counts"]["CHEMISTRY"]
        assert chemistry_explorer_count == 38871

        search_resp = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Chemistry"},
            "page": 1,
            "page_size": 25
        })
        assert search_resp.status_code == 200
        search_data = search_resp.json()

        assert search_data["total_found"] == chemistry_explorer_count == 38871
        assert search_data["total_matching"] == 38871
        assert search_data["page"] == 1
        assert search_data["page_size"] == 25
        assert len(search_data["results"]) == 25

        # Navigate to Page 2
        page2_resp = client.post("/api/search", json={
            "query": "",
            "filters": {"field_of_invention": "Chemistry"},
            "page": 2,
            "page_size": 25
        })
        assert page2_resp.status_code == 200
        page2_data = page2_resp.json()
        assert page2_data["total_found"] == 38871
        assert page2_data["page"] == 2
        assert len(page2_data["results"]) == 25

        p1_ids = [r["patent"]["id"] for r in search_data["results"]]
        p2_ids = [r["patent"]["id"] for r in page2_data["results"]]
        assert set(p1_ids).isdisjoint(set(p2_ids)), "Page 1 and Page 2 must not share patent IDs!"

    def test_direct_get_patents_endpoint(self):
        resp = client.get("/api/patents?field=Chemistry&page=1&page_size=25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 38871
        assert len(data["results"]) == 25
        assert data["results"][0]["patent"]["ipc"] == "CHEMISTRY"

    # -------------------------------------------------------------
    # Test 5: Edge cases
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

    def test_empty_filters_returns_all_patents(self):
        payload = {
            "query": "",
            "filters": {},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 151438
        assert len(data["results"]) == 25

    # -------------------------------------------------------------
    # Test 6: Word Boundary and Unwanted Term Tests (Tata, Inventor, Organisation)
    # -------------------------------------------------------------
    def test_query_tata_returns_zero_patents(self):
        """Searching 'tata' must NOT match substrings like 'rotatable' or 'ortataxel'."""
        payload = {
            "query": "tata",
            "filters": {},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0, f"Expected 0 patents for 'tata', got {data['total_found']}"
        assert data["results"] == []

    def test_filter_organization_tata_returns_zero_patents(self):
        """Filtering organization 'tata' must return 0 patents since TATA is not in dataset."""
        payload = {
            "query": "",
            "filters": {"organization": "tata"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0, f"Expected 0 patents for org 'tata', got {data['total_found']}"
        assert data["results"] == []

    def test_filter_inventor_tata_returns_zero_patents(self):
        """Filtering inventor 'tata' must return 0 patents."""
        payload = {
            "query": "",
            "filters": {"inventor": "tata"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0, f"Expected 0 patents for inv 'tata', got {data['total_found']}"
        assert data["results"] == []

    def test_filter_organization_delhi_returns_delhi_patents(self):
        """Filtering organization 'Delhi' must return all 57,345 Delhi branch patents."""
        payload = {
            "query": "",
            "filters": {"organization": "Delhi"},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 57345, f"Expected 57,345 patents for org 'Delhi', got {data['total_found']}"
        assert len(data["results"]) == 25
        for item in data["results"]:
            assert "Delhi" in item["patent"]["ipoLocation"]

    def test_query_rotatable_returns_actual_rotatable_patents(self):
        """Searching 'rotatable' must match genuine rotatable/rotatory patents, while 'tata' returns 0."""
        payload = {
            "query": "rotatable",
            "filters": {},
            "page": 1,
            "page_size": 25
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] > 0, f"Expected >0 patents for 'rotatable', got {data['total_found']}"
        assert len(data["results"]) > 0
        assert data["results"][0]["score"] > 0.0
