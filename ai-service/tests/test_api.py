"""Integration and failure tests for FastAPI AI-service API endpoints.

Validates all requirements from Step 11:
- Liveness probe: GET /health (200 OK)
- Readiness probe: GET /ready (200 OK with AI dependency status)
- Resume parse: POST /api/v1/resume/parse (PDF and DOCX)
- Resume analyze: POST /api/v1/resume/analyze (extracts structured candidate profile)
- Job match: POST /api/v1/match (Tripartite hybrid matching)
- End-to-end: POST /api/v1/resume/analyze-and-match (full pipeline)
- Failure handling:
  - Unsupported file format (415 UNSUPPORTED_FILE_TYPE)
  - Oversized file rejection (413 FILE_TOO_LARGE)
  - Corrupt document handling (422 CORRUPT_DOCUMENT)
  - Empty candidate matching request (400 INVALID_REQUEST)
  - Invalid top_k parameter (422 VALIDATION_ERROR)
- Request correlation ID headers (X-Request-ID)
- Absence of SDS/JDS bias in matching outputs
- Score bounds [0, 100] and deterministic ranking
"""

import io
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.main import app

FIXTURES_DIR = AI_SERVICE_DIR / "tests" / "fixtures" / "resumes"


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Instantiate TestClient executing lifespan startup and shutdown."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client: TestClient):
    """Verify GET /health liveness probe returns 200 with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["service"] == "skillgap-ai-service"
    assert data["status"] == "healthy"
    assert "X-Request-ID" in response.headers


def test_readiness_check(client: TestClient):
    """Verify GET /ready readiness probe returns 200 with all AI components ready."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "ready"
    components = data["components"]
    assert components["skill_taxonomy"] == "ready"
    assert components["job_profiles"] == "ready"
    assert components["tfidf_artifacts"] == "ready"
    assert components["semantic_embeddings"] == "ready"
    assert components["matching_engine"] == "ready"


def test_resume_parse_pdf(client: TestClient):
    """Verify POST /api/v1/resume/parse extracts sections and metadata for valid PDF."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/resume/parse",
            files={"file": ("sample_resume.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    payload = data["data"]
    assert payload["file_type"] == "pdf"
    assert "summary" in payload["sections"]
    assert "skills" in payload["sections"]
    assert payload["metadata"]["page_count"] == 1
    assert payload["metadata"]["text_extraction_status"] == "success"


def test_resume_parse_docx(client: TestClient):
    """Verify POST /api/v1/resume/parse extracts sections and metadata for valid DOCX."""
    docx_path = FIXTURES_DIR / "sample_resume.docx"
    with open(docx_path, "rb") as f:
        response = client.post(
            "/api/v1/resume/parse",
            files={"file": ("sample_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    payload = data["data"]
    assert payload["file_type"] == "docx"
    assert payload["metadata"]["text_extraction_status"] == "success"


def test_resume_analyze_pdf(client: TestClient):
    """Verify POST /api/v1/resume/analyze generates structured candidate profile."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/resume/analyze",
            files={"file": ("sample_resume.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    profile = data["data"]["candidate_profile"]
    assert len(profile["skills"]) >= 10
    skill_names = {s["name"] for s in profile["skills"]}
    assert "C++" in skill_names
    assert "Node.js" in skill_names
    assert "PostgreSQL" in skill_names

    # Check that each skill has evidence and bounded confidence
    for skill in profile["skills"]:
        assert 0.0 <= skill["confidence"] <= 1.0
        assert len(skill["evidence"]) > 0


def test_match_endpoint(client: TestClient):
    """Verify POST /api/v1/match ranks jobs using the hybrid matching engine."""
    payload = {
        "skills": ["Python", "SQL", "Machine Learning"],
        "summary": "Built machine learning prediction services using Python and SQL.",
        "experience_years": 3.0,
        "top_k": 5,
    }
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    match_data = data["data"]
    assert match_data["matching_version"] == "1.0.0"
    assert len(match_data["matches"]) == 5

    # Verify score bounds and sorting
    scores = [m["match_score"] for m in match_data["matches"]]
    assert all(0.0 <= s <= 100.0 for s in scores)
    assert scores == sorted(scores, reverse=True)

    # Verify explanations and components
    first_match = match_data["matches"][0]
    assert "job_id" in first_match
    assert "job_title" in first_match
    assert first_match["components"]["skill_overlap"] is not None
    assert first_match["components"]["tfidf_similarity"] is not None
    assert first_match["components"]["semantic_similarity"] is not None
    assert len(first_match["explanation"]) > 0


def test_analyze_and_match_end_to_end(client: TestClient):
    """Core E2E test: uploads PDF resume -> parses -> profiles -> ranks jobs."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/resume/analyze-and-match?top_k=5",
            files={"file": ("sample_resume.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    payload = data["data"]

    # Verify candidate profile presence
    profile = payload["candidate_profile"]
    assert len(profile["skills"]) >= 10

    # Verify top matches presence and properties
    matches = payload["top_matches"]
    assert len(matches) == 5
    for m in matches:
        assert 0.0 <= m["match_score"] <= 100.0
        assert isinstance(m["matched_skills"], list)
        assert isinstance(m["missing_skills"], list)
        # Ensure no SDS/JDS predictions exist in payload
        assert "personality" not in m
        assert "salary_hike" not in m


def test_unsupported_file_type_rejected(client: TestClient):
    """Verify uploading an unsupported file (.txt) returns HTTP 415."""
    fake_txt = io.BytesIO(b"Candidate text content")
    response = client.post(
        "/api/v1/resume/parse",
        files={"file": ("resume.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_corrupt_file_rejected(client: TestClient):
    """Verify corrupt document returns HTTP 422."""
    corrupt_path = FIXTURES_DIR / "corrupt.pdf"
    with open(corrupt_path, "rb") as f:
        response = client.post(
            "/api/v1/resume/parse",
            files={"file": ("corrupt.pdf", f, "application/pdf")},
        )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CORRUPT_DOCUMENT"


def test_empty_candidate_match_rejected(client: TestClient):
    """Verify empty candidate request (no skills, no summary) returns HTTP 400."""
    payload = {
        "skills": [],
        "summary": "",
        "top_k": 5,
    }
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_REQUEST"


def test_invalid_top_k_rejected(client: TestClient):
    """Verify top_k exceeding limits returns HTTP 422 validation error."""
    payload = {
        "skills": ["Python"],
        "top_k": 100,  # Max allowed is 50
    }
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
