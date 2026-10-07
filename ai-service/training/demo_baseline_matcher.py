"""CLI Demonstration Script for SkillGap AI Baseline Job Matcher.

Allows running demonstration candidate profiles through the baseline matching engine:
Usage:
    python training/demo_baseline_matcher.py
"""

from pathlib import Path
import sys
import time

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.schemas import CandidateProfile
from app.services.job_matching_service import JobMatchingService


def run_demo() -> None:
    print("=" * 70)
    print("SKILLGAP AI - BASELINE CANDIDATE-TO-JOB MATCHING ENGINE DEMO")
    print("=" * 70)

    service = JobMatchingService()

    demo_candidate = CandidateProfile(
        candidate_id="candidate_demo_ds",
        skills=["Python", "SQL", "Machine Learning", "Pandas", "Scikit-Learn"],
        summary=(
            "Aspiring Data Scientist with strong foundational skills in Python, "
            "SQL databases, exploratory data analysis, and predictive machine learning models."
        ),
        experience_years=2.0,
    )

    print(f"\nCandidate ID:    {demo_candidate.candidate_id}")
    print(f"Candidate Skills: {', '.join(demo_candidate.skills)}")
    print(f"Experience:       {demo_candidate.experience_years} years")
    print(f"Summary:          {demo_candidate.summary}")
    print("\nEvaluating against 14,840 processed Analytics Jobs...")

    t0 = time.time()
    response = service.match_candidate(demo_candidate, top_k=5)
    elapsed_ms = round((time.time() - t0) * 1000, 2)

    print(f"Match completed in {elapsed_ms} ms (Total evaluated: {response.total_jobs_evaluated} jobs)")
    print("\n" + "=" * 70)
    print("TOP 5 MATCHED JOBS")
    print("=" * 70)

    for i, match in enumerate(response.top_matches, start=1):
        matched_str = ", ".join(match.matched_skills) if match.matched_skills else "None"
        missing_str = ", ".join(match.missing_skills[:6]) if match.missing_skills else "None"

        print(f"\n{i}. {match.job_title} (ID: {match.job_id})")
        print(f"   Match Score:     {match.match_score:.1f}%")
        print(f"   - Skill Overlap: {match.components.skill_overlap * 100:.1f}%")
        print(f"   - Text Sim:      {match.components.text_similarity * 100:.1f}%")
        print(f"   Matched Skills:  {matched_str}")
        print(f"   Missing Skills:  {missing_str}")
        print(f"   Experience:      Candidate ({match.experience.candidate_years:g} yrs) vs Job Req (min: {match.experience.required_min_years}) -> Status: {match.experience.status}")
        if match.location:
            print(f"   Location:        {match.location}")
        print("   Explanations:")
        for exp in match.explanation:
            print(f"     * {exp}")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
