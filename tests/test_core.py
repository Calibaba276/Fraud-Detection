import pandas as pd
from fastapi.testclient import TestClient

from fraud_detection.features import engineer_features
from fraud_detection.generator import generate_transactions
from fraud_detection.risk import RiskConfig, decide
from fraud_detection.rules import RuleEngine
from fraud_detection.schemas import ScoreResponse, Transaction


def test_generator_prevalence_and_features():
    data = generate_transactions(2_000, seed=3)
    features = engineer_features(data)
    assert 0.005 <= data.is_fraud.mean() <= 0.02
    assert {"velocity_1h", "amount_ratio", "is_night"}.issubset(features.columns)
    assert (features.velocity_1h >= 0).all()


def test_decision_thresholds():
    config = RiskConfig(0.3, 0.8)
    assert decide(0.2, config) == "approve"
    assert decide(0.5, config) == "review"
    assert decide(0.9, config) == "decline"


def test_review_verification_keeps_transaction_on_hold():
    from fraud_detection.service import FraudService

    service = FraudService.__new__(FraudService)
    service._results = {
        "tx-1": ScoreResponse(
            transaction_id="tx-1",
            risk_score=0.5,
            decision="review",
            rule_matches=[],
            model_probability=0.5,
            model_version="test",
            processing_ms=1,
            workflow_status="pending_verification",
            next_action="verify_transaction",
            user_message="Confirm this transaction.",
        )
    }
    service.session_factory = None

    result = service.verify("tx-1", confirmed=True)

    assert result.workflow_status == "verification_received"
    assert result.next_action == "manual_review"


def test_rules_are_configurable():
    transaction = Transaction(transaction_id="1", timestamp="2025-01-01T00:00:00Z", account_id="a", card_id="c", amount=1000, currency="usd", merchant_id="m", merchant_category="online", transaction_type="purchase", location="US", device_id="d", ip_address="1.1.1.1", account_age_days=10, avg_monthly_spend=100, is_foreign_transaction=True)
    rules = RuleEngine({"abnormal_amount": {"enabled": True, "ratio": 5, "severity": .6}, "excessive_activity": {"enabled": True, "max_transactions": 2, "severity": .5}, "blocklists": {"enabled": False, "merchants": [], "devices": [], "ip_addresses": [], "severity": 1}, "impossible_travel": {"enabled": False}})
    assert rules.evaluate(transaction, {"velocity_1h": 0})[0].rule_id == "abnormal_amount"


def test_api_validation():
    from fraud_detection.api import app
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/score", json={"amount": -1})
    assert response.status_code == 422
