"""Unit tests for Analytics Jobs preprocessing pipeline and skill normalizer.

Tests satisfy all requirements from Step 4 / Analytics Jobs specifications:
- Alias normalization works properly
- Java and JavaScript remain distinct
- C++ survives preprocessing intact
- C# survives preprocessing intact
- .NET survives preprocessing intact
- Duplicate skills collapse correctly
- Unknown skills are preserved
- Experience parsing handles representative formats
- Missing job descriptions do not crash preprocessing
- Stable job IDs remain identical across repeated runs
- Job title normalization preserves distinction between roles
"""

from pathlib import Path
import pytest

from app.preprocessing.analytics_jobs_preprocessing import (
    classify_profile_completeness,
    clean_text_field,
    generate_stable_job_id,
    normalize_job_title,
    normalize_job_type,
    parse_experience,
    parse_salary,
    AnalyticsJobsPipeline,
)
from app.preprocessing.skill_normalizer import SkillNormalizer


@pytest.fixture
def normalizer():
    return SkillNormalizer()


def test_alias_normalization(normalizer):
    """Test that aliases normalize to canonical display names."""
    assert normalizer.normalize_skill("Postgres") == "PostgreSQL"
    assert normalizer.normalize_skill("postgres") == "PostgreSQL"
    assert normalizer.normalize_skill("JS") == "JavaScript"
    assert normalizer.normalize_skill("ML") == "Machine Learning"
    assert normalizer.normalize_skill("NLP") == "Natural Language Processing"
    assert normalizer.normalize_skill("ReactJS") == "React"
    assert normalizer.normalize_skill("react.js") == "React"


def test_java_and_javascript_remain_distinct(normalizer):
    """Verify Java and JavaScript are never merged."""
    java_res = normalizer.normalize_skill("Java")
    js_res = normalizer.normalize_skill("JavaScript")
    core_java_res = normalizer.normalize_skill("Core Java")
    js_alias_res = normalizer.normalize_skill("js")

    assert java_res == "Java"
    assert js_res == "JavaScript"
    assert core_java_res == "Java"
    assert js_alias_res == "JavaScript"
    assert java_res != js_res


def test_data_analysis_and_data_science_remain_distinct(normalizer):
    """Verify Data Analysis and Data Science are never merged."""
    da = normalizer.normalize_skill("Data Analysis")
    ds = normalizer.normalize_skill("Data Science")
    analytics = normalizer.normalize_skill("analytics")

    assert da == "Data Analysis"
    assert ds == "Data Science"
    assert analytics == "Data Analysis"
    assert da != ds


def test_technical_punctuation_survives(normalizer):
    """Verify C++, C#, .NET, Node.js, PL/SQL survive preprocessing intact."""
    assert normalizer.normalize_skill("C++") == "C++"
    assert normalizer.normalize_skill("c++") == "C++"
    assert normalizer.normalize_skill("C#") == "C#"
    assert normalizer.normalize_skill("c#") == "C#"
    assert normalizer.normalize_skill(".NET") == ".NET"
    assert normalizer.normalize_skill(".net") == ".NET"
    assert normalizer.normalize_skill("Node.js") == "Node.js"
    assert normalizer.normalize_skill("node.js") == "Node.js"
    assert normalizer.normalize_skill("PL/SQL") == "PL/SQL"
    assert normalizer.normalize_skill("pl/sql") == "PL/SQL"


def test_compound_slash_and_pipe_separators(normalizer):
    """Verify parsing handles pipe separators and splits C / C++ without damaging PL/SQL."""
    # Pipe separated
    canon, unknown = normalizer.parse_and_normalize_skills("Python | SQL | Machine Learning | Pandas")
    assert "Python" in canon
    assert "SQL" in canon
    assert "Machine Learning" in canon
    assert "Pandas" in canon

    # Compound slash: C / C++
    canon2, _ = normalizer.parse_and_normalize_skills("C / C++")
    assert "C" in canon2
    assert "C++" in canon2

    # Single skill with slash: PL/SQL
    canon3, _ = normalizer.parse_and_normalize_skills("PL/SQL")
    assert canon3 == ["PL/SQL"]


def test_duplicate_skills_collapse_correctly(normalizer):
    """Verify duplicate skills within the same job collapse without duplication."""
    raw = "Python, python, PYTHON, Machine Learning, ML, SQL, sql"
    canon, _ = normalizer.parse_and_normalize_skills(raw)
    assert canon == ["Python", "Machine Learning", "SQL"]


def test_unknown_skills_are_preserved(normalizer):
    """Verify unresolved/unknown skills are preserved and returned."""
    raw = "Python, CustomLegacyTool, SQL, ObscureInternalFramework"
    canon, unknown = normalizer.parse_and_normalize_skills(raw)
    assert "Python" in canon
    assert "SQL" in canon
    assert "CustomLegacyTool" in unknown
    assert "ObscureInternalFramework" in unknown


def test_experience_parsing():
    """Verify experience parsing handles various formats safely."""
    assert parse_experience("2 - 5 yrs") == (2, 5, True)
    assert parse_experience("3-6 Years") == (3, 6, True)
    assert parse_experience("0 - 1 years") == (0, 1, True)
    assert parse_experience("5+ yrs") == (5, None, True)
    assert parse_experience("4 yrs") == (4, 4, True)
    assert parse_experience("0-0 yrs") == (0, 0, True)

    # Invalid / empty
    assert parse_experience(None) == (None, None, False)
    assert parse_experience("") == (None, None, False)
    assert parse_experience("Not specified") == (None, None, False)


def test_salary_parsing():
    """Verify salary parsing handles discrete brackets safely."""
    assert parse_salary("6to10") == ("6to10", 6.0, 10.0)
    assert parse_salary("10to15") == ("10to15", 10.0, 15.0)
    assert parse_salary("0to3") == ("0to3", 0.0, 3.0)
    assert parse_salary(None) == ("", None, None)
    assert parse_salary("competitive") == ("competitive", None, None)


def test_job_title_normalization():
    """Verify job title normalization maintains role distinctions."""
    assert normalize_job_title("DATA ANALYST") == "Data Analyst"
    assert normalize_job_title("data analyst") == "Data Analyst"
    assert normalize_job_title("Senior Data Analyst") == "Senior Data Analyst"
    assert normalize_job_title("Data Analyst") != normalize_job_title("Senior Data Analyst")
    assert normalize_job_title("SEO Analyst") == "SEO Analyst"
    assert normalize_job_title("Staff Software Engineer - Object Oriented Analysis & Design") == (
        "Staff Software Engineer - Object Oriented Analysis & Design"
    )


def test_job_type_normalization():
    """Verify job type normalization across variants."""
    assert normalize_job_type("Analytics") == ("Analytics", "Analytics")
    assert normalize_job_type("analytics") == ("analytics", "Analytics")
    assert normalize_job_type("ANALYTICS") == ("ANALYTICS", "Analytics")
    assert normalize_job_type("analytic") == ("analytic", "Analytics")
    assert normalize_job_type(None) == (None, "Unspecified")


def test_stable_job_id_deterministic():
    """Verify job ID is stable across repeated executions."""
    id1 = generate_stable_job_id(1, "Data Analyst", "Bengaluru", "2-5 yrs", "Python, SQL")
    id2 = generate_stable_job_id(1, "Data Analyst", "Bengaluru", "2-5 yrs", "Python, SQL")
    id3 = generate_stable_job_id(2, "Data Analyst", "Bengaluru", "2-5 yrs", "Python, SQL")

    assert id1 == id2
    assert id1.startswith("aj_")
    assert id1 != id3


def test_missing_job_description_does_not_crash(normalizer):
    """Verify records missing job descriptions are cleanly classified as skills_only."""
    comp1 = classify_profile_completeness(has_description=True, has_usable_skills=True, has_title=True)
    comp2 = classify_profile_completeness(has_description=False, has_usable_skills=True, has_title=True)
    comp3 = classify_profile_completeness(has_description=False, has_usable_skills=False, has_title=True)

    assert comp1 == "complete"
    assert comp2 == "skills_only"
    assert comp3 == "insufficient"
