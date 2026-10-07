"""Pydantic v2 schemas for parsed resume documents and extraction metadata."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ResumeMetadata(BaseModel):
    """Metadata detailing extraction execution and document characteristics."""

    page_count: int = Field(default=1, ge=0, description="Total number of document pages or sections")
    pages_with_text: int = Field(default=0, ge=0, description="Pages containing extractable text")
    pages_without_text: int = Field(default=0, ge=0, description="Pages containing no extractable text")
    paragraph_count: Optional[int] = Field(default=None, description="Paragraph count (DOCX)")
    table_count: Optional[int] = Field(default=None, description="Table count (DOCX)")
    character_count: int = Field(default=0, ge=0, description="Total characters extracted")
    text_extraction_status: Literal["success", "partial", "insufficient_text", "failed"] = Field(
        default="success",
        description="Overall text extraction health status",
    )
    file_size_bytes: int = Field(default=0, ge=0, description="File size in bytes")
    processing_time_ms: float = Field(default=0.0, ge=0.0, description="Parser runtime in milliseconds")
    warning_message: Optional[str] = Field(
        default=None,
        description="Quality warning if text is sparse or document appears scanned",
    )


class ResumeSections(BaseModel):
    """Structured partitions of detected resume sections."""

    summary: Optional[str] = Field(default="", description="Summary, Objective, or Profile section")
    objective: Optional[str] = Field(default="", description="Objective statement section")
    education: Optional[str] = Field(default="", description="Education and academic credentials section")
    experience: Optional[str] = Field(default="", description="Work and professional employment history section")
    projects: Optional[str] = Field(default="", description="Key technical, academic, or personal projects")
    skills: Optional[str] = Field(default="", description="Technical and core skills section text (raw)")
    certifications: Optional[str] = Field(default="", description="Licenses and certifications section")
    coursework: Optional[str] = Field(default="", description="Relevant coursework section")
    achievements: Optional[str] = Field(default="", description="Honors, awards, and achievements section")
    other: Optional[str] = Field(default="", description="Miscellaneous content not matched to known sections")


class ParsedResume(BaseModel):
    """Complete structured representation of an extracted and sanitized resume document."""

    filename: str = Field(..., description="Original filename without path")
    file_type: Literal["pdf", "docx"] = Field(..., description="Document format ('pdf' or 'docx')")
    raw_text: str = Field(..., description="Unmodified extracted text prior to cleaning")
    cleaned_text: str = Field(..., description="Sanitized, normalized, human-readable text")
    sections: ResumeSections = Field(default_factory=ResumeSections, description="Detected resume sections")
    metadata: ResumeMetadata = Field(default_factory=ResumeMetadata, description="Extraction health metadata")


class ExtractedSkill(BaseModel):
    """Normalized canonical skill with confidence and traceable evidence."""

    name: str = Field(..., description="Canonical skill name from taxonomy")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Heuristic evidence confidence score (0.0 to 1.0)",
    )
    original_mentions: List[str] = Field(
        default_factory=list,
        description="Exact textual mentions matched in the resume",
    )
    source_sections: List[str] = Field(
        default_factory=list,
        description="List of detected sections where the skill was found",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Concise evidence sentences or bullet points containing the skill",
    )


class UnresolvedSkill(BaseModel):
    """Plausible technical term found in the resume not present in taxonomy."""

    term: str = Field(..., description="Raw technical skill or tool name")
    evidence: str = Field(default="", description="Sentence or line containing the mention")
    reason: str = Field(
        default="not_in_current_taxonomy",
        description="Reason the skill was unresolved",
    )
    source_section: Optional[str] = Field(
        default=None,
        description="Section where the term was discovered",
    )


class ExperienceSection(BaseModel):
    """Structured container for raw professional experience lines/sections."""

    raw_sections: List[str] = Field(
        default_factory=list,
        description="Unfabricated raw experience bullet points and descriptions",
    )


class CandidateProfileMetadata(BaseModel):
    """Operational metadata for extracted candidate profile."""

    skill_count: int = Field(default=0, ge=0, description="Total canonical skills identified")
    unresolved_count: int = Field(default=0, ge=0, description="Count of unresolved terms")
    parser_status: str = Field(default="success", description="Upstream document parsing health status")
    source_file: Optional[str] = Field(default=None, description="Original resume filename")
    confidence_model: str = Field(
        default="heuristic_evidence_v1",
        description="Rule-based evidence confidence scoring version",
    )


class StructuredCandidateProfile(BaseModel):
    """Full structured candidate profile extracted from a parsed resume."""

    candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate identifier (None if not explicitly provided)",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Extracted professional summary or objective, or None if absent",
    )
    skills: List[ExtractedSkill] = Field(
        default_factory=list,
        description="List of canonical skills with evidence and confidence",
    )
    unresolved_skills: List[UnresolvedSkill] = Field(
        default_factory=list,
        description="Non-taxonomy technical terms preserved for observability",
    )
    education: List[str] = Field(
        default_factory=list,
        description="Education lines extracted without fabrication",
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Certifications listed in resume without fabrication",
    )
    experience: ExperienceSection = Field(
        default_factory=ExperienceSection,
        description="Experience evidence without fabricated duration estimates",
    )
    metadata: CandidateProfileMetadata = Field(
        default_factory=CandidateProfileMetadata,
        description="Profile extraction metadata",
    )

