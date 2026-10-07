"""Baseline Candidate-to-Job Matching Engine for SkillGap AI.

This module provides a deterministic and explainable baseline matching engine:
- Normalizes candidate skills using canonical taxonomy and alias resolution
- Fits once and persists job TF-IDF representations (vectorizer and sparse matrix)
- Preserves technical identifiers (C, C++, C#, .NET, Node.js, React.js, R, SQL)
- Calculates explicit skill overlap score (0.0 to 1.0)
- Calculates TF-IDF cosine text similarity (0.0 to 1.0)
- Combines scores using explainable baseline heuristic weighting:
    Final Match Score = (0.70 * Skill Overlap + 0.30 * Text Similarity) * 100
- Performs deterministic ranking with clear tie-breakers
- Evaluates experience compatibility as an explanatory factor without biasing core score
- Generates transparent, human-readable explanations
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.matching.schemas import (
    CandidateProfile,
    ExperienceComparison,
    JobMatchResult,
    MatchingResponse,
    ScoreComponents,
)
from app.preprocessing.skill_normalizer import SkillNormalizer

# Token pattern preserving C, C++, C#, .NET, Node.js, React.js, R, etc.
TFIDF_TOKEN_PATTERN: str = (
    r"(?u)\b[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+|\.[a-zA-Z0-9_]+|\b[a-zA-Z0-9_]+(?:\+\+|#)?"
)

# Baseline heuristic weights (documented as baseline heuristic, not production ML)
WEIGHT_SKILL_OVERLAP: float = 0.70
WEIGHT_TEXT_SIMILARITY: float = 0.30


def get_matching_paths() -> Dict[str, Path]:
    """Resolve repository paths for matching engine artifacts."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    processed_jobs_json = repo_root / "data" / "processed" / "analytics_jobs" / "job_profiles.json"
    matching_models_dir = repo_root / "ai-service" / "models" / "matching"
    matching_eval_dir = repo_root / "ai-service" / "evaluation" / "matching"

    matching_models_dir.mkdir(parents=True, exist_ok=True)
    matching_eval_dir.mkdir(parents=True, exist_ok=True)

    return {
        "repo_root": repo_root,
        "job_profiles_json": processed_jobs_json,
        "models_dir": matching_models_dir,
        "vectorizer_file": matching_models_dir / "tfidf_vectorizer.joblib",
        "job_matrix_file": matching_models_dir / "job_tfidf_matrix.joblib",
        "job_ids_file": matching_models_dir / "job_tfidf_job_ids.json",
        "metadata_file": matching_models_dir / "baseline_matching_metadata.json",
        "eval_dir": matching_eval_dir,
        "test_candidates_file": matching_eval_dir / "test_candidates.json",
        "report_file": repo_root / "ai-service" / "evaluation" / "baseline_matching_evaluation.md",
    }


def build_job_text(job: Dict[str, Any]) -> str:
    """Build composite textual representation of a job posting for TF-IDF vectorization."""
    parts: List[str] = []
    title = job.get("job_title_normalized") or job.get("job_title") or ""
    if title:
        parts.append(title)

    canonical_skills = job.get("skills") or []
    if canonical_skills:
        parts.append(" ".join(canonical_skills))

    unknown_skills = job.get("unknown_skills") or []
    if unknown_skills:
        parts.append(" ".join(unknown_skills))

    desc = job.get("job_description") or ""
    if desc:
        parts.append(desc)

    return " ".join(parts).strip()


def build_candidate_text(
    summary: str,
    canonical_skills: List[str],
    unknown_skills: List[str],
) -> str:
    """Build composite textual representation of a candidate for TF-IDF vectorization."""
    parts: List[str] = []
    if summary and summary.strip():
        parts.append(summary.strip())
    if canonical_skills:
        parts.append(" ".join(canonical_skills))
    if unknown_skills:
        parts.append(" ".join(unknown_skills))
    return " ".join(parts).strip()


def compare_experience(
    candidate_years: Optional[float],
    min_years: Optional[float],
    max_years: Optional[float],
) -> ExperienceComparison:
    """Compare candidate experience against job requirement as explanatory metadata."""
    if candidate_years is None or min_years is None:
        return ExperienceComparison(
            candidate_years=candidate_years,
            required_min_years=min_years,
            required_max_years=max_years,
            status="unspecified",
        )

    if candidate_years >= min_years:
        status = "compatible"
    else:
        status = "gap"

    return ExperienceComparison(
        candidate_years=candidate_years,
        required_min_years=min_years,
        required_max_years=max_years,
        status=status,
    )


class BaselineMatcher:
    """Explainable baseline matching engine combining skill overlap and TF-IDF similarity."""

    def __init__(
        self,
        paths: Optional[Dict[str, Path]] = None,
        normalizer: Optional[SkillNormalizer] = None,
        auto_load: bool = True,
    ) -> None:
        self.paths = paths or get_matching_paths()
        self.normalizer = normalizer or SkillNormalizer()
        self.job_profiles: List[Dict[str, Any]] = []
        self.job_id_to_profile: Dict[str, Dict[str, Any]] = {}
        self.job_ids: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.job_matrix: Optional[Any] = None

        if auto_load:
            self.load_or_fit()

    def load_job_profiles(self) -> List[Dict[str, Any]]:
        """Load processed job profiles from disk."""
        profiles_file = self.paths["job_profiles_json"]
        if not profiles_file.exists():
            raise FileNotFoundError(
                f"Processed job profiles not found at {profiles_file}. "
                "Run analytics_jobs_preprocessing.py first."
            )
        with open(profiles_file, "r", encoding="utf-8") as f:
            self.job_profiles = json.load(f)

        self.job_ids = [p["job_id"] for p in self.job_profiles]
        self.job_id_to_profile = {p["job_id"]: p for p in self.job_profiles}
        return self.job_profiles

    def fit_and_persist(self) -> None:
        """Fit TF-IDF vectorizer exclusively on the job corpus and persist artifacts."""
        if not self.job_profiles:
            self.load_job_profiles()

        job_texts = [build_job_text(job) for job in self.job_profiles]

        self.vectorizer = TfidfVectorizer(
            token_pattern=TFIDF_TOKEN_PATTERN,
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_features=10000,
        )

        self.job_matrix = self.vectorizer.fit_transform(job_texts)

        # Persist vectorizer, matrix, and job IDs
        joblib.dump(self.vectorizer, self.paths["vectorizer_file"])
        joblib.dump(self.job_matrix, self.paths["job_matrix_file"])
        with open(self.paths["job_ids_file"], "w", encoding="utf-8") as f:
            json.dump(self.job_ids, f, indent=2)

        # Persist metadata
        metadata = {
            "version": "1.0.0",
            "algorithm": "Baseline Hybrid (Explicit Skill Overlap + TF-IDF Cosine Similarity)",
            "weighting_formula": f"{WEIGHT_SKILL_OVERLAP:.2f} * Skill Overlap + {WEIGHT_TEXT_SIMILARITY:.2f} * Text Similarity",
            "weights": {
                "skill_overlap": WEIGHT_SKILL_OVERLAP,
                "text_similarity": WEIGHT_TEXT_SIMILARITY,
            },
            "total_jobs": len(self.job_profiles),
            "tfidf_configuration": {
                "token_pattern": TFIDF_TOKEN_PATTERN,
                "ngram_range": [1, 2],
                "min_df": 2,
                "max_features": 10000,
                "stop_words": "english",
                "vocabulary_size": len(self.vectorizer.vocabulary_),
            },
            "artifacts": {
                "vectorizer": str(self.paths["vectorizer_file"].name),
                "matrix": str(self.paths["job_matrix_file"].name),
                "job_ids": str(self.paths["job_ids_file"].name),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": (
                "Baseline heuristic weighting. Excludes JDS salary-hike classifier and "
                "SDS personality-success classifier to prevent algorithmic bias in job suitability."
            ),
        }
        with open(self.paths["metadata_file"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_or_fit(self) -> None:
        """Load persisted TF-IDF artifacts if available, otherwise fit and persist."""
        self.load_job_profiles()

        vec_path = self.paths["vectorizer_file"]
        mat_path = self.paths["job_matrix_file"]
        ids_path = self.paths["job_ids_file"]

        if vec_path.exists() and mat_path.exists() and ids_path.exists():
            self.vectorizer = joblib.load(vec_path)
            self.job_matrix = joblib.load(mat_path)
            with open(ids_path, "r", encoding="utf-8") as f:
                saved_ids = json.load(f)
            # Verify ordering consistency
            if saved_ids != self.job_ids:
                # Re-fit if job IDs changed
                self.fit_and_persist()
        else:
            self.fit_and_persist()

    def compute_skill_overlap(
        self,
        candidate_skills: Set[str],
        job_skills: Set[str],
    ) -> Tuple[float, List[str], List[str], List[str]]:
        """Calculate normalized explicit skill overlap score and skill partitions.

        Returns:
            (overlap_score, matched_skills, missing_skills, candidate_only_skills)
        """
        if not job_skills:
            # Policy: if job has no required skills, overlap is 0.0 (cannot divide by zero)
            matched = []
            missing = []
            candidate_only = sorted(list(candidate_skills))
            return 0.0, matched, missing, candidate_only

        matched_set = candidate_skills.intersection(job_skills)
        missing_set = job_skills.difference(candidate_skills)
        candidate_only_set = candidate_skills.difference(job_skills)

        overlap_score = len(matched_set) / len(job_skills)
        overlap_score = max(0.0, min(1.0, float(overlap_score)))

        return (
            overlap_score,
            sorted(list(matched_set)),
            sorted(list(missing_set)),
            sorted(list(candidate_only_set)),
        )

    def generate_explanations(
        self,
        matched_skills: List[str],
        missing_skills: List[str],
        total_required: int,
        overlap_score: float,
        text_similarity: float,
        experience: ExperienceComparison,
    ) -> List[str]:
        """Generate human-readable, factual explanation bullet points."""
        bullets: List[str] = []

        if total_required == 0:
            bullets.append(
                "Job has no explicitly listed required skills; match is driven by text similarity."
            )
        else:
            bullets.append(
                f"{len(matched_skills)} of {total_required} required skills matched "
                f"({round(overlap_score * 100, 1)}% coverage)."
            )

        if matched_skills:
            bullets.append(f"Matched skills: {', '.join(matched_skills[:6])}")
        if missing_skills:
            bullets.append(f"Missing skills to acquire: {', '.join(missing_skills[:6])}")

        bullets.append(f"Textual context similarity: {round(text_similarity * 100, 1)}%.")

        if experience.status == "compatible":
            bullets.append(
                f"Experience compatible: candidate ({experience.candidate_years:g} yrs) "
                f"meets minimum requirement ({experience.required_min_years:g} yrs)."
            )
        elif experience.status == "gap":
            bullets.append(
                f"Experience gap: job requires {experience.required_min_years:g} yrs "
                f"(candidate has {experience.candidate_years:g} yrs)."
            )

        return bullets

    def match_candidate(
        self,
        candidate: Union[CandidateProfile, Dict[str, Any]],
        top_k: int = 10,
    ) -> MatchingResponse:
        """Rank job postings against candidate profile using explainable baseline formula."""
        if isinstance(candidate, dict):
            profile = CandidateProfile(**candidate)
        else:
            profile = candidate

        # 1. Normalize candidate skills
        canon_skills, unknown_skills = self.normalizer.parse_and_normalize_skills(
            profile.skills
        )
        # Unified candidate skills set (case-insensitive internally for unknown skills)
        candidate_skills_set = set(canon_skills) | set(unknown_skills)
        candidate_skills_lower_map = {s.lower(): s for s in candidate_skills_set}

        # 2. Compute TF-IDF text similarity
        cand_text = build_candidate_text(
            summary=profile.summary or "",
            canonical_skills=canon_skills,
            unknown_skills=unknown_skills,
        )

        if not cand_text.strip():
            # Empty candidate produces 0.0 text similarity across all jobs
            text_sims = np.zeros(len(self.job_profiles), dtype=float)
        else:
            cand_vec = self.vectorizer.transform([cand_text])
            # Sparse dot product cosine similarity
            sims = cosine_similarity(cand_vec, self.job_matrix).ravel()
            # Clip bounds safely to 0.0 <= sim <= 1.0
            text_sims = np.clip(sims, 0.0, 1.0)

        # 3. Evaluate each job and calculate combined score
        results: List[JobMatchResult] = []

        for idx, job in enumerate(self.job_profiles):
            job_canon_skills = job.get("skills") or []
            job_unknown_skills = job.get("unknown_skills") or []
            job_skills_list = job_canon_skills + job_unknown_skills

            # Standardize job skills set
            job_skills_set = set(job_skills_list)

            # Case-insensitive resolution between candidate and job skills
            resolved_job_skills: Set[str] = set()
            resolved_cand_skills: Set[str] = set()

            for js in job_skills_set:
                js_lower = js.lower()
                if js_lower in candidate_skills_lower_map:
                    # Match found! Map to common representation
                    canonical_repr = candidate_skills_lower_map[js_lower]
                    resolved_cand_skills.add(canonical_repr)
                    resolved_job_skills.add(canonical_repr)
                else:
                    resolved_job_skills.add(js)

            # Add remaining candidate skills
            for cs in candidate_skills_set:
                if cs not in resolved_cand_skills:
                    resolved_cand_skills.add(cs)

            # Skill overlap
            overlap_score, matched_skills, missing_skills, candidate_only_skills = (
                self.compute_skill_overlap(
                    candidate_skills=resolved_cand_skills,
                    job_skills=resolved_job_skills,
                )
            )

            sim_score = float(text_sims[idx])

            # Weighted final score: 0.70 * Skill Overlap + 0.30 * Text Similarity
            final_score_raw = (
                WEIGHT_SKILL_OVERLAP * overlap_score
                + WEIGHT_TEXT_SIMILARITY * sim_score
            )
            # Normalization check: bound to 0.0 to 1.0
            final_score_raw = max(0.0, min(1.0, final_score_raw))
            match_score_pct = round(final_score_raw * 100.0, 2)

            # Experience comparison (explanatory only)
            exp_info = job.get("experience") or {}
            min_exp = exp_info.get("min_years")
            max_exp = exp_info.get("max_years")
            exp_comp = compare_experience(
                candidate_years=profile.experience_years,
                min_years=float(min_exp) if min_exp is not None else None,
                max_years=float(max_exp) if max_exp is not None else None,
            )

            # Generate explanations
            explanation = self.generate_explanations(
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                total_required=len(resolved_job_skills),
                overlap_score=overlap_score,
                text_similarity=sim_score,
                experience=exp_comp,
            )

            results.append(
                JobMatchResult(
                    job_id=job["job_id"],
                    job_title=job.get("job_title_normalized") or job.get("job_title") or "Unknown",
                    match_score=match_score_pct,
                    components=ScoreComponents(
                        skill_overlap=round(overlap_score, 4),
                        text_similarity=round(sim_score, 4),
                    ),
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    candidate_only_skills=candidate_only_skills,
                    experience=exp_comp,
                    explanation=explanation,
                    location=job.get("location"),
                    salary_raw=job.get("salary_raw"),
                )
            )

        # 4. Deterministic Ranking
        # Primary: match_score descending
        # Secondary tie-breaker: skill_overlap descending
        # Final tie-breaker: job_id ascending
        ranked_results = sorted(
            results,
            key=lambda r: (-r.match_score, -r.components.skill_overlap, r.job_id),
        )

        top_matches = ranked_results[:top_k]

        return MatchingResponse(
            candidate_id=profile.candidate_id,
            normalized_candidate_skills=canon_skills,
            unknown_candidate_skills=unknown_skills,
            total_jobs_evaluated=len(self.job_profiles),
            top_matches=top_matches,
        )
