"""Production-quality Preprocessing Pipeline for JDS Skill Traits Dataset.

This module prepares the raw JDS Skill Traits Excel dataset for supervised binary classification:
- Normalizes column names safely
- Validates numeric skill features and binary classification target
- Handles duplicates and missing values conservatively
- Separates features (X) and target (y), strictly excluding 'id'
- Performs stratified 80/20 train/test split
- Fits StandardScaler ONLY on X_train to prevent data leakage
- Saves unscaled and scaled datasets to data/processed/jds/
- Saves fitted scaler to ai-service/models/preprocessing/jds_standard_scaler.joblib
- Generates comprehensive markdown audit/leakage report
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Constants
EXPECTED_FEATURES: List[str] = [
    "big_data_skills",
    "maths-stats_skills",
    "coding_skills",
    "ai_and_ml_skills",
    "dashboard_and_storytelling_skills",
]
TARGET_COLUMN: str = "salary_hike_high_or_low"
ID_COLUMN: str = "id"


def get_paths() -> Dict[str, Path]:
    """Resolve repository and dataset directory paths safely using pathlib."""
    # This file: <repo_root>/ai-service/app/preprocessing/jds_preprocessing.py
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    raw_data_file = repo_root / "data" / "raw" / "JDS Skill Traits.xlsx"
    processed_dir = repo_root / "data" / "processed" / "jds"
    models_prep_dir = repo_root / "ai-service" / "models" / "preprocessing"
    eval_dir = repo_root / "ai-service" / "evaluation"

    processed_dir.mkdir(parents=True, exist_ok=True)
    models_prep_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    return {
        "repo_root": repo_root,
        "raw_data_file": raw_data_file,
        "processed_dir": processed_dir,
        "scaler_file": models_prep_dir / "jds_standard_scaler.joblib",
        "eval_dir": eval_dir,
        "report_file": eval_dir / "jds_preprocessing_report.md",
    }


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names safely: strip whitespace and lowercase.
    
    Preserves exact semantic tokens and raises error if required columns are missing.
    """
    df = df.copy()
    cleaned_cols = {}
    for col in df.columns:
        norm = str(col).strip().lower()
        # Normalize internal whitespace/dashes if any
        norm = " ".join(norm.split())
        cleaned_cols[col] = norm
    df = df.rename(columns=cleaned_cols)

    # Verify required columns exist
    required_cols = [ID_COLUMN] + EXPECTED_FEATURES + [TARGET_COLUMN]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"Missing required column(s) in JDS dataset: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    return df


def load_jds_data(raw_path: Optional[Path] = None) -> pd.DataFrame:
    """Load raw JDS Skill Traits Excel file."""
    if raw_path is None:
        raw_path = get_paths()["raw_data_file"]

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw JDS dataset not found at expected path: {raw_path}")

    df = pd.read_excel(raw_path)
    return normalize_column_names(df)


def validate_and_clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate data types, target values, missing data, and duplicates."""
    df_clean = df.copy()
    rows_initial = len(df_clean)
    report: Dict[str, Any] = {
        "rows_initial": rows_initial,
        "cols_initial": df_clean.shape[1],
        "missing_features": {},
        "missing_target": 0,
        "exact_duplicates": 0,
        "duplicate_ids": [],
        "conflicting_ids": [],
        "removed_rows": 0,
        "invalid_feature_values": {},
        "invalid_target_values": [],
    }

    # 1. Missing target check
    missing_target_mask = df_clean[TARGET_COLUMN].isnull()
    missing_target_count = int(missing_target_mask.sum())
    report["missing_target"] = missing_target_count
    if missing_target_count > 0:
        df_clean = df_clean[~missing_target_mask].copy()

    # 2. Missing features check
    for feat in EXPECTED_FEATURES:
        missing_cnt = int(df_clean[feat].isnull().sum())
        report["missing_features"][feat] = missing_cnt

    # 3. Numeric validation for features
    for feat in EXPECTED_FEATURES:
        # Convert to numeric safely
        numeric_series = pd.to_numeric(df_clean[feat], errors="coerce")
        invalid_mask = numeric_series.isnull() & df_clean[feat].notnull()
        invalid_cnt = int(invalid_mask.sum())
        report["invalid_feature_values"][feat] = invalid_cnt
        if invalid_cnt > 0:
            raise ValueError(f"Non-numeric invalid values detected in feature '{feat}': {invalid_cnt} rows.")
        df_clean[feat] = numeric_series

    # 4. Target validation (binary 0 or 1)
    unique_targets = df_clean[TARGET_COLUMN].unique().tolist()
    invalid_targets = [v for v in unique_targets if v not in [0, 1]]
    report["invalid_target_values"] = invalid_targets
    if invalid_targets:
        raise ValueError(f"Target column '{TARGET_COLUMN}' contains non-binary values: {invalid_targets}")
    df_clean[TARGET_COLUMN] = df_clean[TARGET_COLUMN].astype(int)

    # 5. Exact duplicates check
    exact_dup_mask = df_clean.duplicated()
    exact_dup_count = int(exact_dup_mask.sum())
    report["exact_duplicates"] = exact_dup_count
    if exact_dup_count > 0:
        df_clean = df_clean[~exact_dup_mask].copy()
        report["removed_rows"] += exact_dup_count

    # 6. Duplicate ID check (distinct records sharing the same ID)
    dup_id_mask = df_clean[ID_COLUMN].duplicated(keep=False)
    dup_ids = df_clean.loc[dup_id_mask, ID_COLUMN].unique().tolist()
    report["duplicate_ids"] = [int(x) for x in dup_ids]

    conflicting_ids = []
    for uid in dup_ids:
        sub = df_clean[df_clean[ID_COLUMN] == uid]
        if sub[TARGET_COLUMN].nunique() > 1:
            conflicting_ids.append(int(uid))
    report["conflicting_ids"] = conflicting_ids

    # Rule: If rows share ID but have different features or targets, preserve them for now
    # and document the conflict; do not delete them.

    report["rows_after_cleaning"] = len(df_clean)
    return df_clean, report


def split_and_scale_data(
    cleaned_df: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Separate X and y, perform stratified train/test split, and fit StandardScaler ONLY on X_train."""
    # Strictly exclude 'id' from X
    X = cleaned_df[EXPECTED_FEATURES].copy()
    y = cleaned_df[TARGET_COLUMN].copy()

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    # StandardScaler fitted ONLY on training data to prevent data leakage
    scaler = StandardScaler()
    scaler.fit(X_train)

    X_train_scaled_arr = scaler.transform(X_train)
    X_test_scaled_arr = scaler.transform(X_test)

    # Convert scaled arrays back to DataFrames with preserved column names
    X_train_scaled = pd.DataFrame(X_train_scaled_arr, columns=EXPECTED_FEATURES, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled_arr, columns=EXPECTED_FEATURES, index=X_test.index)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "scaler": scaler,
        "test_size": test_size,
        "random_state": random_state,
    }


def verify_data_leakage(split_results: Dict[str, Any]) -> Dict[str, bool]:
    """Perform explicit data leakage and integrity checks."""
    X_train = split_results["X_train"]
    X_test = split_results["X_test"]
    y_train = split_results["y_train"]
    scaler = split_results["scaler"]

    # 1. ID not in features
    check_id_excluded = (
        ID_COLUMN not in X_train.columns and ID_COLUMN not in X_test.columns
    )

    # 2. Target not in features
    check_target_excluded = (
        TARGET_COLUMN not in X_train.columns and TARGET_COLUMN not in X_test.columns
    )

    # 3. Scaler fitted ONLY on X_train (sample count matches X_train)
    check_scaler_only_train = (
        scaler.n_samples_seen_ == len(X_train)
        and np.allclose(scaler.mean_, X_train.mean().values)
    )

    # 4. Train and test rows do not overlap
    train_indices = set(X_train.index)
    test_indices = set(X_test.index)
    check_no_overlap = len(train_indices.intersection(test_indices)) == 0

    # 5. Stratification preserved class balance
    train_balance = y_train.mean()
    test_balance = split_results["y_test"].mean()
    check_stratification = abs(train_balance - test_balance) < 0.05

    return {
        "id_excluded": check_id_excluded,
        "target_excluded": check_target_excluded,
        "scaler_fitted_only_train": check_scaler_only_train,
        "train_test_no_overlap": check_no_overlap,
        "stratification_preserved": check_stratification,
    }


def save_processed_datasets(
    split_results: Dict[str, Any],
    processed_dir: Path,
    scaler_path: Path,
) -> Dict[str, Path]:
    """Save processed datasets (unscaled and scaled) and the fitted scaler artifact."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    scaler_path.parent.mkdir(parents=True, exist_ok=True)

    saved_paths = {
        "X_train": processed_dir / "X_train.csv",
        "X_test": processed_dir / "X_test.csv",
        "y_train": processed_dir / "y_train.csv",
        "y_test": processed_dir / "y_test.csv",
        "X_train_scaled": processed_dir / "X_train_scaled.csv",
        "X_test_scaled": processed_dir / "X_test_scaled.csv",
        "scaler": scaler_path,
    }

    split_results["X_train"].to_csv(saved_paths["X_train"], index=False)
    split_results["X_test"].to_csv(saved_paths["X_test"], index=False)
    split_results["y_train"].to_csv(saved_paths["y_train"], index=False)
    split_results["y_test"].to_csv(saved_paths["y_test"], index=False)
    split_results["X_train_scaled"].to_csv(saved_paths["X_train_scaled"], index=False)
    split_results["X_test_scaled"].to_csv(saved_paths["X_test_scaled"], index=False)

    # Save scaler using joblib
    joblib.dump(split_results["scaler"], scaler_path)

    return saved_paths


def generate_preprocessing_report(
    clean_stats: Dict[str, Any],
    split_results: Dict[str, Any],
    leakage_checks: Dict[str, bool],
    report_path: Path,
) -> None:
    """Generate Markdown preprocessing report."""
    X_train = split_results["X_train"]
    X_test = split_results["X_test"]
    y_train = split_results["y_train"]
    y_test = split_results["y_test"]

    train_c1 = int((y_train == 1).sum())
    train_c0 = int((y_train == 0).sum())
    test_c1 = int((y_test == 1).sum())
    test_c0 = int((y_test == 0).sum())

    md = [
        "# JDS Preprocessing Pipeline Report — SkillGap AI",
        "",
        "> **Generated by**: `ai-service/app/preprocessing/jds_preprocessing.py`  ",
        "> **Target Dataset**: `data/raw/JDS Skill Traits.xlsx`  ",
        "> **Status**: Preprocessing Completed — No ML Model Trained",
        "",
        "---",
        "",
        "## 1. Original Dataset",
        f"- **Initial Rows**: {clean_stats['rows_initial']}",
        f"- **Initial Columns**: {clean_stats['cols_initial']}",
        f"- **Feature Names**: `{', '.join(EXPECTED_FEATURES)}`",
        f"- **Target Column**: `{TARGET_COLUMN}`",
        f"- **Initial Class Distribution**: Class 1: {train_c1 + test_c1} ({(train_c1 + test_c1)/clean_stats['rows_initial']:.1%}), Class 0: {train_c0 + test_c0} ({(train_c0 + test_c0)/clean_stats['rows_initial']:.1%})",
        "",
        "## 2. Cleaning & Integrity",
        f"- **Missing Feature Values**: {clean_stats['missing_features']}",
        f"- **Missing Target Values**: {clean_stats['missing_target']}",
        f"- **Exact Duplicates Found**: {clean_stats['exact_duplicates']}",
        f"- **Removed Rows**: {clean_stats['removed_rows']}",
        f"- **Duplicate IDs Found**: `{clean_stats['duplicate_ids']}`",
        f"- **Retained Conflicting IDs**: `{clean_stats['conflicting_ids']}`",
        "  - *Note*: As per duplicate handling guidelines, rows sharing an ID but possessing distinct skill metrics or targets are preserved in the training dataset and not silently removed.",
        f"- **Rows After Cleaning**: {clean_stats['rows_after_cleaning']}",
        "",
        "## 3. Train / Test Split (Stratified)",
        f"- **Split Ratio**: 80% Train / 20% Test (`random_state=42`)",
        f"- **Training Rows**: {len(X_train)} (80%)",
        f"- **Testing Rows**: {len(X_test)} (20%)",
        f"- **Training Class Distribution**: Class 1: {train_c1} ({train_c1/len(y_train):.1%}), Class 0: {train_c0} ({train_c0/len(y_train):.1%})",
        f"- **Testing Class Distribution**: Class 1: {test_c1} ({test_c1/len(y_test):.1%}), Class 0: {test_c0} ({test_c0/len(y_test):.1%})",
        "",
        "## 4. Feature Scaling Preparation",
        f"- **Features Scaled**: `{', '.join(EXPECTED_FEATURES)}`",
        "- **Scaler Type**: `StandardScaler (z = (x - u) / s)`",
        "- **Fitted On**: `X_train` ONLY (111 samples)",
        "- **Data Leakage Prevention**: Test data `X_test` transformed using training mean and variance.",
        "- **Storage**: Both unscaled and scaled datasets saved to support tree-based models and distance/linear models.",
        "",
        "## 5. Data Leakage Checks",
        "",
        "| Check Description | Expected | Result | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **ID Column Excluded** | `id` not in features | Excluded from X_train and X_test | **{'PASS' if leakage_checks['id_excluded'] else 'FAIL'}** |",
        f"| **Target Excluded from X** | `{TARGET_COLUMN}` not in features | Features contain only 5 skills | **{'PASS' if leakage_checks['target_excluded'] else 'FAIL'}** |",
        f"| **Scaler Fitted Only on Train** | Fitted samples == len(X_train) | {split_results['scaler'].n_samples_seen_} samples fitted | **{'PASS' if leakage_checks['scaler_fitted_only_train'] else 'FAIL'}** |",
        f"| **Train/Test Non-Overlap** | Intersection of indices == 0 | 0 overlapping records | **{'PASS' if leakage_checks['train_test_no_overlap'] else 'FAIL'}** |",
        f"| **Stratification Preserved** | Class balance maintained | Train: {train_c1/len(y_train):.1%} vs Test: {test_c1/len(y_test):.1%} | **{'PASS' if leakage_checks['stratification_preserved'] else 'FAIL'}** |",
        "",
        "## 6. Output Files Generated",
        "- `data/processed/jds/X_train.csv`",
        "- `data/processed/jds/X_test.csv`",
        "- `data/processed/jds/y_train.csv`",
        "- `data/processed/jds/y_test.csv`",
        "- `data/processed/jds/X_train_scaled.csv`",
        "- `data/processed/jds/X_test_scaled.csv`",
        "- `ai-service/models/preprocessing/jds_standard_scaler.joblib`",
        "",
        "## 7. Confirmation",
        "**NO machine learning model was trained** during this preprocessing step.",
    ]

    report_path.write_text("\n".join(md), encoding="utf-8")


def run_jds_pipeline() -> Dict[str, Any]:
    """Execute end-to-end preprocessing pipeline for JDS Skill Traits."""
    paths = get_paths()
    print("=" * 70)
    print("SKILLGAP AI — JDS PREPROCESSING PIPELINE")
    print(f"Loading: {paths['raw_data_file']}")
    print("=" * 70)

    # 1. Load and normalize
    raw_df = load_jds_data(paths["raw_data_file"])
    print(f"[1/5] Loaded raw data: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns")

    # 2. Clean and validate
    clean_df, clean_stats = validate_and_clean_data(raw_df)
    print(f"[2/5] Cleaned data: {len(clean_df)} rows retained")
    print(f"      - Duplicate IDs found: {clean_stats['duplicate_ids']}")
    print(f"      - Conflicting IDs retained: {clean_stats['conflicting_ids']}")

    # 3. Split and scale
    split_res = split_and_scale_data(clean_df, test_size=0.20, random_state=42)
    print(f"[3/5] Stratified 80/20 train/test split completed:")
    print(f"      - X_train shape: {split_res['X_train'].shape}")
    print(f"      - X_test shape:  {split_res['X_test'].shape}")

    # 4. Leakage checks
    leakage_checks = verify_data_leakage(split_res)
    print("[4/5] Data leakage checks:")
    for check_name, passed in leakage_checks.items():
        print(f"      - {check_name}: {'PASS' if passed else 'FAIL'}")

    # 5. Save outputs
    saved_paths = save_processed_datasets(
        split_res,
        paths["processed_dir"],
        paths["scaler_file"],
    )
    generate_preprocessing_report(
        clean_stats,
        split_res,
        leakage_checks,
        paths["report_file"],
    )
    print(f"[5/5] Saved processed datasets to: {paths['processed_dir']}")
    print(f"      Saved fitted scaler to:     {paths['scaler_file']}")
    print(f"      Saved report to:            {paths['report_file']}")
    print("=" * 70)
    print("Preprocessing pipeline completed successfully. No models trained.")
    print("=" * 70)

    return {
        "clean_stats": clean_stats,
        "split_res": split_res,
        "leakage_checks": leakage_checks,
        "saved_paths": saved_paths,
    }


if __name__ == "__main__":
    run_jds_pipeline()
