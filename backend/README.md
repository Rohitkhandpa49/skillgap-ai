# SkillGap AI Backend Service

The Node.js + Express + TypeScript public API backend for **SkillGap AI**. It serves as the primary gateway for clients, orchestrating the PostgreSQL database via Prisma ORM and delegating AI/NLP extraction and matching workloads to the internal Python FastAPI service.

---

## 1. Architecture Overview

```text
       Browser / Client
              ↓
  [ Express Gateway (Port 5000) ]
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[ Prisma ORM ]   [ AI Service Client ]
    │                   │
    ▼                   ▼
[ PostgreSQL ]   [ FastAPI AI Service (Port 8000) ]
(System of Record) (Resume Parsing & Hybrid Matching)
```

- **Express Public Boundary**: The frontend and public clients only communicate with Express. Neither PostgreSQL nor FastAPI is directly exposed to clients.
- **PostgreSQL / Prisma**: Authoritative system-of-record for users, resumes, structured candidate profiles, canonical skills, job postings, and matches.
- **FastAPI AI Service**: Stateless NLP/AI processing engine handling PDF/DOCX parsing, skill extraction, sentence transformer semantic matching, and hybrid candidate-to-job matching.

---

## 2. Technology Stack

- **Runtime**: Node.js (v20+ Recommended)
- **Framework**: Express 4.x with TypeScript (ES Modules)
- **Database Client**: Prisma Client 5.x
- **Schema Validation**: Zod 3.x (strictly validates both incoming HTTP requests and outgoing FastAPI AI responses)
- **File Uploads**: Multer with strict MIME type/extension enforcement and collision-free UUID storage
- **HTTP Client**: Axios with configured timeouts and domain error translation
- **Security & Reliability**: Helmet, CORS, express-rate-limit, structured request-ID tracing

---

## 3. Environment Variables

Create a `.env` file in `backend/` based on `.env.example`:

| Variable | Default | Description |
|---|---|---|
| `NODE_ENV` | `development` | Runtime environment (`development`, `production`, `test`) |
| `PORT` | `5000` | Port for Express server |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `AI_SERVICE_URL` | `http://localhost:8000` | Base URL of internal FastAPI AI service |
| `AI_SERVICE_TIMEOUT_MS` | `30000` | Timeout in milliseconds for AI requests |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origin for frontend client |
| `UPLOAD_DIR` | `../uploads` | Storage directory for uploaded resumes |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload size in megabytes |
| `LOG_LEVEL` | `info` | Structured logging level (`debug`, `info`, `warn`, `error`) |

---

## 4. Setup and Installation

### Prerequisites
1. PostgreSQL running with migrations applied and database seeded (`npm run prisma:seed` in `database/`).
2. Python FastAPI AI service running on `http://localhost:8000` (`uvicorn app.main:app --port 8000`).

### Install Dependencies
```bash
cd backend
npm install
```

### Generate Prisma Client
```bash
# Generated from database/prisma/schema.prisma
cd ../database
npx prisma generate
```

---

## 5. Available Scripts

| Script | Command | Description |
|---|---|---|
| `npm run dev` | `tsx watch src/server.ts` | Start development server with live reload |
| `npm run build` | `tsc` | Compile TypeScript into `dist/` |
| `npm start` | `node dist/server.js` | Run compiled production server |
| `npm test` | `tsx tests/run_backend_tests.ts` | Run end-to-end integration test suite |
| `npm run typecheck` | `tsc --noEmit` | Validate type-checking across codebase |

---

## 6. API Routes

All public API endpoints are prefixed with `/api/v1`.

### System Health
- `GET /api/v1/health`: Lightweight process liveness check.
- `GET /api/v1/ready`: Comprehensive readiness check inspecting PostgreSQL and FastAPI `/ready`.

### Jobs
- `GET /api/v1/jobs?page=1&limit=20`: List paginated job requisitions.
- `GET /api/v1/jobs/:jobId`: Retrieve detailed job description, required skills, and metadata.

### Resumes
- `POST /api/v1/resumes/upload`: Upload PDF/DOCX resume file (`multipart/form-data`, field: `file`).
- `POST /api/v1/resumes/:resumeId/analyze`: Trigger AI parsing and candidate profile generation; idempotent.
- `POST /api/v1/resumes/:resumeId/analyze-and-match`: One-shot pipeline: parses resume, extracts skills, generates profile, executes hybrid matching against job corpus, and persists top matches.

### Profile
- `GET /api/v1/profile`: Retrieve candidate profile for current authenticated/demo user.
- `GET /api/v1/profile/skills`: Retrieve candidate's extracted skills with confidence and evidence.

### Matching
- `POST /api/v1/matches`: Run FastAPI hybrid matcher using persisted candidate profile and store results.
- `GET /api/v1/matches?limit=20`: Retrieve persisted job match results with scores and identified skill gaps.
- `GET /api/v1/matches/:matchId`: Retrieve single match detail by ID.

---

## 7. Temporary Development Ownership Strategy

Full authentication (JWT, OAuth, password hashing) is scheduled for **Step 15**.

To enable realistic testing before Step 15 without compromising security:
1. `backend/src/middleware/devContext.ts` injects a deterministic `demo.candidate@example.com` candidate context.
2. The user context is resolved against the seeded PostgreSQL `User` table.
3. Insecure query parameters (e.g., `?userId=...`) are explicitly **disallowed** to prevent dangerous authorization bypasses once real auth is introduced.

---

## 8. Known Limitations (Step 13)

- **Authentication**: JWT/session authentication is not yet enabled (arrives in Step 15).
- **Frontend**: React UI is not yet connected (arrives in Step 14).
- **Skill Gap Prioritization**: Advanced graph-based gap weighting, career roadmaps, and What-If simulation logic belong to Step 16.
- **Rate Limiting**: Rate limiting uses an in-memory window suitable for local development rather than Redis.
