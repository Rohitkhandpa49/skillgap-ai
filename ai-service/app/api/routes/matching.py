"""Candidate-to-Job Matching API Endpoints."""

import logging
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_hybrid_matcher
from app.api.schemas.common import APIResponse
from app.api.schemas.matching import MatchRequest, MatchResponseData
from app.core.errors import InvalidCandidateRequestError
from app.matching.hybrid_matcher import HybridMatcher
from app.matching.schemas import CandidateProfile

logger = logging.getLogger("skillgap.ai_service.matching")
router = APIRouter(prefix="/api/v1", tags=["Job Matching"])


@router.post(
    "/match",
    response_model=APIResponse[MatchResponseData],
    status_code=status.HTTP_200_OK,
    summary="Match Candidate Profile to Jobs",
    description="Ranks job postings using the Tripartite Hybrid Matching Engine (50% Skill Overlap, 20% TF-IDF, 30% Dense Semantics).",
)
async def match_candidate_endpoint(
    request_data: MatchRequest,
    hybrid_matcher: HybridMatcher = Depends(get_hybrid_matcher),
) -> APIResponse[MatchResponseData]:
    """Rank job postings against candidate skills and summary."""
    # Ensure profile has actionable technical content
    has_skills = bool(request_data.skills and any(s.strip() for s in request_data.skills))
    has_summary = bool(request_data.summary and request_data.summary.strip())

    if not has_skills and not has_summary:
        raise InvalidCandidateRequestError(
            "Candidate profile must provide at least one skill or a professional summary for job matching."
        )

    # Convert request payload into internal CandidateProfile schema
    candidate = CandidateProfile(
        candidate_id="api_candidate",
        skills=request_data.skills,
        summary=request_data.summary or "",
        experience_years=request_data.experience_years,
    )

    # Run hybrid matching
    match_response = hybrid_matcher.match_candidate(candidate, top_k=request_data.top_k)

    data = MatchResponseData(
        matching_version="1.0.0",
        formula=match_response.weighting_formula,
        total_jobs_evaluated=match_response.total_jobs_evaluated,
        matches=match_response.top_matches,
    )
    return APIResponse(success=True, data=data)
