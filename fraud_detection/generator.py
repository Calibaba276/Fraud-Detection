from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

LOCATIONS = ["US", "CA", "GB", "DE", "FR", "NG", "BR", "AU"]
CATEGORIES = ["grocery", "electronics", "travel", "fuel", "online", "restaurant", "cash"]


def generate_transactions(n: int = 20_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    accounts = rng.integers(100_000, 101_000, n)
    account_spend = rng.lognormal(7.4, 0.45, 1_000)
    account_age = rng.integers(30, 4_000, 1_000)
    fraud = (rng.random(n) < 0.012).astype(int)
    timestamps = pd.Timestamp(datetime.now(timezone.utc)) - pd.to_timedelta(rng.integers(0, 90 * 24 * 60, n), unit="m")
    account_index = accounts - 100_000
    amounts = rng.lognormal(3.8, 1.0, n)
    amounts *= np.where(fraud, rng.uniform(4, 12, n), 1)
    foreign = rng.random(n) < np.where(fraud, 0.65, 0.08)
    locations = rng.choice(LOCATIONS, n)
    suspicious_categories = rng.choice(["electronics", "online", "cash"], n)
    categories = np.where(fraud & (rng.random(n) < 0.7), suspicious_categories, rng.choice(CATEGORIES, n))
    return pd.DataFrame({
        "transaction_id": [f"txn_{i:08d}" for i in range(n)],
        "timestamp": timestamps,
        "account_id": [f"acct_{value}" for value in accounts],
        "card_id": [f"card_{value}" for value in rng.integers(1, 5_000, n)],
        "amount": amounts.round(2),
        "currency": np.where(foreign, "USD", "USD"),
        "merchant_id": [f"merchant_{value}" for value in rng.integers(1, 2_000, n)],
        "merchant_category": categories,
        "transaction_type": rng.choice(["purchase", "withdrawal", "transfer"], n, p=[.72, .12, .16]),
        "location": locations,
        "device_id": [f"device_{value}" for value in rng.integers(1, 3_000, n)],
        "ip_address": [f"10.{value // 256}.{value % 256}.1" for value in rng.integers(1, 65_000, n)],
        "account_age_days": account_age[account_index],
        "avg_monthly_spend": account_spend[account_index].round(2),
        "is_foreign_transaction": foreign,
        "is_fraud": fraud,
    })


def write_dataset(path: str | Path, n: int = 20_000, seed: int = 42) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = generate_transactions(n, seed)
    if output.suffix.lower() == ".parquet":
        data.to_parquet(output, index=False)
    else:
        data.to_csv(output, index=False)
    return output
