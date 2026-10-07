"""Schemas for Candidate Profiles and Matching Engine Results.

Provides strongly-typed schemas using Pydantic v2 for:
- CandidateProfile: structured candidate representation
- ExperienceComparison: candidate vs job experience compatibility
- ScoreComponents: breakdown of skill overlap and text similarity
- JobMatchResult: individual job match outcome with explanations
- MatchingResponse: ranked list of top job matches and metadata
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Structured representation of a candidate for job matching."""

    candidate_id: str = Field(
        ...,
        description="Unique identifier for candidate (e.g. candidate_demo_001)",
    )
    skills: List[str] = Field(
        default_factory=list,
        description="List of raw or normalized skill names",
    )
    summary: Optional[str] = Field(
        default="",
        description="Textual professional summary or project statement",
    )
    experience_years: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Total relevant work experience in years",
    )


class ExperienceComparison(BaseModel):
    """Comparison of candidate experience against job requirements."""

    candidate_years: Optional[float] = None
    required_min_years: Optional[float] = None
    required_max_years: Optional[float] = None
    status: Literal["compatible", "gap", "unspecified"] = "unspecified"


class ScoreComponents(BaseModel):
    """Individual normalized sub-scores (0.0 to 1.0)."""

    skill_overlap: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized explicit skill overlap score (0.0 to 1.0)",
    )
    text_similarity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized TF-IDF cosine similarity score (0.0 to 1.0) - baseline compatibility",
    )
    tfidf_similarity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized TF-IDF lexical similarity score (0.0 to 1.0)",
    )
    semantic_similarity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized Sentence Transformer semantic cosine similarity score (0.0 to 1.0)",
    )

    def model_post_init(self, __context: Any) -> None:
        """Synchronize text_similarity and tfidf_similarity for backwards compatibility."""
        if self.text_similarity is not None and self.tfidf_similarity is None:
            self.tfidf_similarity = self.text_similarity
        elif self.tfidf_similarity is not None and self.text_similarity is None:
            self.text_similarity = self.tfidf_similarity


class JobMatchResult(BaseModel):
    """Detailed matching result for a single job posting."""

    job_id: str
    job_title: str
    match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Combined weighted percentage score (0.0 to 100.0)",
    )
    components: ScoreComponents
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    candidate_only_skills: List[str] = Field(default_factory=list)
    experience: ExperienceComparison
    explanation: List[str] = Field(
        default_factory=list,
        description="Explainable human-readable reasoning points",
    )
    location: Optional[str] = None
    salary_raw: Optional[str] = None


class MatchingResponse(BaseModel):
    """Complete ranked response from the matching engine."""

    candidate_id: str
    normalized_candidate_skills: List[str]
    unknown_candidate_skills: List[str]
    total_jobs_evaluated: int
    top_matches: List[JobMatchResult]
    weighting_formula: str = "0.70 * Skill Overlap + 0.30 * TF-IDF Text Similarity"
