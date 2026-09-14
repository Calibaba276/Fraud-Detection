from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException

from .schemas import ScoreResponse, Transaction, VerificationRequest
from .persistence import create_store
from .service import FraudService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fraud_detection")
app = FastAPI(title="Banking Fraud Detection API", version="0.1.0")
_service: FraudService | None = None


def get_service() -> FraudService:
    global _service
    if _service is None:
        model_path = os.getenv("FRAUD_MODEL_PATH", "artifacts/model.joblib")
        rules_path = os.getenv("FRAUD_RULES_PATH", "rules.yaml")
        if not Path(model_path).exists():
            raise HTTPException(status_code=503, detail="Model artifact is not available; run fraud-train first")
        database_url = os.getenv("DATABASE_URL")
        session_factory = create_store(database_url) if database_url else None
        _service = FraudService(model_path, rules_path, session_factory=session_factory)
    return _service


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    get_service()
    return {"status": "ready"}


@app.post("/score", response_model=ScoreResponse)
def score(transaction: Transaction, x_api_key: str | None = Header(default=None)) -> ScoreResponse:
    _check_api_key(x_api_key)
    result = get_service().score(transaction)
    if result.decision != "approve":
        logger.warning("fraud_alert transaction_id=%s decision=%s risk_score=%s", result.transaction_id, result.decision, result.risk_score)
    return result


@app.post("/transactions/{transaction_id}/verify", response_model=ScoreResponse)
def verify_transaction(transaction_id: str, request: VerificationRequest, x_api_key: str | None = Header(default=None), x_account_id: str | None = Header(default=None)) -> ScoreResponse:
    _check_api_key(x_api_key)
    if not x_account_id:
        raise HTTPException(status_code=401, detail="Account identity required")
    try:
        return get_service().verify(transaction_id, request.confirmed, x_account_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Transaction was not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


def _check_api_key(value: str | None) -> None:
    expected = os.getenv("FRAUD_API_KEY")
    if expected and value != expected:
        raise HTTPException(status_code=401, detail="Valid API key required")
