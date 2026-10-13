import os
import sys
import time
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from typing import List, Dict, Any
from backend.app.retrieval.keyword_search import bm25_retriever
from backend.app.retrieval.vector_search import faiss_retriever
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Representative benchmark queries with expected relevant domains
BENCHMARK_QUERIES = [
    {"query": "lithium ion battery anode active material", "expected_domain": "ELECTRICAL"},
    {"query": "surgical robotic arm cutting instrument", "expected_domain": "BIOMEDICAL"},
    {"query": "wireless communication antenna transmission", "expected_domain": "COMMUNICATION"},
    {"query": "pharmaceutical crystalline composition container", "expected_domain": "CHEMISTRY"},
    {"query": "automotive engine hydraulic braking piston", "expected_domain": "MECHANICAL"},
    {"query": "solar photovoltaic cell panel", "expected_domain": "ELECTRICAL"},
    {"query": "neural network image classification computer vision", "expected_domain": "COMPUTER"},
    {"query": "wastewater filtration treatment membrane", "expected_domain": "CHEMISTRY"},
]

def evaluate_retrievers(k: int = 5) -> Dict[str, Any]:
    """Evaluate and benchmark BM25 vs Vector vs Hybrid retrieval engines."""
    results = {
        "k": k,
        "bm25": {"precision_at_k": 0.0, "avg_latency_ms": 0.0},
        "vector": {"precision_at_k": 0.0, "avg_latency_ms": 0.0},
        "hybrid": {"precision_at_k": 0.0, "avg_latency_ms": 0.0},
    }

    n_queries = len(BENCHMARK_QUERIES)

    for mode in ["bm25", "vector", "hybrid"]:
        total_precision = 0.0
        total_time_ms = 0.0

        for item in BENCHMARK_QUERIES:
            q = item["query"]
            domain = item["expected_domain"]

            t0 = time.time()
            search_res = hybrid_retrieval_engine.search(query=q, top_k=k, retrieval_method=mode)
            elapsed_ms = (time.time() - t0) * 1000

            total_time_ms += elapsed_ms
            retrieved = search_res.results

            # Relevant if field matches or relevant concepts present
            relevant_count = sum(
                1 for r in retrieved
                if domain in str(r.patent.ipc).upper() or domain in str(r.patent.technology).upper()
            )
            precision = relevant_count / max(len(retrieved), 1)
            total_precision += precision

        results[mode]["precision_at_k"] = round(total_precision / n_queries, 4)
        results[mode]["avg_latency_ms"] = round(total_time_ms / n_queries, 2)

    logger.info("Evaluation Complete. Results:")
    logger.info(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    rep = evaluate_retrievers(k=5)
    print("\n=== RETRIEVAL BENCHMARK REPORT (Precision@5 & Latency) ===")
    for mode, data in rep.items():
        if mode != "k":
            print(f"[{mode.upper():>6}] Precision@5: {data['precision_at_k'] * 100:.1f}% | Avg Latency: {data['avg_latency_ms']:.1f}ms")
