"""API routes package exports."""

from app.api.routes.health import router as health_router
from app.api.routes.matching import router as matching_router
from app.api.routes.resume import router as resume_router

__all__ = ["health_router", "resume_router", "matching_router"]
