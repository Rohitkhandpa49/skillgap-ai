# SkillGap AI - Step 13 Backend Integration Report

**Date**: 2026-10-07  
**Branch**: `feature/backend`  
**Integration Status**: **PASS (18 / 18 Tests Succeeded)**

---

## 1. Architecture

```text
Client / Frontend (Step 14)
           │
           ▼
[ Express Backend Gateway (Port 5000) ]
  ├── Request ID & Structured Logging
  ├── Input & Response Zod Validation
  ├── Rate Limiter & Helmet Security
  │
  ├── Prisma ORM
  │     ▼
  │  [ PostgreSQL 16 ] (Database System of Record)
  │
  └── AI Service Client (Axios + Timeout Translation)
        ▼
     [ FastAPI AI Service (Port 8000) ]
     (Resume Parsing & Hybrid Matcher)
```

- **Express Gateway**: Primary public API boundary. Frontend clients never communicate directly with PostgreSQL or FastAPI.
- **System of Record**: PostgreSQL stores users, resumes, structured candidate profiles, canonical skills, job postings, matches, and skill gaps.
- **Stateless AI Computation**: FastAPI executes CPU/GPU intensive parsing and vector similarity calculations.

---

## 2. Routes Implemented

| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/api/v1/health` | Process liveness check | Verified |
| `GET` | `/api/v1/ready` | Readiness check inspecting DB & FastAPI | Verified |
| `GET` | `/api/v1/jobs` | Paginated job postings list | Verified |
| `GET` | `/api/v1/jobs/:jobId` | Detailed job posting by ID | Verified |
| `POST` | `/api/v1/resumes/upload` | Multipart PDF/DOCX upload & storage | Verified |
| `POST` | `/api/v1/resumes/:resumeId/analyze` | AI extraction and profile persistence | Verified |
| `POST` | `/api/v1/resumes/:resumeId/analyze-and-match` | One-shot end-to-end orchestration | Verified |
| `GET` | `/api/v1/profile` | Retrieve candidate profile | Verified |
| `GET` | `/api/v1/profile/skills` | Retrieve candidate's extracted skills | Verified |
| `POST` | `/api/v1/matches` | Hybrid matching against profile & persist | Verified |
| `GET` | `/api/v1/matches` | Retrieve persisted matches with scores | Verified |
| `GET` | `/api/v1/matches/:matchId` | Retrieve single match detail | Verified |

---

## 3. Test & Verification Results

### 3.1 Runtime Integration: **PASS**
- Express successfully boots on port 5000.
- All requests tagged with UUID `x-request-id` header and logged with latency metrics.
- Clean JSON envelope standard applied:
  - Success: `{ "success": true, "data": ... }`
  - Error: `{ "success": false, "error": { "code": ..., "message": ... }, "requestId": ... }`

### 3.2 Database Integration: **PASS**
- Prisma client handles transactional writes atomically (`$transaction`).
- Resumes, CandidateProfiles, CandidateSkills, Matches, and SkillGaps persisted with relational integrity.
- Idempotency verified: re-analyzing the same resume updates the existing profile version rather than duplicating candidate profiles.

### 3.3 AI Service Integration: **PASS**
- AI service client communicates with FastAPI over HTTP with 30s timeout.
- Candidate skills and profile payloads validated with Zod prior to database persistence.
- Real hybrid matcher scores (Skill Overlap + TF-IDF + Semantic embeddings) returned and stored.

### 3.4 Failure & Resilience Tests: **PASS**
- **AI Unavailable**: `AIServiceError` with HTTP 503 and safe message returned.
- **AI Timeout**: Translated to `AITimeoutError` (code `AI_TIMEOUT`) with HTTP 504.
- **Malformed AI Response**: Detected by Zod validator and safely rejected with HTTP 502 before polluting database.
- **Invalid Uploads**:
  - Executable (`.exe`) rejected with HTTP 415.
  - Empty upload rejected with HTTP 400.

### 3.5 Security Checks: **PASS**
- Helmet sets secure HTTP headers.
- Path traversal prevention: uploaded files stored under internal UUID filenames; direct path manipulation blocked.
- PII & Credential protection: Passwords, tokens, and raw resume contents redacted from logs.
- Rate limiting active on expensive upload/analyze/match routes.

---

## 4. Latency & Performance Observations

Approximate timings recorded during integration test execution:

| Operation | Latency |
|---|---|
| Resume Upload (`POST /resumes/upload`) | ~13 ms |
| AI Resume Analysis (`POST /resumes/:id/analyze`) | ~75 ms |
| Re-analysis (Idempotent update) | ~58 ms |
| Hybrid Job Matching (`POST /matches`) | ~1,193 ms |
| Full One-Shot Orchestration (`upload + analyze + match`) | ~1,463 ms |
| Profile Retrieval (`GET /profile`) | ~3 ms |
| Jobs List (`GET /jobs`) | ~48 ms |

---

## 5. Known Limitations (Step 13)

1. **Authentication**: User authentication (JWT, bcrypt, registration/login) is NOT implemented in Step 13. A controlled development identity (`demo.candidate@example.com`) is injected by `devContext` middleware. Step 15 will replace this with full JWT authentication.
2. **Frontend**: React application is NOT integrated yet (Step 14).
3. **Advanced Skill Gap Logic**: Graph-based priority weighting, career roadmaps, and What-If simulations are NOT implemented yet (Step 16).
4. **Rate Limiting**: Rate limiting uses memory storage suitable for development/hackathon deployment.
