import re
import logging
from typing import List, Set, Dict, Any
from backend.app.schemas.chat import VerificationReport, ChatCitation
from backend.app.services.patent_service import patent_service

logger = logging.getLogger(__name__)

class VerificationService:
    @staticmethod
    def extract_patent_ids_from_text(text: str) -> Set[str]:
        """Extract patent application numbers formatted like 10/DEL/2010 or 1005/MUMNP/2007 or IN..."""
        pattern = r'\b(?:\d+/[A-Z]+/\d+|\d+/[A-Z]+NP/\d+|IN\d+[A-Z0-9]*)\b'
        matches = set(re.findall(pattern, text, flags=re.IGNORECASE))
        return {m.upper() for m in matches}

    def verify_answer(
        self,
        answer: str,
        retrieved_ids: List[str]
    ) -> VerificationReport:
        """Verify that all patent numbers cited in the generated answer exist in evidence or verified DB."""
        cited_in_text = self.extract_patent_ids_from_text(answer)
        retrieved_set = {pid.upper() for pid in retrieved_ids}

        verified_citations = []
        unverified_citations = []

        for cid in cited_in_text:
            if cid in retrieved_set:
                verified_citations.append(cid)
            else:
                # Check DB directly
                if patent_service.get_patent_by_id(cid):
                    verified_citations.append(cid)
                else:
                    unverified_citations.append(cid)

        total_cited = len(cited_in_text)
        total_verified = len(verified_citations)
        grounding_ratio = round(total_verified / total_cited, 2) if total_cited > 0 else 1.0
        all_valid = (len(unverified_citations) == 0)

        return VerificationReport(
            total_citations_claimed=total_cited,
            citations_verified=total_verified,
            grounding_ratio=grounding_ratio,
            all_citations_valid=all_valid,
            unverified_citations=unverified_citations
        )

verification_service = VerificationService()
