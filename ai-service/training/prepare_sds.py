"""Executable Runner for SDS Personality Traits Preprocessing Pipeline.

Run with:
    python training/prepare_sds.py
from inside the ai-service/ directory.
"""

from pathlib import Path
import sys

# Ensure ai-service root is in sys.path
ai_service_dir = Path(__file__).resolve().parents[1]
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from app.preprocessing.sds_preprocessing import run_sds_pipeline


def main() -> None:
    """Execute SDS preprocessing pipeline."""
    run_sds_pipeline()


if __name__ == "__main__":
    main()
