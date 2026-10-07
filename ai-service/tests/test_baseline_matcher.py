"""Automated tests for Baseline Candidate-to-Job Matching Engine.

Validates all requirements from Step 5 / Matching Engine specifications:
- Score remains strictly between 0 and 100
- Skill overlap remains strictly between 0 and 1
- Text similarity remains strictly between 0 and 1
- Exact skill match gives 1.0 skill overlap
- Adding a required skill does not reduce skill-overlap score (monotonicity)
- Irrelevant skill does not falsely increase required-skill overlap
- Missing job description falls back safely and does not crash
- Missing job skills handled without ZeroDivisionError
- Empty candidate profile does not crash and returns controlled scores
- Alias normalization resolves candidate aliases before matching
- Ranking is strictly deterministic across repeated runs
- Top-K parameter returns requested number of matches
- Matched and missing skill sets are logically consistent and partition job requirements
"""

from pathlib import Path
import sys
import pytest

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.baseline_matcher import BaselineMatcher
from app.matching.schemas import CandidateProfile
from app.services.job_matching_service import JobMatchingService


@pytest.fixture(scope="module")
def matcher():
    """Module-scoped fixture to avoid re-loading/fitting TF-IDF matrix for every test."""
    return BaselineMatcher()


@pytest.fixture(scope="module")
def service(matcher):
    return JobMatchingService(matcher=matcher)


def test_score_bounds_and_components(service):
    """Verify match score is between 0 and 100, and components between 0 and 1."""
    candidate = CandidateProfile(
        candidate_id="test_bounds",
        skills=["Python", "SQL", "Machine Learning"],
        summary="Data scientist with Python and SQL experience.",
        experience_years=2.0,
    )
    resp = service.match_candidate(candidate, top_k=10)

    assert len(resp.top_matches) == 10
    for match in resp.top_matches:
        assert 0.0 <= match.match_score <= 100.0
        assert 0.0 <= match.components.skill_overlap <= 1.0
        assert 0.0 <= match.components.text_similarity <= 1.0


def test_exact_skill_match_gives_unity(matcher):
    """Verify that a candidate matching all required skills of a job gets 1.0 skill overlap."""
    target_job = next(
        j for j in matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 2
    )
    all_job_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    candidate = CandidateProfile(
        candidate_id="test_exact_unity",
        skills=all_job_skills,
        summary="Exact skill match test candidate.",
    )
    resp = matcher.match_candidate(candidate, top_k=10000)
    target_match = next(m for m in resp.top_matches if m.job_id == target_job["job_id"])

    assert target_match.components.skill_overlap == 1.0
    assert len(target_match.missing_skills) == 0
    assert set(target_match.matched_skills) == set(all_job_skills)


def test_monotonic_skill_addition(matcher):
    """Verify that adding a required missing skill does not reduce skill-overlap score."""
    target_job = next(
        j for j in matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 3
    )
    all_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    cand_before = CandidateProfile(
        candidate_id="test_mono_1",
        skills=[all_skills[0]],
        summary="Base skills",
    )
    cand_after = CandidateProfile(
        candidate_id="test_mono_2",
        skills=[all_skills[0], all_skills[1]],
        summary="Base skills",
    )

    resp_before = matcher.match_candidate(cand_before, top_k=10000)
    resp_after = matcher.match_candidate(cand_after, top_k=10000)

    match_before = next(m for m in resp_before.top_matches if m.job_id == target_job["job_id"])
    match_after = next(m for m in resp_after.top_matches if m.job_id == target_job["job_id"])

    assert match_after.components.skill_overlap >= match_before.components.skill_overlap
    assert match_after.match_score >= match_before.match_score


def test_irrelevant_skill_does_not_inflate_overlap(matcher):
    """Verify that adding unrelated skills does not increase required-skill overlap."""
    target_job = next(
        j for j in matcher.job_profiles
        if (len(j.get("skills", [])) + len(j.get("unknown_skills", []))) >= 2
    )
    all_skills = target_job.get("skills", []) + target_job.get("unknown_skills", [])

    cand_base = CandidateProfile(
        candidate_id="test_base",
        skills=[all_skills[0]],
        summary="Base skill",
    )
    cand_bloated = CandidateProfile(
        candidate_id="test_bloated",
        skills=[all_skills[0], "Ancient Greek", "Pottery", "Origami"],
        summary="Base skill",
    )

    resp_base = matcher.match_candidate(cand_base, top_k=10000)
    resp_bloated = matcher.match_candidate(cand_bloated, top_k=10000)

    match_base = next(m for m in resp_base.top_matches if m.job_id == target_job["job_id"])
    match_bloated = next(m for m in resp_bloated.top_matches if m.job_id == target_job["job_id"])

    assert match_bloated.components.skill_overlap == match_base.components.skill_overlap


def test_empty_candidate_safety(matcher):
    """Verify empty candidate profile runs safely with controlled 0 scores."""
    cand_empty = CandidateProfile(candidate_id="test_empty", skills=[], summary="")
    resp = matcher.match_candidate(cand_empty, top_k=5)

    assert len(resp.top_matches) == 5
    for match in resp.top_matches:
        assert match.components.skill_overlap == 0.0
        assert match.components.text_similarity == 0.0
        assert match.match_score == 0.0
        assert len(match.matched_skills) == 0


def test_job_without_skills_safety(matcher):
    """Verify jobs without skills do not produce ZeroDivisionError or crash."""
    overlap, matched, missing, cand_only = matcher.compute_skill_overlap(
        candidate_skills={"Python", "SQL"},
        job_skills=set(),
    )
    assert overlap == 0.0
    assert matched == []
    assert missing == []
    assert sorted(cand_only) == ["Python", "SQL"]


def test_missing_job_description_handling(matcher):
    """Verify that jobs lacking narrative descriptions do not crash matching."""
    no_desc_job = next(j for j in matcher.job_profiles if not j.get("job_description"))
    cand = CandidateProfile(
        candidate_id="test_no_desc",
        skills=no_desc_job.get("skills", []),
        summary="Testing matching against no description job.",
    )
    resp = matcher.match_candidate(cand, top_k=10000)
    match_found = next(m for m in resp.top_matches if m.job_id == no_desc_job["job_id"])

    assert match_found.match_score >= 0.0


def test_alias_normalization_before_matching(matcher):
    """Verify candidate aliases (e.g. ML, Postgres, ReactJS) resolve to canonical skills."""
    cand_aliases = CandidateProfile(
        candidate_id="test_alias_cand",
        skills=["ML", "Postgres", "ReactJS", "JS"],
    )
    resp = matcher.match_candidate(cand_aliases, top_k=1)

    assert "Machine Learning" in resp.normalized_candidate_skills
    assert "PostgreSQL" in resp.normalized_candidate_skills
    assert "React" in resp.normalized_candidate_skills
    assert "JavaScript" in resp.normalized_candidate_skills


def test_deterministic_ranking(matcher):
    """Verify that multiple runs for the same candidate produce identical results."""
    candidate = CandidateProfile(
        candidate_id="test_det_run",
        skills=["Python", "SQL", "Tableau", "AWS"],
        summary="Senior data analyst with cloud experience.",
        experience_years=5.0,
    )
    resp1 = matcher.match_candidate(candidate, top_k=10)
    resp2 = matcher.match_candidate(candidate, top_k=10)

    ids1 = [m.job_id for m in resp1.top_matches]
    ids2 = [m.job_id for m in resp2.top_matches]
    scores1 = [m.match_score for m in resp1.top_matches]
    scores2 = [m.match_score for m in resp2.top_matches]

    assert ids1 == ids2
    assert scores1 == scores2


def test_top_k_parameter(matcher):
    """Verify top_k parameter returns the exact requested number of matches."""
    candidate = CandidateProfile(
        candidate_id="test_topk",
        skills=["Python", "SQL"],
    )
    for k in [1, 3, 7, 15]:
        resp = matcher.match_candidate(candidate, top_k=k)
        assert len(resp.top_matches) == k


def test_skill_sets_consistency(matcher):
    """Verify matched and missing skill sets partition the job's required skills."""
    candidate = CandidateProfile(
        candidate_id="test_partition",
        skills=["Python", "SQL", "Tableau", "Java"],
    )
    resp = matcher.match_candidate(candidate, top_k=10)

    for match in resp.top_matches:
        matched_set = set(match.matched_skills)
        missing_set = set(match.missing_skills)

        # Matched and missing must be disjoint
        assert matched_set.isdisjoint(missing_set)

        job_profile = matcher.job_id_to_profile[match.job_id]
        all_job_skills = set(job_profile.get("skills", []) + job_profile.get("unknown_skills", []))

        # Union of matched and missing should equal total required job skills
        assert len(matched_set | missing_set) == len(all_job_skills)
