from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from fraud_detection import api
from fraud_detection.features import FEATURE_COLUMNS, engineer_features
from fraud_detection.persistence import create_store
from fraud_detection.schemas import Transaction
from fraud_detection.service import FraudService


class ReviewModel:
    def predict_proba(self, frame):
        return np.array([[0.4, 0.6] for _ in range(len(frame))])


@pytest.fixture
def transaction():
    return Transaction(transaction_id="tx-1", timestamp="2026-01-01T12:00:00Z", account_id="acct-1", card_id="card-1", amount=50, currency="USD", merchant_id="shop-1", merchant_category="grocery", transaction_type="purchase", location="US", device_id="device-1", ip_address="127.0.0.1", account_age_days=365, avg_monthly_spend=1000, is_foreign_transaction=False)


@pytest.fixture
def service_factory(monkeypatch):
    monkeypatch.setattr("fraud_detection.service.load_model", lambda _: {"model": ReviewModel(), "features": FEATURE_COLUMNS, "version": "test"})
    def make(store=None):
        return FraudService("unused.joblib", Path(__file__).parents[1] / "rules.yaml", session_factory=store)
    return make


def test_features_with_history_exclude_future_and_current(transaction):
    current = transaction.model_dump()
    history = [{**current, "transaction_id": "past", "timestamp": "2026-01-01T11:30:00Z", "amount": 20},
               {**current, "transaction_id": "future", "timestamp": "2026-01-01T13:00:00Z", "amount": 900}]
    result = engineer_features(pd.DataFrame([current]), pd.DataFrame(history)).iloc[0]
    assert result.velocity_1h == 1
    assert result.amount_24h == 20


def test_repeated_account_scoring_and_unique_ids(service_factory, transaction):
    service = service_factory()
    service.score(transaction)
    second = transaction.model_copy(update={"transaction_id": "tx-2", "timestamp": pd.Timestamp("2026-01-01T12:01:00Z").to_pydatetime()})
    assert service.score(second).decision == "review"
    assert [row.transaction.transaction_id for row in service.recent_transactions()] == ["tx-2", "tx-1"]
    with pytest.raises(ValueError, match="already been scored"):
        service.score(transaction)


@pytest.mark.parametrize("confirmed,workflow,authorization", [(True, "verification_received", "held"), (False, "blocked", "blocked")])
@pytest.mark.parametrize("restart", [False, True])
def test_verification_updates_payment_and_persisted_history(service_factory, transaction, tmp_path, confirmed, workflow, authorization, restart):
    store = create_store(f"sqlite:///{tmp_path / 'test.db'}")
    service = service_factory(store)
    service.score(transaction)
    if restart:
        service = service_factory(store)
    with pytest.raises(PermissionError):
        service.verify("tx-1", confirmed, "wrong-account")
    result = service.verify("tx-1", confirmed, "acct-1")
    assert result.workflow_status == workflow
    assert result.authorization_status == authorization
    assert service_factory(store).recent_transactions()[0].result == result
    with pytest.raises(ValueError, match="Only transactions pending"):
        service.verify("tx-1", confirmed, "acct-1")


def test_dashboard_api_auth_history_validation_and_verification(monkeypatch, service_factory, transaction):
    monkeypatch.setenv("FRAUD_API_KEY", "test-key")
    monkeypatch.setattr(api, "_service", service_factory())
    client = TestClient(api.app)
    headers = {"X-API-Key": "test-key"}
    for path in ["/transactions", "/system"]:
        assert client.get(path).status_code == 401
        assert client.get(path, headers=headers).status_code == 200
    assert client.get("/transactions", headers=headers).json() == []
    assert client.get("/transactions?limit=1001", headers=headers).status_code == 422
    assert client.post("/score", json=transaction.model_dump(mode="json"), headers=headers).status_code == 200
    assert client.post("/score", json=transaction.model_dump(mode="json"), headers=headers).status_code == 409
    assert client.get("/transactions", headers=headers).json()[0]["transaction"]["account_id"] == "acct-1"
    assert client.get("/system", headers=headers).json()["review_threshold"] == 0.35
    path = "/transactions/tx-1/verify"
    assert client.post(path, json={"confirmed": False}, headers=headers).status_code == 401
    assert client.post(path, json={"confirmed": False}, headers={**headers, "X-Account-ID": "wrong"}).status_code == 403
    result = client.post(path, json={"confirmed": False}, headers={**headers, "X-Account-ID": "acct-1"})
    assert result.json()["authorization_status"] == "blocked"


def test_missing_model_is_actionable(monkeypatch, tmp_path):
    monkeypatch.delenv("FRAUD_API_KEY", raising=False)
    monkeypatch.setattr(api, "_service", None)
    monkeypatch.setenv("FRAUD_MODEL_PATH", str(tmp_path / "missing.joblib"))
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    assert client.get("/system").status_code == 503


class AlignmentModel:
    def __init__(self, **kwargs):
        pass

    def fit(self, frame, labels):
        assert np.array_equal(labels.to_numpy(), (frame.amount.to_numpy() % 5 == 0).astype(int))

    def predict_proba(self, frame):
        probability = np.where(frame.amount.to_numpy() % 5 == 0, 0.9, 0.1)
        return np.column_stack([1 - probability, probability])


def test_training_and_evaluation_labels_follow_sorted_features(monkeypatch, tmp_path):
    from fraud_detection.generator import generate_transactions
    from fraud_detection.model import train_model

    data = generate_transactions(200)
    data["amount"] = np.arange(1, 201)
    data["is_fraud"] = (data.amount % 5 == 0).astype(int)
    monkeypatch.setattr("fraud_detection.model.HistGradientBoostingClassifier", AlignmentModel)
    metrics = train_model(data, tmp_path / "model.joblib")
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["roc_auc"] == 1.0


def test_service_initializes_once_for_parallel_dashboard_requests(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time

    model = tmp_path / "model.joblib"
    model.touch()
    monkeypatch.setenv("FRAUD_MODEL_PATH", str(model))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(api, "_service", None)
    instances = []
    def create(*args, **kwargs):
        time.sleep(0.02)
        instance = object()
        instances.append(instance)
        return instance
    monkeypatch.setattr(api, "FraudService", create)
    with ThreadPoolExecutor(max_workers=4) as pool:
        services = list(pool.map(lambda _: api.get_service(), range(8)))
    assert len(instances) == 1
    assert all(service is instances[0] for service in services)
