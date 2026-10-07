"""PDF Document Text Extraction using pdfplumber.

Extracts text from PDF documents safely:
- Iterates page by page, strictly preserving page order
- Tracks pages with text vs empty/image pages
- Concatenates multi-page text cleanly
- Handles corrupt or encrypted PDF documents safely with CorruptPDFError
- Does NOT perform OCR (marks scanned pages as insufficient text)
"""

from pathlib import Path
from typing import Dict, List, Tuple
import pdfplumber

from app.resume.exceptions import CorruptPDFError


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, Dict[str, int]]:
    """Extract full raw text and page-level metadata from a PDF file.

    Args:
        pdf_path: Path to target PDF document on disk.

    Returns:
        Tuple of (raw_concatenated_text, metadata_dict)
        where metadata_dict contains:
            page_count, pages_with_text, pages_without_text, character_count

    Raises:
        CorruptPDFError: If the PDF cannot be opened or parsed.
    """
    page_texts: List[str] = []
    pages_with_text = 0
    pages_without_text = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for page_idx, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as ex:
                    # In case of minor per-page extraction glitch, treat as empty page
                    text = ""

                stripped_text = text.strip()
                if stripped_text:
                    pages_with_text += 1
                    page_texts.append(stripped_text)
                else:
                    pages_without_text += 1

    except Exception as ex:
        raise CorruptPDFError(f"Unable to read PDF file '{pdf_path.name}': {str(ex)}") from ex

    concatenated_raw_text = "\n\n".join(page_texts)

    metadata = {
        "page_count": total_pages,
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "character_count": len(concatenated_raw_text),
    }

    return concatenated_raw_text, metadata
