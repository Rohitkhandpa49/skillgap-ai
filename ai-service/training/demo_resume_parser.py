"""CLI Demonstration Script for Resume Document Parser.

Parses a target PDF or DOCX resume document and displays structured extraction results.

Usage:
    python training/demo_resume_parser.py [path/to/resume.pdf_or_docx]
"""

from pathlib import Path
import sys
from typing import Optional

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.resume.parser import parse_resume


def run_demo(target_path: Optional[str] = None) -> None:
    if target_path:
        file_path = Path(target_path).resolve()
    else:
        # Default demonstration fixture
        file_path = AI_SERVICE_DIR / "tests" / "fixtures" / "resumes" / "sample_resume.pdf"

    print("=" * 60)
    print("SKILLGAP AI - RESUME DOCUMENT PARSER DEMO")
    print("=" * 60)
    print(f"Target File: {file_path}")

    try:
        parsed = parse_resume(file_path)

        print("\nRESUME PARSE RESULT")
        print("-" * 60)
        print(f"File:              {parsed.filename}")
        print(f"Type:              {parsed.file_type.upper()}")
        print(f"Pages:             {parsed.metadata.page_count}")
        print(f"Characters:        {parsed.metadata.character_count}")
        print(f"Extraction Status: {parsed.metadata.text_extraction_status.upper()}")
        print(f"Processing Time:   {parsed.metadata.processing_time_ms} ms")

        if parsed.metadata.warning_message:
            print(f"Warning:           {parsed.metadata.warning_message}")

        print("\nDetected Sections:")
        sections_dict = parsed.sections.model_dump()
        non_empty_sections = [k.capitalize() for k, v in sections_dict.items() if v and v.strip()]
        for sec in non_empty_sections:
            print(f"  - {sec}")

        print("\nCleaned Text Preview (First 350 chars):")
        preview = parsed.cleaned_text[:350].replace("\n", " ")
        print(f"  \"{preview}...\"")

        print("\n" + "=" * 60)
        print("PARSE DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as ex:
        print(f"\n[ERROR] Failed to parse document: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    arg_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_demo(arg_path)
