# SkillGap AI — AI Service

Python FastAPI microservice for AI talent matching, resume processing, and skill gap intelligence.

## Directory Structure

```text
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entrypoint
│   ├── api/                 # API route handlers
│   ├── core/                # Configuration and shared utilities
│   ├── services/            # Core business logic services
│   ├── preprocessing/       # Text & document preprocessing
│   ├── training/            # Model training workflows
│   ├── evaluation/          # Model evaluation and metrics
│   └── models/              # Pydantic models & schemas
├── tests/                   # Automated tests
├── requirements.txt         # Minimal service dependencies
└── README.md                # Service documentation
```

## Getting Started

### 1. Create and Activate Virtual Environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI Service

From inside the `ai-service/` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Health Check

Verify the service is running:

```bash
curl http://127.0.0.1:8000/health
```

Expected Response:
```json
{
  "success": true,
  "service": "skillgap-ai-service",
  "status": "healthy"
}
```
