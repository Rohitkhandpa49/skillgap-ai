"""CLI Demonstration tool for Candidate Profile Extraction in SkillGap AI.

Usage:
    python training/demo_candidate_profile.py <path_to_resume_document>

Demonstrates:
- Document parsing (PDF / DOCX)
- Hybrid deterministic skill extraction
- Traceable evidence collection
- Explainable confidence scoring
- Safe handling of unresolved technologies
- Privacy-conscious display (no full private document dump)
"""

from pathlib import Path
import sys
import time

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.candidate_profile_service import analyze_resume_file


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python training/demo_candidate_profile.py <path_to_resume_document>")
        sys.exit(1)

    target_path = Path(sys.argv[1]).resolve()
    if not target_path.exists():
        print(f"Error: Target file not found: {target_path}")
        sys.exit(1)

    print("=" * 60)
    print("SKILLGAP AI - CANDIDATE PROFILE EXTRACTION DEMO")
    print("=" * 60)
    print(f"File:   {target_path.name}")
    print(f"Path:   {target_path}")

    start_time = time.perf_counter()
    try:
        profile = analyze_resume_file(target_path)
    except Exception as exc:
        print(f"\nExtraction Error: {exc}")
        sys.exit(1)
    duration_ms = (time.perf_counter() - start_time) * 1000

    print("-" * 60)
    print("CANDIDATE PROFILE")
    print("-" * 60)
    print(f"Status:          {profile.metadata.parser_status.upper()}")
    print(f"Extraction Time: {duration_ms:.2f} ms")
    print(f"Skills detected: {len(profile.skills)}")
    print()

    # Collect distinct sections used across skills
    sections_used = set()
    for s in profile.skills:
        for sec in s.source_sections:
            sections_used.add(sec.capitalize())

    # Print skills with confidence and evidence
    if profile.skills:
        for idx, skill in enumerate(profile.skills, 1):
            print(f"{idx}. {skill.name}")
            print(f"   Confidence:      {skill.confidence:.2f}")
            print(f"   Source Sections: {', '.join(skill.source_sections)}")
            if skill.original_mentions and skill.original_mentions != [skill.name]:
                print(f"   Original Forms:  {', '.join(skill.original_mentions)}")
            print("   Evidence:")
            for ev in skill.evidence[:2]:  # Show up to 2 concise evidence snippets
                print(f"   - {ev}")
            print()
    else:
        print("No canonical skills detected.\n")

    # Unresolved skills
    print("Unresolved Skills:")
    if profile.unresolved_skills:
        for u in profile.unresolved_skills:
            print(f"  - {u.term} (Reason: {u.reason}, Section: {u.source_section or 'N/A'})")
    else:
        print("  None (all technical terms matched to canonical taxonomy)")
    print()

    # Education preview
    if profile.education:
        print(f"Education Entries ({len(profile.education)}):")
        for ed in profile.education[:2]:
            print(f"  - {ed}")
        print()

    # Sections used
    print(f"Sections Used:")
    print(f"  {', '.join(sorted(sections_used)) if sections_used else 'None'}")
    print("=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
