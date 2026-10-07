"""Schemas for Job Matching Endpoints."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.matching.schemas import JobMatchResult
from app.resume.schemas import StructuredCandidateProfile


class MatchRequest(BaseModel):
    """Input payload for POST /api/v1/match."""

    skills: List[str] = Field(
        default_factory=list,
        description="Candidate technical and domain skills",
        max_length=100,
    )
    summary: Optional[str] = Field(
        default="",
        description="Candidate professional summary, project description, or narrative text",
        max_length=5000,
    )
    experience_years: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=60.0,
        description="Total relevant years of work experience",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top ranked job recommendations to return",
    )


class MatchResponseData(BaseModel):
    """Payload returned by POST /api/v1/match."""

    matching_version: str = Field(default="1.0.0", description="Algorithm version identifier")
    formula: str = Field(
        default="0.50 * Skill Overlap + 0.20 * TF-IDF Similarity + 0.30 * Semantic Similarity",
        description="Scoring formula applied",
    )
    total_jobs_evaluated: int = Field(..., description="Total job postings evaluated in dataset")
    matches: List[JobMatchResult] = Field(..., description="Ranked list of job matches")


class AnalyzeAndMatchResponseData(BaseModel):
    """Payload returned by POST /api/v1/resume/analyze-and-match."""

    candidate_profile: StructuredCandidateProfile = Field(
        ..., description="Extracted candidate profile"
    )
    matching_version: str = Field(default="1.0.0", description="Algorithm version identifier")
    formula: str = Field(
        default="0.50 * Skill Overlap + 0.20 * TF-IDF Similarity + 0.30 * Semantic Similarity",
        description="Scoring formula applied",
    )
    total_jobs_evaluated: int = Field(..., description="Total job postings evaluated in dataset")
    top_matches: List[JobMatchResult] = Field(..., description="Ranked list of top job recommendations")
