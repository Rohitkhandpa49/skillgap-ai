"""Schemas for Resume Parsing and Analysis Endpoints."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.resume.schemas import (
    CandidateProfileMetadata,
    ExperienceSection,
    ExtractedSkill,
    ResumeMetadata,
    ResumeSections,
    StructuredCandidateProfile,
    UnresolvedSkill,
)


class ResumeParseResponseData(BaseModel):
    """Payload returned by POST /api/v1/resume/parse."""

    filename: str = Field(..., description="Document filename")
    file_type: Literal["pdf", "docx"] = Field(..., description="Detected format")
    sections: ResumeSections = Field(..., description="Detected resume sections")
    metadata: ResumeMetadata = Field(..., description="Document extraction health metadata")


class ResumeAnalyzeResponseData(BaseModel):
    """Payload returned by POST /api/v1/resume/analyze."""

    candidate_profile: StructuredCandidateProfile = Field(
        ..., description="Complete structured profile extracted from document"
    )
