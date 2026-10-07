"""Application Configuration for SkillGap AI Service."""

import os
from pathlib import Path
from typing import List


class Settings:
    """Core application settings and environment configurations."""

    SERVICE_NAME: str = "skillgap-ai-service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("SKILLGAP_ENV", "development")

    # Security: File upload limits (default 10 MB)
    MAX_RESUME_SIZE_BYTES: int = int(
        os.getenv("SKILLGAP_MAX_RESUME_SIZE_BYTES", str(10 * 1024 * 1024))
    )

    # CORS origins: Specific allowed frontends, never wildcard '*' with credentials
    _DEFAULT_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("SKILLGAP_CORS_ORIGINS", "").split(",")
        if origin.strip()
    ] or _DEFAULT_ORIGINS

    # Model paths
    AI_SERVICE_DIR: Path = Path(__file__).resolve().parents[2]
    REPO_ROOT: Path = AI_SERVICE_DIR.parent
    DATA_DIR: Path = REPO_ROOT / "data"
    MODELS_DIR: Path = AI_SERVICE_DIR / "models"


settings = Settings()
