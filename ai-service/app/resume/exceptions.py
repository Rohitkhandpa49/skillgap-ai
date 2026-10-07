"""Custom controlled exceptions for resume document parsing."""

from typing import Any, Dict, Optional


class ResumeParserError(Exception):
    """Base exception for all resume document parsing errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ResumeFileNotFoundError(ResumeParserError):
    """Raised when the specified resume file does not exist on disk."""

    def __init__(self, path: str) -> None:
        super().__init__(
            error_code="FILE_NOT_FOUND",
            message=f"Resume file not found at path: {path}",
            details={"path": str(path)},
        )


class UnsupportedFileTypeError(ResumeParserError):
    """Raised when the uploaded file type/extension is not supported (.pdf, .docx only)."""

    def __init__(self, filename: str, detected_type: str = "unknown") -> None:
        super().__init__(
            error_code="UNSUPPORTED_FILE_TYPE",
            message=f"Unsupported file format '{detected_type}'. Only .pdf and .docx documents are accepted.",
            details={"filename": filename, "detected_type": detected_type},
        )


class FileTooLargeError(ResumeParserError):
    """Raised when the resume file exceeds the configured maximum byte size."""

    def __init__(self, file_size: int, max_size: int) -> None:
        super().__init__(
            error_code="FILE_TOO_LARGE",
            message=f"File size ({file_size} bytes) exceeds maximum allowable limit ({max_size} bytes).",
            details={"file_size_bytes": file_size, "max_size_bytes": max_size},
        )


class CorruptPDFError(ResumeParserError):
    """Raised when the PDF document is damaged, unreadable, or password-protected."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            error_code="CORRUPT_PDF",
            message=f"Failed to read or parse PDF document: {reason}",
            details={"reason": reason},
        )


class CorruptDocxError(ResumeParserError):
    """Raised when the DOCX file is corrupt, unreadable, or not a valid Word archive."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            error_code="CORRUPT_DOCX",
            message=f"Failed to read or parse DOCX document: {reason}",
            details={"reason": reason},
        )


class TextExtractionInsufficientError(ResumeParserError):
    """Raised or reported when document yields no extractable text (e.g. scanned image PDF)."""

    def __init__(self, char_count: int, reason: str = "Scanned or image-only document") -> None:
        super().__init__(
            error_code="TEXT_EXTRACTION_INSUFFICIENT",
            message=f"Insufficient extractable text ({char_count} chars). Scanned/image-only PDFs require OCR.",
            details={"character_count": char_count, "reason": reason},
        )


class ResumeParseFailedError(ResumeParserError):
    """Generic fallback error for unexpected parsing execution failures."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            error_code="RESUME_PARSE_FAILED",
            message=f"An unexpected failure occurred while parsing resume: {reason}",
            details={"reason": reason},
        )
