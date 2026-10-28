"""
RAG Request Logger — structured per-request logging for the RAG pipeline.

Writes to a rotating log file (rag_requests.log) in the backend directory and
to the standard application logger. Structured fields include:

  trace_id, timestamp_utc, query, retrieval_method,
  retrieved_patent_ids (list), retrieval_scores (list),
  num_retrieved, evidence_sufficient,
  llm_provider, latency_ms, error (optional)

Debug mode (RAG_ENABLE_DEBUG_LOGGING=True) additionally writes the full
context window and LLM prompt to a separate debug log. Debug logs are never
served to end users.
"""

import uuid
import time
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pathlib import Path

# Standard application logger (shows in uvicorn/gunicorn output)
logger = logging.getLogger("rag_pipeline")

# Dedicated structured file logger
_log_dir = Path(__file__).resolve().parent.parent.parent  # backend/
_log_path = _log_dir / "rag_requests.log"
_debug_log_path = _log_dir / "rag_debug.log"

# Set up rotating file handler lazily
_file_handler_initialized = False


def _init_file_handler():
    global _file_handler_initialized
    if _file_handler_initialized:
        return
    try:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            str(_log_path), maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(message)s"))
        rag_file_logger = logging.getLogger("rag_file")
        rag_file_logger.addHandler(fh)
        rag_file_logger.setLevel(logging.INFO)
        rag_file_logger.propagate = False
        _file_handler_initialized = True
    except Exception as exc:
        logger.warning(f"[rag_logger] Could not initialize file handler: {exc}")


class RAGRequestContext:
    """
    Context manager that tracks a single RAG request lifecycle.

    Usage:
        ctx = RAGRequestContext(query="battery patents")
        # ... retrieval ...
        ctx.set_retrieval(patent_ids=["123/DEL/2017"], scores=[0.91])
        # ... generation ...
        ctx.set_generation(provider="groq (llama3-8b-8192)", answer="...")
        ctx.log()
    """

    def __init__(self, query: str, retrieval_method: str = "hybrid"):
        self.trace_id: str = str(uuid.uuid4())[:12]
        self.timestamp_utc: str = datetime.now(timezone.utc).isoformat()
        self.query: str = query
        self.retrieval_method: str = retrieval_method
        self.retrieved_patent_ids: List[str] = []
        self.retrieval_scores: List[float] = []
        self.num_retrieved: int = 0
        self.evidence_sufficient: bool = False
        self.llm_provider: str = "unknown"
        self.latency_ms: int = 0
        self.error: Optional[str] = None
        self._start_time: float = time.monotonic()

    def set_retrieval(
        self,
        patent_ids: List[str],
        scores: Optional[List[float]] = None,
    ):
        self.retrieved_patent_ids = patent_ids
        self.retrieval_scores = [round(float(s), 4) for s in (scores or [])]
        self.num_retrieved = len(patent_ids)
        self.evidence_sufficient = self.num_retrieved > 0

    def set_generation(self, provider: str):
        self.llm_provider = provider

    def set_error(self, error: str):
        self.error = error

    def log(self, enable_debug: bool = False, context_window: Optional[str] = None):
        """Write the structured log entry. Safe to call even if file logging fails."""
        self.latency_ms = int((time.monotonic() - self._start_time) * 1000)

        record: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "timestamp_utc": self.timestamp_utc,
            "query": self.query[:300],  # truncate for log safety
            "retrieval_method": self.retrieval_method,
            "num_retrieved": self.num_retrieved,
            "evidence_sufficient": self.evidence_sufficient,
            "retrieved_patent_ids": self.retrieved_patent_ids[:20],  # cap list size
            "retrieval_scores": self.retrieval_scores[:20],
            "llm_provider": self.llm_provider,
            "latency_ms": self.latency_ms,
        }
        if self.error:
            record["error"] = self.error

        # Write to application logger
        level = logging.ERROR if self.error else logging.INFO
        logger.log(level, f"[RAG trace={self.trace_id}] {json.dumps(record)}")

        # Write to rotating file log
        _init_file_handler()
        try:
            file_logger = logging.getLogger("rag_file")
            file_logger.info(json.dumps(record))
        except Exception:
            pass  # never let logging crash the RAG pipeline

        # Debug mode: write full context to separate debug log (developer only)
        if enable_debug and context_window:
            try:
                debug_record = {**record, "context_window": context_window[:4000]}
                with open(_debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(debug_record) + "\n")
            except Exception:
                pass

        return self.trace_id


# Module-level convenience function
def new_rag_context(query: str, retrieval_method: str = "hybrid") -> RAGRequestContext:
    """Create and return a new RAGRequestContext for a single RAG request."""
    return RAGRequestContext(query=query, retrieval_method=retrieval_method)
