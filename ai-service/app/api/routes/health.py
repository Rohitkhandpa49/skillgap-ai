"""Health and Readiness Monitoring Endpoints for SkillGap AI Service."""

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import ServiceContainer, get_service_container
from app.core.config import settings

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/health",
    summary="Service Liveness Probe",
    description="Returns 200 if the FastAPI application process is alive and responsive.",
)
def health_check() -> dict:
    """Liveness probe: verifies server process is responsive."""
    return {
        "success": True,
        "service": settings.SERVICE_NAME,
        "status": "healthy",
    }


@router.get(
    "/ready",
    summary="AI Dependencies Readiness Probe",
    description="Verifies that all required AI models, embeddings, and dataset artifacts are loaded and ready.",
)
def readiness_check(
    response: Response,
    container: ServiceContainer = Depends(get_service_container),
) -> dict:
    """Readiness probe: validates availability of core AI models and artifacts."""
    is_ready = container.readiness.get("ready", False)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "success": is_ready,
        "service": settings.SERVICE_NAME,
        "status": "ready" if is_ready else "degraded",
        "components": container.readiness.get("components", {}),
    }
