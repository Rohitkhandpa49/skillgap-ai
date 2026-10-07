"""Skill Normalization Module for SkillGap AI.

This module provides canonical skill resolution and taxonomy matching:
- Loads canonical skills from data/skills.json
- Loads alias mappings from data/aliases.json
- Performs case-insensitive matching while preserving readable display names
- Distinguishes distinct technologies (Java != JavaScript, Data Analysis != Data Science)
- Preserves technical punctuation in skills (C, C++, C#, .NET, Node.js, React.js, R, SQL, PL/SQL)
- Splits raw skill lists on common delimiters (,, |, ;, \n, and safe / handling)
- Deduplicates canonical skills per record
- Preserves unresolved/unknown skills rather than silently dropping them
"""

import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple, Union


def get_taxonomy_paths() -> Tuple[Path, Path]:
    """Resolve paths to skills.json and aliases.json relative to repository root."""
    # Current file: <repo_root>/ai-service/app/preprocessing/skill_normalizer.py
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    skills_file = repo_root / "data" / "skills.json"
    aliases_file = repo_root / "data" / "aliases.json"
    return skills_file, aliases_file


class SkillNormalizer:
    """Canonical skill normalizer and taxonomy matcher."""

    def __init__(
        self,
        skills_path: Optional[Union[str, Path]] = None,
        aliases_path: Optional[Union[str, Path]] = None,
    ) -> None:
        default_skills_path, default_aliases_path = get_taxonomy_paths()
        self.skills_path = Path(skills_path) if skills_path else default_skills_path
        self.aliases_path = Path(aliases_path) if aliases_path else default_aliases_path

        self.canonical_skills: List[str] = []
        self.canonical_lower_map: Dict[str, str] = {}
        self.aliases_lower_map: Dict[str, str] = {}

        self.load_taxonomy()

    def load_taxonomy(self) -> None:
        """Load canonical skills and aliases from JSON files."""
        if self.skills_path.exists():
            with open(self.skills_path, "r", encoding="utf-8") as f:
                self.canonical_skills = json.load(f)
                self.canonical_lower_map = {
                    s.lower(): s for s in self.canonical_skills
                }
        else:
            self.canonical_skills = []
            self.canonical_lower_map = {}

        if self.aliases_path.exists():
            with open(self.aliases_path, "r", encoding="utf-8") as f:
                raw_aliases: Dict[str, str] = json.load(f)
                self.aliases_lower_map = {
                    k.lower(): v for k, v in raw_aliases.items()
                }
        else:
            self.aliases_lower_map = {}

    @staticmethod
    def clean_token(token: str) -> str:
        """Clean whitespace and safe artifacts while preserving technical punctuation."""
        if not token:
            return ""
        s = token.strip()
        # Remove repeated whitespace
        s = re.sub(r"\s+", " ", s)
        # Strip trailing 2+ dots (ellipses like 'Rest...' or '...')
        s = re.sub(r"\.{2,}$", "", s).strip()
        # Strip trailing colon, comma, or semicolon if attached
        s = re.sub(r"[,;:]$", "", s).strip()
        return s

    def normalize_skill(self, skill: str) -> str:
        """Normalize a single skill string to its canonical display name if mapped.

        If unresolved, returns the cleaned original skill string to preserve unknown skills.
        """
        cleaned = self.clean_token(skill)
        if not cleaned or cleaned == "...":
            return ""

        lower_key = cleaned.lower()

        # 1. Direct alias match
        if lower_key in self.aliases_lower_map:
            return self.aliases_lower_map[lower_key]

        # 2. Direct canonical match
        if lower_key in self.canonical_lower_map:
            return self.canonical_lower_map[lower_key]

        return cleaned

    def is_canonical(self, skill: str) -> bool:
        """Check whether a skill string resolves to a canonical skill in the taxonomy."""
        cleaned = self.clean_token(skill)
        if not cleaned or cleaned == "...":
            return False
        lower_key = cleaned.lower()
        return (
            lower_key in self.aliases_lower_map
            or lower_key in self.canonical_lower_map
        )

    def parse_raw_skills(self, skills_input: Optional[Union[str, List[str]]]) -> List[str]:
        """Split raw skill strings using common delimiters (comma, pipe, semicolon, newline).

        Carefully handles compound slash tokens (e.g. 'C / C++' -> ['C', 'C++']
        while preserving single tokens like 'PL/SQL', 'CI/CD', 'UI/UX').
        """
        if skills_input is None:
            return []

        if isinstance(skills_input, list):
            raw_tokens: List[str] = [str(x) for x in skills_input]
        else:
            text = str(skills_input)
            if not text.strip():
                return []
            # Split by comma, pipe, semicolon, newline
            split_pattern = re.compile(r"[,|;\n]+")
            raw_tokens = split_pattern.split(text)

        tokens: List[str] = []
        for raw_tok in raw_tokens:
            cleaned = self.clean_token(raw_tok)
            if not cleaned or cleaned == "...":
                continue

            # Check if token contains slash
            if "/" in cleaned:
                lower_tok = cleaned.lower()
                # If the entire token matches an alias or canonical skill (e.g. PL/SQL, CI/CD, UI/UX)
                if (
                    lower_tok in self.aliases_lower_map
                    or lower_tok in self.canonical_lower_map
                ):
                    tokens.append(cleaned)
                else:
                    # Split on slash (e.g. C / C++, SPSS / SAS, Java / J2EE)
                    sub_parts = [self.clean_token(p) for p in cleaned.split("/") if self.clean_token(p)]
                    if sub_parts:
                        tokens.extend(sub_parts)
                    else:
                        tokens.append(cleaned)
            else:
                tokens.append(cleaned)

        return tokens

    def parse_and_normalize_skills(
        self, skills_input: Optional[Union[str, List[str]]]
    ) -> Tuple[List[str], List[str]]:
        """Parse raw skill text or list and return (canonical_skills, unresolved_skills).

        Both lists are deduplicated while preserving order of first appearance.
        """
        tokens = self.parse_raw_skills(skills_input)

        canonical_skills: List[str] = []
        unresolved_skills: List[str] = []
        seen_canonical: Set[str] = set()
        seen_unresolved: Set[str] = set()

        for token in tokens:
            cleaned = self.clean_token(token)
            if not cleaned or cleaned == "...":
                continue

            lower_key = cleaned.lower()

            if lower_key in self.aliases_lower_map:
                canon_name = self.aliases_lower_map[lower_key]
                if canon_name not in seen_canonical:
                    seen_canonical.add(canon_name)
                    canonical_skills.append(canon_name)
            elif lower_key in self.canonical_lower_map:
                canon_name = self.canonical_lower_map[lower_key]
                if canon_name not in seen_canonical:
                    seen_canonical.add(canon_name)
                    canonical_skills.append(canon_name)
            else:
                # Unresolved skill
                if cleaned.lower() not in seen_unresolved:
                    seen_unresolved.add(cleaned.lower())
                    unresolved_skills.append(cleaned)

        return canonical_skills, unresolved_skills

    def normalize_skills(
        self, skills_input: Optional[Union[str, List[str]]]
    ) -> Dict[str, List[str]]:
        """Convenience method returning a dictionary with canonical and unknown skills."""
        canon, unknown = self.parse_and_normalize_skills(skills_input)
        return {
            "canonical_skills": canon,
            "unknown_skills": unknown,
        }
