"""Resume Parsing and Analysis API Endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.dependencies import (
    get_candidate_profile_service,
    get_hybrid_matcher,
    temporary_upload_file,
)
from app.api.schemas.common import APIResponse
from app.api.schemas.matching import AnalyzeAndMatchResponseData
from app.api.schemas.resume import (
    ResumeAnalyzeResponseData,
    ResumeParseResponseData,
)
from app.matching.hybrid_matcher import HybridMatcher
from app.resume.parser import parse_resume
from app.services.candidate_profile_service import CandidateProfileService

logger = logging.getLogger("skillgap.ai_service.resume")
router = APIRouter(prefix="/api/v1/resume", tags=["Resume Intelligence"])


@router.post(
    "/parse",
    response_model=APIResponse[ResumeParseResponseData],
    status_code=status.HTTP_200_OK,
    summary="Parse Resume Document",
    description="Securely validates, extracts, and partitions a PDF or DOCX resume into structured sections.",
)
async def parse_resume_endpoint(
    file: UploadFile = File(..., description="Uploaded resume file (.pdf or .docx)"),
) -> APIResponse[ResumeParseResponseData]:
    """Parse resume into structured sections without executing skill extraction."""
    with temporary_upload_file(file) as temp_path:
        parsed = parse_resume(temp_path)
        safe_filename = file.filename or "uploaded_document"

        data = ResumeParseResponseData(
            filename=safe_filename,
            file_type=parsed.file_type,
            sections=parsed.sections,
            metadata=parsed.metadata,
        )
        return APIResponse(success=True, data=data)


@router.post(
    "/analyze",
    response_model=APIResponse[ResumeAnalyzeResponseData],
    status_code=status.HTTP_200_OK,
    summary="Analyze Resume & Extract Candidate Profile",
    description="Parses document, extracts skills with evidence, estimates heuristic confidence, and returns structured candidate profile.",
)
async def analyze_resume_endpoint(
    file: UploadFile = File(..., description="Uploaded resume file (.pdf or .docx)"),
    candidate_service: CandidateProfileService = Depends(get_candidate_profile_service),
) -> APIResponse[ResumeAnalyzeResponseData]:
    """Extract skills and assemble candidate profile from resume document."""
    with temporary_upload_file(file) as temp_path:
        parsed = parse_resume(temp_path)
        profile = candidate_service.build_candidate_profile(parsed)

        data = ResumeAnalyzeResponseData(candidate_profile=profile)
        return APIResponse(success=True, data=data)


@router.post(
    "/analyze-and-match",
    response_model=APIResponse[AnalyzeAndMatchResponseData],
    status_code=status.HTTP_200_OK,
    summary="Analyze Resume and Match Against Job Postings",
    description="Core end-to-end pipeline: parses resume, extracts candidate profile, and ranks matching jobs using Tripartite Hybrid Matcher.",
)
async def analyze_and_match_endpoint(
    file: UploadFile = File(..., description="Uploaded resume file (.pdf or .docx)"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of top job recommendations (1-50)"),
    candidate_service: CandidateProfileService = Depends(get_candidate_profile_service),
    hybrid_matcher: HybridMatcher = Depends(get_hybrid_matcher),
) -> APIResponse[AnalyzeAndMatchResponseData]:
    """End-to-end resume intelligence: parse document -> extract candidate profile -> rank top jobs."""
    with temporary_upload_file(file) as temp_path:
        parsed = parse_resume(temp_path)
        profile = candidate_service.build_candidate_profile(parsed)
        matcher_candidate = candidate_service.to_matcher_profile(profile)

        # Call tripartite hybrid matcher
        match_response = hybrid_matcher.match_candidate(matcher_candidate, top_k=top_k)

        data = AnalyzeAndMatchResponseData(
            candidate_profile=profile,
            matching_version="1.0.0",
            formula=match_response.weighting_formula,
            total_jobs_evaluated=match_response.total_jobs_evaluated,
            top_matches=match_response.top_matches,
        )
        return APIResponse(success=True, data=data)
