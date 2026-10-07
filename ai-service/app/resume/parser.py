"""Unified resume parser entry point for SkillGap AI.

Validates security, format, and size; routes to format-specific extractors (PDF / DOCX);
sanitizes text; partitions sections; and constructs a strongly typed ParsedResume model.
"""

from pathlib import Path
import time
from typing import Optional, Union

from app.resume.cleaner import clean_resume_text
from app.resume.docx_parser import extract_text_from_docx
from app.resume.exceptions import (
    CorruptDocxError,
    CorruptPDFError,
    FileTooLargeError,
    ResumeFileNotFoundError,
    UnsupportedFileTypeError,
)
from app.resume.pdf_parser import extract_text_from_pdf
from app.resume.schemas import ParsedResume, ResumeMetadata
from app.resume.section_detector import detect_sections

# Default maximum allowable file size (10 MB)
DEFAULT_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024

# Quality thresholds
MIN_SUCCESS_CHARS: int = 150
MIN_PARTIAL_CHARS: int = 50

# Supported magic bytes
PDF_MAGIC: bytes = b"%PDF"
DOCX_MAGIC: bytes = b"PK\x03\x04"


def validate_file_format_and_magic(file_path: Path) -> str:
    """Verify file extension and document magic bytes to reject disguised or unsupported files."""
    ext = file_path.suffix.lower()

    if ext not in [".pdf", ".docx"]:
        raise UnsupportedFileTypeError(filename=file_path.name, detected_type=ext or "unknown")

    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
    except Exception as ex:
        raise UnsupportedFileTypeError(filename=file_path.name, detected_type="unreadable") from ex

    if ext == ".pdf":
        if not header.startswith(PDF_MAGIC):
            raise CorruptPDFError("File does not start with valid PDF magic bytes (%PDF)")
        return "pdf"
    elif ext == ".docx":
        if not header.startswith(DOCX_MAGIC):
            raise CorruptDocxError("File does not start with valid DOCX magic bytes (PK\\x03\\x04)")
        return "docx"

    raise UnsupportedFileTypeError(filename=file_path.name, detected_type=ext)


def parse_resume(
    file_path: Union[str, Path],
    max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> ParsedResume:
    """Unified entry point to parse a PDF or DOCX resume document.

    Args:
        file_path: Path to the target resume file.
        max_size_bytes: Maximum allowed file size in bytes (defaults to 10MB).

    Returns:
        Structured ParsedResume with cleaned text, sections, and metadata.

    Raises:
        ResumeFileNotFoundError: If the file does not exist.
        FileTooLargeError: If file exceeds max_size_bytes.
        UnsupportedFileTypeError: If file is not a supported PDF or DOCX format.
        CorruptPDFError: If PDF structure is invalid.
        CorruptDocxError: If DOCX structure is invalid.
    """
    t0 = time.time()
    path = Path(file_path).resolve()

    # 1. Existence Check
    if not path.is_file():
        raise ResumeFileNotFoundError(str(file_path))

    # 2. File Size Check
    file_size = path.stat().st_size
    if file_size > max_size_bytes:
        raise FileTooLargeError(file_size=file_size, max_size=max_size_bytes)

    # 3. Format and Magic Bytes Validation
    doc_type = validate_file_format_and_magic(path)

    # 4. Format-Specific Text Extraction
    if doc_type == "pdf":
        raw_text, ext_meta = extract_text_from_pdf(path)
        page_count = ext_meta.get("page_count", 1)
        pages_with_text = ext_meta.get("pages_with_text", 0)
        pages_without_text = ext_meta.get("pages_without_text", 0)
        paragraph_count = None
        table_count = None
    else:  # docx
        raw_text, ext_meta = extract_text_from_docx(path)
        page_count = 1
        pages_with_text = 1 if raw_text.strip() else 0
        pages_without_text = 0 if raw_text.strip() else 1
        paragraph_count = ext_meta.get("paragraph_count", 0)
        table_count = ext_meta.get("table_count", 0)

    # 5. Conservative Text Cleaning
    cleaned_text = clean_resume_text(raw_text)
    char_count = len(cleaned_text)

    # 6. Section Detection
    sections = detect_sections(cleaned_text)

    # 7. Quality Status Evaluation
    if char_count >= MIN_SUCCESS_CHARS:
        status = "success"
        warning = None
    elif char_count >= MIN_PARTIAL_CHARS:
        status = "partial"
        warning = "Sparse text extracted from document; some sections may be incomplete."
    else:
        status = "insufficient_text"
        warning = (
            "Extracted text is empty or sparse (< 50 characters). "
            "If this document is a scanned or image-based PDF, OCR is required."
        )

    processing_time_ms = round((time.time() - t0) * 1000.0, 2)

    metadata = ResumeMetadata(
        page_count=page_count,
        pages_with_text=pages_with_text,
        pages_without_text=pages_without_text,
        paragraph_count=paragraph_count,
        table_count=table_count,
        character_count=char_count,
        text_extraction_status=status,
        file_size_bytes=file_size,
        processing_time_ms=processing_time_ms,
        warning_message=warning,
    )

    return ParsedResume(
        filename=path.name,
        file_type=doc_type,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        sections=sections,
        metadata=metadata,
    )
