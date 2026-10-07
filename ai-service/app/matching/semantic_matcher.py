"""Semantic Job Matching Engine using Sentence Transformers.

This module provides dense semantic vector representations for SkillGap AI:
- Uses sentence-transformers/all-MiniLM-L6-v2 (384-dimensional embeddings)
- Normalizes embeddings (L2 unit vectors) for fast dot-product cosine similarity
- Builds semantic job text from title, skills, and narrative descriptions
- Precomputes and caches job embeddings under ai-service/models/matching/semantic/
- Validates embedding arrays against NaN, Inf, and dimension consistency
- Computes candidate-to-job semantic similarity without recomputing job embeddings
- Independent of web frameworks / FastAPI routing
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import transformers
import sentence_transformers

from app.matching.schemas import (
    CandidateProfile,
    ExperienceComparison,
    JobMatchResult,
    MatchingResponse,
    ScoreComponents,
)
from app.preprocessing.skill_normalizer import SkillNormalizer

MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_EMBEDDING_DIM: int = 384


def get_semantic_paths() -> Dict[str, Path]:
    """Resolve repository paths for semantic matching artifacts."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    processed_jobs_json = repo_root / "data" / "processed" / "analytics_jobs" / "job_profiles.json"
    semantic_dir = repo_root / "ai-service" / "models" / "matching" / "semantic"

    semantic_dir.mkdir(parents=True, exist_ok=True)

    return {
        "repo_root": repo_root,
        "job_profiles_json": processed_jobs_json,
        "semantic_dir": semantic_dir,
        "job_embeddings_file": semantic_dir / "job_embeddings.npy",
        "job_ids_file": semantic_dir / "job_embedding_job_ids.json",
        "metadata_file": semantic_dir / "semantic_embedding_metadata.json",
    }


def build_semantic_job_text(job: Dict[str, Any]) -> str:
    """Build dense semantic text representation for a job posting.

    Excludes job IDs, salary figures, and classification model predictions.
    """
    title = (job.get("job_title_normalized") or job.get("job_title") or "").strip()
    canon_skills = job.get("skills") or []
    unknown_skills = job.get("unknown_skills") or []
    all_skills = canon_skills + unknown_skills
    skills_text = ", ".join(all_skills) if all_skills else ""
    desc = (job.get("job_description") or "").strip()

    parts: List[str] = []
    if title:
        parts.append(f"Job Title: {title}")
    if skills_text:
        parts.append(f"Required Skills: {skills_text}")
    if desc:
        parts.append(f"Description: {desc}")

    return ". ".join(parts).strip()


def build_semantic_candidate_text(
    summary: str,
    canonical_skills: List[str],
    unknown_skills: List[str],
) -> str:
    """Build dense semantic text representation for a candidate.

    Excludes candidate ID, personal demographic attributes, or fabricated info.
    """
    parts: List[str] = []
    clean_summary = (summary or "").strip()
    all_skills = canonical_skills + unknown_skills
    skills_text = ", ".join(all_skills) if all_skills else ""

    if clean_summary:
        parts.append(f"Summary: {clean_summary}")
    if skills_text:
        parts.append(f"Skills: {skills_text}")

    return ". ".join(parts).strip()


class SemanticMatcher:
    """Semantic candidate-to-job matching engine using dense neural embeddings."""

    def __init__(
        self,
        paths: Optional[Dict[str, Path]] = None,
        normalizer: Optional[SkillNormalizer] = None,
        model: Optional[SentenceTransformer] = None,
        auto_load: bool = True,
    ) -> None:
        self.paths = paths or get_semantic_paths()
        self.normalizer = normalizer or SkillNormalizer()
        self._model = model
        self.job_profiles: List[Dict[str, Any]] = []
        self.job_ids: List[str] = []
        self.job_id_to_profile: Dict[str, Dict[str, Any]] = {}
        self.job_embeddings: Optional[np.ndarray] = None

        if auto_load:
            self.load_or_compute_embeddings()

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loader for Sentence Transformer model to optimize memory."""
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME, device="cpu")
        return self._model

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

    def validate_embeddings(self, embeddings: np.ndarray, job_ids: List[str]) -> None:
        """Strict validation of generated embedding matrix."""
        if len(embeddings) != len(job_ids):
            raise ValueError(
                f"Embedding count ({len(embeddings)}) does not match job ID count ({len(job_ids)})"
            )
        if embeddings.shape[1] != EXPECTED_EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) does not match expected {EXPECTED_EMBEDDING_DIM}"
            )
        if np.isnan(embeddings).any():
            raise ValueError("Embedding matrix contains NaN values")
        if np.isinf(embeddings).any():
            raise ValueError("Embedding matrix contains Infinite values")

    def compute_and_save_embeddings(self) -> np.ndarray:
        """Compute semantic embeddings for all job postings and persist artifacts."""
        if not self.job_profiles:
            self.load_job_profiles()

        job_texts = [build_semantic_job_text(job) for job in self.job_profiles]

        t0 = time.time()
        # Encode in batches with L2 unit-norm normalization
        embeddings = self.model.encode(
            job_texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        generation_time = time.time() - t0

        # Validate
        self.validate_embeddings(embeddings, self.job_ids)

        # Persist artifacts
        np.save(self.paths["job_embeddings_file"], embeddings)
        with open(self.paths["job_ids_file"], "w", encoding="utf-8") as f:
            json.dump(self.job_ids, f, indent=2)

        metadata = {
            "model_name": MODEL_NAME,
            "sentence_transformers_version": sentence_transformers.__version__,
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "embedding_dimension": int(embeddings.shape[1]),
            "job_count": len(self.job_ids),
            "normalize_embeddings": True,
            "device": "cpu",
            "generation_time_seconds": round(generation_time, 2),
            "text_fields_used": ["job_title_normalized", "skills", "unknown_skills", "job_description"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": (
                "Normalized L2 embeddings for exact dot-product cosine similarity. "
                "Excludes JDS salary-hike and SDS personality predictions to prevent algorithmic bias."
            ),
        }
        with open(self.paths["metadata_file"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.job_embeddings = embeddings
        return embeddings

    def load_or_compute_embeddings(self) -> np.ndarray:
        """Load cached job embeddings if available and valid; otherwise compute."""
        self.load_job_profiles()

        emb_path = self.paths["job_embeddings_file"]
        ids_path = self.paths["job_ids_file"]

        if emb_path.exists() and ids_path.exists():
            embeddings = np.load(emb_path)
            with open(ids_path, "r", encoding="utf-8") as f:
                saved_ids = json.load(f)

            if len(embeddings) == len(self.job_ids) and saved_ids == self.job_ids:
                self.validate_embeddings(embeddings, saved_ids)
                self.job_embeddings = embeddings
                return embeddings

        return self.compute_and_save_embeddings()

    def encode_candidate(
        self,
        summary: str,
        canonical_skills: List[str],
        unknown_skills: List[str],
    ) -> Optional[np.ndarray]:
        """Generate normalized 384-dimensional embedding for candidate profile."""
        cand_text = build_semantic_candidate_text(summary, canonical_skills, unknown_skills)
        if not cand_text.strip():
            return None

        # Return 1D float32 normalized vector
        emb = self.model.encode(
            [cand_text],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )[0]
        return emb

    def compute_semantic_similarities(
        self,
        candidate: Union[CandidateProfile, Dict[str, Any]],
    ) -> np.ndarray:
        """Compute cosine similarity across all jobs for the candidate profile.

        Returns array of shape (N_jobs,) bounded between 0.0 and 1.0.
        """
        if isinstance(candidate, dict):
            profile = CandidateProfile(**candidate)
        else:
            profile = candidate

        canon_skills, unknown_skills = self.normalizer.parse_and_normalize_skills(
            profile.skills
        )

        cand_emb = self.encode_candidate(
            summary=profile.summary or "",
            canonical_skills=canon_skills,
            unknown_skills=unknown_skills,
        )

        if cand_emb is None:
            # Empty candidate produces 0.0 similarity across all jobs
            return np.zeros(len(self.job_ids), dtype=np.float32)

        # Dot product of L2 normalized vectors = Cosine similarity
        raw_sims = np.dot(self.job_embeddings, cand_emb)

        # Clip bounds safely to 0.0 <= sim <= 1.0
        # Negative cosine similarities represent opposite/unrelated content -> clamped to 0.0
        clipped_sims = np.clip(raw_sims, 0.0, 1.0)
        return clipped_sims

    def match_candidate(
        self,
        candidate: Union[CandidateProfile, Dict[str, Any]],
        top_k: int = 10,
    ) -> MatchingResponse:
        """Perform semantic-only matching and ranking for candidate."""
        if isinstance(candidate, dict):
            profile = CandidateProfile(**candidate)
        else:
            profile = candidate

        canon_skills, unknown_skills = self.normalizer.parse_and_normalize_skills(
            profile.skills
        )

        similarities = self.compute_semantic_similarities(profile)

        results: List[JobMatchResult] = []
        for idx, job in enumerate(self.job_profiles):
            sim = float(similarities[idx])
            match_score = round(sim * 100.0, 2)

            exp_info = job.get("experience") or {}
            min_exp = exp_info.get("min_years")
            max_exp = exp_info.get("max_years")
            exp_status = "unspecified"
            if profile.experience_years is not None and min_exp is not None:
                exp_status = "compatible" if profile.experience_years >= float(min_exp) else "gap"

            exp_comp = ExperienceComparison(
                candidate_years=profile.experience_years,
                required_min_years=float(min_exp) if min_exp is not None else None,
                required_max_years=float(max_exp) if max_exp is not None else None,
                status=exp_status,
            )

            results.append(
                JobMatchResult(
                    job_id=job["job_id"],
                    job_title=job.get("job_title_normalized") or job.get("job_title") or "Unknown",
                    match_score=match_score,
                    components=ScoreComponents(
                        skill_overlap=0.0,
                        text_similarity=0.0,
                        semantic_similarity=round(sim, 4),
                    ),
                    matched_skills=[],
                    missing_skills=job.get("skills", []),
                    candidate_only_skills=canon_skills,
                    experience=exp_comp,
                    explanation=[f"Semantic embedding similarity: {round(sim * 100, 1)}%."],
                    location=job.get("location"),
                    salary_raw=job.get("salary_raw"),
                )
            )

        ranked = sorted(results, key=lambda r: (-r.match_score, r.job_id))
        return MatchingResponse(
            candidate_id=profile.candidate_id,
            normalized_candidate_skills=canon_skills,
            unknown_candidate_skills=unknown_skills,
            total_jobs_evaluated=len(self.job_profiles),
            top_matches=ranked[:top_k],
            weighting_formula="1.00 * Semantic Similarity",
        )
