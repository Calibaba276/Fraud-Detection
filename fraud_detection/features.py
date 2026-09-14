from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "amount", "account_age_days", "avg_monthly_spend", "is_foreign_transaction",
    "velocity_1h", "velocity_24h", "velocity_7d", "amount_24h",
    "amount_ratio", "hour", "day_of_week", "is_weekend", "is_night",
    "merchant_frequency", "merchant_fraud_rate", "category_fraud_rate",
]


def engineer_features(frame: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.DataFrame:
    current = frame.copy()
    current["timestamp"] = pd.to_datetime(current["timestamp"], utc=True)
    current = current.sort_values(["account_id", "timestamp", "transaction_id"]).reset_index(drop=True)
    reference = (history if history is not None else current).copy()
    reference["timestamp"] = pd.to_datetime(reference["timestamp"], utc=True)
    fraud_rates = _target_rate(current, reference, "merchant_id", leave_one_out=history is None)
    category_rates = _target_rate(current, reference, "merchant_category", leave_one_out=history is None)
    rolling_source = pd.concat([reference, current], ignore_index=True) if history is not None else current
    current["velocity_1h"] = _historical_values(current, rolling_source, _rolling_count, "1h")
    current["velocity_24h"] = _historical_values(current, rolling_source, _rolling_count, "24h")
    current["velocity_7d"] = _historical_values(current, rolling_source, _rolling_count, "7d")
    current["amount_24h"] = _historical_values(current, rolling_source, _rolling_sum, "24h")
    current["amount_ratio"] = current["amount"] / current["avg_monthly_spend"].clip(lower=1)
    current["hour"] = current["timestamp"].dt.hour
    current["day_of_week"] = current["timestamp"].dt.dayofweek
    current["is_weekend"] = (current["day_of_week"] >= 5).astype(int)
    current["is_night"] = current["hour"].isin([0, 1, 2, 3, 4, 5, 22, 23]).astype(int)
    frequencies = rolling_source.groupby("merchant_id").size()
    current["merchant_frequency"] = current["merchant_id"].map(frequencies).fillna(0).astype(float)
    current["merchant_fraud_rate"] = current["merchant_id"].map(fraud_rates).astype(float).fillna(0)
    current["category_fraud_rate"] = current["merchant_category"].map(category_rates).astype(float).fillna(0)
    return current


def _target_rate(current: pd.DataFrame, reference: pd.DataFrame, key: str, leave_one_out: bool = False) -> pd.Series:
    if "is_fraud" not in reference:
        return pd.Series(dtype=float)
    if leave_one_out:
        totals = current.groupby(key)["is_fraud"].transform("sum") - current["is_fraud"]
        counts = current.groupby(key)["is_fraud"].transform("count") - 1
        return pd.Series((totals / counts.replace(0, np.nan)).fillna(0).to_numpy(), index=current[key].index)
    return reference.groupby(key)["is_fraud"].mean()


def _historical_values(current: pd.DataFrame, source: pd.DataFrame, function, window: str) -> pd.Series:
    if source is current:
        return function(current, window)
    combined = source.copy()
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
    values = function(combined, window)
    history_length = len(source)
    return values.iloc[history_length:].reset_index(drop=True)


def _rolling_count(frame: pd.DataFrame, window: str) -> pd.Series:
    values = pd.Series(0.0, index=frame.index)
    for _, group in frame.groupby("account_id", sort=False):
        times = group["timestamp"].astype("int64").to_numpy()
        values.loc[group.index] = [((times < timestamp) & (times >= timestamp - pd.Timedelta(window).value)).sum() for timestamp in times]
    return values


def _rolling_sum(frame: pd.DataFrame, window: str) -> pd.Series:
    values = pd.Series(0.0, index=frame.index)
    for _, group in frame.groupby("account_id", sort=False):
        times = group["timestamp"].astype("int64").to_numpy()
        amounts = group["amount"].to_numpy()
        values.loc[group.index] = [amounts[(times < timestamp) & (times >= timestamp - pd.Timedelta(window).value)].sum() for timestamp in times]
    return values


def model_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    matrix = frame[FEATURE_COLUMNS].copy()
    matrix["is_foreign_transaction"] = matrix["is_foreign_transaction"].astype(int)
    return matrix.replace([np.inf, -np.inf], 0).fillna(0)
