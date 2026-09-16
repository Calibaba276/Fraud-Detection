from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ScoreResponse, Transaction, TransactionRecord, VerificationRequest
from .persistence import create_store
from .service import FraudService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fraud_detection")
app = FastAPI(title="Banking Fraud Detection API", version="0.1.0")
_service: FraudService | None = None
_service_lock = Lock()
allowed_origins = [value.strip() for value in os.getenv("FRAUD_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173").split(",") if value.strip()]
if allowed_origins:
    app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key", "X-Account-ID"])


def get_service() -> FraudService:
    with _service_lock:
        return _initialize_service()


def _initialize_service() -> FraudService:
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
    try:
        result = get_service().score(transaction)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if result.decision != "approve":
        logger.warning("fraud_alert transaction_id=%s decision=%s risk_score=%s", result.transaction_id, result.decision, result.risk_score)
    return result


@app.get("/transactions", response_model=list[TransactionRecord])
def transactions(x_api_key: str | None = Header(default=None), limit: int = Query(default=500, ge=1, le=1000)):
    _check_api_key(x_api_key)
    return get_service().recent_transactions(limit)


@app.get("/system")
def system_info(x_api_key: str | None = Header(default=None)) -> dict:
    _check_api_key(x_api_key)
    return get_service().system_info()


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
