"""Hybrid Candidate-to-Job Matching Engine for SkillGap AI.

Combines three distinct matching signals using explainable Version 1 heuristic weights:
- 50% Explicit Skill Overlap (highest weight for transparent explainability)
- 20% TF-IDF Lexical Similarity (preserves exact technical keywords)
- 30% Sentence Transformer Semantic Similarity (recognizes contextual intent & synonymy)

Formula:
    Final Score = (0.50 * Skill Overlap + 0.20 * TF-IDF Similarity + 0.30 * Semantic Similarity) * 100

Excludes JDS salary-hike classifier and SDS personality-success classifier to prevent
algorithmic bias in job suitability.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

import numpy as np

from app.matching.baseline_matcher import BaselineMatcher
from app.matching.schemas import (
    CandidateProfile,
    ExperienceComparison,
    JobMatchResult,
    MatchingResponse,
    ScoreComponents,
)
from app.matching.semantic_matcher import SemanticMatcher
from app.preprocessing.skill_normalizer import SkillNormalizer

# Version 1 Heuristic Weights
WEIGHT_HYBRID_SKILL_OVERLAP: float = 0.50
WEIGHT_HYBRID_TFIDF: float = 0.20
WEIGHT_HYBRID_SEMANTIC: float = 0.30


def get_hybrid_metadata_path() -> Path:
    """Return path to hybrid matching metadata artifact."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    models_dir = repo_root / "ai-service" / "models" / "matching"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir / "hybrid_matching_metadata.json"


class HybridMatcher:
    """Explainable hybrid matching engine blending skill overlap, TF-IDF, and dense semantics."""

    def __init__(
        self,
        baseline_matcher: Optional[BaselineMatcher] = None,
        semantic_matcher: Optional[SemanticMatcher] = None,
        normalizer: Optional[SkillNormalizer] = None,
        auto_persist_metadata: bool = True,
    ) -> None:
        self.normalizer = normalizer or SkillNormalizer()
        self.baseline_matcher = baseline_matcher or BaselineMatcher(normalizer=self.normalizer)
        self.semantic_matcher = semantic_matcher or SemanticMatcher(normalizer=self.normalizer)

        if auto_persist_metadata:
            self.save_metadata()

    def save_metadata(self) -> None:
        """Persist metadata describing hybrid matching configuration and weights."""
        metadata_file = get_hybrid_metadata_path()
        metadata = {
            "version": "1.0.0",
            "model_type": "Hybrid Matcher v1 (Heuristic)",
            "weights": {
                "skill_overlap": WEIGHT_HYBRID_SKILL_OVERLAP,
                "tfidf_similarity": WEIGHT_HYBRID_TFIDF,
                "semantic_similarity": WEIGHT_HYBRID_SEMANTIC,
            },
            "formula": (
                f"{WEIGHT_HYBRID_SKILL_OVERLAP:.2f} * Skill Overlap + "
                f"{WEIGHT_HYBRID_TFIDF:.2f} * TF-IDF Similarity + "
                f"{WEIGHT_HYBRID_SEMANTIC:.2f} * Semantic Similarity"
            ),
            "rationale": (
                "Explicit required skills get the highest weight (50%) to ensure transparent explainability. "
                "Semantic embeddings (30%) capture meaning and synonyms across titles and project summaries. "
                "TF-IDF (20%) grounds recommendations in exact technical vocabulary. "
                "JDS and SDS predictions are strictly excluded."
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def generate_hybrid_explanations(
        self,
        matched_skills: List[str],
        missing_skills: List[str],
        total_required: int,
        overlap_score: float,
        tfidf_sim: float,
        semantic_sim: float,
        experience: ExperienceComparison,
    ) -> List[str]:
        """Generate human-readable explanations summarizing all three signals."""
        bullets: List[str] = []

        if total_required == 0:
            bullets.append("Job has no explicitly listed required skills; match is driven by contextual text.")
        else:
            bullets.append(
                f"{len(matched_skills)} of {total_required} required skills matched "
                f"({round(overlap_score * 100, 1)}% coverage)."
            )

        if matched_skills:
            bullets.append(f"Matched skills: {', '.join(matched_skills[:6])}.")
        if missing_skills:
            bullets.append(f"Missing skills to acquire: {', '.join(missing_skills[:6])}.")

        bullets.append(
            f"Semantic contextual similarity: {round(semantic_sim * 100, 1)}% | "
            f"Lexical keyword overlap: {round(tfidf_sim * 100, 1)}%."
        )

        if experience.status == "compatible":
            bullets.append(
                f"Experience compatible: candidate ({experience.candidate_years:g} yrs) "
                f"meets minimum requirement ({experience.required_min_years:g} yrs)."
            )
        elif experience.status == "gap":
            bullets.append(
                f"Experience gap: requires {experience.required_min_years:g} yrs "
                f"(candidate has {experience.candidate_years:g} yrs)."
            )

        return bullets

    def match_candidate(
        self,
        candidate: Union[CandidateProfile, Dict[str, Any]],
        top_k: int = 10,
    ) -> MatchingResponse:
        """Rank job postings using the tripartite hybrid scoring formula."""
        if isinstance(candidate, dict):
            profile = CandidateProfile(**candidate)
        else:
            profile = candidate

        # 1. Run baseline matcher (yields skill overlap, TF-IDF similarity, partitions, experience)
        # Request all jobs to combine scores uniformly
        baseline_resp = self.baseline_matcher.match_candidate(
            profile,
            top_k=len(self.baseline_matcher.job_profiles),
        )

        # 2. Run semantic matcher to obtain semantic cosine similarity vector
        semantic_sims = self.semantic_matcher.compute_semantic_similarities(profile)

        # Build mapping from job_id to semantic similarity
        job_id_to_semantic = {
            job_id: float(semantic_sims[i])
            for i, job_id in enumerate(self.semantic_matcher.job_ids)
        }

        # 3. Combine scores into Hybrid Match v1
        hybrid_results: List[JobMatchResult] = []

        for b_match in baseline_resp.top_matches:
            job_id = b_match.job_id
            overlap = b_match.components.skill_overlap
            tfidf_sim = (
                b_match.components.tfidf_similarity
                if b_match.components.tfidf_similarity is not None
                else b_match.components.text_similarity
            )
            semantic_sim = job_id_to_semantic.get(job_id, 0.0)

            # Version 1 Heuristic Formula
            final_raw = (
                WEIGHT_HYBRID_SKILL_OVERLAP * overlap
                + WEIGHT_HYBRID_TFIDF * tfidf_sim
                + WEIGHT_HYBRID_SEMANTIC * semantic_sim
            )
            final_raw = max(0.0, min(1.0, final_raw))
            match_score = round(final_raw * 100.0, 2)

            total_required = len(b_match.matched_skills) + len(b_match.missing_skills)
            explanations = self.generate_hybrid_explanations(
                matched_skills=b_match.matched_skills,
                missing_skills=b_match.missing_skills,
                total_required=total_required,
                overlap_score=overlap,
                tfidf_sim=tfidf_sim,
                semantic_sim=semantic_sim,
                experience=b_match.experience,
            )

            hybrid_results.append(
                JobMatchResult(
                    job_id=job_id,
                    job_title=b_match.job_title,
                    match_score=match_score,
                    components=ScoreComponents(
                        skill_overlap=round(overlap, 4),
                        text_similarity=round(tfidf_sim, 4),
                        tfidf_similarity=round(tfidf_sim, 4),
                        semantic_similarity=round(semantic_sim, 4),
                    ),
                    matched_skills=b_match.matched_skills,
                    missing_skills=b_match.missing_skills,
                    candidate_only_skills=b_match.candidate_only_skills,
                    experience=b_match.experience,
                    explanation=explanations,
                    location=b_match.location,
                    salary_raw=b_match.salary_raw,
                )
            )

        # 4. Deterministic Ranking
        # Primary: match_score desc
        # Secondary tie-breaker: skill_overlap desc
        # Final tie-breaker: job_id asc
        ranked = sorted(
            hybrid_results,
            key=lambda r: (-r.match_score, -r.components.skill_overlap, r.job_id),
        )

        return MatchingResponse(
            candidate_id=profile.candidate_id,
            normalized_candidate_skills=baseline_resp.normalized_candidate_skills,
            unknown_candidate_skills=baseline_resp.unknown_candidate_skills,
            total_jobs_evaluated=len(hybrid_results),
            top_matches=ranked[:top_k],
            weighting_formula="0.50 * Skill Overlap + 0.20 * TF-IDF + 0.30 * Semantic Similarity",
        )
