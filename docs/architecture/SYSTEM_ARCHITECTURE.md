# System Architecture — SkillGap AI

## 1. Document Purpose

This document defines the complete system architecture for **SkillGap AI — AI Talent Matching & Skill Gap Engine**.

The architecture is designed for a five-member hackathon team and a rapid MVP implementation while keeping clear boundaries between:

- React frontend
- Node.js/Express backend
- Python/FastAPI AI service
- PostgreSQL/Prisma database
- Skill/job knowledge data
- Matching and career-intelligence modules
- Integration, security, testing, and deployment

The architecture supports the complete product journey:

```text
Resume Upload
      ↓
Resume Understanding
      ↓
Skill Extraction
      ↓
Skill Normalization
      ↓
Candidate Profile
      ↓
Semantic Representation / Embeddings
      ↓
Job Matching
      ↓
Explainable Match Score
      ↓
Skill Gap Analysis
      ↓
Career Roadmap
      ↓
What-if Skill Simulation
```

---

# 2. Product Goal

SkillGap AI converts an unstructured candidate resume into a structured, explainable career profile and uses it to:

1. Understand the candidate.
2. Extract and normalize skills.
3. Build a structured candidate profile.
4. Compare the candidate with available jobs.
5. Rank jobs using semantic and structured signals.
6. Explain why a job matches.
7. Identify missing skills.
8. Prioritize skill gaps.
9. Generate a career-learning roadmap.
10. Simulate how additional skills could improve job compatibility.

The system should prioritize **explainability, modularity, security, and fast integration** rather than unnecessary complexity.

---

# 3. High-Level Architecture

```text
                         ┌─────────────────────────┐
                         │         USER            │
                         │ Candidate / Recruiter   │
                         └────────────┬────────────┘
                                      │
                                      │ HTTPS / REST
                                      ▼
                         ┌─────────────────────────┐
                         │     REACT FRONTEND      │
                         │ React + TypeScript      │
                         │ Tailwind CSS            │
                         └────────────┬────────────┘
                                      │
                                      │ /api/v1/*
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       NODE.JS / EXPRESS BACKEND        │
                  │                                        │
                  │ Routes → Controllers → Services       │
                  │ Validation → Business Logic            │
                  └───────────────┬───────────────┬────────┘
                                  │               │
                            Prisma│               │HTTP/JSON
                                  │               │
                                  ▼               ▼
                    ┌──────────────────┐   ┌─────────────────────┐
                    │   POSTGRESQL     │   │ PYTHON FASTAPI AI   │
                    │                  │   │       SERVICE       │
                    │ Users            │   │                     │
                    │ Resumes          │   │ Resume Parser       │
                    │ Profiles         │   │ NLP                 │
                    │ Skills           │   │ Extraction           │
                    │ Jobs             │   │ Normalization        │
                    │ Matches          │   │ Embeddings           │
                    │ Skill Gaps       │   │ Matching             │
                    │ Roadmaps         │   │ Skill Gap            │
                    └──────────────────┘   │ Roadmap              │
                                           └──────────┬──────────┘
                                                      │
                                                      ▼
                                           ┌─────────────────────┐
                                           │ KNOWLEDGE / DATA    │
                                           │ Skills              │
                                           │ Aliases             │
                                           │ Jobs                │
                                           │ Career Paths        │
                                           └─────────────────────┘
```

---

# 4. Architectural Principles

## 4.1 Separation of Responsibilities

Each service should have one clear responsibility.

```text
Frontend
    → Presentation and user interaction

Backend
    → API gateway, orchestration, authorization, persistence

AI Service
    → NLP, embeddings, matching intelligence, recommendations

Database
    → Persistent structured application state

Data
    → Static/seed knowledge used by the application
```

## 4.2 Contract-First Development

API contracts are frozen before parallel implementation.

```text
Architecture
     ↓
API Contract
     ↓
Parallel Development
     ↓
Integration
     ↓
End-to-End Validation
```

## 4.3 Backend as the System Boundary

The browser should communicate with the Node backend, not directly with PostgreSQL or internal AI endpoints.

```text
Browser
   ↓
Backend
   ├── Database
   └── AI Service
```

This protects internal services and keeps credentials out of the browser.

## 4.4 Explainability by Design

The matching system should return not only a score but also:

- matched skills
- missing skills
- score breakdown
- relevant experience signals
- education/certification signals
- improvement opportunities

## 4.5 MVP-First Architecture

The architecture intentionally avoids unnecessary infrastructure such as:

- Kubernetes
- multiple databases
- complex event buses
- live job scraping
- large distributed systems
- heavyweight MLOps platforms

These can be introduced later if the product grows.

---

# 5. Repository Architecture

```text
skillgap-ai/
│
├── frontend/
│
├── backend/
│
├── ai-service/
│
├── database/
│   └── prisma/
│
├── data/
│   ├── skills.json
│   ├── aliases.json
│   ├── jobs.json
│   ├── career_paths.json
│   └── evaluation/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── backend/
│   ├── ai-nlp/
│   ├── frontend/
│   ├── integration/
│   ├── system/
│   └── ai-evaluation/
│
├── docker/
├── scripts/
├── uploads/
│
├── .github/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── CONTRIBUTING.md
└── README.md
```

---

# 6. Frontend Architecture

## Technology

```text
React
TypeScript
Vite
Tailwind CSS
React Router
Axios
Charts
```

## Responsibilities

The frontend is responsible for:

- navigation
- resume upload
- loading/progress states
- candidate dashboard
- skill visualization
- job recommendations
- match explanation
- skill-gap presentation
- roadmap visualization
- what-if simulation
- error and empty states

## Suggested structure

```text
frontend/
└── src/
    ├── assets/
    ├── components/
    │   ├── common/
    │   ├── dashboard/
    │   ├── resume/
    │   ├── jobs/
    │   ├── matching/
    │   ├── skill-gap/
    │   ├── roadmap/
    │   └── simulator/
    ├── pages/
    ├── hooks/
    ├── services/
    │   └── api.ts
    ├── store/
    ├── types/
    ├── utils/
    ├── App.tsx
    └── main.tsx
```

## Frontend flow

```text
Landing
   ↓
Upload Resume
   ↓
Analyzing
   ↓
Candidate Profile
   ↓
Recommended Jobs
   ↓
Match Details
   ↓
Skill Gap
   ↓
Career Roadmap
   ↓
What-if Simulator
```

The frontend should consume typed API responses and should not implement database or AI-service logic.

---

# 7. Backend Architecture

## Technology

```text
Node.js
Express
TypeScript
Prisma
PostgreSQL
Multer
Zod
Axios
Helmet
CORS
```

## Layered architecture

```text
HTTP Request
     ↓
Route
     ↓
Middleware
     ↓
Controller
     ↓
Validation
     ↓
Service
     ↓
Repository / Prisma
     ↓
Database
```

For AI operations:

```text
Controller
    ↓
Service
    ↓
AI Client
    ↓
FastAPI
```

## Responsibilities

The backend should:

- expose public APIs
- validate requests
- authenticate users when authentication is enabled
- authorize resource access
- handle file upload
- orchestrate AI requests
- persist structured results
- manage jobs and candidate data
- return stable API contracts
- handle errors
- log operational events without leaking PII

---

# 8. AI/NLP Service Architecture

## Technology

```text
Python
FastAPI
PyMuPDF
python-docx
spaCy / rule-based NLP
Sentence Transformers
scikit-learn
NumPy
Pydantic
```

## AI pipeline

```text
Resume File
    ↓
Text Extraction
    ↓
Text Cleaning
    ↓
Section Detection
    ↓
Skill Extraction
    ↓
Skill Normalization
    ↓
Experience / Education / Certification Extraction
    ↓
Structured Candidate Profile
    ↓
Embedding Generation
```

## AI service modules

```text
ai-service/
└── app/
    ├── api/
    ├── core/
    ├── models/
    ├── schemas/
    ├── services/
    │   ├── parser/
    │   ├── extraction/
    │   ├── normalization/
    │   ├── embeddings/
    │   ├── matching/
    │   ├── skill_gap/
    │   └── roadmap/
    ├── utils/
    └── main.py
```

The AI service must return validated structured JSON rather than arbitrary text.

---

# 9. Database Architecture

## Technology

```text
PostgreSQL
Prisma ORM
```

## Core entities

```text
User
  │
  └── Resume
        │
        └── CandidateProfile
              │
              └── CandidateSkill ─── Skill ─── SkillAlias

Job ─── JobSkill ─── Skill

CandidateProfile
        │
        └── Match ─── Job

Match
  │
  └── SkillGap

CandidateProfile
        │
        └── CareerPath / Roadmap
```

## Responsibilities

The database stores:

- user identity
- resume metadata
- candidate profiles
- normalized skills
- skill aliases
- candidate-skill relationships
- job information
- job-skill requirements
- match results
- skill gaps
- career roadmap state

Static seed data can remain in JSON where appropriate and be imported into the database during setup.

---

# 10. Data Architecture

The `data/` directory contains controlled knowledge and seed data.

```text
data/
├── skills.json
├── aliases.json
├── jobs.json
├── career_paths.json
└── evaluation/
```

## Skills

Example:

```json
{
  "id": "skill_python",
  "name": "Python",
  "category": "programming"
}
```

## Aliases

```json
{
  "alias": "ReactJS",
  "canonical": "React"
}
```

## Jobs

```json
{
  "jobId": "job_001",
  "title": "Machine Learning Engineer",
  "requiredSkills": [
    "Python",
    "Machine Learning",
    "Pandas"
  ],
  "optionalSkills": [
    "PyTorch",
    "Docker"
  ]
}
```

## Career Paths

```text
Python
   ↓
Data Analysis
   ↓
Machine Learning
   ↓
Deep Learning
   ↓
PyTorch
   ↓
ML Engineer
```

---

# 11. Resume Processing Architecture

```text
                    Resume
                       │
              ┌────────┴────────┐
              │                 │
             PDF               DOCX
              │                 │
              └────────┬────────┘
                       ↓
                Text Extraction
                       ↓
                 Text Cleaning
                       ↓
               Section Detection
                       ↓
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
    Skills         Experience       Education
       ↓               ↓                ↓
       └───────────────┼────────────────┘
                       ↓
                Normalization
                       ↓
              Candidate Profile
```

---

# 12. Skill Normalization Architecture

The same skill can appear in multiple forms.

```text
React
React.js
ReactJS
React JS
```

These should map to:

```text
React
```

Pipeline:

```text
Raw Skill
    ↓
Cleaning
    ↓
Alias Lookup
    ↓
Canonical Skill
    ↓
Ontology Category
    ↓
Candidate Skill
```

Normalization should preserve evidence from the original resume where possible.

---

# 13. Candidate Profile Architecture

The resume becomes:

```text
Candidate Profile
│
├── Identity / Metadata
├── Skills
│   ├── Canonical Name
│   ├── Confidence
│   └── Evidence
│
├── Experience
├── Education
├── Certifications
├── Projects
└── Embedding
```

Important distinction:

```text
Confidence ≠ Proficiency
```

A model may be highly confident that the resume contains "Python" without knowing whether the candidate is beginner, intermediate, or expert.

---

# 14. Job Representation

Each job should have a structured representation:

```text
Job
│
├── Title
├── Description
├── Required Skills
├── Optional Skills
├── Experience Requirement
├── Education Requirement
└── Embedding
```

The same normalization system used for candidates should be used for job skills.

---

# 15. Matching Architecture

Matching uses both semantic and structured signals.

```text
Candidate Profile
       │
       ├──────────────→ Candidate Embedding
       │
       └──────────────→ Candidate Skills
                              │
                              │
Job Profile              Job Skills
       │                    │
       ├────────→ Job Embedding
       │                    │
       └────────────────────┘
                ↓
        Hybrid Match Engine
                ↓
         Match Score
```

Recommended MVP score:

```text
50% Semantic Similarity
30% Skill Match
10% Experience
10% Education/Certification
```

The weights should be configurable rather than scattered as constants throughout the codebase.

---

# 16. Matching Explainability

Instead of returning only:

```text
85%
```

return:

```text
85% Match

Matched:
✓ Python
✓ Pandas
✓ Machine Learning

Missing:
⚠ PyTorch
⚠ Docker

Experience:
✓ Good alignment

Education:
✓ Meets requirement
```

Architecture:

```text
Raw Signals
    ↓
Score Components
    ↓
Final Score
    ↓
Explanation Generator
    ↓
Frontend
```

---

# 17. Skill Gap Architecture

```text
Candidate Skills
       +
Target Job Skills
       ↓
Skill Comparison
       ↓
┌──────┼───────────────┐
↓      ↓               ↓
Match  Partial       Missing
       ↓               ↓
       └──────┬────────┘
              ↓
        Priority Engine
              ↓
        Skill Gap Result
```

Priorities may be:

```text
High
Medium
Low
```

Priority should consider role requirements and dependencies rather than only frequency.

---

# 18. Career Roadmap Architecture

```text
Current Candidate State
          ↓
Target Job
          ↓
Missing Skills
          ↓
Skill Dependencies
          ↓
Recommended Learning Order
          ↓
Career Roadmap
```

Example:

```text
Current:
Python + SQL + Pandas

Target:
ML Engineer

Roadmap:
1. Machine Learning
2. Scikit-learn
3. Deep Learning
4. PyTorch
5. Docker
```

The roadmap should be grounded in structured skill/job knowledge rather than blindly generating unsupported claims.

---

# 19. What-if Simulation Architecture

The simulator creates a temporary candidate state.

```text
Current Profile
      ↓
Current Match
      ↓
User Adds Skill(s)
      ↓
Temporary Skill Set
      ↓
Recalculate Match
      ↓
Compare Before / After
      ↓
Return Simulation
```

Important:

```text
Simulation
    ≠
Permanent Profile Update
```

Example:

```text
Current Score: 72%

+ PyTorch
      ↓
78%

+ Docker
      ↓
84%
```

---

# 20. End-to-End Request Flow

## Resume upload

```text
User
 ↓
React
 ↓
POST /api/v1/resume/upload
 ↓
Express
 ↓
File Validation
 ↓
Safe Storage
 ↓
Database Metadata
 ↓
Resume ID
 ↓
React
```

## Resume analysis

```text
React
 ↓
POST /api/v1/resume/analyze
 ↓
Backend
 ↓
FastAPI
 ↓
Parser
 ↓
NLP
 ↓
Skill Extraction
 ↓
Normalization
 ↓
Profile
 ↓
Backend
 ↓
PostgreSQL
 ↓
React
```

## Matching

```text
React
 ↓
Backend
 ↓
Candidate Profile + Job
 ↓
AI Matching
 ↓
Embedding Similarity
 +
Skill Matching
 +
Experience
 +
Education
 ↓
Match Score
 ↓
Explanation
 ↓
Database
 ↓
React
```

---

# 21. Integration Architecture

Integration should happen progressively.

## Phase 1

```text
Frontend ↔ Backend
```

## Phase 2

```text
Backend ↔ Database
```

## Phase 3

```text
Backend ↔ AI Service
```

## Phase 4

```text
Frontend
   ↕
Backend
   ↕
AI Service
   ↕
Database
```

## Phase 5

```text
Complete:
Upload → Parse → Profile → Match → Gap → Roadmap → Simulator
```

---

# 22. Deployment Architecture

For the hackathon, Docker Compose is sufficient.

```text
                  Docker Compose
                        │
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
   Frontend         Backend          AI Service
   :5173             :5000              :8000
                        │                 │
                        └───────┬─────────┘
                                ↓
                           PostgreSQL
                              :5432
```

Production deployment can later replace local Compose services with managed hosting.

---

# 23. Environment Architecture

Never hard-code environment-specific values.

Example:

```env
NODE_ENV=development
PORT=5000
DATABASE_URL=...
AI_SERVICE_URL=http://localhost:8000
CORS_ORIGIN=http://localhost:5173
JWT_SECRET=...
MAX_FILE_SIZE_MB=10
```

Frontend should use only public configuration.

Backend secrets must remain server-side.

---

# 24. Security Architecture

```text
Internet
   ↓
Frontend
   ↓
Backend Security Layer
   ├── CORS
   ├── Helmet
   ├── Rate Limiting
   ├── Validation
   ├── Authentication
   └── Authorization
        ↓
   ┌────┴─────┐
   ↓          ↓
Database    AI Service
```

Security requirements:

- Validate uploads.
- Sanitize filenames.
- Prevent path traversal.
- Limit request/file size.
- Validate all API inputs.
- Keep credentials in environment variables.
- Do not expose internal AI endpoints.
- Avoid logging resume contents.
- Do not expose stack traces.
- Protect database credentials.
- Never commit `.env`.
- Do not execute arbitrary content extracted from resumes.

---

# 25. Privacy Architecture

Resumes can contain personal information.

Therefore:

```text
Resume
  ↓
Private storage
  ↓
Controlled processing
  ↓
Structured profile
  ↓
Minimal required persistence
```

The system should avoid:

- unnecessary PII logging
- public upload directories
- exposing raw resume paths
- putting resumes into Git
- sending sensitive data to unrelated third-party services

---

# 26. Observability

Every service should provide at least:

```text
Health check
Structured logs
Request ID
Error logging
Latency measurement
```

Example:

```text
Request ID: req_123
Endpoint: POST /api/v1/resume/analyze
Duration: 2.8s
Status: 200
```

Do not log raw resume text or secrets.

---

# 27. Testing Architecture

Testing should exist at four levels.

```text
Unit Tests
    ↓
Service/API Tests
    ↓
Integration Tests
    ↓
End-to-End Tests
```

Critical E2E scenario:

```text
Upload Resume
     ↓
Parse Resume
     ↓
Extract Skills
     ↓
Normalize Skills
     ↓
Create Profile
     ↓
Retrieve Jobs
     ↓
Calculate Match
     ↓
Identify Skill Gap
     ↓
Generate Roadmap
     ↓
Run Simulator
```

---

# 28. Git Architecture

```text
main
  │
  └── integration
       │
       ├── feature/database
       ├── feature/backend
       ├── feature/ai-nlp
       ├── feature/frontend
       └── feature/matching-integration
```

## Branch responsibilities

| Branch | Owner | Area |
|---|---|---|
| `feature/database` | Ankit | Prisma/PostgreSQL |
| `feature/backend` | Adil | Express/API |
| `feature/ai-nlp` | Mayank | FastAPI/NLP |
| `feature/frontend` | Kanishaka | React UI |
| `feature/matching-integration` | Rohit | Matching/Integration |

Flow:

```text
Feature Branch
      ↓
Pull Request
      ↓
integration
      ↓
Integration Tests
      ↓
Pull Request
      ↓
main
```

---

# 29. Team Ownership Architecture

## Ankit — Database

```text
database/
data/
```

Focus:

- Prisma schema
- migrations
- seed data
- skills/jobs relationships

## Adil — Backend

```text
backend/
```

Focus:

- Express
- APIs
- validation
- authentication
- orchestration

## Mayank — AI/NLP

```text
ai-service/
```

Focus:

- parsing
- NLP
- extraction
- normalization
- embeddings
- AI evaluation

## Kanishaka — Frontend

```text
frontend/
```

Focus:

- UX
- dashboard
- job matching
- skill gap
- roadmap
- simulator

## Rohit — Integration

```text
integration
docker
.github
docs/architecture
```

Focus:

- API contract
- service integration
- matching
- Docker
- E2E
- deployment

---

# 30. 15-Hour Implementation Architecture

## Hour 0–1

```text
Requirements
     ↓
Architecture
     ↓
API Contracts
     ↓
DB Schema
     ↓
Git Setup
```

## Hour 1–4

Parallel:

```text
Database
Backend
AI/NLP
Frontend
Integration setup
```

## Hour 4–7

```text
Basic Integration
     ↓
Upload
     ↓
Parse
     ↓
Extract
     ↓
Store
     ↓
Display Profile
```

## Hour 7–10

```text
Embeddings
     ↓
Matching
     ↓
Explainability
     ↓
Skill Gap
     ↓
Roadmap
```

## Hour 10–12

```text
What-if Simulator
Security
E2E
UI Polish
```

## Hour 12–13

```text
AI Evaluation
Ontology
Dataset validation
```

## Hour 13–15

```text
Final Testing
Deployment
Demo Script
Presentation
Backup Demo
```

---

# 31. Failure and Fallback Architecture

The demo must not depend on a single fragile component.

If advanced AI processing fails:

```text
Advanced AI
     ↓
Fallback extraction
     ↓
Rule/keyword skill extraction
     ↓
Seeded job matching
     ↓
Demo continues
```

This fallback should be clearly separated from the primary AI path and must not falsely claim that an AI model performed an operation when it did not.

---

# 32. RAG Positioning

RAG is **not required for the core matching engine**.

Core:

```text
Resume
 ↓
Skills
 ↓
Embeddings
 ↓
Semantic Similarity
 ↓
Matching
```

Optional RAG:

```text
Candidate Profile
       ↓
Skill Gap
       ↓
Knowledge Base Retrieval
       ↓
Grounded Career Recommendation
```

Therefore:

```text
Embeddings ≠ RAG
```

RAG should only be added if it improves grounded recommendations without risking the MVP timeline.

---

# 33. Scalability Path

The hackathon architecture can later evolve:

```text
Current MVP
   ↓
Managed PostgreSQL
   ↓
Object Storage
   ↓
Redis / Cache
   ↓
Background Job Queue
   ↓
Dedicated Embedding Service
   ↓
Model Serving
   ↓
Observability Platform
   ↓
Scalable Deployment
```

Do not implement these prematurely during the 15-hour hackathon.

---

# 34. Architecture Decision Summary

| Decision | Choice | Reason |
|---|---|---|
| Frontend | React + TS | Fast UI development |
| Backend | Node + Express + TS | Clear API/orchestration layer |
| AI | Python + FastAPI | NLP/ML ecosystem |
| Database | PostgreSQL | Structured relational data |
| ORM | Prisma | Type-safe database access |
| Matching | Hybrid | Better than keyword-only matching |
| Embeddings | Transformer-based | Semantic similarity |
| Upload | Backend controlled | Security |
| Deployment | Docker Compose | Fast reproducible setup |
| API | REST/JSON | Simple team integration |
| RAG | Optional | Not required for core matching |

---

# 35. Definition of Done

Architecture is considered implemented when:

```text
☐ Frontend runs
☐ Backend runs
☐ AI service runs
☐ PostgreSQL runs
☐ Services have defined responsibilities
☐ API contract is frozen
☐ Database schema is defined
☐ Resume flow is defined
☐ AI pipeline is defined
☐ Matching pipeline is defined
☐ Skill-gap pipeline is defined
☐ Roadmap pipeline is defined
☐ Simulator is defined
☐ Security boundary is defined
☐ Testing strategy is defined
☐ Docker architecture is defined
☐ Git branching strategy is defined
☐ Team ownership is defined
☐ End-to-end flow is testable
```

---

# 36. Final Architecture

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │ REACT FRONTEND  │
                  │ Upload/Dashboard│
                  └────────┬────────┘
                           │
                     REST / JSON
                           │
                           ▼
                ┌──────────────────────┐
                │ NODE / EXPRESS API   │
                │ Auth + Validation    │
                │ Orchestration        │
                └───────┬────────┬─────┘
                        │        │
                  Prisma│        │HTTP
                        │        │
                        ▼        ▼
              ┌────────────┐  ┌──────────────────┐
              │ POSTGRESQL │  │ PYTHON FASTAPI   │
              │            │  │                  │
              │ Profiles   │  │ Parser           │
              │ Skills     │  │ NLP              │
              │ Jobs       │  │ Extraction       │
              │ Matches    │  │ Normalization    │
              │ Gaps       │  │ Embeddings       │
              │ Roadmaps   │  │ Matching         │
              └────────────┘  │ Skill Gap        │
                              │ Roadmap           │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ KNOWLEDGE DATA   │
                              │ Skills/Aliases   │
                              │ Jobs/Career Paths│
                              └──────────────────┘
                                       │
                                       ▼
                              EXPLAINABLE RESULTS
                                       │
                                       ▼
                               CAREER DECISIONS
```

This architecture is the reference design for the implementation. Any major structural change should be agreed upon by the team and reflected in the architecture/API documentation before integration.
