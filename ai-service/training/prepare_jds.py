"""Executable Runner for JDS Skill Traits Preprocessing Pipeline.

Run with:
    python training/prepare_jds.py
from inside the ai-service/ directory.
"""

from pathlib import Path
import sys

# Ensure ai-service root is in sys.path for clean imports
ai_service_dir = Path(__file__).resolve().parents[1]
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from app.preprocessing.jds_preprocessing import run_jds_pipeline


def main() -> None:
    """Execute JDS preprocessing pipeline."""
    run_jds_pipeline()


if __name__ == "__main__":
    main()
