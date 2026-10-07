# SkillGap AI - FastAPI Internal AI Service Integration Evaluation Report

**Date:** 2026-10-07  
**Module:** `ai-service/app/main.py`, `ai-service/app/api/`  
**Step:** 11 - FastAPI AI-Service Endpoint Integration  
**Branch:** `feature/ai-nlp`

---

## 1. Endpoints

The internal AI service exposes six dedicated endpoints designed for server-to-server consumption:

| Endpoint | Method | Input | Purpose | Output Status |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | Process liveness probe | `200 OK` |
| `/ready` | `GET` | None | AI dependency and artifact readiness probe | `200 OK` / `503 Service Unavailable` |
| `/api/v1/resume/parse` | `POST` | `multipart/form-data` (`file`) | Document validation and structured section parsing | `200 OK` |
| `/api/v1/resume/analyze` | `POST` | `multipart/form-data` (`file`) | Section parsing, evidence extraction, candidate profile | `200 OK` |
| `/api/v1/match` | `POST` | `application/json` (`MatchRequest`) | Candidate-to-job matching via Tripartite Hybrid Matcher | `200 OK` |
| `/api/v1/resume/analyze-and-match` | `POST` | `multipart/form-data` (`file`, `top_k`) | End-to-end resume intelligence pipeline | `200 OK` |

Interactive Swagger documentation is available at `/docs` and OpenAPI schema at `/openapi.json`.

---

## 2. Internal Architecture

```text
[HTTP Client / Backend Service]
       │
       ▼
[FastAPI Application (app/main.py)]
   • Correlation ID Middleware (X-Request-ID propagation)
   • Safe Structured Logging (Request metadata only; zero PII logged)
   • Strict CORS Middleware (Whitelisted development origins)
   • Centralized Error Handlers (Controlled error payloads, zero tracebacks)
       │
       ├── GET /health -> Lightweight process liveness check
       ├── GET /ready  -> Pre-loaded ServiceContainer readiness validation
       │
       ▼
[Resume Intelligence Routes (app/api/routes/resume.py)]
   • temporary_upload_file: Context manager streaming to secure UUID temp path
   • parse_resume: Validates magic bytes, enforces max size (10MB), extracts sections
   • CandidateProfileService: Extracts boundary-aware skills, computes heuristic confidence
       │
       ▼
[Candidate Matching Routes (app/api/routes/matching.py)]
   • HybridMatcher (Pre-loaded singleton in ServiceContainer):
     - 50% Explicit Canonical Skill Overlap
     - 20% TF-IDF Keyword Lexical Similarity
     - 30% Sentence Transformer (all-MiniLM-L6-v2) Dense Semantics
     - Strictly isolates JDS salary-hike and SDS personality models
       │
       ▼
[API Response (app/api/schemas/common.py)]
   • Standard success envelope: {"success": true, "data": {...}}
   • Standard error envelope:   {"success": false, "error": {"code": "...", "message": "..."}, "request_id": "..."}
```

---

## 3. Integration Tests

Automated integration tests executed via [`ai-service/tests/test_api.py`](file:///c:/Users/Mayank%20Bhambhani/Downloads/skillgap-ai/ai-service/tests/test_api.py):

| Test Case | Target Endpoint | Verification Criteria | Result |
| :--- | :--- | :--- | :--- |
| `test_health_check` | `GET /health` | Returns 200 with `status="healthy"` and `X-Request-ID` header | **PASS** |
| `test_readiness_check` | `GET /ready` | Returns 200 with all 5 component flags verified `ready` | **PASS** |
| `test_resume_parse_pdf` | `POST /api/v1/resume/parse` | Single-page PDF parsed into structured sections with metadata | **PASS** |
| `test_resume_parse_docx` | `POST /api/v1/resume/parse` | Technical DOCX parsed into structured sections with metadata | **PASS** |
| `test_resume_analyze_pdf` | `POST /api/v1/resume/analyze` | Generates structured candidate profile with evidence and confidence | **PASS** |
| `test_match_endpoint` | `POST /api/v1/match` | Ranks jobs with bounds `[0, 100]`, sorted scores, explanations | **PASS** |
| `test_analyze_and_match_end_to_end` | `POST /api/v1/resume/analyze-and-match` | Executes full pipeline: parse -> profile -> hybrid ranking | **PASS** |

**Overall Integration Test Status:** **PASS**

---

## 4. Failure Tests

Tested controlled domain error handling and HTTP status mapping:

| Failure Scenario | Request Condition | Expected Response | Result |
| :--- | :--- | :--- | :--- |
| Unsupported file format | Uploading `.txt` file | `HTTP 415` (`UNSUPPORTED_FILE_TYPE`) | **PASS** |
| Corrupt document | Uploading malformed PDF | `HTTP 422` (`CORRUPT_DOCUMENT`) | **PASS** |
| Empty candidate match | Request with no skills or summary | `HTTP 400` (`INVALID_REQUEST`) | **PASS** |
| Invalid `top_k` | `top_k=100` (exceeding 50 limit) | `HTTP 422` (`VALIDATION_ERROR`) | **PASS** |

**Overall Failure Test Status:** **PASS**

---

## 5. Performance Benchmarks

Measured on local CPU runtime across active endpoints:

- **Resume Parsing Latency (`/api/v1/resume/parse`):** ~35 – 85 ms
- **Candidate Analysis Latency (`/api/v1/resume/analyze`):** ~30 – 60 ms
- **Hybrid Matching Latency (`/api/v1/match`):** ~45 – 110 ms *(post-startup model warmup)*
- **End-to-End Pipeline Latency (`/api/v1/resume/analyze-and-match`):** ~150 – 250 ms *(steady state)*

Sentence Transformer model weights and precomputed embeddings (14,840 job postings) are cached in the singleton `ServiceContainer` on application startup to eliminate cold-start overhead per request.

---

## 6. Privacy & Lifecycle Guarantees

1. **Safe Logging:**
   - Every request is tagged with an `X-Request-ID` correlation UUID.
   - Structured logs record HTTP method, path, response status, and duration in milliseconds.
   - Request bodies, raw resume text, candidate emails, and phone numbers are **never logged**.
2. **Temporary-File Lifecycle:**
   - Uploaded multipart streams are saved to UUID-named files in a dedicated temporary directory.
   - The `temporary_upload_file` context manager uses `try...finally` to guarantee that temporary files are deleted immediately after parsing completes, even if parsing or extraction throws an exception.
3. **PII Redaction in Matching Texts:**
   - Candidate matching texts sanitize contact emails, phone numbers, and web URLs prior to embedding computation.

---

## 7. Known Limitations

1. **No OCR Support:** Scanned or image-only documents lacking embedded text glyphs report `TEXT_EXTRACTION_INSUFFICIENT` rather than performing OCR.
2. **Stateless Operations (No DB Persistence):** FastAPI does not connect directly to PostgreSQL or Prisma. Persistence and user association are deferred to the Node.js backend.
3. **No End-User Authentication:** FastAPI is designed as an internal microservice; user authentication and JWT session verification are responsibilities of the Node.js gateway.
4. **Finite Taxonomy:** Non-taxonomy skills are captured as `unresolved_skills` and do not contribute to explicit skill overlap in job matching.
5. **Heuristic Confidence:** Skill confidence scores represent deterministic heuristic evidence strength and section provenance, not statistical probabilities.
6. **Segregated Experimental Models:** JDS salary hike and SDS personality classifiers remain strictly excluded from job matching and candidate scoring.
