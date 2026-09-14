from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from math import isfinite

Decision = Literal["approve", "review", "decline"]
WorkflowStatus = Literal["approved", "pending_verification", "blocked", "verification_received"]
NextAction = Literal["none", "verify_transaction", "contact_support", "manual_review"]


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1)
    timestamp: datetime
    account_id: str = Field(min_length=1)
    card_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant_id: str = Field(min_length=1)
    merchant_category: str = Field(min_length=1)
    transaction_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    ip_address: str = Field(min_length=1)
    account_age_days: int = Field(ge=0)
    avg_monthly_spend: float = Field(ge=0)
    is_foreign_transaction: bool

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("amount", "avg_monthly_spend")
    @classmethod
    def validate_finite(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("value must be finite")
        return value


class RuleMatch(BaseModel):
    rule_id: str
    reason: str
    severity: float = Field(ge=0, le=1)


class ScoreResponse(BaseModel):
    transaction_id: str
    risk_score: float = Field(ge=0, le=1)
    decision: Decision
    rule_matches: list[RuleMatch]
    model_probability: float = Field(ge=0, le=1)
    model_version: str
    processing_ms: float
    workflow_status: WorkflowStatus
    next_action: NextAction
    user_message: str
    authorization_status: Literal["authorized", "held", "blocked"] = "authorized"


class VerificationRequest(BaseModel):
    confirmed: bool
