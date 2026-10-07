"""Lightweight tests for SDS Personality Traits preprocessing, model artifacts, and evaluation.

Covers:
- required columns validation
- ID exclusion
- binary target validation
- scaler training-only fit
- model file existence
- metadata existence and limitation disclosure
- prediction output belongs to valid classes
- incorrect feature count handled safely
"""

import json
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
import pytest

# Ensure ai-service is in sys.path
ai_service_dir = Path(__file__).resolve().parents[1]
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from app.preprocessing.sds_preprocessing import (
    EXPECTED_PERSONALITY_FEATURES,
    ID_COLUMN,
    TARGET_COLUMN,
    normalize_sds_columns,
    split_and_scale_sds_data,
    validate_and_clean_sds_data,
    verify_sds_data_leakage,
)


@pytest.fixture
def sample_sds_df() -> pd.DataFrame:
    """Fixture providing synthetic sample SDS data."""
    np.random.seed(42)
    n = 60
    return pd.DataFrame(
        {
            "id": range(8001, 8001 + n),
            "neuroticism": np.random.randint(17, 65, n),
            " extraversion": np.random.randint(17, 65, n),  # Raw whitespace style
            "openness_to_experience": np.random.randint(18, 65, n),
            "agreeableness": np.random.randint(17, 65, n),
            "conscientiousness": np.random.randint(18, 65, n),
            "success_ classification_ high_low": np.random.choice([0, 1], size=n, p=[0.45, 0.55]),
        }
    )


@pytest.fixture
def sds_artifact_paths():
    """Fixture resolving paths to trained SDS artifacts."""
    repo_root = ai_service_dir.parent
    return {
        "model_file": repo_root / "ai-service" / "models" / "sds" / "sds_best_model.joblib",
        "metadata_file": repo_root / "ai-service" / "models" / "sds" / "sds_model_metadata.json",
        "scaler_file": repo_root / "ai-service" / "models" / "preprocessing" / "sds_standard_scaler.joblib",
    }


def test_sds_required_columns(sample_sds_df: pd.DataFrame) -> None:
    """Verify KeyError is raised when required columns are missing."""
    invalid_df = sample_sds_df.drop(columns=["agreeableness"])
    with pytest.raises(KeyError) as exc_info:
        normalize_sds_columns(invalid_df)
    assert "Missing required column(s)" in str(exc_info.value)
    assert "agreeableness" in str(exc_info.value)


def test_sds_id_exclusion(sample_sds_df: pd.DataFrame) -> None:
    """Verify ID is strictly excluded from features in splits and scalers."""
    norm_df = normalize_sds_columns(sample_sds_df)
    clean_df, _ = validate_and_clean_sds_data(norm_df)
    res = split_and_scale_sds_data(clean_df, test_size=0.2, random_state=42)

    assert ID_COLUMN not in res["X_train"].columns
    assert ID_COLUMN not in res["X_test"].columns
    assert ID_COLUMN not in res["X_train_scaled"].columns
    assert ID_COLUMN not in res["X_test_scaled"].columns
    assert list(res["X_train"].columns) == EXPECTED_PERSONALITY_FEATURES


def test_sds_binary_target_validation(sample_sds_df: pd.DataFrame) -> None:
    """Verify ValueError is raised if target contains non-binary values."""
    norm_df = normalize_sds_columns(sample_sds_df)
    bad_df = norm_df.copy()
    bad_df.loc[0, TARGET_COLUMN] = 99
    with pytest.raises(ValueError) as exc_info:
        validate_and_clean_sds_data(bad_df)
    assert "non-binary" in str(exc_info.value)


def test_sds_scaler_training_only_fit(sample_sds_df: pd.DataFrame) -> None:
    """Verify scaler was fitted ONLY on X_train and not test data."""
    norm_df = normalize_sds_columns(sample_sds_df)
    clean_df, _ = validate_and_clean_sds_data(norm_df)
    res = split_and_scale_sds_data(clean_df, test_size=0.2, random_state=42)
    leakage = verify_sds_data_leakage(res)

    assert leakage["scaler_fitted_only_train"] is True
    assert leakage["id_excluded"] is True
    assert leakage["target_excluded"] is True
    assert res["scaler"].n_samples_seen_ == len(res["X_train"])
    assert np.allclose(res["scaler"].mean_, res["X_train"].mean().values)


def test_sds_model_file_exists(sds_artifact_paths):
    """Verify persisted SDS model file exists and has predict capability."""
    assert sds_artifact_paths["model_file"].exists()
    model = joblib.load(sds_artifact_paths["model_file"])
    assert hasattr(model, "predict")


def test_sds_metadata_existence(sds_artifact_paths):
    """Verify metadata exists and contains required fields and limitation disclosures."""
    assert sds_artifact_paths["metadata_file"].exists()
    with open(sds_artifact_paths["metadata_file"], "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["model_name"] == "SVM (RBF)"
    assert meta["expected_features"] == EXPECTED_PERSONALITY_FEATURES
    assert "limitations" in meta
    assert len(meta["limitations"]) >= 4
    assert "held_out_test_metrics" in meta


def test_sds_prediction_output_valid_classes(sds_artifact_paths):
    """Verify model predictions belong strictly to valid binary classes {0, 1}."""
    model = joblib.load(sds_artifact_paths["model_file"])
    scaler = joblib.load(sds_artifact_paths["scaler_file"])

    sample_inputs = pd.DataFrame(
        [
            {
                "neuroticism": 25,
                "extraversion": 55,
                "openness_to_experience": 50,
                "agreeableness": 60,
                "conscientiousness": 58,
            },
            {
                "neuroticism": 55,
                "extraversion": 20,
                "openness_to_experience": 25,
                "agreeableness": 22,
                "conscientiousness": 28,
            },
        ]
    )
    scaled_inputs = pd.DataFrame(scaler.transform(sample_inputs), columns=EXPECTED_PERSONALITY_FEATURES)
    preds = model.predict(scaled_inputs)
    for p in preds:
        assert p in [0, 1]


def test_sds_incorrect_feature_count_handled_safely(sds_artifact_paths):
    """Verify passing incorrect feature count raises a controlled ValueError."""
    model = joblib.load(sds_artifact_paths["model_file"])
    invalid_input = np.array([[30.0, 40.0, 50.0]])  # 3 features instead of 5
    with pytest.raises(ValueError):
        model.predict(invalid_input)
