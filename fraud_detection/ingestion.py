from pathlib import Path

import pandas as pd

from .schemas import Transaction


def load_transactions(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if source.suffix.lower() == ".parquet":
        frame = pd.read_parquet(source)
    elif source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    else:
        raise ValueError("Only CSV and Parquet files are supported")
    if "transaction_id" not in frame or frame["transaction_id"].duplicated().any():
        raise ValueError("transaction_id is required and must be unique")
    return clean_transactions(frame)


def clean_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce", utc=True)
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    result["avg_monthly_spend"] = pd.to_numeric(result["avg_monthly_spend"], errors="coerce")
    result = result.dropna(subset=["timestamp", "amount", "avg_monthly_spend"])
    result = result[(result["amount"] > 0) & (result["avg_monthly_spend"] >= 0)]
    for column in ("is_foreign_transaction",):
        result[column] = result[column].astype(bool)
    return result.reset_index(drop=True)


def validate_transaction(payload: dict) -> Transaction:
    return Transaction.model_validate(payload)
