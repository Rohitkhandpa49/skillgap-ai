# INTEGRATION + DEVOPS + QA MASTER PROMPT

## Purpose
Build, integrate, validate, secure, containerize, deploy, and demo the AI Talent Matching & Skill Gap Engine under a 15-hour hackathon constraint.

This master prompt is the final system-level engineering instruction after the Database, Backend, Python AI/NLP, and Frontend workstreams. It is designed to make five independently developed components behave as one reliable product.

Core product flow:

```text
Resume PDF/DOCX
      ↓
Frontend Upload
      ↓
Node.js Backend API
      ↓
Python AI/NLP Service
      ↓
Text Extraction
      ↓
Skill Extraction + Normalization
      ↓
Candidate Profile
      ↓
Embeddings + Semantic Matching
      ↓
Job Matching + Explainability
      ↓
Skill Gap Analysis
      ↓
Career Roadmap
      ↓
What-If Skill Simulation
      ↓
Frontend Dashboard
```

Primary principle:

> Integrate by stable contracts, not by directly coupling implementation details.


# 1. SYSTEM OBJECTIVE

The finished application must demonstrate one complete user journey:

1. User opens the application.
2. User uploads a PDF/DOCX resume.
3. Frontend validates the file.
4. Backend receives and stores the upload safely.
5. Backend calls the Python AI service.
6. AI service extracts text and structured candidate information.
7. Skills are normalized against the project skill knowledge base.
8. Candidate profile is returned.
9. Matching engine compares candidate profile with available jobs.
10. The UI displays ranked jobs and match scores.
11. User opens a job.
12. UI explains why the candidate matches.
13. Missing skills are identified.
14. A personalized career roadmap is generated.
15. User changes a hypothetical skill in the simulator.
16. The system recalculates the projected match.
17. The result is visible in a polished dashboard.

The demo must never depend on manually editing database records during presentation.


# 2. NON-NEGOTIABLE ARCHITECTURE

Use this architecture:

```text
                         ┌──────────────────────┐
                         │       USER           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ React + TypeScript   │
                         │ Tailwind + Charts    │
                         └──────────┬───────────┘
                                    │ HTTPS/JSON
                                    ▼
                         ┌──────────────────────┐
                         │ Node.js + Express    │
                         │ API Gateway          │
                         └───────┬───────┬──────┘
                                 │       │
                         REST/API │       │ DB
                                 ▼       ▼
                    ┌────────────────┐  ┌──────────────┐
                    │ Python FastAPI │  │ PostgreSQL   │
                    │ AI/NLP Engine  │  │ + Prisma     │
                    └───────┬────────┘  └──────────────┘
                            │
              ┌─────────────┼────────────────┐
              ▼             ▼                ▼
        Resume Parser   Skill Engine    Embeddings
        PDF/DOCX        Normalize       Similarity
              │             │                │
              └─────────────┼────────────────┘
                            ▼
                    Matching Engine
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
           Skill Gap Engine      Career Engine
                 │                     │
                 └──────────┬──────────┘
                            ▼
                     JSON Response
                            │
                            ▼
                       Dashboard
```

Rules:
- Frontend never talks directly to PostgreSQL.
- Frontend normally talks only to Node backend.
- Node backend is the public API boundary.
- Python AI service is internal/private where possible.
- Database credentials never reach frontend.
- Secrets never enter Git.
- API response contracts must remain stable.


# 3. MONOREPO CONTRACT

Required repository:

```text
skillgap-ai/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── backend/
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── .env.example
├── ai-service/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── database/
│   ├── prisma/
│   │   ├── schema.prisma
│   │   └── seed.ts
│   └── seeds/
├── data/
│   ├── skills.json
│   ├── aliases.json
│   ├── jobs.json
│   └── career_paths.json
├── uploads/
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── testing.md
│   └── deployment.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

No generated secrets, uploaded resumes, database files, node_modules, Python virtual environments, or build output should be committed.


# 4. ENVIRONMENT CONTRACT

Define environment variables centrally and document them.

Example:

```env
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://USER:PASSWORD@postgres:5432/skillgap
AI_SERVICE_URL=http://ai-service:8000
FRONTEND_URL=http://localhost:5173
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=5

AI_MODEL_NAME=all-MiniLM-L6-v2
LOG_LEVEL=info
CORS_ORIGIN=http://localhost:5173
```

Rules:
- `.env` is local only.
- `.env.example` contains placeholders.
- Never hardcode passwords, API keys, tokens, or credentials.
- Validate environment variables at startup.
- Fail fast when a required production variable is missing.
- Never print secrets in logs.


# 5. API CONTRACT

All public APIs must have predictable JSON.

Success:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": []
  },
  "requestId": "..."
}
```

Recommended endpoints:

```text
POST /api/resume/upload
POST /api/resume/analyze
GET  /api/profile
GET  /api/jobs
GET  /api/jobs/:id
POST /api/match
GET  /api/matches
GET  /api/skill-gaps/:jobId
GET  /api/roadmap/:jobId
POST /api/simulate
GET  /api/health
GET  /api/ready
```

Every endpoint must define:
- method
- URL
- request body
- query parameters
- authentication requirement
- validation
- success response
- error responses
- status codes
- example request
- example response


# 6. END-TO-END RESUME CONTRACT

Request:

```text
multipart/form-data
file=<resume.pdf>
```

Backend processing:

```text
Upload
 ↓
Validate extension
 ↓
Validate MIME type
 ↓
Validate size
 ↓
Generate safe internal filename
 ↓
Store temporarily
 ↓
Call AI service
 ↓
Receive structured profile
 ↓
Persist profile
 ↓
Run matching
 ↓
Return result
```

AI response must be structured, not free-form prose:

```json
{
  "candidate": {
    "name": "",
    "email": "",
    "phone": "",
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": []
  },
  "skills": [
    {
      "name": "Python",
      "normalizedName": "python",
      "category": "programming",
      "confidence": 0.96,
      "evidence": "Python development"
    }
  ],
  "metadata": {
    "parserVersion": "1.0.0",
    "modelVersion": "1.0.0"
  }
}
```

Do not let downstream systems depend on raw parser text.


# 7. SERVICE-TO-SERVICE INTEGRATION

Node → Python request:

```text
POST /internal/analyze-resume
Content-Type: multipart/form-data
```

Python → Node response:

```text
HTTP 200
structured JSON
```

Rules:
- Set connection timeout.
- Set response timeout.
- Retry only safe/idempotent operations.
- Do not retry indefinitely.
- Return a controlled error if AI is unavailable.
- Include request/correlation ID.
- Log latency without logging resume contents.
- Version internal contracts if breaking changes occur.

Failure behavior:

```text
AI unavailable
    ↓
Backend catches timeout
    ↓
Structured error
    ↓
Frontend shows:
"Resume analysis is temporarily unavailable."
    ↓
Retry button
```


# 8. DATABASE INTEGRATION CHECK

Required logical entities:

```text
users
resumes
candidate_profiles
skills
candidate_skills
jobs
job_skills
matches
skill_gaps
career_paths
```

Verify:
- primary keys
- foreign keys
- unique constraints
- indexes
- timestamps
- cascade behavior
- ownership rules
- decimal/score precision
- transaction boundaries

Critical indexes should cover common lookup paths such as:
- user → resumes
- candidate → skills
- job → skills
- candidate/job match
- normalized skill name


# 9. MATCHING CONTRACT

Recommended hybrid score:

```text
Final Score =
0.50 × Semantic Similarity
+ 0.30 × Skill Match
+ 0.10 × Experience Match
+ 0.10 × Education/Certification Match
```

Normalize all components to 0–1 before combining.

Example:

```text
Semantic similarity = 0.82
Skill match         = 0.75
Experience match    = 0.90
Education match     = 0.80

Final =
0.50(0.82) +
0.30(0.75) +
0.10(0.90) +
0.10(0.80)
= 0.815
= 81.5%
```

The UI must show the score as an explainable result, not as an unexplained AI number.


# 10. EXPLAINABILITY CONTRACT

For every match, expose:

```json
{
  "score": 81.5,
  "matchedSkills": ["Python", "SQL", "Machine Learning"],
  "missingSkills": ["Docker", "Kubernetes"],
  "strengths": [
    "Strong Python experience",
    "Relevant machine-learning projects"
  ],
  "gaps": [
    "Docker is required by the target role"
  ]
}
```

Never claim that a score proves employability.

Use language such as:
- "Strong match"
- "Based on the supplied resume"
- "Potential skill gap"
- "Recommended next skill"


# 11. WHAT-IF SIMULATOR

The simulator is a high-value hackathon feature.

Flow:

```text
Current Profile
      ↓
Select hypothetical skill
      ↓
Temporary skill set
      ↓
Recalculate matching
      ↓
Compare old vs projected score
      ↓
Show impact
```

Example:

```text
Current match: 72%
Add Docker
Projected match: 79%
Improvement: +7%
```

Rules:
- Simulation must not permanently modify the candidate profile.
- Use a clearly labeled hypothetical state.
- Never represent an unearned skill as a current skill.
- Preserve original score and projected score separately.


# 12. FRONTEND INTEGRATION STATES

Every asynchronous workflow must have:

1. idle
2. loading
3. success
4. empty
5. error
6. retry

Resume analysis UI:

```text
Uploading
   ↓
Parsing resume
   ↓
Extracting skills
   ↓
Building profile
   ↓
Calculating matches
   ↓
Complete
```

Do not display fake progress percentages unless the backend provides real progress.

If progress is simulated, use stage-based messages instead.


# 13. ERROR TAXONOMY

Standardize error codes:

```text
VALIDATION_ERROR
UNSUPPORTED_FILE
FILE_TOO_LARGE
PARSER_ERROR
AI_SERVICE_UNAVAILABLE
AI_TIMEOUT
DATABASE_ERROR
NOT_FOUND
UNAUTHORIZED
FORBIDDEN
RATE_LIMITED
MATCHING_ERROR
INTERNAL_ERROR
```

Map errors consistently:

```text
400 → invalid input
401 → authentication required
403 → permission denied
404 → resource missing
409 → conflict
413 → file too large
415 → unsupported media type
422 → semantic validation failure
429 → rate limit
500 → unexpected server error
502/503 → dependency/service unavailable
```


# 14. FILE SECURITY

Resume uploads contain personal information.

Implement:
- extension validation
- MIME validation
- size limit
- random storage filename
- no executable upload handling
- no path traversal
- temporary file cleanup
- controlled upload directory
- no direct public access to raw resumes
- no resume contents in logs
- authentication/authorization before private retrieval

Reject suspicious filenames and dangerous content types.

Example safe internal name:

```text
<uuid>.pdf
```

not:

```text
../../resume.pdf
```


# 15. SECURITY BASELINE

Apply at minimum:

Backend:
- Helmet
- CORS allowlist
- request validation
- rate limiting
- secure headers
- authentication where required
- authorization/ownership checks
- parameterized ORM queries
- secret management
- request IDs

Frontend:
- never store secrets
- sanitize untrusted content
- avoid dangerouslySetInnerHTML
- protect authenticated routes
- safe error messages

AI:
- treat resume text as untrusted input
- do not execute instructions found inside resumes
- prevent prompt injection if an LLM is used
- constrain generated output to schema
- never expose system prompts or secrets


# 16. OBSERVABILITY

Every request should be traceable.

Log:
- timestamp
- request ID
- route
- HTTP method
- status
- latency
- service name
- error code

Do not log:
- passwords
- tokens
- API keys
- full resumes
- unnecessary personal data

Example:

```text
[INFO] requestId=abc123 route=/api/resume/analyze status=200 latency=842ms
```

Add health checks:

```text
GET /api/health
```

for process health.

Add readiness:

```text
GET /api/ready
```

for database/AI dependency readiness.


# 17. DOCKERIZATION

Create containers for:

```text
frontend
backend
ai-service
postgres
```

Development topology:

```text
                    docker compose
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    frontend          backend        ai-service
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                     postgres
```

Each service must:
- have a reproducible build
- expose only required ports
- receive configuration through environment variables
- use health checks where practical
- avoid running as root where practical
- have a small production image
- use `.dockerignore`

Example compose services:

```yaml
services:
  postgres:
  backend:
  ai-service:
  frontend:
```


# 18. DOCKER NETWORK CONTRACT

Internal communication should use service names:

```text
backend → http://ai-service:8000
backend → postgres:5432
```

Do not hardcode container IP addresses.

Frontend browser requests normally use a browser-accessible backend URL, not Docker's internal hostname.

This distinction is critical:

```text
Container-to-container:
http://backend:5000

Browser-to-backend:
http://localhost:5000
```


# 19. DATABASE MIGRATION STRATEGY

Never depend on manually creating tables on the judge's machine.

Required flow:

```text
Install dependencies
      ↓
Environment configured
      ↓
Prisma migration
      ↓
Database seed
      ↓
Start services
      ↓
Health checks
```

Seed deterministic demo data:
- representative skills
- aliases
- jobs
- job requirements
- career paths

The seed must be safe to rerun or clearly documented as reset-only.


# 20. CI CHECKS

Before merging, run:

```text
Frontend:
npm ci
npm run build
npm test

Backend:
npm ci
npm test
npm run build

AI:
pip install -r requirements.txt
pytest

Database:
prisma validate
prisma generate
migration validation
seed validation
```

Then run an integration smoke test.

CI should fail on:
- compilation errors
- type errors
- failing tests
- malformed schema
- missing required environment configuration
- broken API contract


# 21. CONTRACT TESTING

Test the boundaries, not only individual functions.

Required contract checks:

```text
Frontend → Backend
Backend → AI
Backend → Database
Backend → Matching
Matching → Frontend
```

Verify:
- property names
- data types
- nullable fields
- score ranges
- enum values
- error format
- HTTP status
- pagination shape
- IDs

A backend change is incomplete if it breaks the frontend contract.


# 22. INTEGRATION TEST MATRIX

### Critical path

| Test | Expected |
|---|---|
| Upload valid PDF | 200/201 |
| Upload valid DOCX | 200/201 |
| Upload invalid extension | 400/415 |
| Upload oversized file | 413 |
| AI extraction | structured profile |
| Skill normalization | canonical skills |
| Candidate persistence | database record |
| Job retrieval | seeded jobs |
| Matching | ranked results |
| Explainability | matched + missing skills |
| Skill gap | actionable gaps |
| Roadmap | ordered recommendations |
| Simulation | projected score only |
| AI timeout | controlled 503/502 |
| DB unavailable | controlled failure |
| Frontend retry | request repeated safely |


# 23. E2E SMOKE TEST

The single most important automated/manual test:

```text
Open app
 ↓
Upload demo resume
 ↓
Wait for analysis
 ↓
Candidate profile appears
 ↓
Skills appear
 ↓
Top jobs appear
 ↓
Open one job
 ↓
Match score appears
 ↓
Why-this-match section appears
 ↓
Skill gaps appear
 ↓
Roadmap appears
 ↓
Add hypothetical skill
 ↓
Projected score changes
```

If this flow fails, stop adding features and fix integration.


# 24. PERFORMANCE TARGETS

For the hackathon demo, optimize for perceived responsiveness and reliability.

Targets:
- frontend initial load: reasonable on local network
- API responses: fast for seeded data
- resume analysis: preferably under several seconds for normal resumes
- matching: near-instant after profile generation
- simulator: near-instant
- no blocking database queries
- no repeated embedding computation when cached

Do not prematurely optimize complex distributed systems.


# 25. CACHING

Useful cache candidates:
- normalized skill taxonomy
- job embeddings
- career-path data
- frequently requested job lists

Do not cache:
- sensitive responses without a clear strategy
- stale personalized results without invalidation
- temporary simulation state as permanent user data

For 15 hours, an in-memory cache is acceptable for static demo knowledge if documented.


# 26. AI MODEL VERSIONING

Record model metadata:

```json
{
  "embeddingModel": "all-MiniLM-L6-v2",
  "parserVersion": "1.0.0",
  "matchingVersion": "1.0.0"
}
```

This makes results explainable and reproducible.

If model configuration changes, increment the relevant version.


# 27. RAG POSITIONING

RAG is optional for this MVP.

Core system:

```text
Resume
 ↓
Skills
 ↓
Embeddings
 ↓
Semantic similarity
 ↓
Match
```

Optional RAG layer:

```text
Candidate context
      +
Target role
      ↓
Retrieve relevant occupational/skill knowledge
      ↓
LLM
      ↓
Grounded career recommendation
```

Do not introduce RAG merely because it is fashionable.

If implemented, restrict retrieval to trusted project knowledge:
- skill definitions
- role requirements
- career paths
- learning resources

The core matching engine must continue working if the RAG layer is unavailable.


# 28. TEST DATA STRATEGY

Create at least:
- 3 demo resumes
- 20–50 representative jobs
- 50–100 normalized skills
- aliases for common skills
- several career paths

Demo resumes should represent:
1. strong match
2. partial match with obvious gaps
3. career-transition candidate

Do not use real people's personal resumes without permission.


# 29. DEMO RESUME REQUIREMENTS

The primary demo resume should intentionally contain:

```text
Programming:
Python, JavaScript, C++

Data:
SQL, PostgreSQL

AI:
Machine Learning, NLP

Tools:
Git, Docker

Projects:
2–3 relevant projects

Education:
B.E./B.Tech CSE
```

This ensures the extraction, matching, gap analysis, and roadmap features visibly activate.


# 30. GIT WORKFLOW

Use small, meaningful commits.

Recommended branches:

```text
main
integration
feature/database
feature/backend
feature/ai
feature/frontend
feature/integration
```

Commit examples:

```text
feat(db): add job and skill seed data
feat(api): add resume upload endpoint
feat(ai): add normalized skill extraction
feat(ui): add match dashboard
feat(integration): connect resume analysis pipeline
test(e2e): add resume-to-match smoke test
fix(api): handle AI timeout
```

Rules:
- pull/rebase before integration
- resolve conflicts deliberately
- never force-push shared branches unless the team explicitly agrees
- never commit secrets


# 31. MERGE GATE

A feature is mergeable only when:

```text
Code compiles
AND
Tests pass
AND
API contract is documented
AND
No secret is committed
AND
No critical console/server error exists
AND
Integration impact is understood
```

Do not merge broken work merely because the deadline is close.


# 32. 15-HOUR EXECUTION PLAN

### Hour 0–1 — Integration contract
- freeze architecture
- freeze endpoints
- freeze database entities
- create repo structure
- create `.env.example`
- assign ownership
- create demo resume

### Hour 1–4 — Parallel implementation
- DB + seeds
- backend APIs
- frontend mock UI
- parser/NLP
- embeddings/matching

### Hour 4 — Integration checkpoint
Must have:
- services start
- database connects
- API responds
- AI endpoint responds
- frontend loads

### Hour 4–7 — Core integration
Connect:

```text
Frontend
 → Backend
 → AI
 → Database
 → Backend
 → Frontend
```

### Hour 7 — Critical demo checkpoint
Must work:

```text
Upload → Analyze → Profile
```

### Hour 7–10 — Intelligence
Implement:
- matching
- score
- explainability
- gaps
- roadmap

### Hour 10 — Feature freeze
Only bug fixes and high-value polish.

### Hour 10–12 — WOW
- what-if simulator
- polished score visualization
- explainable cards
- loading stages

### Hour 12–13 — QA
- E2E
- invalid files
- AI failure
- DB failure
- empty states
- mobile/responsive check

### Hour 13–14 — Deployment + presentation
- Docker
- environment
- README
- architecture slide
- demo script

### Hour 14–15 — Freeze
- no new features
- final test
- backup
- rehearse
- prepare fallback demo


# 33. P0 / P1 / P2 PRIORITY

### P0 — Must work

```text
Resume upload
Resume parsing
Skill extraction
Skill normalization
Candidate profile
Job matching
Match score
Skill gap
Career roadmap
Database persistence
Frontend integration
```

### P1 — Strong differentiators

```text
Explainable matching
What-if simulator
Charts
Authentication
Docker
Robust error states
```

### P2 — Only if time remains

```text
RAG
OCR
Multimodal resume analysis
Live job scraping
Advanced recruiter analytics
Complex recommendation models
Real-time external integrations
```

Never sacrifice P0 for P2.


# 34. FALLBACK STRATEGY

If the AI service fails during judging:

```text
Primary:
Live AI analysis

Fallback:
Precomputed demo analysis stored in controlled seed/demo data
```

The fallback must be clearly a demo resilience mechanism, not falsely presented as a live AI result.

If database fails:
- show a controlled error
- use only preloaded client demo data if necessary

If external services fail:
- core local pipeline must still demonstrate the product.


# 35. FRONTEND QA CHECKLIST

Check:
- no broken routes
- no blank screens
- no console errors
- upload button works
- drag/drop works if implemented
- loading state visible
- error state readable
- score visualization correct
- percentages are mathematically consistent
- skill chips do not overflow
- long job titles wrap
- charts are readable
- responsive layout works
- keyboard navigation works
- contrast is adequate
- buttons have disabled states
- retry buttons actually retry


# 36. BACKEND QA CHECKLIST

Check:
- startup configuration validation
- health endpoint
- readiness endpoint
- request validation
- correct status codes
- centralized error handler
- request IDs
- upload limits
- MIME checks
- safe filenames
- AI timeout
- AI failure handling
- database transaction boundaries
- authorization
- no secret leakage
- no stack traces in production responses


# 37. AI QA CHECKLIST

Check:
- PDF parsing
- DOCX parsing
- malformed document handling
- empty resume handling
- section detection
- duplicate skills
- aliases
- capitalization
- skill normalization
- false-positive control
- evidence extraction
- confidence scoring
- deterministic output where possible
- embedding generation
- score range 0–100
- missing-skill detection
- recommendation ordering


# 38. DATABASE QA CHECKLIST

Check:
- migration succeeds
- seed succeeds
- seed rerun behavior documented
- foreign keys valid
- duplicate prevention
- indexes exist
- required fields enforced
- timestamps correct
- ownership constraints
- transactions rollback correctly
- no orphan records


# 39. SECURITY QA CHECKLIST

Run a final security pass for:
- exposed secrets
- `.env` files
- Git history
- hardcoded tokens
- unrestricted CORS
- unrestricted upload types
- oversized uploads
- path traversal
- SQL injection
- XSS
- insecure direct object references
- missing authorization
- verbose production errors
- leaked resume data in logs


# 40. RELEASE CHECKLIST

Before declaring the project finished:

```text
[ ] frontend build passes
[ ] backend build passes
[ ] AI tests pass
[ ] database migration passes
[ ] database seed passes
[ ] docker compose starts
[ ] health endpoint passes
[ ] readiness endpoint passes
[ ] resume upload works
[ ] PDF works
[ ] DOCX works
[ ] skill extraction works
[ ] matching works
[ ] explainability works
[ ] skill gaps work
[ ] roadmap works
[ ] simulator works
[ ] invalid upload handled
[ ] AI failure handled
[ ] DB failure handled
[ ] no secrets committed
[ ] README complete
[ ] demo resume ready
[ ] backup ready
```


# 41. JUDGE DEMO SCRIPT

Use a 3–5 minute demo.

### 0:00–0:30 — Problem
"Resumes are unstructured, job requirements use inconsistent terminology, and candidates often do not know which skills they are missing."

### 0:30–1:00 — Upload
Upload resume.

### 1:00–1:40 — AI understanding
Show:
- extracted candidate profile
- normalized skills
- evidence

### 1:40–2:20 — Matching
Show:
- ranked roles
- match percentage
- matched skills

### 2:20–3:00 — Explainability
Open one role:
- why matched
- missing skills
- evidence

### 3:00–3:40 — Career growth
Show:
- skill gaps
- roadmap

### 3:40–4:20 — WOW
Use what-if simulator:
"Suppose this candidate learns Docker."

Show projected score improvement.

### 4:20–5:00 — Architecture
Briefly explain:
React → Node → Python AI → PostgreSQL → matching engine.


# 42. JUDGE QUESTIONS

### Why use a separate Python AI service?
Because NLP and embedding libraries have a strong Python ecosystem, while Node provides a clean application/API layer.

### Why PostgreSQL?
Structured relational data such as candidates, jobs, skills, and matches requires consistency and relationships.

### Why embeddings?
They capture semantic similarity beyond exact keyword matching.

### Why not keyword matching only?
"JS", "JavaScript", and related descriptions can vary. Semantic representations help compare meaning.

### Why normalize skills?
Different spellings and aliases should map to a canonical skill.

### Why explain the score?
A recommendation system should provide evidence and visible reasons rather than an unexplained number.

### Is RAG required?
No. Core matching uses extraction, normalization, embeddings, and similarity. RAG can optionally ground career recommendations.

### How do you handle fairness?
Use explainable signals, avoid protected attributes, validate data quality, and present scores as decision support rather than absolute hiring decisions.

### Can it scale?
Services can be independently scaled; embeddings and static job representations can be cached; asynchronous processing can be introduced later.

### What happens if AI is down?
The backend returns a controlled dependency error and the demo has a prepared fallback.


# 43. FINAL ACCEPTANCE TEST

The project is accepted only if a new machine can follow the README and reach:

```text
docker compose up
      ↓
database ready
      ↓
services healthy
      ↓
frontend opens
      ↓
demo resume uploads
      ↓
AI analysis completes
      ↓
candidate profile appears
      ↓
jobs are ranked
      ↓
match explanation appears
      ↓
skill gaps appear
      ↓
roadmap appears
      ↓
what-if simulation works
```

No undocumented manual database edits should be required.


# 44. FINAL CODE-REVIEW MASTER PROMPT

Act as a Principal Engineer performing the final production-readiness review of this hackathon system.

Review the complete repository as one product.

Inspect:
- architecture
- frontend
- backend
- Python AI service
- PostgreSQL/Prisma
- API contracts
- Docker
- environment configuration
- tests
- security
- observability
- performance
- error handling
- integration boundaries
- README
- demo flow

Do not merely list files.

For every finding classify:
- P0 blocker
- P1 high
- P2 medium
- P3 low

For each finding provide:
1. exact problem
2. why it matters
3. affected component
4. reproduction
5. recommended fix
6. smallest safe fix
7. verification command/test

Then verify this exact critical path:

```text
Resume upload
→ Backend
→ Python parser
→ Skill extraction
→ Skill normalization
→ Candidate profile
→ Embeddings
→ Job matching
→ Explainability
→ Skill gaps
→ Career roadmap
→ What-if simulation
→ Frontend
```

Finally produce:
- release verdict
- blockers
- top 10 fixes
- test summary
- security summary
- deployment summary
- judge-demo readiness
- exact commands to start the system
- exact commands to run the final test suite


# 45. TEAM OWNERSHIP

### Ankit — Database/Data
Own:
- Prisma schema
- migrations
- seeds
- indexes
- data quality

### Adil — Backend
Own:
- Express API
- validation
- upload
- auth
- AI communication
- database API integration

### Kanishaka — Frontend
Own:
- pages
- components
- dashboard
- upload UX
- matching UI
- roadmap
- simulator

### Mayank — AI/NLP
Own:
- PDF/DOCX extraction
- preprocessing
- skill extraction
- normalization
- candidate profile

### Rohit — Integration/Matching
Own:
- embeddings
- matching
- explainability
- skill-gap logic
- integration
- Docker/deployment
- final demo

Everyone must help with integration and QA during the final hours.


# 46. GOLDEN RULES

1. **Contracts before integration.**
2. **P0 before P1, P1 before P2.**
3. **Never commit secrets.**
4. **Never expose database credentials to the frontend.**
5. **Never trust uploaded documents.**
6. **Never present hypothetical skills as real skills.**
7. **Never make AI scores look more certain than they are.**
8. **Never add RAG just to claim RAG.**
9. **Never add live scraping if it destabilizes the MVP.**
10. **At hour 10, freeze features.**
11. **The complete demo path matters more than isolated feature count.**
12. **A boring reliable system beats five broken AI features.**


# INTEGRATION AUDIT

- [ ] Verify every producer and consumer agrees on field names, types, nullability, units, score ranges, and error formats.
- [ ] Verify IDs are generated once and reused rather than silently recreated across services.
- [ ] Verify timestamps use one documented convention and are serialized consistently.
- [ ] Verify frontend loading states correspond to actual backend operations.
- [ ] Verify retry behavior cannot create duplicate records.

# FAILURE INJECTION AUDIT

- [ ] Temporarily stop PostgreSQL and verify the backend returns a controlled readiness/dependency error.
- [ ] Temporarily stop the AI service and verify resume analysis fails gracefully with retry guidance.
- [ ] Upload an invalid file and verify validation happens before expensive AI work.
- [ ] Send an empty profile to matching and verify the API returns a useful validation response.
- [ ] Return malformed AI JSON in a test and verify backend schema validation rejects it safely.

# DATA QUALITY AUDIT

- [ ] Verify duplicate skills collapse into canonical skills.
- [ ] Verify aliases map to the same normalized skill.
- [ ] Verify unknown skills are preserved as unresolved evidence instead of silently disappearing.
- [ ] Verify missing fields do not become fabricated facts.
- [ ] Verify confidence and proficiency are not treated as the same concept.

# DEMO AUDIT

- [ ] Run the entire demo from a clean browser session.
- [ ] Use the exact demo resume that the team has tested.
- [ ] Do not rely on hidden manual edits between demo steps.
- [ ] Keep a local fallback copy of the seeded data.
- [ ] Rehearse every click and know the expected result before judging.

# FINAL SYSTEM CHECK 01

Run integration check 01 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 02

Run integration check 02 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 03

Run integration check 03 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 04

Run integration check 04 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 05

Run integration check 05 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 06

Run integration check 06 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 07

Run integration check 07 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 08

Run integration check 08 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 09

Run integration check 09 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 10

Run integration check 10 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 11

Run integration check 11 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 12

Run integration check 12 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 13

Run integration check 13 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 14

Run integration check 14 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 15

Run integration check 15 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 16

Run integration check 16 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 17

Run integration check 17 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 18

Run integration check 18 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 19

Run integration check 19 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 20

Run integration check 20 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 21

Run integration check 21 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 22

Run integration check 22 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 23

Run integration check 23 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 24

Run integration check 24 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 25

Run integration check 25 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 26

Run integration check 26 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 27

Run integration check 27 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 28

Run integration check 28 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 29

Run integration check 29 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# FINAL SYSTEM CHECK 30

Run integration check 30 against the complete system.

Required evidence:
- the responsible service is running;
- its contract is documented;
- its happy path is tested;
- at least one failure path is tested;
- logs do not expose secrets or unnecessary PII;
- the result is compatible with the next service;
- the user-visible behavior is understandable.

Record the result as:
`PASS / FAIL / BLOCKED`, with the exact command, endpoint, or manual action used.

Do not mark a check PASS based only on code inspection when runtime verification is practical.

# APPENDIX — FINAL TEAM INSTRUCTION

Use this README as the system integration contract. Do not blindly implement every optional capability. Under the 15-hour constraint, prioritize the working end-to-end path:

**Upload → AI Understand → Profile → Match → Explain → Skill Gap → Roadmap → What-If**

The final submission should feel like one product, not five separate student projects.
