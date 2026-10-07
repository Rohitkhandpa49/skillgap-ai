"""Unit and regression tests for resume document parser package.

Validates all requirements from Step 9:
- Valid PDF parsing
- Valid DOCX parsing
- Multi-page PDF page ordering
- DOCX table text extraction
- Unsupported extension rejection (e.g. .txt, .exe, .zip)
- Missing file error handling (ResumeFileNotFoundError)
- Oversized file rejection (FileTooLargeError)
- Empty / sparse document handling (insufficient_text status)
- Corrupt document handling (CorruptPDFError, CorruptDocxError)
- Technical token preservation regression test:
  "Built C++ and C# services with .NET, Node.js, REST APIs and PostgreSQL."
- Section detection for Summary, Education, Projects, Skills, Certifications
- Unknown heading tolerance without crashing
"""

from pathlib import Path
import sys
import pytest

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.resume.cleaner import clean_resume_text
from app.resume.exceptions import (
    CorruptDocxError,
    CorruptPDFError,
    FileTooLargeError,
    ResumeFileNotFoundError,
    UnsupportedFileTypeError,
)
from app.resume.parser import parse_resume
from app.resume.section_detector import detect_sections

FIXTURES_DIR = AI_SERVICE_DIR / "tests" / "fixtures" / "resumes"


def test_valid_pdf_parsing():
    """Verify normal single-page PDF extracts cleanly with sections and metadata."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    parsed = parse_resume(pdf_path)

    assert parsed.filename == "sample_resume.pdf"
    assert parsed.file_type == "pdf"
    assert parsed.metadata.text_extraction_status == "success"
    assert parsed.metadata.page_count == 1
    assert parsed.metadata.character_count > 200

    # Section verification
    assert "Full-stack software engineer" in parsed.sections.summary
    assert "State University" in parsed.sections.education
    assert "TechCorp" in parsed.sections.experience
    assert "C++" in parsed.sections.skills
    assert "AWS Certified" in parsed.sections.certifications


def test_multipage_pdf_preserves_page_order():
    """Verify multi-page PDF extracts pages sequentially."""
    pdf_path = FIXTURES_DIR / "multipage_resume.pdf"
    parsed = parse_resume(pdf_path)

    assert parsed.metadata.page_count == 2
    assert parsed.metadata.pages_with_text == 2

    # Check sequential occurrence of page text
    pos_page1 = parsed.cleaned_text.find("PAGE ONE: SUMMARY AND EXPERIENCE")
    pos_page2 = parsed.cleaned_text.find("PAGE TWO: EDUCATION AND SKILLS")

    assert pos_page1 != -1
    assert pos_page2 != -1
    assert pos_page1 < pos_page2, "Page ordering inverted in multi-page PDF"


def test_valid_docx_parsing():
    """Verify DOCX parser extracts paragraphs and structure."""
    docx_path = FIXTURES_DIR / "sample_resume.docx"
    parsed = parse_resume(docx_path)

    assert parsed.filename == "sample_resume.docx"
    assert parsed.file_type == "docx"
    assert parsed.metadata.text_extraction_status == "success"
    assert "Data Analyst" in parsed.sections.summary
    assert "UC Berkeley" in parsed.sections.education
    assert "Python, SQL" in parsed.sections.skills


def test_docx_table_extraction():
    """Verify DOCX parser extracts content from embedded tables."""
    tables_path = FIXTURES_DIR / "tables_resume.docx"
    parsed = parse_resume(tables_path)

    assert parsed.metadata.table_count == 2
    assert "PostgreSQL" in parsed.cleaned_text
    assert "Informatics" in parsed.cleaned_text


def test_unsupported_file_type_rejection(tmp_path):
    """Verify unsupported file extensions and magic headers are rejected."""
    txt_file = FIXTURES_DIR / "unsupported.txt"
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        parse_resume(txt_file)
    assert exc_info.value.error_code == "UNSUPPORTED_FILE_TYPE"

    # Fake PDF (wrong header)
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("not a real pdf header")
    with pytest.raises(CorruptPDFError):
        parse_resume(fake_pdf)


def test_missing_file_handling():
    """Verify missing file raises ResumeFileNotFoundError."""
    with pytest.raises(ResumeFileNotFoundError) as exc_info:
        parse_resume(FIXTURES_DIR / "non_existent_file.pdf")
    assert exc_info.value.error_code == "FILE_NOT_FOUND"


def test_file_too_large_rejection():
    """Verify file exceeding max_size_bytes is rejected."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    # Set limit to 100 bytes (file is ~2.3 KB)
    with pytest.raises(FileTooLargeError) as exc_info:
        parse_resume(pdf_path, max_size_bytes=100)
    assert exc_info.value.error_code == "FILE_TOO_LARGE"


def test_corrupt_pdf_handling():
    """Verify corrupt PDF raises CorruptPDFError."""
    corrupt_pdf = FIXTURES_DIR / "corrupt.pdf"
    with pytest.raises(CorruptPDFError) as exc_info:
        parse_resume(corrupt_pdf)
    assert exc_info.value.error_code == "CORRUPT_PDF"


def test_corrupt_docx_handling():
    """Verify corrupt DOCX raises CorruptDocxError."""
    corrupt_docx = FIXTURES_DIR / "corrupt.docx"
    with pytest.raises(CorruptDocxError) as exc_info:
        parse_resume(corrupt_docx)
    assert exc_info.value.error_code == "CORRUPT_DOCX"


def test_nearly_empty_pdf_warning():
    """Verify sparse text marks status as insufficient_text."""
    sparse_pdf = FIXTURES_DIR / "nearly_empty.pdf"
    parsed = parse_resume(sparse_pdf)

    assert parsed.metadata.text_extraction_status == "insufficient_text"
    assert parsed.metadata.warning_message is not None
    assert "OCR is required" in parsed.metadata.warning_message


def test_technical_term_preservation_regression():
    """Exact test sentence verification:

    'Built C++ and C# services with .NET, Node.js, REST APIs and PostgreSQL.'
    Must survive cleaning intact.
    """
    sentence = "Built C++ and C# services with .NET, Node.js, REST APIs and PostgreSQL."
    cleaned = clean_resume_text(sentence)

    assert "C++" in cleaned
    assert "C#" in cleaned
    assert ".NET" in cleaned
    assert "Node.js" in cleaned
    assert "REST" in cleaned
    assert "PostgreSQL" in cleaned
    assert cleaned == sentence, "Sentence structure was altered unexpectedly"


def test_section_detection_full_suite():
    """Verify complete section detection across standard resume headers."""
    sample_text = """
JOHN DOE
john@example.com

SUMMARY
Software Engineer with extensive experience.

EDUCATION
BS in Computer Science

PROJECTS
Developed distributed systems.

TECHNICAL SKILLS
Python, SQL, C++, Docker

CERTIFICATIONS
Certified Kubernetes Administrator
"""
    sections = detect_sections(sample_text)

    assert "Software Engineer" in sections.summary
    assert "BS in Computer Science" in sections.education
    assert "Developed distributed systems" in sections.projects
    assert "Python, SQL, C++, Docker" in sections.skills
    assert "Certified Kubernetes" in sections.certifications


def test_unknown_heading_tolerance():
    """Verify unknown headings do not crash section detection."""
    text = """
EXPERIENCE
Software Developer at Acme.

RANDOM WEIRD HEADING 123
Did various interesting tasks here.

SKILLS
Python, Go
"""
    sections = detect_sections(text)

    assert "Acme" in sections.experience
    assert "Did various interesting tasks here." in sections.experience
    assert "Python, Go" in sections.skills
