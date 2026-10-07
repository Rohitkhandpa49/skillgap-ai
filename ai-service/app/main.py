"""Main FastAPI Application Entry Point for SkillGap AI Service.

Exposes internal AI service endpoints:
- GET  /health                      (Liveness probe)
- GET  /ready                       (Readiness probe for AI artifacts)
- POST /api/v1/resume/parse         (Document structure extraction)
- POST /api/v1/resume/analyze       (Candidate profile generation)
- POST /api/v1/match                (Candidate-to-job matching)
- POST /api/v1/resume/analyze-and-match (End-to-end resume intelligence pipeline)
"""

from contextlib import asynccontextmanager
import logging
import time
from typing import AsyncGenerator
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import ServiceContainer
from app.api.routes import health_router, matching_router, resume_router
from app.core.config import settings
from app.core.errors import register_exception_handlers

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("skillgap.ai_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI Lifespan: Pre-load and cache AI models and dataset artifacts on startup."""
    logger.info("Initializing SkillGap AI Service container and dependencies...")
    container = ServiceContainer()
    container.initialize()
    app.state.services = container

    logger.info("SkillGap AI Service startup complete.")
    yield

    logger.info("Shutting down SkillGap AI Service.")


app = FastAPI(
    title="SkillGap AI Service",
    description=(
        "Internal AI/NLP service for SkillGap AI. "
        "Provides secure resume parsing, boundary-aware skill extraction, "
        "and explainable tripartite hybrid candidate-job matching."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
)

# 1. Register centralized error handlers
register_exception_handlers(app)

# 2. Configure CORS middleware (restricts origins to configured frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# 3. Request correlation ID & safe logging middleware
@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    # Extract or generate correlation ID
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Attach correlation ID to response headers
    response.headers["X-Request-ID"] = request_id

    # Safe structured logging: never log request body or private candidate data
    logger.info(
        f"request_id={request_id} method={request.method} path={request.url.path} "
        f"status={response.status_code} latency_ms={duration_ms:.2f}"
    )
    return response


# 4. Include API routers
app.include_router(health_router)
app.include_router(resume_router)
app.include_router(matching_router)
