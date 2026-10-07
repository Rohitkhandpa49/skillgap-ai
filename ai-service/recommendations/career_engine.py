from typing import Any

def build_career_recommendations(
    job_insights: list[dict[str, Any]],
    skill_insights: list[dict[str, Any]],
    personality_insights: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Combine validated analytics outputs into dashboard-ready recommendations.

    The actual ranking logic should be implemented after the organizer datasets
    have been profiled and their real column semantics are confirmed.
    """
    return {
        "job_insights": job_insights,
        "skill_insights": skill_insights,
        "personality_insights": personality_insights or [],
    }
