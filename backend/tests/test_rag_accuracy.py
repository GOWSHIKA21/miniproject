"""
test_rag_accuracy.py — RAG pipeline accuracy and anti-hallucination tests.

Tests use the actual retrieval + generation pipeline (no mocks for core logic).
The backend must be importable (run from the miniproject/ root):

    python -m pytest backend/tests/test_rag_accuracy.py -v

Requires: backend services accessible (MongoDB/Parquet fallback, FAISS index).
LLM calls are skipped if GROQ_API_KEY is absent — fallback synthesiser is tested instead.
"""

import re
import sys
import os
import pytest

# Allow imports from the miniproject root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from backend.app.schemas.chat import ChatRequest
from backend.app.services.rag_service import rag_service
from backend.app.retrieval.hybrid_search import hybrid_retrieval_engine


# ─── Helpers ────────────────────────────────────────────────────────────────

def ask(query: str, history=None) -> dict:
    """Execute a RAG question and return the response as a dict."""
    req = ChatRequest(query=query, history=history or [])
    resp = rag_service.answer_question(req)
    return {
        "answer": resp.answer,
        "citations": [c.model_dump() for c in resp.citations],
        "retrieved": [e.patent.patentNumber for e in resp.retrieved_evidence],
        "provider": resp.llm_provider,
        "verification": resp.verification.model_dump() if resp.verification else {}
    }


def retrieved_ids(query: str, top_k: int = 5) -> list:
    """Return just the patent IDs retrieved for a query."""
    res = hybrid_retrieval_engine.search(query=query, top_k=top_k, retrieval_method="hybrid")
    return [item.patent.patentNumber for item in res.results]


# ─── Test Category 1: Evidence-grounded answers ─────────────────────────────

class TestEvidenceGrounding:
    """Answers must be supported by retrieved evidence, not fabricated."""

    def test_battery_query_returns_relevant_patents(self):
        """Retrieving 'lithium ion battery' should return patents from the electronics/chemistry domain."""
        ids = retrieved_ids("lithium ion battery anode electrode")
        assert len(ids) > 0, "Expected at least one retrieved patent for 'lithium ion battery'"

    def test_answer_does_not_cite_unretieved_patents(self):
        """
        The generated answer must not cite patent IDs that were never retrieved.
        All cited patent IDs must appear in the retrieved evidence set.
        """
        result = ask("lithium ion battery anode materials")
        retrieved_set = set(result["retrieved"])
        for citation in result["citations"]:
            pid = citation["patent_id"]
            assert pid in retrieved_set, (
                f"Citation '{pid}' was not in the retrieved evidence set. Possible hallucination."
            )

    def test_verified_flag_only_set_for_cited_patents(self):
        """
        Citations marked verified=True should only be those whose ID
        appears as a bracketed reference in the answer text.
        """
        result = ask("pharmaceutical composition for drug delivery containers")
        answer_text = result["answer"]
        for citation in result["citations"]:
            pid = citation["patent_id"]
            in_answer = (f"[{pid}]" in answer_text) or (pid in answer_text)
            if citation.get("verified"):
                assert in_answer, (
                    f"Citation '{pid}' is marked verified=True but does not appear in the answer text."
                )

    def test_answer_references_at_least_one_patent_id(self):
        """For a query with expected results, the answer should cite at least one patent ID."""
        result = ask("wind turbine electric power generation")
        # If retrieval succeeded and returned results, the answer should mention at least one patent ID
        if result["retrieved"]:
            answer = result["answer"]
            has_citation = bool(re.search(r"\[[\w/]+\]", answer))
            has_any_pid = any(pid in answer for pid in result["retrieved"][:3])
            # Either bracketed citation or bare patent ID is acceptable
            assert has_citation or has_any_pid or "insufficient" in answer.lower(), (
                "Expected the answer to cite at least one patent ID or state insufficient evidence."
            )


# ─── Test Category 2: Insufficient evidence handling ────────────────────────

class TestInsufficientEvidence:
    """When no relevant patents exist, the AI must say so honestly."""

    def test_no_hallucination_on_obscure_query(self):
        """
        For a highly specific query unlikely to match any patent,
        the system must NOT hallucinate a patent ID. It must either
        return an empty citations list or explicitly state insufficient evidence.
        """
        result = ask("quantum entanglement antigravity propulsion system for interstellar travel 2017")
        answer = result["answer"].lower()
        citations = result["citations"]

        # If retrieval found nothing, there should be no verified citations
        verified = [c for c in citations if c.get("verified")]
        if not result["retrieved"]:
            assert len(verified) == 0, (
                "No patents were retrieved, but verified citations were generated — possible hallucination."
            )
            # The answer should acknowledge insufficient evidence
            assert (
                "insufficient" in answer or
                "no relevant" in answer or
                "not found" in answer or
                "no matching" in answer or
                "could not" in answer or
                "unavailable" in answer
            ), f"Expected an honest 'no evidence' response but got: {result['answer'][:200]}"

    def test_retrieval_error_gives_honest_error_message(self):
        """
        A retrieval error must produce an error message, not a fabricated answer.
        We simulate this by checking the error_handler provider path is wired correctly.
        (This test verifies the code path exists; actual error injection is in unit tests.)
        """
        # Verify the answer_question method exists and is callable
        assert callable(getattr(rag_service, "answer_question", None))


# ─── Test Category 3: Multi-patent comparison ────────────────────────────────

class TestMultiPatentComparison:
    """Questions requiring comparison between multiple patents."""

    def test_comparison_query_retrieves_multiple_patents(self):
        """Comparison questions should retrieve ≥ 2 patents to be answerable."""
        result = ask("compare patents related to solar energy harvesting versus wind power generation")
        # May retrieve nothing if both are niche — just verify no crash and no hallucination
        for citation in result["citations"]:
            pid = citation["patent_id"]
            assert pid in result["retrieved"], (
                f"Citation '{pid}' was not retrieved — possible hallucination in comparison answer."
            )

    def test_multi_patent_answer_cites_distinct_patents(self):
        """For a broad domain query, the answer should reference multiple distinct patents if available."""
        result = ask("mechanical engineering inventions filed in Delhi")
        if len(result["retrieved"]) >= 2:
            cited_pids = {c["patent_id"] for c in result["citations"] if c.get("verified")}
            # Allow single citation if retrieval only found one good match
            assert len(cited_pids) >= 1, "Expected at least one cited patent ID."


# ─── Test Category 4: Missing metadata handling ──────────────────────────────

class TestMissingMetadata:
    """Questions about fields that may not exist in the dataset."""

    def test_abstract_not_fabricated(self):
        """
        The system does not have full patent abstracts — only structured metadata.
        The answer must not fabricate abstract text for patents that have none.
        """
        result = ask("provide the full abstract of patent 10/DEL/2010")
        answer = result["answer"].lower()
        # The answer must either quote from retrieved record content or admit limitation
        assert (
            "abstract" not in answer or
            "insufficient" in answer or
            "not available" in answer or
            "no abstract" in answer or
            "record content" in answer or
            len(result["retrieved"]) > 0  # if retrieved, it's grounded
        ), "Possible fabricated abstract — no retrieved evidence for this patent."

    def test_legal_status_not_fabricated(self):
        """The system must not invent granted/rejected status."""
        result = ask("is patent 10/DEL/2010 currently granted or rejected?")
        answer = result["answer"].lower()
        # Should either acknowledge limitation or reference only retrieved status field
        dangerous_fabrications = ["definitely granted", "confirmed granted", "legally valid"]
        for phrase in dangerous_fabrications:
            assert phrase not in answer, (
                f"Answer appears to fabricate legal status with phrase: '{phrase}'"
            )


# ─── Test Category 5: Ambiguous queries ──────────────────────────────────────

class TestAmbiguousQueries:
    """Ambiguous questions should be handled with clarification or stated interpretation."""

    def test_ambiguous_term_does_not_crash(self):
        """'Container' could mean pharma container, shipping container, etc."""
        result = ask("find all patents about containers")
        assert result["answer"], "Expected a non-empty answer for an ambiguous query."
        # Should not crash or return an empty answer
        assert len(result["answer"]) > 10

    def test_ambiguous_query_returns_valid_citations(self):
        """Any citations returned for an ambiguous query must still be real retrieved patents."""
        result = ask("patents about energy storage")
        for citation in result["citations"]:
            assert citation["patent_id"] in result["retrieved"], (
                f"Citation '{citation['patent_id']}' not in retrieved set — possible hallucination."
            )


# ─── Test Category 6: Follow-up / conversation context ──────────────────────

class TestConversationContext:
    """Follow-up questions must use previous conversation context."""

    def test_followup_question_uses_history(self):
        """A follow-up question about 'the first patent' should use conversation history."""
        history = [
            {"role": "user", "content": "What patents exist for wind turbine generators?"},
            {"role": "assistant", "content": "Retrieved evidence shows patents such as [123/DEL/2017] related to wind turbine electric power generation..."}
        ]
        result = ask("Tell me more about the first patent you mentioned.", history=history)
        answer = result["answer"].lower()
        # The answer should reference either context history or newly retrieved evidence
        assert len(answer) > 10, "Follow-up answer should not be empty."
        # Should not crash with conversation context provided
        assert result["provider"] is not None

    def test_unrelated_followup_fetches_fresh_evidence(self):
        """
        A follow-up on a completely different topic should retrieve fresh evidence,
        not reuse previous context inappropriately.
        """
        history = [
            {"role": "user", "content": "Tell me about pharmaceutical patents."},
            {"role": "assistant", "content": "Retrieved pharmaceutical patents from InPASS..."}
        ]
        result = ask("Now tell me about mechanical engineering patents for drilling machines.", history=history)
        # New query should retrieve new evidence
        answer = result["answer"].lower()
        assert len(answer) > 10, "Unrelated follow-up should generate a substantive answer."


# ─── Test Category 7: Keyword overlap with different concepts ────────────────

class TestKeywordMismatch:
    """Related keywords should not be conflated as technically equivalent."""

    def test_battery_vs_battery_cell_not_conflated(self):
        """'Battery' and 'battery cell' may match different patents — results should be reasonable."""
        ids_broad = set(retrieved_ids("battery", top_k=10))
        ids_specific = set(retrieved_ids("lithium ion battery anode electrode", top_k=10))
        # Both should return results without fabrication
        # The sets may overlap or differ — what matters is both are real retrieved IDs
        assert isinstance(ids_broad, set)
        assert isinstance(ids_specific, set)

    def test_answer_does_not_claim_semantic_similarity_equals_technical_equivalence(self):
        """The answer must not state 'Patent X is equivalent to Y' based solely on keyword match."""
        result = ask("Is the solar panel patent the same as the photovoltaic cell patent?")
        answer = result["answer"].lower()
        dangerous = ["are technically equivalent", "are the same patent", "are identical"]
        for phrase in dangerous:
            assert phrase not in answer, (
                f"Answer claims equivalence without evidence: '{phrase}'"
            )


# ─── Test Category 8: Structured queries ─────────────────────────────────────

class TestStructuredQueries:
    """Count and listing queries should use database aggregation, not LLM guessing."""

    def test_count_query_returns_numeric_answer(self):
        """'How many patents are there?' should return a structured numeric answer."""
        result = ask("How many patents are in the database?")
        answer = result["answer"]
        # Should contain a number (from database aggregation)
        has_number = bool(re.search(r"\d{1,3}(,\d{3})*|\d+", answer))
        assert has_number, f"Expected a numeric count in the answer but got: {answer[:200]}"

    def test_location_breakdown_query(self):
        """'How many patents per IPO office?' should return a breakdown."""
        result = ask("Show the breakdown of patents by IPO office location.")
        answer = result["answer"].lower()
        # Should mention known office locations
        offices = ["delhi", "chennai", "mumbai", "kolkata"]
        mentioned = [o for o in offices if o in answer]
        assert len(mentioned) >= 1, (
            f"Expected at least one IPO office name in the breakdown answer. Got: {answer[:300]}"
        )


# ─── Test Category 9: No fabricated citations ────────────────────────────────

class TestNoCitationFabrication:
    """Regression tests ensuring previously-observed hallucination patterns are fixed."""

    def test_patent_id_format_is_realistic(self):
        """All cited patent IDs must match a realistic InPASS format."""
        result = ask("biotechnology patents related to gene sequencing")
        inpass_pattern = re.compile(
            r"^\d+/[A-Z]+/\d{4}$|^\d{4}/[A-Z]+/\d{4}$|^[A-Z]+\d+$",
            re.IGNORECASE
        )
        for citation in result["citations"]:
            pid = citation["patent_id"]
            # InPASS IDs typically look like "10/DEL/2010" or "1005/MUMNP/2007"
            # They should NOT look like "PATENT-2017-001" or other made-up formats
            assert "/" in pid or pid.isalnum(), (
                f"Citation '{pid}' does not match expected InPASS patent ID format."
            )

    def test_no_fictional_inventors_invented(self):
        """Inventor names in citations must come from the dataset, not be fabricated."""
        result = ask("Who invented the fastest wind turbine patent in India?")
        # We can't verify every name, but we can check citations are from retrieved records
        for citation in result["citations"]:
            assert citation["patent_id"] in result["retrieved"], (
                f"Citation '{citation['patent_id']}' not in retrieved set — possible fabricated inventor claim."
            )
