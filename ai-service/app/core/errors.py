"""Controlled HTTP and Domain Error Handlers for SkillGap AI Service.

Translates internal domain exceptions into clean, safe HTTP responses
without exposing Python tracebacks, internal filesystem paths, or credentials.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.resume.exceptions import (
    CorruptDocxError,
    CorruptPDFError,
    FileTooLargeError,
    ResumeFileNotFoundError,
    ResumeParserError,
    TextExtractionInsufficientError,
    UnsupportedFileTypeError,
)


class APIError(Exception):
    """Base class for user-facing controlled API errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class MatchingServiceUnavailableError(APIError):
    """Raised when hybrid/matching model artifacts are uninitialized or missing."""

    def __init__(self, message: str = "Matching engine dependencies are unavailable.") -> None:
        super().__init__(
            message=message,
            code="MATCHING_SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class InvalidCandidateRequestError(APIError):
    """Raised when matching request contains insufficient or invalid candidate data."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="INVALID_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def make_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Construct standard error envelope."""
    payload: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if request_id:
        payload["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(UnsupportedFileTypeError)
    async def unsupported_file_handler(
        request: Request, exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="UNSUPPORTED_FILE_TYPE",
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(CorruptPDFError)
    @app.exception_handler(CorruptDocxError)
    async def corrupt_doc_handler(request: Request, exc: ResumeParserError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="CORRUPT_DOCUMENT",
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(TextExtractionInsufficientError)
    async def sparse_text_handler(
        request: Request, exc: TextExtractionInsufficientError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="TEXT_EXTRACTION_INSUFFICIENT",
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(ResumeFileNotFoundError)
    async def not_found_handler(request: Request, exc: ResumeFileNotFoundError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return make_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND",
            message=exc.message,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Summarize first error cleanly
        errors = exc.errors()
        msg = errors[0]["msg"] if errors else "Invalid request body or parameters"
        return make_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=msg,
            request_id=request_id,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        code_map = {
            400: "INVALID_REQUEST",
            404: "NOT_FOUND",
            413: "FILE_TOO_LARGE",
            415: "UNSUPPORTED_FILE_TYPE",
            422: "UNPROCESSABLE_ENTITY",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return make_error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Return generic safe message without leaking stack trace
        return make_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred while processing the request.",
            request_id=request_id,
        )
