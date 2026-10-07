"""Robust resume section detection and text partitioning.

Detects standard resume sections:
- Summary / Objective / Profile
- Education
- Experience / Work Experience
- Projects
- Skills / Technical Skills
- Certifications
- Coursework
- Achievements
- Other / Miscellaneous
"""

import re
from typing import Dict, List, Optional, Tuple

from app.resume.schemas import ResumeSections

# Section heading patterns (case-insensitive regexes)
SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("summary", re.compile(r"^(?:professional\s+|career\s+|executive\s+)?(?:summary|profile|about\s+me)$", re.IGNORECASE)),
    ("objective", re.compile(r"^(?:career\s+)?objective$", re.IGNORECASE)),
    ("education", re.compile(r"^(?:education(?:al)?|academic(?:\s+background|\s+qualifications)?|qualifications|education\s+&\s+training)$", re.IGNORECASE)),
    ("experience", re.compile(r"^(?:work\s+|professional\s+|employment\s+)?(?:experience|history)$", re.IGNORECASE)),
    ("projects", re.compile(r"^(?:key\s+|technical\s+|academic\s+|personal\s+)?projects$", re.IGNORECASE)),
    ("skills", re.compile(r"^(?:technical\s+|core\s+|key\s+)?(?:skills|competencies|areas\s+of\s+expertise|technologies|tools\s+&\s+technologies)$", re.IGNORECASE)),
    ("certifications", re.compile(r"^(?:licenses\s+&\s+)?(?:certifications|certificates|professional\s+certifications)$", re.IGNORECASE)),
    ("coursework", re.compile(r"^(?:relevant\s+)?(?:coursework|courses)$", re.IGNORECASE)),
    ("achievements", re.compile(r"^(?:honors\s+&\s+)?(?:awards|achievements|accomplishments)$", re.IGNORECASE)),
]


def normalize_header_candidate(line: str) -> str:
    """Clean a candidate line for section heading evaluation.

    Strips numbering (e.g. '1. ', 'I. '), trailing colons, and extra spacing.
    """
    s = line.strip()
    # Strip bullet indicators or markdown headers
    s = re.sub(r"^[\#\*\-•\s]+", "", s)
    # Strip leading numbering like '1. ', '1) ', 'I. '
    s = re.sub(r"^(?:[0-9]+|[IVXLCDMivxlcdm]+)[\.\)]\s*", "", s)
    # Strip trailing colons or punctuation
    s = re.sub(r"[:\-_]+$", "", s)
    return s.strip()


def detect_section_header(line: str) -> Optional[str]:
    """Check if a line matches any known resume section header.

    Returns the canonical section name or None.
    """
    clean_line = normalize_header_candidate(line)
    if not clean_line or len(clean_line) > 50:
        return None

    for section_name, pattern in SECTION_PATTERNS:
        if pattern.match(clean_line):
            return section_name

    return None


def detect_sections(cleaned_text: str) -> ResumeSections:
    """Partition cleaned resume text into structured section blocks.

    Args:
        cleaned_text: Cleaned full-text string from cleaner.py.

    Returns:
        Populated ResumeSections model instance.
    """
    if not cleaned_text:
        return ResumeSections()

    lines = cleaned_text.split("\n")
    sections_dict: Dict[str, List[str]] = {
        "summary": [],
        "objective": [],
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "certifications": [],
        "coursework": [],
        "achievements": [],
        "other": [],
    }

    current_section: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_section = detect_section_header(stripped)

        if matched_section:
            current_section = matched_section
        else:
            if current_section:
                sections_dict[current_section].append(stripped)
            else:
                # Text before the first formal section header (e.g. name, contact, brief intro)
                sections_dict["other"].append(stripped)

    # Convert line arrays to trimmed newline-separated strings
    return ResumeSections(
        summary="\n".join(sections_dict["summary"]).strip(),
        objective="\n".join(sections_dict["objective"]).strip(),
        education="\n".join(sections_dict["education"]).strip(),
        experience="\n".join(sections_dict["experience"]).strip(),
        projects="\n".join(sections_dict["projects"]).strip(),
        skills="\n".join(sections_dict["skills"]).strip(),
        certifications="\n".join(sections_dict["certifications"]).strip(),
        coursework="\n".join(sections_dict["coursework"]).strip(),
        achievements="\n".join(sections_dict["achievements"]).strip(),
        other="\n".join(sections_dict["other"]).strip(),
    )
