"""Common API Envelopes and Response Schemas."""

from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""

    success: bool = Field(default=True, description="Request execution status")
    data: T = Field(..., description="Response payload")


class ErrorDetail(BaseModel):
    """Structured error payload."""

    code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable safe explanation")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = Field(default=False, description="Always false for error envelopes")
    error: ErrorDetail = Field(..., description="Error detail object")
    request_id: Optional[str] = Field(default=None, description="Traceable request correlation ID")
