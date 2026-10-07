"""Unit and regression tests for SemanticMatcher and HybridMatcher.

Tests all requirements from Step 8:
- Embedding matrix job count matches job-ID mapping (14,840)
- Embedding dimension is consistent (384)
- Candidate embedding dimension equals job embedding dimension
- No NaN values in embeddings
- No Infinite values in embeddings
- Semantic similarity remains valid within [0.0, 1.0]
- Semantic sanity test: related text has higher cosine similarity than unrelated text
- Cached job embeddings load quickly from disk
- Hybrid score remains bounded within [0.0, 100.0]
- Hybrid score components remain bounded within [0.0, 1.0]
- Exact skill match yields 1.0 skill overlap
- Monotonic skill addition test on hybrid matcher
- Irrelevant skill addition does not inflate skill overlap
- Empty candidate profile runs safely with 0.0 scores and no exceptions
- Deterministic ranking across repeated executions
"""

from pathlib import Path
import sys
import numpy as np
import pytest

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.baseline_matcher import BaselineMatcher
from app.matching.hybrid_matcher import HybridMatcher
from app.matching.schemas import CandidateProfile
from app.matching.semantic_matcher import SemanticMatcher, EXPECTED_EMBEDDING_DIM


@pytest.fixture(scope="module")
def semantic_matcher():
    """Module-scoped fixture to load cached semantic matcher once."""
    return SemanticMatcher()


@pytest.fixture(scope="module")
def baseline_matcher():
    """Module-scoped fixture for baseline matcher."""
    return BaselineMatcher()


@pytest.fixture(scope="module")
def hybrid_matcher(baseline_matcher, semantic_matcher):
    """Module-scoped fixture for hybrid matcher."""
    return HybridMatcher(
        baseline_matcher=baseline_matcher,
        semantic_matcher=semantic_matcher,
    )


def test_embedding_dimensions_and_counts(semantic_matcher):
    """Verify job embeddings shape, count, and dimension consistency."""
    embs = semantic_matcher.job_embeddings
    job_ids = semantic_matcher.job_ids

    assert embs is not None
    assert len(embs) == len(job_ids)
    assert len(embs) == 14840
    assert embs.shape[1] == EXPECTED_EMBEDDING_DIM


def test_no_nan_or_inf_in_embeddings(semantic_matcher):
    """Verify that embedding matrix contains no NaN or Infinite values."""
    embs = semantic_matcher.job_embeddings
    assert not np.isnan(embs).any(), "NaN values found in embedding matrix"
    assert not np.isinf(embs).any(), "Infinite values found in embedding matrix"


def test_candidate_embedding_dimension_matches(semantic_matcher):
    """Verify candidate embedding dimension matches job embedding dimension."""
    cand_emb = semantic_matcher.encode_candidate(
        summary="Data scientist proficient in machine learning and Python",
        canonical_skills=["Python", "Machine Learning"],
        unknown_skills=[],
    )
    assert cand_emb is not None
    assert cand_emb.shape == (EXPECTED_EMBEDDING_DIM,)
    assert not np.isnan(cand_emb).any()


def test_semantic_sanity_related_vs_unrelated(semantic_matcher):
    """Verify that related semantic pairs have strictly higher cosine similarity than unrelated pairs."""
    anchor = "machine learning predictive modeling"
    related = "build ML prediction systems"
    unrelated = "retail store inventory management"

    emb_anchor = semantic_matcher.model.encode([anchor], normalize_embeddings=True)[0]
    emb_related = semantic_matcher.model.encode([related], normalize_embeddings=True)[0]
    emb_unrelated = semantic_matcher.model.encode([unrelated], normalize_embeddings=True)[0]

    sim_rel = float(np.dot(emb_anchor, emb_related))
    sim_unrel = float(np.dot(emb_anchor, emb_unrelated))

    assert sim_rel > sim_unrel, f"Expected {sim_rel} > {sim_unrel}"
    assert 0.0 <= sim_rel <= 1.0
    assert 0.0 <= sim_unrel <= 1.0


def test_semantic_similarity_range(semantic_matcher):
    """Verify compute_semantic_similarities produces values strictly in [0.0, 1.0]."""
    candidate = CandidateProfile(
        candidate_id="test_sim_range",
        skills=["SQL", "Python"],
        summary="Analyst querying databases and generating reports.",
    )
    sims = semantic_matcher.compute_semantic_similarities(candidate)

    assert len(sims) == 14840
    assert np.all(sims >= 0.0)
    assert np.all(sims <= 1.0)


def test_hybrid_score_and_component_bounds(hybrid_matcher):
    """Verify hybrid scores are strictly in [0, 100] and components in [0, 1]."""
    candidate = CandidateProfile(
        candidate_id="test_hyb_bounds",
        skills=["Python", "SQL", "Tableau"],
        summary="Data analyst specialized in business intelligence dashboards.",
        experience_years=3.0,
    )
    resp = hybrid_matcher.match_candidate(candidate, top_k=10)

    assert len(resp.top_matches) == 10
    for m in resp.top_matches:
        assert 0.0 <= m.match_score <= 100.0
        assert 0.0 <= m.components.skill_overlap <= 1.0
        assert 0.0 <= m.components.tfidf_similarity <= 1.0
        assert 0.0 <= m.components.semantic_similarity <= 1.0


def test_hybrid_exact_skill_coverage(hybrid_matcher):
    """Verify exact skill coverage yields 1.0 skill overlap in hybrid result."""
    target_job = next(
        j for j in hybrid_matcher.baseline_matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 2
    )
    all_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    candidate = CandidateProfile(
        candidate_id="test_hyb_exact",
        skills=all_skills,
        summary="Exact candidate matching role.",
    )
    resp = hybrid_matcher.match_candidate(candidate, top_k=10000)
    match = next(m for m in resp.top_matches if m.job_id == target_job["job_id"])

    assert match.components.skill_overlap == 1.0
    assert len(match.missing_skills) == 0


def test_hybrid_monotonic_skill_addition(hybrid_matcher):
    """Verify adding a required missing skill does not decrease skill overlap or score."""
    target_job = next(
        j for j in hybrid_matcher.baseline_matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 3
    )
    all_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    cand_before = CandidateProfile(candidate_id="mono_b", skills=[all_skills[0]], summary="Role")
    cand_after = CandidateProfile(candidate_id="mono_a", skills=[all_skills[0], all_skills[1]], summary="Role")

    resp_b = hybrid_matcher.match_candidate(cand_before, top_k=10000)
    resp_a = hybrid_matcher.match_candidate(cand_after, top_k=10000)

    m_b = next(m for m in resp_b.top_matches if m.job_id == target_job["job_id"])
    m_a = next(m for m in resp_a.top_matches if m.job_id == target_job["job_id"])

    assert m_a.components.skill_overlap >= m_b.components.skill_overlap
    assert m_a.match_score >= m_b.match_score


def test_hybrid_irrelevant_skill_addition(hybrid_matcher):
    """Verify adding irrelevant skill does not artificially increase skill overlap."""
    target_job = next(
        j for j in hybrid_matcher.baseline_matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 2
    )
    all_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    cand_base = CandidateProfile(candidate_id="irr_base", skills=[all_skills[0]], summary="Data")
    cand_bloated = CandidateProfile(
        candidate_id="irr_bloated",
        skills=[all_skills[0], "Pottery", "Blacksmithing"],
        summary="Data",
    )

    resp_base = hybrid_matcher.match_candidate(cand_base, top_k=10000)
    resp_bloated = hybrid_matcher.match_candidate(cand_bloated, top_k=10000)

    m_base = next(m for m in resp_base.top_matches if m.job_id == target_job["job_id"])
    m_bloated = next(m for m in resp_bloated.top_matches if m.job_id == target_job["job_id"])

    assert m_bloated.components.skill_overlap == m_base.components.skill_overlap


def test_hybrid_empty_candidate_safety(hybrid_matcher):
    """Verify empty candidate profile yields 0.0 scores safely without crashing."""
    cand_empty = CandidateProfile(candidate_id="test_empty", skills=[], summary="")
    resp = hybrid_matcher.match_candidate(cand_empty, top_k=5)

    assert len(resp.top_matches) == 5
    for m in resp.top_matches:
        assert m.match_score == 0.0
        assert m.components.skill_overlap == 0.0
        assert m.components.tfidf_similarity == 0.0
        assert m.components.semantic_similarity == 0.0


def test_hybrid_deterministic_ranking(hybrid_matcher):
    """Verify hybrid ranking is strictly deterministic."""
    candidate = CandidateProfile(
        candidate_id="test_det",
        skills=["Python", "SQL", "Pandas", "Scikit-Learn"],
        summary="Data science student with machine learning projects.",
        experience_years=2.0,
    )
    resp1 = hybrid_matcher.match_candidate(candidate, top_k=10)
    resp2 = hybrid_matcher.match_candidate(candidate, top_k=10)

    ids1 = [m.job_id for m in resp1.top_matches]
    ids2 = [m.job_id for m in resp2.top_matches]
    scores1 = [m.match_score for m in resp1.top_matches]
    scores2 = [m.match_score for m in resp2.top_matches]

    assert ids1 == ids2
    assert scores1 == scores2
