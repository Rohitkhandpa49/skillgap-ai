"""API Dependencies and Service Container for SkillGap AI Service.

Handles:
- Modern FastAPI lifespan service initialization
- Singleton caching of HybridMatcher and CandidateProfileService to avoid reloading models on every request
- Secure temporary file lifecycle with guaranteed cleanup
"""

from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Dict, Generator, Optional
import uuid

from fastapi import HTTPException, Request, UploadFile, status

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.core.config import settings
from app.core.errors import FileTooLargeError, MatchingServiceUnavailableError, UnsupportedFileTypeError
from app.matching.hybrid_matcher import HybridMatcher
from app.resume.exceptions import FileTooLargeError as ResumeFileTooLargeError
from app.services.candidate_profile_service import CandidateProfileService

logger = logging.getLogger("skillgap.ai_service")


class ServiceContainer:
    """Manages pre-loaded models and service instances across the application lifetime."""

    def __init__(self) -> None:
        self.hybrid_matcher: Optional[HybridMatcher] = None
        self.candidate_service: Optional[CandidateProfileService] = None
        self.readiness: Dict[str, Any] = {
            "ready": False,
            "components": {
                "skill_taxonomy": "not_checked",
                "job_profiles": "not_checked",
                "tfidf_artifacts": "not_checked",
                "semantic_embeddings": "not_checked",
                "matching_engine": "not_checked",
            },
            "errors": [],
        }

    def initialize(self) -> None:
        """Pre-load models and artifacts during application startup."""
        logger.info("ServiceContainer: Loading AI service dependencies...")
        errors = []

        # 1. Verify skill taxonomy
        skills_path = settings.DATA_DIR / "skills.json"
        aliases_path = settings.DATA_DIR / "aliases.json"
        if skills_path.exists() and aliases_path.exists():
            self.readiness["components"]["skill_taxonomy"] = "ready"
        else:
            self.readiness["components"]["skill_taxonomy"] = "missing"
            errors.append("Skill taxonomy JSON files not found in data/")

        # 2. Verify processed job profiles
        job_profiles_path = settings.DATA_DIR / "processed" / "analytics_jobs" / "job_profiles.json"
        if job_profiles_path.exists():
            self.readiness["components"]["job_profiles"] = "ready"
        else:
            self.readiness["components"]["job_profiles"] = "missing"
            errors.append("Processed job profiles JSON not found")

        # 3. Verify TF-IDF artifacts
        models_dir = settings.MODELS_DIR / "matching"
        tfidf_vec = models_dir / "tfidf_vectorizer.joblib"
        tfidf_mat = models_dir / "job_tfidf_matrix.joblib"
        if tfidf_vec.exists() and tfidf_mat.exists():
            self.readiness["components"]["tfidf_artifacts"] = "ready"
        else:
            self.readiness["components"]["tfidf_artifacts"] = "missing"
            errors.append("TF-IDF vectorizer / job matrix artifacts not found")

        # 4. Verify Semantic embeddings
        sem_dir = models_dir / "semantic"
        sem_emb = sem_dir / "job_embeddings.npy"
        sem_ids = sem_dir / "job_embedding_job_ids.json"
        if sem_emb.exists() and sem_ids.exists():
            self.readiness["components"]["semantic_embeddings"] = "ready"
        else:
            self.readiness["components"]["semantic_embeddings"] = "missing"
            errors.append("Job semantic embeddings or ID mapping not found")


        # 5. Initialize CandidateProfileService
        try:
            self.candidate_service = CandidateProfileService()
        except Exception as exc:
            logger.error(f"Failed to initialize CandidateProfileService: {exc}")
            errors.append(f"CandidateProfileService init failure: {exc}")

        # 6. Initialize HybridMatcher (loads artifacts into memory once)
        try:
            self.hybrid_matcher = HybridMatcher(auto_persist_metadata=False)
            # Warm up SentenceTransformer embedding cache on CPU
            _ = self.hybrid_matcher.semantic_matcher.encode_candidate("warmup", ["Python"], [])
            self.readiness["components"]["matching_engine"] = "ready"
        except Exception as exc:


            logger.error(f"Failed to initialize HybridMatcher: {exc}")
            self.readiness["components"]["matching_engine"] = "failed"
            errors.append(f"HybridMatcher init failure: {exc}")

        self.readiness["errors"] = errors
        self.readiness["ready"] = len(errors) == 0
        if self.readiness["ready"]:
            logger.info("ServiceContainer: All AI components loaded successfully and READY.")
        else:
            logger.warning(f"ServiceContainer: AI service not fully ready. Errors: {errors}")


_global_service_container: Optional[ServiceContainer] = None


def get_global_service_container() -> ServiceContainer:
    """Retrieve or initialize global ServiceContainer singleton."""
    global _global_service_container
    if _global_service_container is None:
        _global_service_container = ServiceContainer()
        _global_service_container.initialize()
    return _global_service_container


def get_service_container(request: Request) -> ServiceContainer:
    """FastAPI dependency to access the global ServiceContainer."""
    services = getattr(request.app.state, "services", None)
    if services is not None and getattr(services, "readiness", {}).get("ready", False):
        return services

    return get_global_service_container()




def get_candidate_profile_service(request: Request) -> CandidateProfileService:
    """FastAPI dependency to retrieve initialized CandidateProfileService."""
    container = get_service_container(request)
    if container.candidate_service:
        return container.candidate_service
    # Fallback initialization if container not ready
    return CandidateProfileService()


def get_hybrid_matcher(request: Request) -> HybridMatcher:
    """FastAPI dependency to retrieve initialized HybridMatcher."""
    container = get_service_container(request)
    if container.hybrid_matcher:
        return container.hybrid_matcher
    # Attempt lazy initialization
    try:
        container.hybrid_matcher = HybridMatcher(auto_persist_metadata=False)
        return container.hybrid_matcher
    except Exception as exc:
        raise MatchingServiceUnavailableError(
            f"Matching engine cannot be initialized: {exc}"
        )


@contextmanager
def temporary_upload_file(
    upload_file: UploadFile,
    max_size_bytes: int = settings.MAX_RESUME_SIZE_BYTES,
) -> Generator[Path, None, None]:
    """Securely stream uploaded file to a temporary path with strict size and format validation.

    Guarantees automatic cleanup in a `finally` block to prevent lingering files.
    """
    original_name = upload_file.filename or "unknown"
    ext = Path(original_name).suffix.lower()

    if ext not in (".pdf", ".docx"):
        raise UnsupportedFileTypeError(
            f"Unsupported file extension '{ext}'. Only .pdf and .docx are supported."
        )

    # Use secure UUID temporary filename
    temp_dir = Path(tempfile.gettempdir()) / "skillgap_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"upload_{uuid.uuid4().hex}{ext}"

    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB chunks

    try:
        with open(temp_file_path, "wb") as dst:
            while True:
                chunk = upload_file.file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    raise FileTooLargeError(
                        f"Uploaded file exceeds maximum limit of {max_size_bytes / (1024 * 1024):.1f} MB."
                    )
                dst.write(chunk)

        yield temp_file_path

    finally:
        # Guarantee cleanup even on errors
        try:
            if temp_file_path.exists():
                temp_file_path.unlink()
        except Exception as cleanup_err:
            logger.warning(f"Failed to remove temporary upload file {temp_file_path}: {cleanup_err}")
        try:
            upload_file.file.close()
        except Exception:
            pass
