"""Hybrid Deterministic Skill Extraction Module for SkillGap AI.

This module provides boundary-aware, section-aware skill extraction from parsed resumes:
- Reuses canonical taxonomy and alias definitions via SkillNormalizer
- Implements boundary-aware pattern matching to prevent false substring hits (e.g. R in 'program', Java in 'JavaScript')
- Preserves technical identifiers (C, C++, C#, .NET, ASP.NET, Node.js, React.js, Java, JavaScript, R, SQL, PL/SQL, REST API)
- Associates each detected skill with source resume sections and concise evidence sentences
- Computes explainable, deterministic heuristic evidence confidence (0.0 to 1.0)
- Merges multiple occurrences into unified canonical skill representations
- Detects contextual negations ("No experience with Kubernetes") to exclude false claims
- Captures unresolved candidate skills (technologies not in the taxonomy) without crashing
"""

from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.preprocessing.skill_normalizer import SkillNormalizer
from app.resume.schemas import ExtractedSkill, ParsedResume, UnresolvedSkill

# Negation trigger patterns that invalidate positive skill assertions in a clause
NEGATION_PATTERNS = [
    re.compile(r"\bno\s+experience\s+(?:with|in)\b", re.IGNORECASE),
    re.compile(r"\bunfamiliar\s+with\b", re.IGNORECASE),
    re.compile(r"\b(?:have\s+not|haven'?t)\s+used\b", re.IGNORECASE),
    re.compile(r"\bnot\s+experienced\s+in\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+experience\s+(?:in|with)\b", re.IGNORECASE),
    re.compile(r"\blittle\s+to\s+no\s+experience\s+(?:with|in)\b", re.IGNORECASE),
    re.compile(r"\bno\s+knowledge\s+of\b", re.IGNORECASE),
    re.compile(r"\bnever\s+worked\s+with\b", re.IGNORECASE),
    re.compile(r"\bnot\s+used\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bno\s+prior\s+experience\s+(?:with|in)\b", re.IGNORECASE),
    re.compile(r"\blacks?\s+experience\s+(?:with|in)\b", re.IGNORECASE),
]

# Section headers / noisy phrases to exclude from unresolved skills
GENERIC_HEADER_TOKENS = {
    "skills",
    "technical skills",
    "core skills",
    "key skills",
    "technologies",
    "tools",
    "frameworks",
    "languages",
    "programming languages",
    "databases",
    "libraries",
    "others",
    "other",
    "competencies",
    "core competencies",
    "areas of expertise",
    "proficiencies",
    "software",
    "platforms",
    "concepts",
    "and",
    "or",
    "etc",
    "etc.",
    "with",
    "using",
}


class SkillExtractor:
    """Hybrid deterministic NLP skill extractor for parsed resume documents."""

    def __init__(self, normalizer: Optional[SkillNormalizer] = None) -> None:
        self.normalizer = normalizer or SkillNormalizer()
        self._compiled_patterns: List[Tuple[str, str, re.Pattern[str], int]] = []
        self._build_compiled_patterns()

    def _build_compiled_patterns(self) -> None:
        """Compile boundary-aware regex patterns for canonical skills and aliases.

        Sorts patterns by length descending to match more specific/longer phrases first.
        """
        # Collect (surface_form, canonical_name)
        pattern_candidates: List[Tuple[str, str]] = []

        # 1. Aliases
        for alias_key, canon_name in self.normalizer.aliases_lower_map.items():
            pattern_candidates.append((alias_key, canon_name))

        # 2. Canonical skills
        for canon_name in self.normalizer.canonical_skills:
            pattern_candidates.append((canon_name.lower(), canon_name))

        # Deduplicate
        seen_pairs: Set[Tuple[str, str]] = set()
        unique_candidates: List[Tuple[str, str]] = []
        for surface, canon in pattern_candidates:
            pair = (surface.strip().lower(), canon)
            if pair not in seen_pairs and pair[0]:
                seen_pairs.add(pair)
                unique_candidates.append(pair)

        # Sort by surface length descending so "machine learning" matches before "learning",
        # "javascript" before "java", "c++" before "c", "asp.net" before ".net"
        unique_candidates.sort(key=lambda x: len(x[0]), reverse=True)

        for surface, canon in unique_candidates:
            regex_pat = self._create_boundary_regex(surface, canon)
            if regex_pat:
                self._compiled_patterns.append((surface, canon, regex_pat, len(surface)))

    def _create_boundary_regex(self, surface: str, canon: str) -> Optional[re.Pattern[str]]:
        """Construct precise boundary-aware regex respecting technical punctuation."""
        s = surface.strip().lower()

        # Special case: Java vs JavaScript
        if s == "java":
            return re.compile(r"\bJava\b(?!\s*Script)", re.IGNORECASE)

        # Special case: JavaScript (must not match .js in Node.js or Vue.js)
        if s in ("javascript", "js"):
            return re.compile(r"(?<!\.)\b(?:JavaScript|Javascript)\b|(?<!\.)\bJS\b", 0 if s == "js" else re.IGNORECASE)


        # Special case: C++
        if s in ("c++", "cpp", "c plus plus"):
            return re.compile(r"\bC\+\+|\bCpp\b|\bC\s+Plus\s+Plus\b", re.IGNORECASE)

        # Special case: C#
        if s in ("c#", "csharp", "c sharp"):
            return re.compile(r"\bC#|\bC\s*Sharp\b|\bCSharp\b", re.IGNORECASE)

        # Special case: C (lone letter language)
        if s in ("c", "c language", "c programming"):
            # Avoid matching inside C++, C#, or as arbitrary letter C
            # In prose, look for "C language", "C programming", or C in programming list contexts
            return re.compile(
                r"\bC\b(?!\s*(?:\+\+|#|[a-zA-Z0-9_]))(?=(?:\s*[,/]\s*(?:C\+\+|C#|Java|Python)|(?:\s+(?:programming|language|code))))|"
                r"\b(?:in|using|with)\s+C\b(?!\s*(?:\+\+|#|[a-zA-Z0-9_]))",
                re.IGNORECASE,
            )

        # Special case: R (lone letter stats language)
        if s in ("r", "r language", "r programming", "r studio", "r-project"):
            return re.compile(
                r"\bR\b(?=(?:\s*[,/]\s*(?:Python|SQL|SAS|SPSS)|(?:\s+(?:programming|language|script|studio))))|"
                r"\b(?:in|using|with)\s+R\b(?!\s*[a-zA-Z0-9_])",
                re.IGNORECASE,
            )

        # Special case: .NET and ASP.NET
        if s in (".net", ".net core", ".net framework", "dotnet"):
            return re.compile(r"(?<![a-zA-Z0-9])\.NET(?:\s+(?:Core|Framework))?\b|\bDOTNET\b", re.IGNORECASE)
        if s == "asp.net":
            return re.compile(r"\bASP\.NET\b", re.IGNORECASE)

        # Special case: Node.js
        if s in ("node.js", "nodejs", "node"):
            return re.compile(r"\bNode(?:\.js|js)?\b", re.IGNORECASE)

        # Special case: React
        if s in ("react", "react.js", "reactjs"):
            return re.compile(r"\bReact(?:\.js|js)?\b", re.IGNORECASE)

        # Special case: SQL vs PL/SQL, MySQL, PostgreSQL, NoSQL
        if s == "sql":
            return re.compile(r"(?<![a-zA-Z0-9/])SQL\b", re.IGNORECASE)
        if s in ("pl/sql", "pl-sql", "plsql"):
            return re.compile(r"\bPL\s*/\s*SQL\b|\bPLSQL\b", re.IGNORECASE)
        if s in ("postgresql", "postgres"):
            return re.compile(r"\b(?:PostgreSQL|Postgres(?:ql)?)\b", re.IGNORECASE)
        if s == "mysql":
            return re.compile(r"\bMySQL\b", re.IGNORECASE)
        if s == "nosql":
            return re.compile(r"\bNoSQL\b", re.IGNORECASE)

        # Special case: CI/CD
        if s in ("ci/cd", "ci / cd", "continuous integration"):
            return re.compile(r"\bCI\s*/\s*CD\b|\bContinuous\s+Integration\b", re.IGNORECASE)

        # Special case: REST API
        if s in ("rest api", "rest", "restful", "rest apis"):
            return re.compile(r"\bREST(?:ful)?(?:\s+API(?:s)?)?\b|\bREST\s+APIs\b", re.IGNORECASE)

        # Short acronyms: require uppercase in text or word boundary
        if s in ("ml", "nlp", "dl", "bi", "ba", "bd", "hr", "mis", "sem", "seo", "etl", "aws", "gcp", "sap"):
            return re.compile(rf"\b{re.escape(s.upper())}\b")

        # Multi-word or generic skills: escape characters and allow flexible whitespace
        tokens = s.split()
        if len(tokens) > 1:
            escaped_tokens = [re.escape(t) for t in tokens]
            pattern_str = r"\b" + r"\s+".join(escaped_tokens) + r"\b"
            return re.compile(pattern_str, re.IGNORECASE)

        # Single word default
        return re.compile(rf"\b{re.escape(s)}\b", re.IGNORECASE)

    @staticmethod
    def _is_negated_in_sentence(sentence: str, match_start: int) -> bool:
        """Check if skill occurrence is governed by a preceding negation cue."""
        for neg_pat in NEGATION_PATTERNS:
            for neg_match in neg_pat.finditer(sentence):
                neg_end = neg_match.end()
                # If negation appears before skill in the same sentence within ~80 characters
                if 0 <= (match_start - neg_end) <= 80:
                    intervening = sentence[neg_end:match_start]
                    # If there is a clause boundary like semicolon or 'but', negation might not apply
                    if not re.search(r"[;]|,\s*but\s+", intervening, re.IGNORECASE):
                        return True
        return False

    @staticmethod
    def _split_into_sentences_or_bullets(text: str) -> List[str]:
        """Split prose text into discrete, readable sentences or bullet items."""
        if not text:
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result: List[str] = []
        for line in lines:
            # Strip bullet marker
            cleaned_line = re.sub(r"^[-*•▪\d+\.]\s*", "", line).strip()
            if not cleaned_line:
                continue
            # If line contains multiple sentences, split gently on punctuation
            sub_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned_line)
            for s in sub_sentences:
                s_trimmed = s.strip()
                if len(s_trimmed) > 3:
                    result.append(s_trimmed)
        return result

    def extract_skills_from_section_text(
        self,
        section_text: str,
        section_name: str,
    ) -> List[Dict[str, Any]]:
        """Extract skill occurrences from a specific resume section."""
        occurrences: List[Dict[str, Any]] = []
        if not section_text or not section_text.strip():
            return occurrences

    @staticmethod
    def _clean_skills_section_text(text: str) -> str:
        """Strip category label prefixes (e.g. 'Languages:', 'Tools:') from skills lines."""
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            l = line.strip()
            if not l:
                continue
            # Strip bullet prefixes
            l = re.sub(r"^[-*•▪\d+\.]\s*", "", l).strip()
            # If line has a category prefix like 'Languages: ...' or 'Tools: ...'
            l_sub = re.sub(r"^[A-Za-z0-9\s/]+:\s*", "", l)
            cleaned_lines.append(l_sub if l_sub.strip() else l)
        return "\n".join(cleaned_lines)

    def extract_skills_from_section_text(
        self,
        section_text: str,
        section_name: str,
    ) -> List[Dict[str, Any]]:
        """Extract skill occurrences from a specific resume section."""
        occurrences: List[Dict[str, Any]] = []
        if not section_text or not section_text.strip():
            return occurrences

        # If it's a dedicated skills section:
        if section_name.lower() in ("skills", "technical skills"):
            cleaned_skills_text = self._clean_skills_section_text(section_text)
            # Parse delimited items directly for high precision
            raw_tokens = self.normalizer.parse_raw_skills(cleaned_skills_text)
            for token in raw_tokens:
                cleaned = self.normalizer.clean_token(token)
                if not cleaned:
                    continue
                # Handle single-letter C or R in dedicated skills lists
                if cleaned.upper() in ("C", "R"):
                    canon = cleaned.upper()
                    occurrences.append({
                        "canonical_name": canon,
                        "original_mention": cleaned,
                        "evidence": f"Skills: {cleaned}",
                        "section": "skills",
                    })
                    continue

                if self.normalizer.is_canonical(cleaned):
                    canon = self.normalizer.normalize_skill(cleaned)
                    occurrences.append({
                        "canonical_name": canon,
                        "original_mention": cleaned,
                        "evidence": f"Skills: {cleaned}",
                        "section": "skills",
                    })

        # Process text line by line / sentence by sentence with regex patterns
        sentences = self._split_into_sentences_or_bullets(section_text)
        for sentence in sentences:
            # Check for patterns
            for surface, canon, regex_pat, _ in self._compiled_patterns:
                for match in regex_pat.finditer(sentence):
                    start_idx = match.start()
                    matched_str = match.group(0)

                    # Check for negation
                    if self._is_negated_in_sentence(sentence, start_idx):
                        continue

                    occurrences.append({
                        "canonical_name": canon,
                        "original_mention": matched_str,
                        "evidence": sentence,
                        "section": section_name.lower(),
                    })

        return occurrences

    def extract_unresolved_skills(
        self,
        skills_section_text: str,
        canonical_found: Set[str],
    ) -> List[UnresolvedSkill]:
        """Extract non-taxonomy technical candidates listed in the skills section."""
        unresolved: List[UnresolvedSkill] = []
        if not skills_section_text:
            return unresolved

        seen_terms: Set[str] = set()
        cleaned_skills_text = self._clean_skills_section_text(skills_section_text)
        raw_tokens = self.normalizer.parse_raw_skills(cleaned_skills_text)

        for token in raw_tokens:
            cleaned = self.normalizer.clean_token(token)
            if not cleaned or len(cleaned) < 2:
                continue

            cleaned_lower = cleaned.lower()
            # Strip trailing colon if any
            cleaned_lower = cleaned_lower.rstrip(":")

            # Skip generic headings or stopwords
            if cleaned_lower in GENERIC_HEADER_TOKENS:
                continue

            # Skip if resolved to canonical
            if self.normalizer.is_canonical(cleaned):
                continue
            if cleaned_lower in [c.lower() for c in canonical_found]:
                continue

            # If plausible technical term (contains letters, not pure numbers)
            if re.search(r"[a-zA-Z]", cleaned) and cleaned_lower not in seen_terms:
                seen_terms.add(cleaned_lower)

                unresolved.append(
                    UnresolvedSkill(
                        term=cleaned,
                        evidence=f"Listed in Skills section: {cleaned}",
                        reason="not_in_current_taxonomy",
                        source_section="skills",
                    )
                )

        return unresolved

    @staticmethod
    def _compute_skill_confidence(
        source_sections: Set[str],
        evidence_count: int,
    ) -> float:
        """Compute deterministic heuristic evidence confidence score (0.0 to 1.0).

        Baseline weights:
        - Skills section: 0.90
        - Projects / Experience: 0.85
        - Certifications / Coursework: 0.80
        - Summary / Objective: 0.75
        - Other: 0.70

        Boosts:
        - Mentioned in Skills AND (Projects or Experience): +0.06
        - Each additional section beyond primary: +0.03
        - Multiple distinct evidence sentences (> 1): +0.02
        Bounded strictly <= 1.0.
        """
        # Determine base from strongest section
        if "skills" in source_sections:
            base = 0.90
        elif "experience" in source_sections or "projects" in source_sections:
            base = 0.85
        elif "certifications" in source_sections or "coursework" in source_sections:
            base = 0.80
        elif "summary" in source_sections or "objective" in source_sections:
            base = 0.75
        else:
            base = 0.70

        boost = 0.0

        # Synergy: Skills + practical application (projects or experience)
        if "skills" in source_sections and ("projects" in source_sections or "experience" in source_sections):
            boost += 0.06

        # Additional section breadth
        if len(source_sections) > 1:
            boost += 0.03 * (len(source_sections) - 1)

        # Depth of evidence sentences
        if evidence_count > 1:
            boost += 0.02

        final_score = min(1.0, base + boost)
        return round(final_score, 2)

    def extract_skills(
        self, parsed_resume: ParsedResume
    ) -> Tuple[List[ExtractedSkill], List[UnresolvedSkill]]:
        """Extract, normalize, and score all skills from a parsed resume document."""
        all_occurrences: List[Dict[str, Any]] = []

        # Sections to inspect with priorities
        section_map = {
            "skills": parsed_resume.sections.skills or "",
            "projects": parsed_resume.sections.projects or "",
            "experience": parsed_resume.sections.experience or "",
            "summary": parsed_resume.sections.summary or "",
            "objective": parsed_resume.sections.objective or "",
            "certifications": parsed_resume.sections.certifications or "",
            "coursework": parsed_resume.sections.coursework or "",
            "education": parsed_resume.sections.education or "",
            "achievements": parsed_resume.sections.achievements or "",
            "other": parsed_resume.sections.other or "",
        }

        # If sections are entirely empty (e.g. unsegmented resume), fall back to cleaned_text
        has_any_section = any(bool(v.strip()) for v in section_map.values())
        if not has_any_section and parsed_resume.cleaned_text:
            all_occurrences.extend(
                self.extract_skills_from_section_text(parsed_resume.cleaned_text, "other")
            )
        else:
            for sec_name, sec_text in section_map.items():
                if sec_text and sec_text.strip():
                    occurrences = self.extract_skills_from_section_text(sec_text, sec_name)
                    all_occurrences.extend(occurrences)

        # Group by canonical skill name
        grouped: Dict[str, Dict[str, Any]] = {}
        for occ in all_occurrences:
            canon = occ["canonical_name"]
            if canon not in grouped:
                grouped[canon] = {
                    "canonical_name": canon,
                    "original_mentions": set(),
                    "source_sections": set(),
                    "evidence": [],
                }
            grouped[canon]["original_mentions"].add(occ["original_mention"])
            grouped[canon]["source_sections"].add(occ["section"])
            # Add evidence if not already present
            ev = occ["evidence"].strip()
            if ev and ev not in grouped[canon]["evidence"]:
                grouped[canon]["evidence"].append(ev)

        # Construct ExtractedSkill objects
        extracted_skills: List[ExtractedSkill] = []
        canonical_names_found: Set[str] = set()

        for canon, data in grouped.items():
            canonical_names_found.add(canon)
            confidence = self._compute_skill_confidence(
                source_sections=data["source_sections"],
                evidence_count=len(data["evidence"]),
            )
            extracted_skills.append(
                ExtractedSkill(
                    name=canon,
                    confidence=confidence,
                    original_mentions=sorted(list(data["original_mentions"])),
                    source_sections=sorted(list(data["source_sections"])),
                    evidence=data["evidence"],
                )
            )

        # Sort by confidence descending, then name ascending
        extracted_skills.sort(key=lambda s: (-s.confidence, s.name))

        # Extract unresolved skills from skills section
        unresolved_skills = self.extract_unresolved_skills(
            skills_section_text=section_map["skills"],
            canonical_found=canonical_names_found,
        )

        return extracted_skills, unresolved_skills
