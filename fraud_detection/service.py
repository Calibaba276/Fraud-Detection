from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from .authorization import InMemoryPaymentAuthorizer, PaymentAuthorizer
from .features import engineer_features
from .model import load_model, predict_probability
from .persistence import get_account_history, get_prediction, get_recent_predictions, record_prediction, update_workflow_status
from .risk import RiskConfig, aggregate_risk, decide
from .rules import RuleEngine, load_rule_config
from .schemas import RuleMatch, ScoreResponse, Transaction, TransactionRecord


class FraudService:
    def __init__(self, model_path="artifacts/model.joblib", rules_path="rules.yaml", session_factory=None, authorizer: PaymentAuthorizer | None = None):
        self.bundle = load_model(model_path)
        config = load_rule_config(rules_path)
        self.rules = RuleEngine(config)
        self.risk_config = RiskConfig(**config["decision"])
        self.session_factory = session_factory
        self.authorizer = authorizer or InMemoryPaymentAuthorizer()
        self._results: dict[str, ScoreResponse] = {}
        self._history: list[dict] = []
        self._transactions: dict[str, Transaction] = {}

    def score(self, transaction: Transaction, context: dict | None = None) -> ScoreResponse:
        if transaction.transaction_id in self._results or (self.session_factory and get_prediction(self.session_factory, transaction.transaction_id)):
            raise ValueError("This transaction ID has already been scored. Use a new transaction ID.")
        started = time.perf_counter()
        frame = pd.DataFrame([transaction.model_dump()])
        history = self._load_history(transaction)
        features = engineer_features(frame, history=history if not history.empty else None)
        probability = predict_probability(self.bundle, features)
        feature_context = {"velocity_1h": int(features.iloc[0]["velocity_1h"]), **(context or {})}
        matches = self.rules.evaluate(transaction, feature_context)
        risk_score = aggregate_risk(probability, matches)
        decision = decide(risk_score, self.risk_config)
        workflow_status = {"approve": "approved", "review": "pending_verification", "decline": "blocked"}[decision]
        next_action = {"approve": "none", "review": "verify_transaction", "decline": "contact_support"}[decision]
        user_message = {"approve": "Transaction approved.", "review": "This transaction is on hold. Please confirm whether you made it.", "decline": "This transaction was stopped for your protection. Contact support if you believe it is legitimate."}[decision]
        authorization_status = self.authorizer.authorize(transaction, decision)
        result = ScoreResponse(transaction_id=transaction.transaction_id, risk_score=risk_score, decision=decision, rule_matches=matches, model_probability=probability, model_version=self.bundle["version"], processing_ms=(time.perf_counter() - started) * 1000, workflow_status=workflow_status, next_action=next_action, user_message=user_message, authorization_status=authorization_status)
        self._results[result.transaction_id] = result
        self._transactions[result.transaction_id] = transaction
        self._history.append(transaction.model_dump(mode="json"))
        if self.session_factory:
            record_prediction(self.session_factory, result, transaction)
        return result

    def recent_transactions(self, limit: int = 500) -> list[TransactionRecord]:
        if self.session_factory:
            return [TransactionRecord(transaction=Transaction.model_validate(row.transaction_data), result=self._result_from_record(row))
                    for row in get_recent_predictions(self.session_factory, limit) if row.transaction_data]
        ids = list(reversed(self._results))[:limit]
        return [TransactionRecord(transaction=self._transactions[key], result=self._results[key]) for key in ids]

    def system_info(self) -> dict:
        return {
            "model_version": self.bundle["version"],
            "model_name": type(self.bundle["model"]).__name__,
            "feature_count": len(self.bundle["features"]),
            "review_threshold": self.risk_config.review_threshold,
            "decline_threshold": self.risk_config.decline_threshold,
            "model_weight": 0.7,
            "rule_weight": 0.3,
            "persistence": "database" if self.session_factory else "memory",
            "rules": [{"id": key, "enabled": value.get("enabled", False)} for key, value in self.rules.config.items() if key != "decision"],
        }

    def _load_history(self, transaction: Transaction) -> pd.DataFrame:
        if self.session_factory:
            rows = get_account_history(self.session_factory, transaction.account_id)
        else:
            rows = [row for row in self._history if row.get("account_id") == transaction.account_id]
        return pd.DataFrame(rows)

    def verify(self, transaction_id: str, confirmed: bool, account_id: str | None = None) -> ScoreResponse:
        result = self._results.get(transaction_id)
        transaction = getattr(self, "_transactions", {}).get(transaction_id)
        if result is None and self.session_factory:
            record = get_prediction(self.session_factory, transaction_id)
            if record is not None and account_id is not None and record.account_id != account_id:
                raise PermissionError("Transaction does not belong to this account")
            result = self._result_from_record(record)
            if record is not None and record.transaction_data:
                transaction = Transaction.model_validate(record.transaction_data)
        if result is None:
            raise KeyError(transaction_id)
        if transaction is not None and account_id is not None and transaction.account_id != account_id:
            raise PermissionError("Transaction does not belong to this account")
        if result.workflow_status != "pending_verification":
            raise ValueError("Only transactions pending verification can be confirmed")
        if confirmed:
            updated = result.model_copy(update={"workflow_status": "verification_received", "next_action": "manual_review", "user_message": "Your confirmation was received. The transaction remains on hold pending review."})
        else:
            if transaction is None:
                raise ValueError("Transaction details are unavailable; contact support to block this payment")
            authorization_status = self.authorizer.authorize(transaction, "decline")
            updated = result.model_copy(update={"workflow_status": "blocked", "authorization_status": authorization_status, "next_action": "contact_support", "user_message": "The transaction was blocked. Contact support if you need help securing your account."})
        self._results[transaction_id] = updated
        if self.session_factory:
            update_workflow_status(self.session_factory, transaction_id, updated)
        return updated

    @staticmethod
    def _result_from_record(record) -> ScoreResponse | None:
        if record is None:
            return None
        return ScoreResponse(transaction_id=record.transaction_id, risk_score=record.risk_score, decision=record.decision, rule_matches=[RuleMatch.model_validate(match) for match in record.rule_matches or []], model_probability=record.model_probability, model_version=record.model_version, processing_ms=record.processing_ms, workflow_status=record.workflow_status, next_action=record.next_action, user_message=record.user_message, authorization_status=record.authorization_status)
