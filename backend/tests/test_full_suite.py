import pytest
import os
import json
import pandas as pd
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.database.mongodb import mongo_client
from backend.app.retrieval.keyword_search import bm25_retriever
from backend.app.retrieval.vector_search import faiss_retriever
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine
from backend.app.graph.graph_queries import graph_engine
from backend.app.services.patent_service import patent_service
from backend.app.services.rag_service import rag_service
from backend.app.schemas.chat import ChatRequest
from backend.app.schemas.search import SearchFilters

client = TestClient(app)

# ---------------------------------------------------------
# 1. DATASET INTEGRITY & ISOLATION TESTS
# ---------------------------------------------------------
class TestDataIntegrity:
    def test_review_dataset_file_exists(self):
        assert os.path.exists(settings.CLEANED_DATA_PATH), f"Review dataset missing at {settings.CLEANED_DATA_PATH}"

    def test_review_dataset_counts_and_years(self):
        df = pd.read_parquet(settings.CLEANED_DATA_PATH)
        assert len(df) == 33825, f"Expected 33,825 total records, got {len(df)}"

        # Verify publication years
        pub_years = pd.to_datetime(df["publication_date"]).dt.year.value_counts().to_dict()
        assert set(pub_years.keys()) == {2016, 2017, 2018}, f"Unexpected years present: {pub_years.keys()}"
        assert pub_years[2016] == 8064, f"Expected 8,064 for 2016, got {pub_years[2016]}"
        assert pub_years[2017] == 12306, f"Expected 12,306 for 2017, got {pub_years[2017]}"
        assert pub_years[2018] == 13455, f"Expected 13,455 for 2018, got {pub_years[2018]}"

        # Confirm no 2019-2023 records
        for y in (2019, 2020, 2021, 2022, 2023):
            assert y not in pub_years, f"Found unexpected record year {y} in review dataset!"

    def test_no_duplicate_patent_ids(self):
        df = pd.read_parquet(settings.CLEANED_DATA_PATH)
        dup_count = df.duplicated(subset=["patent_id"]).sum()
        assert dup_count == 0, f"Found {dup_count} duplicate patent IDs in review dataset"

    def test_original_dataset_files_preserved(self):
        dataset_dir = "dataset"
        for y in range(2016, 2024):
            expected_csv = os.path.join(dataset_dir, f"application_details_granted_{y}.csv")
            assert os.path.exists(expected_csv), f"Original CSV missing: {expected_csv}"

# ---------------------------------------------------------
# 2. MONGODB INTEGRATION TESTS
# ---------------------------------------------------------
class TestMongoDB:
    def test_mongodb_connection_and_collection(self):
        assert mongo_client.connected, "MongoDB should be connected locally"
        assert mongo_client.collection_name == "patents_2016_2018"

    def test_mongodb_record_counts(self):
        coll = mongo_client.db[mongo_client.collection_name]
        total_docs = coll.count_documents({})
        assert total_docs == 33825, f"Expected 33,825 documents in MongoDB, found {total_docs}"

    def test_mongodb_sample_lookup(self):
        doc = mongo_client.get_patent("10/DEL/2010")
        assert doc is not None, "Failed to retrieve sample patent 10/DEL/2010 from MongoDB"
        assert "PHARMACEUTICAL CONTAINER" in doc["title"].upper()
        assert doc["publication_date"] == "2016-01-01"

    def test_mongodb_idempotent_insert_no_duplicates(self):
        # Repeated import should NOT add duplicate records
        count_before = mongo_client.db[mongo_client.collection_name].count_documents({})
        re_imported = mongo_client.insert_patents_from_parquet()
        count_after = mongo_client.db[mongo_client.collection_name].count_documents({})
        assert count_before == count_after == 33825, "MongoDB insert resulted in duplicated records"

# ---------------------------------------------------------
# 3. RETRIEVAL & INDEX INTEGRATION TESTS
# ---------------------------------------------------------
class TestRetrieval:
    def test_faiss_index_integrity(self):
        assert faiss_retriever.index is not None
        assert faiss_retriever.index.ntotal == 33825, f"FAISS index has {faiss_retriever.index.ntotal} vectors, expected 33,825"
        assert len(faiss_retriever.index_to_patent_id) == 33825

    def test_bm25_index_integrity(self):
        assert bm25_retriever.bm25 is not None
        assert len(bm25_retriever.patent_ids) == 33825, f"BM25 index has {len(bm25_retriever.patent_ids)} docs, expected 33,825"

    def test_vector_search_results(self):
        res = faiss_retriever.search("lithium ion battery cathode anode", top_k=5)
        assert len(res) == 5
        assert all("patent_id" in r and "score" in r for r in res)
        # Verify resolution to MongoDB/Parquet
        first_pid = res[0]["patent_id"]
        patent = patent_service.get_patent_by_id(first_pid)
        assert patent is not None
        assert patent.id == first_pid

    def test_bm25_keyword_search_results(self):
        res = bm25_retriever.search("pharmaceutical container melt", top_k=5)
        assert len(res) > 0
        assert any(r["patent_id"] == "10/DEL/2010" for r in res)

    def test_hybrid_search_with_filtering(self):
        # Search with field filter
        filters = SearchFilters(field_of_invention="CHEMISTRY", ipo_location="Delhi")
        res = hybrid_retrieval_engine.search("pharmaceutical melt", filters=filters, top_k=5)
        assert res.total_found > 0
        for item in res.results:
            assert "CHEMISTRY" in item.patent.ipc.upper()
            assert "Delhi" in item.patent.ipoLocation

# ---------------------------------------------------------
# 4. KNOWLEDGE GRAPH TESTS
# ---------------------------------------------------------
class TestKnowledgeGraph:
    def test_graph_loaded_and_nodes_count(self):
        assert graph_engine.G is not None
        assert graph_engine.G.number_of_nodes() >= 40000
        assert graph_engine.G.number_of_edges() >= 100000

    def test_global_sample_structure(self):
        sample = graph_engine.get_global_sample(max_patents=6)
        assert "nodes" in sample and "edges" in sample
        assert len(sample["nodes"]) > 0
        assert len(sample["edges"]) > 0

    def test_patent_subgraph_and_related(self):
        subgraph = graph_engine.get_patent_subgraph("10/DEL/2010")
        assert len(subgraph["nodes"]) >= 3
        related = graph_engine.get_related_patents("10/DEL/2010", limit=4)
        assert len(related) > 0
        assert all("patent_id" in r and "title" in r for r in related)

# ---------------------------------------------------------
# 5. BACKEND API ENDPOINTS TESTS
# ---------------------------------------------------------
class TestAPIEndpoints:
    def test_health_endpoint_details(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["components"]["mongodb"]["connected"] is True
        assert data["components"]["mongodb"]["total_documents"] == 33825
        assert data["components"]["faiss_vector_index"]["total_vectors"] == 33825
        assert data["components"]["bm25_keyword_index"]["total_documents"] == 33825
        assert data["components"]["knowledge_graph"]["loaded"] is True

    def test_stats_endpoint(self):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_patents"] == 33825
        assert "CHEMISTRY" in data["field_counts"]
        assert "Delhi" in data["location_counts"]

    def test_patent_details_with_slashes(self):
        # Indian patent ID containing slashes
        pid = "10/DEL/2010"
        resp = client.get(f"/api/patents/{pid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pid
        assert "PHARMACEUTICAL" in data["title"].upper()

    def test_nonexistent_patent_details(self):
        resp = client.get("/api/patents/999999/INVALID/9999")
        assert resp.status_code == 404

    def test_search_endpoint_query(self):
        payload = {
            "query": "wind turbine generator rotor",
            "top_k": 4,
            "retrieval_method": "hybrid"
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 4
        assert data["results"][0]["patent"]["id"] is not None

    def test_empty_search_query(self):
        payload = {
            "query": "xyznonexistentpatentword999",
            "top_k": 5,
            "retrieval_method": "bm25"
        }
        resp = client.post("/api/search", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 0
        assert data["results"] == []

    def test_chat_ask_and_alias(self):
        payload = {
            "query": "What patents relate to surgical fastening and cutting instruments?",
            "history": []
        }
        # /api/chat/ask
        resp = client.post("/api/chat/ask", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["citations"]) > 0
        assert len(data["retrieved_evidence"]) > 0

        # /api/ask direct alias
        alias_resp = client.post("/api/ask", json=payload)
        assert alias_resp.status_code == 200
        alias_data = alias_resp.json()
        assert "answer" in alias_data
        assert len(alias_data["citations"]) > 0

    def test_graph_endpoints(self):
        # Global sample
        s_resp = client.get("/api/graph/sample")
        assert s_resp.status_code == 200
        assert len(s_resp.json()["nodes"]) > 0

        # Specific patent neighborhood
        p_resp = client.get("/api/graph/patent/10/DEL/2010")
        assert p_resp.status_code == 200
        assert len(p_resp.json()["nodes"]) > 0
