"""Candidate Profile Builder for SkillGap AI.

This module constructs structured, explainable candidate profiles from parsed resumes
and extracted skills:
- Organizes canonical skills, evidence, and confidence scores
- Preserves raw education, certifications, and experience evidence without fabrication
- Excludes demographic or unverified inferences (gender, race, personality, fabricated years)
- Generates privacy-safe canonical text representations for semantic/hybrid matching
- Integrates seamlessly with existing matching engine schemas (app.matching.schemas.CandidateProfile)
"""

from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.schemas import CandidateProfile
from app.resume.schemas import (
    CandidateProfileMetadata,
    ExperienceSection,
    ExtractedSkill,
    ParsedResume,
    StructuredCandidateProfile,
    UnresolvedSkill,
)

# Regex patterns for stripping non-job personal contact info
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
RE_PHONE = re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_URL = re.compile(r"https?://\S+|www\.\S+")


def sanitize_text_for_matching(text: str) -> str:
    """Strip contact info (emails, phones, URLs) from candidate text."""
    if not text:
        return ""
    cleaned = RE_EMAIL.sub("", text)
    cleaned = RE_PHONE.sub("", cleaned)
    cleaned = RE_URL.sub("", cleaned)
    # Compact excessive whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


class CandidateProfileBuilder:
    """Builds typed StructuredCandidateProfile representations."""

    @staticmethod
    def _extract_section_lines(text: Optional[str]) -> List[str]:
        """Extract clean, non-empty bullet points or lines without fabricating details."""
        if not text:
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result: List[str] = []
        for line in lines:
            # Strip leading bullet indicators
            cleaned = re.sub(r"^[-*•▪\d+\.]\s*", "", line).strip()
            if cleaned and len(cleaned) > 2:
                result.append(cleaned)
        return result

    def build_profile(
        self,
        parsed_resume: ParsedResume,
        extracted_skills: List[ExtractedSkill],
        unresolved_skills: Optional[List[UnresolvedSkill]] = None,
        candidate_id: Optional[str] = None,
    ) -> StructuredCandidateProfile:
        """Assemble structured candidate profile from parser and extractor outputs."""
        unresolved = unresolved_skills or []

        # Extract genuine summary if present; never invent or use LLM
        summary_raw = (
            parsed_resume.sections.summary
            or parsed_resume.sections.objective
            or None
        )
        summary = summary_raw.strip() if summary_raw and summary_raw.strip() else None

        # Extract genuine education entries
        education_lines = self._extract_section_lines(parsed_resume.sections.education)

        # Extract genuine certification entries
        certification_lines = self._extract_section_lines(parsed_resume.sections.certifications)

        # Extract genuine experience entries
        experience_lines = self._extract_section_lines(parsed_resume.sections.experience)

        # Metadata
        metadata = CandidateProfileMetadata(
            skill_count=len(extracted_skills),
            unresolved_count=len(unresolved),
            parser_status=parsed_resume.metadata.text_extraction_status,
            source_file=parsed_resume.filename,
            confidence_model="heuristic_evidence_v1",
        )

        return StructuredCandidateProfile(
            candidate_id=candidate_id,
            summary=summary,
            skills=extracted_skills,
            unresolved_skills=unresolved,
            education=education_lines,
            certifications=certification_lines,
            experience=ExperienceSection(raw_sections=experience_lines),
            metadata=metadata,
        )


def build_candidate_matching_text(profile: StructuredCandidateProfile) -> str:
    """Build canonical candidate text for TF-IDF / Semantic / Hybrid matching.

    Structure:
    1. Normalized canonical skill names (space-separated)
    2. Genuine summary (PII-stripped)
    3. Concise professional evidence sentences

    Explicitly excludes:
    - Personal contact info (phone, email, URLs)
    - Candidate IDs, filenames, file paths
    - Inferred demographics (gender, race, age)
    - Salary or personality model predictions
    """
    parts: List[str] = []

    # 1. Canonical skill names
    skill_names = [s.name for s in profile.skills]
    if skill_names:
        parts.append(" ".join(skill_names))

    # 2. Genuine summary (stripped of contact info)
    if profile.summary:
        clean_sum = sanitize_text_for_matching(profile.summary)
        if clean_sum:
            parts.append(clean_sum)

    # 3. Concise professional evidence sentences
    evidence_collected: List[str] = []
    seen_evidence: set = set()
    for s in profile.skills:
        for ev in s.evidence:
            ev_clean = sanitize_text_for_matching(ev)
            if ev_clean and ev_clean not in seen_evidence and not ev_clean.startswith("Skills:"):
                seen_evidence.add(ev_clean)
                evidence_collected.append(ev_clean)

    if evidence_collected:
        # Include up to top 15 evidence sentences for high information density
        parts.append(" ".join(evidence_collected[:15]))

    return "\n\n".join(parts).strip()


def to_matching_candidate_profile(
    profile: StructuredCandidateProfile,
    candidate_id: Optional[str] = None,
    experience_years: Optional[float] = None,
) -> CandidateProfile:
    """Convert StructuredCandidateProfile to matching engine's CandidateProfile schema.

    Enables direct compatibility with BaselineMatcher, SemanticMatcher, and HybridMatcher.
    """
    effective_id = candidate_id or profile.candidate_id or "candidate_extracted"
    matching_summary = build_candidate_matching_text(profile)
    skill_names = [s.name for s in profile.skills]

    return CandidateProfile(
        candidate_id=effective_id,
        skills=skill_names,
        summary=matching_summary,
        experience_years=experience_years,
    )
