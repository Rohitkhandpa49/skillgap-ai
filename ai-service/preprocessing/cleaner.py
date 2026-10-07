import pandas as pd

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = (
        result.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return result

def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)

def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_column_names(df)
    result = remove_duplicate_rows(result)
    return result
