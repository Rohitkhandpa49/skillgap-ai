# API Contract --- SkillGap AI

## Purpose

This document freezes the API contracts between the React frontend,
Node.js/Express backend, Python FastAPI AI service, and
PostgreSQL/Prisma layer so the five team members can work in parallel.

## Architecture

``` text
React Frontend
      |
      | REST/JSON + multipart/form-data
      v
Node.js + Express Backend
      |
      +---- Prisma ----> PostgreSQL
      |
      | HTTP/JSON
      v
Python FastAPI AI Service
      |
      +-- Resume Parser
      +-- Skill Extraction
      +-- Skill Normalization
      +-- Embeddings
      +-- Matching
      +-- Skill Gap
      +-- Career Roadmap
```

## Base URLs

``` text
Frontend:  http://localhost:5173
Backend:   http://localhost:5000
AI:        http://localhost:8000
Postgres:  localhost:5432
```

Use environment variables; never hard-code secrets.

## API Conventions

-   JSON endpoints use `Content-Type: application/json`.
-   Resume upload uses `multipart/form-data`.
-   API fields use camelCase.
-   IDs are strings.
-   Dates use ISO 8601.
-   Resume uploads are limited to PDF/DOCX and a configurable maximum
    size (recommended 10 MB).

## Standard Success Response

``` json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

## Standard Error Response

``` json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": []
  }
}
```

## HTTP Status Codes

  Status   Meaning
  -------- --------------------------------
  200      Successful request
  201      Resource created
  400      Invalid request
  401      Authentication required/failed
  403      Forbidden
  404      Resource not found
  409      Conflict
  413      File/request too large
  422      Validation failure
  429      Rate limit exceeded
  500      Internal server error
  502      AI/upstream failure
  503      Service unavailable

# Public API

## POST `/api/v1/resume/upload`

Uploads a PDF/DOCX resume.

Form field:

``` text
file
```

Response:

``` json
{
  "success": true,
  "data": {
    "resumeId": "resume_001",
    "filename": "resume.pdf",
    "status": "uploaded"
  },
  "message": "Resume uploaded successfully"
}
```

The backend must validate extension, MIME type, size, filename, and safe
storage path.

## POST `/api/v1/resume/analyze`

Request:

``` json
{
  "resumeId": "resume_001"
}
```

Example response:

``` json
{
  "success": true,
  "data": {
    "resumeId": "resume_001",
    "profile": {
      "skills": [
        {
          "name": "React.js",
          "normalizedName": "React",
          "confidence": 0.94
        }
      ],
      "experience": [],
      "education": [],
      "certifications": [],
      "projects": []
    }
  }
}
```

## GET `/api/v1/profile`

Returns the current candidate profile.

``` json
{
  "success": true,
  "data": {
    "candidateId": "cand_001",
    "name": "Candidate Name",
    "skills": [
      {
        "name": "Python",
        "level": "intermediate"
      }
    ],
    "experience": [],
    "education": [],
    "certifications": [],
    "projects": []
  }
}
```

## GET `/api/v1/jobs`

Optional query parameters:

``` text
?page=1&limit=20&search=machine%20learning
```

Response:

``` json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "jobId": "job_001",
        "title": "Machine Learning Engineer",
        "company": "Example Company",
        "requiredSkills": ["Python", "Machine Learning", "Pandas"],
        "optionalSkills": ["PyTorch", "Docker"]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50
    }
  }
}
```

## GET `/api/v1/jobs/recommended`

Optional query:

``` text
?candidateId=cand_001&limit=10
```

Response:

``` json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "jobId": "job_001",
        "title": "Machine Learning Engineer",
        "matchScore": 85
      }
    ]
  }
}
```

## POST `/api/v1/match`

Request:

``` json
{
  "candidateId": "cand_001",
  "jobId": "job_001"
}
```

Response:

``` json
{
  "success": true,
  "data": {
    "candidateId": "cand_001",
    "jobId": "job_001",
    "matchScore": 85,
    "breakdown": {
      "semanticSimilarity": 82,
      "skillMatch": 90,
      "experienceMatch": 70,
      "educationMatch": 100
    },
    "matchedSkills": ["Python", "Pandas", "Machine Learning"],
    "missingSkills": ["PyTorch", "Docker"]
  }
}
```

MVP scoring:

``` text
50% Semantic Similarity
30% Skill Match
10% Experience
10% Education/Certification
```

## GET `/api/v1/skill-gaps`

Query:

``` text
?candidateId=cand_001&jobId=job_001
```

Response:

``` json
{
  "success": true,
  "data": {
    "candidateId": "cand_001",
    "jobId": "job_001",
    "matchedSkills": ["Python", "Pandas"],
    "missingSkills": [
      {
        "skill": "PyTorch",
        "priority": "high"
      },
      {
        "skill": "Docker",
        "priority": "medium"
      }
    ],
    "gapScore": 30
  }
}
```

## GET `/api/v1/roadmap`

Query:

``` text
?candidateId=cand_001&jobId=job_001
```

Response:

``` json
{
  "success": true,
  "data": {
    "targetRole": "Machine Learning Engineer",
    "currentLevel": "beginner",
    "steps": [
      {
        "order": 1,
        "skill": "Python",
        "status": "completed"
      },
      {
        "order": 2,
        "skill": "Machine Learning",
        "status": "completed"
      },
      {
        "order": 3,
        "skill": "PyTorch",
        "status": "recommended"
      }
    ]
  }
}
```

## POST `/api/v1/simulate`

Request:

``` json
{
  "candidateId": "cand_001",
  "jobId": "job_001",
  "additionalSkills": ["PyTorch", "Docker"]
}
```

Response:

``` json
{
  "success": true,
  "data": {
    "currentMatchScore": 72,
    "simulatedMatchScore": 84,
    "scoreImprovement": 12,
    "newlyMatchedSkills": ["PyTorch", "Docker"],
    "newlyEligibleJobs": 17
  }
}
```

The simulator must not permanently modify the candidate profile.

# Internal AI Service API

The Node backend communicates with FastAPI through internal endpoints:

``` text
POST /internal/parse-resume
POST /internal/extract-skills
POST /internal/normalize-skills
POST /internal/embed
POST /internal/match
POST /internal/skill-gap
POST /internal/roadmap
GET  /health
```

These endpoints should not be directly exposed to public clients.

## Health

Backend:

``` http
GET /health
```

``` json
{
  "status": "ok",
  "service": "backend"
}
```

AI service:

``` http
GET /health
```

``` json
{
  "status": "ok",
  "service": "ai-service"
}
```

# Error Codes

Recommended codes:

``` text
VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
RESUME_NOT_FOUND
INVALID_FILE_TYPE
FILE_TOO_LARGE
RESUME_PARSE_FAILED
AI_SERVICE_UNAVAILABLE
SKILL_EXTRACTION_FAILED
JOB_NOT_FOUND
MATCH_FAILED
SKILL_GAP_FAILED
ROADMAP_GENERATION_FAILED
INTERNAL_SERVER_ERROR
```

Never expose stack traces, credentials, database passwords, or internal
filesystem paths to clients.

# Security Contract

The upload service must:

-   Accept only allowed document formats.
-   Enforce file-size limits.
-   Sanitize filenames.
-   Generate safe internal filenames.
-   Prevent path traversal.
-   Store uploads outside publicly served directories.
-   Never log resume contents.
-   Never commit uploaded resumes to Git.

The frontend must never connect directly to PostgreSQL or the AI
service.

Correct flow:

``` text
React
  ↓
Node Backend
  ↓
AI Service / PostgreSQL
```

# Timeout and Retry

Backend-to-AI requests must use configurable timeouts and limited
retries.

Do not retry indefinitely. Non-idempotent operations must be protected
against duplicate processing.

# API Versioning

The preferred production form is:

``` text
/api/v1/...
```

The team may temporarily use `/api/...` during early development, but
the final implementation should use versioned endpoints.

# Ownership

  Contract Area            Primary Owner   Reviewer
  ------------------------ --------------- ---------------
  Public API               Adil            Rohit
  AI internal API          Mayank          Adil + Rohit
  Database schema          Ankit           Adil
  Frontend API client      Kanishaka       Adil
  Matching response        Rohit           Mayank + Adil
  Skill-gap response       Rohit           Mayank
  Roadmap response         Rohit           Mayank
  Integration validation   Rohit           All

# Contract Freeze Rule

At the end of Hour 0--1:

``` text
API CONTRACT FREEZE
        ↓
Parallel development
        ↓
Any breaking change requires team agreement
        ↓
Update this document
        ↓
Update affected services
        ↓
Run integration tests
```

Do not silently rename or remove response fields while another team
member depends on them.

# End-to-End Flow

``` text
USER
  |
  | Resume PDF/DOCX
  v
FRONTEND
  |
  | POST /api/v1/resume/upload
  v
BACKEND
  |
  | internal AI request
  v
AI SERVICE
  |
  | Extract + Normalize
  v
BACKEND
  |
  | Store candidate profile
  v
DATABASE
  |
  | Candidate + Jobs
  v
MATCHING ENGINE
  |
  | Match score + explanation
  v
SKILL GAP ENGINE
  |
  | Missing skills
  v
ROADMAP ENGINE
  |
  | Career roadmap
  v
FRONTEND DASHBOARD
```

# Definition of Done

``` text
☐ Resume upload works
☐ Resume analysis works
☐ Candidate profile works
☐ Jobs can be retrieved
☐ Recommended jobs work
☐ Match endpoint works
☐ Match explanation is returned
☐ Skill-gap endpoint works
☐ Roadmap endpoint works
☐ Simulator works
☐ Backend health works
☐ AI health works
☐ Errors are consistent
☐ File validation works
☐ Frontend consumes the contracts
☐ End-to-end upload-to-roadmap flow works
```
