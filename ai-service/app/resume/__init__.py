"""Resume Document Parsing Package for SkillGap AI.

Exposes unified parsing interface and structured data models.
"""

from app.resume.candidate_profile_builder import (
    CandidateProfileBuilder,
    build_candidate_matching_text,
    to_matching_candidate_profile,
)
from app.resume.cleaner import clean_resume_text
from app.resume.docx_parser import extract_text_from_docx
from app.resume.exceptions import (
    CorruptDocxError,
    CorruptPDFError,
    FileTooLargeError,
    ResumeFileNotFoundError,
    ResumeParserError,
    UnsupportedFileTypeError,
)
from app.resume.parser import parse_resume
from app.resume.pdf_parser import extract_text_from_pdf
from app.resume.schemas import (
    CandidateProfileMetadata,
    ExperienceSection,
    ExtractedSkill,
    ParsedResume,
    ResumeMetadata,
    ResumeSections,
    StructuredCandidateProfile,
    UnresolvedSkill,
)
from app.resume.section_detector import detect_sections
from app.resume.skill_extractor import SkillExtractor

__all__ = [
    "parse_resume",
    "clean_resume_text",
    "detect_sections",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "ParsedResume",
    "ResumeMetadata",
    "ResumeSections",
    "ExtractedSkill",
    "UnresolvedSkill",
    "ExperienceSection",
    "CandidateProfileMetadata",
    "StructuredCandidateProfile",
    "SkillExtractor",
    "CandidateProfileBuilder",
    "build_candidate_matching_text",
    "to_matching_candidate_profile",
    "ResumeParserError",
    "ResumeFileNotFoundError",
    "UnsupportedFileTypeError",
    "FileTooLargeError",
    "CorruptPDFError",
    "CorruptDocxError",
]

