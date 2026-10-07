from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

def load_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)

def profile_dataframe(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }
