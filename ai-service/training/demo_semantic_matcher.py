"""CLI Demonstration Script for Tripartite Matching Comparison.

Compares:
1. TF-IDF Baseline Matcher
2. Semantic Transformer Matcher
3. Tripartite Hybrid Matcher v1
"""

from pathlib import Path
import sys
import time

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.matching.baseline_matcher import BaselineMatcher
from app.matching.hybrid_matcher import HybridMatcher
from app.matching.schemas import CandidateProfile
from app.matching.semantic_matcher import SemanticMatcher


def run_comparison_demo() -> None:
    print("=" * 80)
    print("SKILLGAP AI - MATCHING ARCHITECTURE COMPARISON DEMO")
    print("=" * 80)

    # Initialize matchers
    baseline_matcher = BaselineMatcher()
    semantic_matcher = SemanticMatcher()
    hybrid_matcher = HybridMatcher(
        baseline_matcher=baseline_matcher,
        semantic_matcher=semantic_matcher,
    )

    candidate = CandidateProfile(
        candidate_id="candidate_demo_comparison",
        skills=["Python", "SQL", "Machine Learning", "Pandas"],
        summary="Engineering student with projects involving predictive modeling, data analysis and Python.",
        experience_years=1.5,
    )

    print(f"\nCANDIDATE PROFILE: {candidate.candidate_id}")
    print(f"Skills:     {', '.join(candidate.skills)}")
    print(f"Experience: {candidate.experience_years} years")
    print(f"Summary:    {candidate.summary}")
    print(f"\nEvaluating against {len(baseline_matcher.job_profiles)} jobs...")

    # 1. Baseline Matcher
    t0 = time.time()
    resp_baseline = baseline_matcher.match_candidate(candidate, top_k=5)
    t_baseline = round((time.time() - t0) * 1000, 1)

    # 2. Semantic Matcher
    t0 = time.time()
    resp_semantic = semantic_matcher.match_candidate(candidate, top_k=5)
    t_semantic = round((time.time() - t0) * 1000, 1)

    # 3. Hybrid Matcher
    t0 = time.time()
    resp_hybrid = hybrid_matcher.match_candidate(candidate, top_k=5)
    t_hybrid = round((time.time() - t0) * 1000, 1)

    print("\n" + "-" * 80)
    print(f"1. TF-IDF BASELINE MATCHER (Latency: {t_baseline} ms)")
    print("   Formula: 0.70 * Skill Overlap + 0.30 * TF-IDF")
    print("-" * 80)
    for i, m in enumerate(resp_baseline.top_matches, start=1):
        print(f"   {i}. {m.job_title} | Score: {m.match_score:.1f}%")
        print(f"      Overlap: {m.components.skill_overlap * 100:.1f}% | TF-IDF: {m.components.text_similarity * 100:.1f}%")
        print(f"      Matched: {', '.join(m.matched_skills) if m.matched_skills else 'None'}")
        print(f"      Missing: {', '.join(m.missing_skills[:4]) if m.missing_skills else 'None'}")

    print("\n" + "-" * 80)
    print(f"2. SEMANTIC MATCHER (Latency: {t_semantic} ms)")
    print("   Formula: 1.00 * Semantic Similarity (all-MiniLM-L6-v2)")
    print("-" * 80)
    for i, m in enumerate(resp_semantic.top_matches, start=1):
        print(f"   {i}. {m.job_title} | Score: {m.match_score:.1f}%")
        print(f"      Semantic Sim: {m.components.semantic_similarity * 100:.1f}%")

    print("\n" + "-" * 80)
    print(f"3. HYBRID MATCHER v1 (Latency: {t_hybrid} ms)")
    print("   Formula: 0.50 * Skill Overlap + 0.20 * TF-IDF + 0.30 * Semantic")
    print("-" * 80)
    for i, m in enumerate(resp_hybrid.top_matches, start=1):
        print(f"   {i}. {m.job_title} | Score: {m.match_score:.1f}%")
        print(
            f"      Overlap: {m.components.skill_overlap * 100:.1f}% | "
            f"TF-IDF: {m.components.tfidf_similarity * 100:.1f}% | "
            f"Semantic: {m.components.semantic_similarity * 100:.1f}%"
        )
        print(f"      Matched: {', '.join(m.matched_skills) if m.matched_skills else 'None'}")
        print(f"      Missing: {', '.join(m.missing_skills[:4]) if m.missing_skills else 'None'}")
        print(f"      Experience: {m.experience.status} (Candidate: {m.experience.candidate_years}y vs Job Min: {m.experience.required_min_years})")

    print("\n" + "=" * 80)
    print("DEMO COMPARISON COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_comparison_demo()
