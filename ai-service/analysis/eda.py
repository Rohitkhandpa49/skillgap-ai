import pandas as pd

def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    return df.describe(include="all").transpose()

def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.isna()
        .sum()
        .rename("missing_count")
        .to_frame()
        .assign(missing_percentage=lambda x: x["missing_count"] / len(df) * 100)
    )
