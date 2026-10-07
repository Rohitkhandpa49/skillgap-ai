"""Lightweight tests for JDS Preprocessing Pipeline.

Covers:
- required columns validation
- ID exclusion
- binary target validation
- train/test stratification
- no scaler leakage
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

# Ensure ai-service root is in sys.path
ai_service_dir = Path(__file__).resolve().parents[1]
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from app.preprocessing.jds_preprocessing import (
    EXPECTED_FEATURES,
    ID_COLUMN,
    TARGET_COLUMN,
    load_jds_data,
    normalize_column_names,
    split_and_scale_data,
    validate_and_clean_data,
    verify_data_leakage,
)


@pytest.fixture
def sample_valid_df() -> pd.DataFrame:
    """Fixture providing a valid synthetic sample DataFrame."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame(
        {
            "id": range(1001, 1001 + n),
            "big_data_skills": np.random.uniform(2.0, 5.0, n),
            "maths-stats_skills": np.random.uniform(2.0, 5.0, n),
            "coding_skills": np.random.uniform(2.0, 5.0, n),
            "ai_and_ml_skills": np.random.uniform(2.0, 5.0, n),
            "dashboard_and_storytelling_skills": np.random.uniform(2.0, 5.0, n),
            "salary_hike_high_or_low": np.random.choice([0, 1], size=n, p=[0.45, 0.55]),
        }
    )


def test_required_columns_validation(sample_valid_df: pd.DataFrame) -> None:
    """Verify KeyError is raised when required columns are missing."""
    # Drop one required feature
    invalid_df = sample_valid_df.drop(columns=["coding_skills"])
    with pytest.raises(KeyError) as exc_info:
        normalize_column_names(invalid_df)
    assert "Missing required column(s)" in str(exc_info.value)
    assert "coding_skills" in str(exc_info.value)


def test_id_exclusion(sample_valid_df: pd.DataFrame) -> None:
    """Verify ID is strictly excluded from features in splits and scalers."""
    clean_df, _ = validate_and_clean_data(sample_valid_df)
    res = split_and_scale_data(clean_df, test_size=0.2, random_state=42)

    assert ID_COLUMN not in res["X_train"].columns
    assert ID_COLUMN not in res["X_test"].columns
    assert ID_COLUMN not in res["X_train_scaled"].columns
    assert ID_COLUMN not in res["X_test_scaled"].columns
    assert list(res["X_train"].columns) == EXPECTED_FEATURES


def test_binary_target_validation(sample_valid_df: pd.DataFrame) -> None:
    """Verify ValueError is raised if target contains non-binary values."""
    bad_df = sample_valid_df.copy()
    bad_df.loc[0, TARGET_COLUMN] = 99  # Invalid target
    with pytest.raises(ValueError) as exc_info:
        validate_and_clean_data(bad_df)
    assert "non-binary" in str(exc_info.value)


def test_train_test_stratification(sample_valid_df: pd.DataFrame) -> None:
    """Verify train/test split preserves target stratification."""
    clean_df, _ = validate_and_clean_data(sample_valid_df)
    res = split_and_scale_data(clean_df, test_size=0.2, random_state=42)

    total_c1_ratio = clean_df[TARGET_COLUMN].mean()
    train_c1_ratio = res["y_train"].mean()
    test_c1_ratio = res["y_test"].mean()

    # Stratification check (tolerates small integer rounding on tiny subsets)
    assert abs(train_c1_ratio - total_c1_ratio) < 0.05
    assert abs(test_c1_ratio - total_c1_ratio) < 0.10


def test_no_scaler_leakage(sample_valid_df: pd.DataFrame) -> None:
    """Verify scaler was fitted ONLY on X_train and not test or total dataset."""
    clean_df, _ = validate_and_clean_data(sample_valid_df)
    res = split_and_scale_data(clean_df, test_size=0.2, random_state=42)
    leakage = verify_data_leakage(res)

    assert leakage["scaler_fitted_only_train"] is True
    assert leakage["id_excluded"] is True
    assert leakage["target_excluded"] is True
    assert leakage["train_test_no_overlap"] is True
    assert res["scaler"].n_samples_seen_ == len(res["X_train"])
    assert np.allclose(res["scaler"].mean_, res["X_train"].mean().values)
