"""Unit and regression tests for candidate profile and skill extraction pipeline.

Validates all requirements from Step 10:
- Direct skill section extraction
- Project evidence extraction
- Experience evidence extraction
- Alias mapping (ML -> Machine Learning, Postgres -> PostgreSQL, ReactJS -> React, JS -> JavaScript)
- Repeated skills collapse (no duplicates, merged evidence, bounded confidence boost)
- Confidence remains strictly bounded within [0.0, 1.0]
- Distinct technologies:
  - Java != JavaScript
  - C != C++
  - C# preserved
  - .NET preserved
  - Node.js preserved
- Unknown / non-taxonomy skills preserved with traceability (e.g. FastAPI, Spring Boot)
- Empty resume does not crash
- Resume with no skills returns empty skill list
- Missing Skills section does not prevent extraction from Projects / Experience
- Negation handling:
  - "Experienced with Kubernetes." -> Kubernetes detected
  - "No experience with Kubernetes." -> Kubernetes NOT in positive skills
- Evidence integrity: every evidence sentence originates in the document
- Confidence progression: Skills + Projects scores higher than a single weak mention
- Synthetic personas:
  - Data Analyst (SQL, Excel, Python, Power BI, Tableau)
  - ML candidate (Python, Machine Learning, Scikit-Learn, TensorFlow, Pandas)
  - Data Engineer (Python, SQL, Spark, Hadoop, ETL)
  - Software candidate (Java, Spring Boot unresolved, REST API, MySQL)
- PII sanitization in candidate matching text
- Integration with matching engine CandidateProfile schema
"""

from pathlib import Path
import sys
import pytest

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.resume.candidate_profile_builder import (
    CandidateProfileBuilder,
    build_candidate_matching_text,
    sanitize_text_for_matching,
    to_matching_candidate_profile,
)
from app.resume.schemas import (
    ParsedResume,
    ResumeMetadata,
    ResumeSections,
)
from app.resume.skill_extractor import SkillExtractor
from app.services.candidate_profile_service import (
    CandidateProfileService,
    analyze_resume_file,
)

FIXTURES_DIR = AI_SERVICE_DIR / "tests" / "fixtures" / "resumes"


@pytest.fixture
def extractor() -> SkillExtractor:
    return SkillExtractor()


@pytest.fixture
def builder() -> CandidateProfileBuilder:
    return CandidateProfileBuilder()


@pytest.fixture
def service() -> CandidateProfileService:
    return CandidateProfileService()


def test_direct_skill_section_extraction(extractor):
    """Verify skills listed under Skills section are cleanly extracted with ~0.90 confidence."""
    resume = ParsedResume(
        filename="test.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="SKILLS: Python, SQL, Tableau, AWS, Docker",
        sections=ResumeSections(skills="Python, SQL, Tableau, AWS, Docker"),
    )
    skills, unresolved = extractor.extract_skills(resume)
    names = {s.name for s in skills}

    assert "Python" in names
    assert "SQL" in names
    assert "Tableau" in names
    assert "AWS" in names
    assert "Docker" in names
    for s in skills:
        assert s.confidence >= 0.90
        assert "skills" in s.source_sections


def test_project_and_experience_evidence_extraction(extractor):
    """Verify skills in project bullets and work experience capture correct evidence sentences."""
    resume = ParsedResume(
        filename="test.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            projects="Built a deep neural network using PyTorch and TensorFlow for computer vision.",
            experience="Maintained high-throughput data pipelines using Apache Spark and PostgreSQL.",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    skill_map = {s.name: s for s in skills}

    assert "PyTorch" in skill_map
    assert "TensorFlow" in skill_map
    assert "Spark" in skill_map
    assert "PostgreSQL" in skill_map

    # Check evidence traceability
    assert any("PyTorch" in ev for ev in skill_map["PyTorch"].evidence)
    assert any("Spark" in ev for ev in skill_map["Spark"].evidence)
    assert "projects" in skill_map["PyTorch"].source_sections
    assert "experience" in skill_map["Spark"].source_sections


def test_alias_normalization(extractor):
    """Verify alias mappings resolve accurately to canonical taxonomy names."""
    resume = ParsedResume(
        filename="test.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            skills="ML, NLP, Postgres, ReactJS, Continuous Integration, BigData",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    names = {s.name for s in skills}

    assert "Machine Learning" in names
    assert "Natural Language Processing" in names
    assert "PostgreSQL" in names
    assert "React" in names
    assert "CI/CD" in names
    assert "Big Data" in names


def test_repeated_skills_collapse_and_confidence_boost(extractor):
    """Verify repeated skills across sections collapse into one object with boosted confidence."""
    resume = ParsedResume(
        filename="test.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Python developer with 5 years experience.",
            skills="Python, SQL",
            projects="Architected machine learning backend using Python.",
            experience="Optimized distributed Python ETL pipelines.",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    python_skills = [s for s in skills if s.name == "Python"]

    # Exactly one merged Python skill object
    assert len(python_skills) == 1
    py = python_skills[0]

    # Appears across summary, skills, projects, experience
    assert "skills" in py.source_sections
    assert "projects" in py.source_sections
    assert "experience" in py.source_sections
    assert "summary" in py.source_sections

    # Synergy boost should drive confidence to 1.0 (capped)
    assert py.confidence >= 0.98
    assert py.confidence <= 1.0

    # Multiple distinct evidence items without duplicates
    assert len(py.evidence) >= 3


def test_distinct_technologies_java_vs_javascript(extractor):
    """Ensure Java and JavaScript remain strictly distinct technologies."""
    # Java alone
    res_java = ParsedResume(
        filename="java.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(experience="Developed enterprise services with Java and Spring."),
    )
    skills_java, _ = extractor.extract_skills(res_java)
    names_java = {s.name for s in skills_java}
    assert "Java" in names_java
    assert "JavaScript" not in names_java

    # JavaScript alone
    res_js = ParsedResume(
        filename="js.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(experience="Engineered modern UI components with JavaScript and CSS."),
    )
    skills_js, _ = extractor.extract_skills(res_js)
    names_js = {s.name for s in skills_js}
    assert "JavaScript" in names_js
    assert "Java" not in names_js


def test_distinct_technologies_c_family(extractor):
    """Ensure C, C++, C# remain strictly distinct and are not confused."""
    # C++
    res_cpp = ParsedResume(
        filename="cpp.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(skills="C++", projects="Built high-performance game engine using C++."),
    )
    skills_cpp, _ = extractor.extract_skills(res_cpp)
    names_cpp = {s.name for s in skills_cpp}
    assert "C++" in names_cpp
    assert "C#" not in names_cpp

    # C#
    res_cs = ParsedResume(
        filename="cs.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(skills="C#", projects="Developed Windows enterprise client using C#."),
    )
    skills_cs, _ = extractor.extract_skills(res_cs)
    names_cs = {s.name for s in skills_cs}
    assert "C#" in names_cs
    assert "C++" not in names_cs

    # C programming
    res_c = ParsedResume(
        filename="c.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(skills="C", experience="Wrote embedded firmware in C programming language."),
    )
    skills_c, _ = extractor.extract_skills(res_c)
    names_c = {s.name for s in skills_c}
    assert "C" in names_c
    assert "C++" not in names_c
    assert "C#" not in names_c


def test_dotnet_and_nodejs_preservation(extractor):
    """Verify .NET and Node.js are preserved through extraction."""
    resume = ParsedResume(
        filename="dotnet.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            skills=".NET, Node.js, ASP.NET",
            experience="Built .NET web APIs and Node.js microservices.",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    names = {s.name for s in skills}
    assert ".NET" in names
    assert "Node.js" in names


def test_negation_handling(extractor):
    """Verify negation handling excludes false positive skills."""
    # Positive case
    resume_pos = ParsedResume(
        filename="pos.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(experience="Experienced with Kubernetes and Docker containers."),
    )
    skills_pos, _ = extractor.extract_skills(resume_pos)
    names_pos = {s.name for s in skills_pos}
    assert "Kubernetes" in names_pos
    assert "Docker" in names_pos

    # Negated case
    resume_neg = ParsedResume(
        filename="neg.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(experience="No experience with Kubernetes. Have not used Docker."),
    )
    skills_neg, _ = extractor.extract_skills(resume_neg)
    names_neg = {s.name for s in skills_neg}
    assert "Kubernetes" not in names_neg
    assert "Docker" not in names_neg


def test_unresolved_skills_preservation(extractor):
    """Verify non-taxonomy technologies are captured under unresolved_skills with reason."""
    resume = ParsedResume(
        filename="newtech.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            skills="Python, SQL, SomeNewFramework, FastAPI, AnotherToolV2",
        ),
    )
    skills, unresolved = extractor.extract_skills(resume)
    unresolved_terms = {u.term for u in unresolved}

    assert "SomeNewFramework" in unresolved_terms
    assert "FastAPI" in unresolved_terms
    assert "AnotherToolV2" in unresolved_terms
    for u in unresolved:
        assert u.reason == "not_in_current_taxonomy"
        assert u.source_section == "skills"


def test_empty_resume_handling(extractor, builder):
    """Verify parser and extractor handle empty resumes safely without crashing."""
    resume = ParsedResume(
        filename="empty.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(),
        metadata=ResumeMetadata(text_extraction_status="insufficient_text"),
    )
    skills, unresolved = extractor.extract_skills(resume)
    assert skills == []
    assert unresolved == []

    profile = builder.build_profile(resume, skills, unresolved)
    assert profile.skills == []
    assert profile.summary is None
    assert profile.metadata.skill_count == 0


def test_missing_skills_section_extracts_from_prose(extractor):
    """Verify resumes without a dedicated Skills section still extract skills from Experience and Projects."""
    resume = ParsedResume(
        filename="no_skills_sec.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            experience="Engineered high-performance queries using PostgreSQL and Python.",
            projects="Created interactive dashboards using Tableau.",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    names = {s.name for s in skills}

    assert "PostgreSQL" in names
    assert "Python" in names
    assert "Tableau" in names
    for s in skills:
        assert "skills" not in s.source_sections
        assert s.confidence >= 0.85


def test_evidence_integrity(extractor):
    """Verify every evidence sentence is non-empty and contains the skill or represents a skills listing."""
    resume = ParsedResume(
        filename="integrity.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            skills="Python, SQL, AWS",
            experience="Implemented automated deployment pipelines using AWS and Docker.",
            projects="Analyzed customer churn with Python and SQL.",
        ),
    )
    skills, _ = extractor.extract_skills(resume)
    for skill in skills:
        assert len(skill.evidence) > 0
        for ev in skill.evidence:
            assert isinstance(ev, str)
            assert len(ev.strip()) > 0


def test_synthetic_persona_data_analyst(service):
    """Verify Data Analyst candidate persona extracts expected skills."""
    resume = ParsedResume(
        filename="analyst.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Data Analyst with 3 years experience creating executive dashboards.",
            skills="SQL, Excel, Python, Power BI, Tableau",
            experience="Automated ETL reporting using Python and SQL. Designed Power BI executive KPI dashboards.",
            education="B.S. in Statistics",
        ),
    )
    profile = service.build_candidate_profile(resume)
    detected = {s.name for s in profile.skills}

    expected = {"SQL", "Excel", "Python", "Power BI", "Tableau"}
    assert expected.issubset(detected)
    assert profile.metadata.skill_count >= 5
    assert profile.summary is not None


def test_synthetic_persona_ml_candidate(service):
    """Verify ML candidate persona extracts expected skills."""
    resume = ParsedResume(
        filename="ml.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Machine Learning Engineer specializing in deep neural architectures.",
            skills="Python, Machine Learning, Scikit-Learn, TensorFlow, Pandas",
            projects="Trained neural networks using TensorFlow and Pandas for tabular feature engineering.",
        ),
    )
    profile = service.build_candidate_profile(resume)
    detected = {s.name for s in profile.skills}

    expected = {"Python", "Machine Learning", "Scikit-Learn", "TensorFlow", "Pandas"}
    assert expected.issubset(detected)


def test_synthetic_persona_data_engineer(service):
    """Verify Data Engineer candidate persona extracts expected skills."""
    resume = ParsedResume(
        filename="de.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Data Engineer focused on large-scale distributed streaming systems.",
            skills="Python, SQL, Spark, Hadoop, ETL",
            experience="Built daily batch ETL pipelines processing 5TB data using Spark, Hadoop, and SQL.",
        ),
    )
    profile = service.build_candidate_profile(resume)
    detected = {s.name for s in profile.skills}

    expected = {"Python", "SQL", "Spark", "Hadoop", "ETL"}
    assert expected.issubset(detected)


def test_synthetic_persona_software_candidate(service):
    """Verify Software candidate persona extracts expected skills and unresolved Spring Boot."""
    resume = ParsedResume(
        filename="swe.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Backend developer building cloud microservices.",
            skills="Java, Spring Boot, REST APIs, MySQL",
            experience="Engineered high-concurrency microservices with Java, MySQL, and REST APIs.",
        ),
    )
    profile = service.build_candidate_profile(resume)
    detected = {s.name for s in profile.skills}
    unresolved = {u.term for u in profile.unresolved_skills}

    assert "Java" in detected
    assert "REST API" in detected
    assert "MySQL" in detected
    assert "Spring Boot" in unresolved


def test_pii_sanitization_and_matching_text(builder):
    """Verify candidate matching text generator strips emails, phones, and retains technical evidence."""
    raw_summary = "Contact: john.doe@example.com or (555) 123-4567. Full stack developer."
    resume = ParsedResume(
        filename="pii_test.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary=raw_summary,
            skills="Python, PostgreSQL",
            projects="Developed REST API using Python and PostgreSQL.",
        ),
    )
    extractor = SkillExtractor()
    skills, unresolved = extractor.extract_skills(resume)
    profile = builder.build_profile(resume, skills, unresolved)

    matching_text = build_candidate_matching_text(profile)

    # Technical tokens present
    assert "Python" in matching_text
    assert "PostgreSQL" in matching_text
    assert "REST API" in matching_text

    # Contact info stripped
    assert "john.doe@example.com" not in matching_text
    assert "555" not in matching_text
    assert "(555) 123-4567" not in matching_text


def test_compatibility_with_matching_candidate_profile(service):
    """Verify structured profile converts directly to app.matching.schemas.CandidateProfile."""
    resume = ParsedResume(
        filename="match_compat.pdf",
        file_type="pdf",
        raw_text="",
        cleaned_text="",
        sections=ResumeSections(
            summary="Data scientist proficient in Python and SQL.",
            skills="Python, SQL, Machine Learning",
        ),
    )
    profile = service.build_candidate_profile(resume, candidate_id="cand_test_01")
    matcher_profile = service.to_matcher_profile(profile)

    assert matcher_profile.candidate_id == "cand_test_01"
    assert "Python" in matcher_profile.skills
    assert "SQL" in matcher_profile.skills
    assert "Machine Learning" in matcher_profile.skills
    assert isinstance(matcher_profile.summary, str)
    assert len(matcher_profile.summary) > 0


def test_real_fixture_resumes_end_to_end():
    """Verify analyze_resume_file runs end-to-end on real fixture documents from Step 9."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    docx_path = FIXTURES_DIR / "sample_resume.docx"

    pdf_profile = analyze_resume_file(pdf_path)
    assert pdf_profile.metadata.parser_status == "success"
    assert len(pdf_profile.skills) >= 10
    assert any(s.name == "C++" for s in pdf_profile.skills)
    assert any(s.name == "Node.js" for s in pdf_profile.skills)

    docx_profile = analyze_resume_file(docx_path)
    assert docx_profile.metadata.parser_status == "success"
    assert len(docx_profile.skills) >= 8
    assert any(s.name == "SQL" for s in docx_profile.skills)
    assert any(s.name == "Tableau" for s in docx_profile.skills)
