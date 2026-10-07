"""Tests for trained JDS Skill Traits model and metadata artifacts.

Verifies:
- model file exists after training
- metadata file exists and contains required fields
- model accepts exactly five expected features
- output class is a valid binary value (0 or 1)
- incorrect feature count raises a controlled ValueError
"""

import json
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
import pytest

# Ensure ai-service root is in sys.path
ai_service_dir = Path(__file__).resolve().parents[1]
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

EXPECTED_FEATURES = [
    "big_data_skills",
    "maths-stats_skills",
    "coding_skills",
    "ai_and_ml_skills",
    "dashboard_and_storytelling_skills",
]


@pytest.fixture
def model_paths():
    """Fixture resolving paths to trained artifacts."""
    repo_root = ai_service_dir.parent
    return {
        "model_file": repo_root / "ai-service" / "models" / "jds" / "jds_best_model.joblib",
        "metadata_file": repo_root / "ai-service" / "models" / "jds" / "jds_model_metadata.json",
        "scaler_file": repo_root / "ai-service" / "models" / "preprocessing" / "jds_standard_scaler.joblib",
    }


def test_model_file_exists(model_paths):
    """Verify that the persisted model file exists and is loadable."""
    assert model_paths["model_file"].exists(), f"Model file not found: {model_paths['model_file']}"
    model = joblib.load(model_paths["model_file"])
    assert hasattr(model, "predict"), "Loaded model does not have a predict method"


def test_metadata_file_exists(model_paths):
    """Verify that metadata JSON exists and contains all required tracking fields."""
    assert model_paths["metadata_file"].exists(), f"Metadata not found: {model_paths['metadata_file']}"
    with open(model_paths["metadata_file"], "r", encoding="utf-8") as f:
        meta = json.load(f)

    required_keys = [
        "model_name",
        "model_type",
        "model_version",
        "dataset_name",
        "target_column",
        "expected_features",
        "trained_timestamp_utc",
        "held_out_test_metrics",
        "confusion_matrix",
    ]
    for key in required_keys:
        assert key in meta, f"Metadata missing required key '{key}'"
    assert meta["expected_features"] == EXPECTED_FEATURES


def test_model_accepts_five_features(model_paths):
    """Verify model accepts a 5-feature input matrix and generates predictions."""
    model = joblib.load(model_paths["model_file"])
    scaler = joblib.load(model_paths["scaler_file"])

    sample_input = pd.DataFrame(
        [
            {
                "big_data_skills": 4.5,
                "maths-stats_skills": 4.8,
                "coding_skills": 4.2,
                "ai_and_ml_skills": 4.9,
                "dashboard_and_storytelling_skills": 4.0,
            }
        ]
    )
    scaled_input = pd.DataFrame(scaler.transform(sample_input), columns=EXPECTED_FEATURES)
    pred = model.predict(scaled_input)
    assert len(pred) == 1


def test_output_class_valid_binary(model_paths):
    """Verify predicted labels are strictly in {0, 1}."""
    model = joblib.load(model_paths["model_file"])
    scaler = joblib.load(model_paths["scaler_file"])

    sample_inputs = pd.DataFrame(
        [
            {
                "big_data_skills": 2.2,
                "maths-stats_skills": 2.3,
                "coding_skills": 2.2,
                "ai_and_ml_skills": 2.5,
                "dashboard_and_storytelling_skills": 2.4,
            },
            {
                "big_data_skills": 4.8,
                "maths-stats_skills": 5.0,
                "coding_skills": 4.9,
                "ai_and_ml_skills": 5.0,
                "dashboard_and_storytelling_skills": 4.9,
            },
        ]
    )
    scaled_inputs = pd.DataFrame(scaler.transform(sample_inputs), columns=EXPECTED_FEATURES)
    preds = model.predict(scaled_inputs)
    for p in preds:
        assert p in [0, 1], f"Predicted value '{p}' is not binary 0 or 1"


def test_incorrect_feature_count_raises_error(model_paths):
    """Verify passing incorrect feature count raises a controlled ValueError."""
    model = joblib.load(model_paths["model_file"])

    # 3 features instead of 5
    invalid_input = np.array([[3.0, 4.0, 5.0]])
    with pytest.raises(ValueError):
        model.predict(invalid_input)
