import os
import uuid
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from backend.app.core.config import settings
from backend.app.database.neo4j_client import Neo4jClient, mask_neo4j_uri
from backend.app.database.qdrant_client import QdrantDatabaseClient, patent_id_to_uuid, mask_qdrant_url
from backend.app.retrieval.vector_search import CloudVectorRetriever
from backend.app.graph.graph_queries import PatentGraphEngine


def test_neo4j_aura_config_and_masking():
    """Verify Neo4j Aura configuration variables and URI masking."""
    assert hasattr(settings, "NEO4J_URI")
    assert hasattr(settings, "NEO4J_USERNAME")
    assert hasattr(settings, "NEO4J_DATABASE")

    masked = mask_neo4j_uri("neo4j+s://neo4j:superSecret123@abc1234.databases.neo4j.io")
    assert "superSecret123" not in masked
    assert "****" in masked
    assert "neo4j+s://" in masked


def test_qdrant_cloud_config_and_masking():
    """Verify Qdrant Cloud configuration variables and URL masking."""
    assert hasattr(settings, "QDRANT_URL")
    assert hasattr(settings, "QDRANT_API_KEY")
    assert hasattr(settings, "QDRANT_COLLECTION")
    assert settings.QDRANT_COLLECTION == "patent_embeddings"

    masked = mask_qdrant_url("https://user:apiKeySecret999@my-cluster.qdrant.io:6333")
    assert "apiKeySecret999" not in masked
    assert "****" in masked


def test_patent_id_to_uuid_stability():
    """Verify deterministic UUIDv5 generation for idempotent Qdrant points."""
    pid1 = "10/DEL/2010"
    uid1 = patent_id_to_uuid(pid1)
    uid2 = patent_id_to_uuid(pid1)
    assert uid1 == uid2, "Same patent_id must always produce identical UUIDv5 point ID"

    # Must be valid UUID format
    parsed = uuid.UUID(uid1)
    assert parsed.version == 5

    # Different patent produces different UUID
    uid3 = patent_id_to_uuid("1005/MUMNP/2007")
    assert uid1 != uid3


def test_neo4j_client_offline_fallback():
    """Verify Neo4jClient handles connection failure without crashing and marks connected=False."""
    client = Neo4jClient(uri="neo4j+s://invalid-host-aura.databases.neo4j.io", user="neo4j", password="dummy")
    assert client.connected is False
    assert client.driver is None
    # run_query returns empty list gracefully
    res = client.run_query("MATCH (n) RETURN n")
    assert res == []


def test_qdrant_client_offline_fallback():
    """Verify QdrantDatabaseClient handles offline cluster gracefully without crashing."""
    client = QdrantDatabaseClient(url="https://invalid-qdrant-host.cloud.qdrant.io:6333", api_key="dummy")
    assert client.connected is False
    stats = client.get_stats()
    assert stats["connected"] is False
    # search returns empty list without raising exception
    dummy_vec = np.zeros(384, dtype=np.float32)
    results = client.search(dummy_vec, top_k=5)
    assert results == []


def test_vector_retriever_fallback_to_faiss():
    """Verify CloudVectorRetriever seamlessly searches local FAISS when Qdrant Cloud is offline."""
    retriever = CloudVectorRetriever()
    # Execute query
    results = retriever.search("solar power cell", top_k=3)
    assert isinstance(results, list)
    if retriever.index and retriever.index.ntotal > 0:
        assert len(results) > 0
        assert "patent_id" in results[0]
        assert "score" in results[0]


def test_patent_graph_engine_fallback():
    """Verify PatentGraphEngine seamlessly uses embedded NetworkX when Neo4j Aura is offline."""
    engine = PatentGraphEngine()
    # Sample subgraph
    subgraph = engine.get_patent_subgraph("1427/MUMNP/2010")
    assert "nodes" in subgraph
    assert "edges" in subgraph
    assert len(subgraph["nodes"]) > 0

    # Related patents
    related = engine.get_related_patents("1427/MUMNP/2010", limit=3)
    assert isinstance(related, list)


def test_qdrant_mock_search_flow():
    """Mock Qdrant client to verify vector search and result formatting."""
    client = QdrantDatabaseClient()
    client.connected = True
    client.client = MagicMock()

    # Mock hit object
    mock_hit = MagicMock()
    mock_hit.score = 0.895
    mock_hit.payload = {
        "patent_id": "10/DEL/2010",
        "title": "PRODUCTION OF A PHARMACEUTICAL CONTAINER",
        "field_of_invention": "CHEMISTRY"
    }

    mock_resp = MagicMock()
    mock_resp.points = [mock_hit]
    client.client.query_points.return_value = mock_resp

    test_vec = np.random.rand(384).astype(np.float32)
    results = client.search(test_vec, top_k=1)

    assert len(results) == 1
    assert results[0]["patent_id"] == "10/DEL/2010"
    assert results[0]["score"] == 0.895
    assert results[0]["retriever"] == "qdrant_cloud"
