"""Candidate Profile Service for SkillGap AI.

Coordinates the end-to-end resume intelligence pipeline:
  parse_resume(path)
  -> extract_skills(parsed_resume)
  -> build_candidate_profile(parsed_resume, extracted_skills, unresolved_skills)

Operates independently of web frameworks (FastAPI), databases, or UI components.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.schemas import CandidateProfile
from app.resume.candidate_profile_builder import (
    CandidateProfileBuilder,
    build_candidate_matching_text,
    to_matching_candidate_profile,
)
from app.resume.parser import parse_resume
from app.resume.schemas import (
    ExtractedSkill,
    ParsedResume,
    StructuredCandidateProfile,
    UnresolvedSkill,
)
from app.resume.skill_extractor import SkillExtractor


class CandidateProfileService:
    """Service orchestrating resume extraction, skill normalization, and candidate profiling."""

    def __init__(
        self,
        extractor: Optional[SkillExtractor] = None,
        builder: Optional[CandidateProfileBuilder] = None,
    ) -> None:
        self.extractor = extractor or SkillExtractor()
        self.builder = builder or CandidateProfileBuilder()

    def extract_skills_from_resume(
        self, parsed_resume: ParsedResume
    ) -> Tuple[List[ExtractedSkill], List[UnresolvedSkill]]:
        """Extract canonical and unresolved skills from a parsed resume."""
        return self.extractor.extract_skills(parsed_resume)

    def build_candidate_profile(
        self,
        parsed_resume: ParsedResume,
        candidate_id: Optional[str] = None,
    ) -> StructuredCandidateProfile:
        """Assemble structured candidate profile from an already-parsed resume."""
        extracted_skills, unresolved_skills = self.extract_skills_from_resume(parsed_resume)
        return self.builder.build_profile(
            parsed_resume=parsed_resume,
            extracted_skills=extracted_skills,
            unresolved_skills=unresolved_skills,
            candidate_id=candidate_id,
        )

    def analyze_resume_file(
        self,
        file_path: Union[str, Path],
        candidate_id: Optional[str] = None,
        max_size_bytes: int = 10 * 1024 * 1024,
    ) -> StructuredCandidateProfile:
        """Parse resume file from disk, extract skills with evidence, and construct candidate profile."""
        parsed_resume = parse_resume(file_path, max_size_bytes=max_size_bytes)
        return self.build_candidate_profile(parsed_resume, candidate_id=candidate_id)

    @staticmethod
    def get_candidate_matching_text(profile: StructuredCandidateProfile) -> str:
        """Generate canonical matching text representation for semantic/hybrid matchers."""
        return build_candidate_matching_text(profile)

    @staticmethod
    def to_matcher_profile(
        profile: StructuredCandidateProfile,
        candidate_id: Optional[str] = None,
        experience_years: Optional[float] = None,
    ) -> CandidateProfile:
        """Convert structured profile to CandidateProfile used by matching engines."""
        return to_matching_candidate_profile(
            profile=profile,
            candidate_id=candidate_id,
            experience_years=experience_years,
        )


# Global default service instance
_default_service: Optional[CandidateProfileService] = None


def get_candidate_profile_service() -> CandidateProfileService:
    """Retrieve or create singleton CandidateProfileService instance."""
    global _default_service
    if _default_service is None:
        _default_service = CandidateProfileService()
    return _default_service


def analyze_resume_file(
    file_path: Union[str, Path],
    candidate_id: Optional[str] = None,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> StructuredCandidateProfile:
    """Convenience functional entry point for parsing and profiling a resume file."""
    service = get_candidate_profile_service()
    return service.analyze_resume_file(
        file_path=file_path,
        candidate_id=candidate_id,
        max_size_bytes=max_size_bytes,
    )
