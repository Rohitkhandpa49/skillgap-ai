"""Job Matching Service Wrapper for SkillGap AI.

Encapsulates candidate validation, skill normalization, and matching engine invocation:
- Independent of web frameworks / FastAPI routing
- Reusable across CLI, test suites, and future API endpoints
"""

from pathlib import Path
import sys
from typing import Any, Dict, Optional, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.baseline_matcher import BaselineMatcher
from app.matching.schemas import CandidateProfile, MatchingResponse


class JobMatchingService:
    """Service wrapper for candidate-to-job matching operations."""

    def __init__(self, matcher: Optional[BaselineMatcher] = None) -> None:
        self.matcher = matcher or BaselineMatcher()

    def match_candidate(
        self,
        candidate_data: Union[CandidateProfile, Dict[str, Any]],
        top_k: int = 10,
    ) -> MatchingResponse:
        """Process candidate profile and return ranked matching results."""
        if isinstance(candidate_data, dict):
            profile = CandidateProfile(**candidate_data)
        else:
            profile = candidate_data

        return self.matcher.match_candidate(candidate=profile, top_k=top_k)
