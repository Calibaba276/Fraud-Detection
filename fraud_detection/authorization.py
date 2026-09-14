from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from .schemas import Transaction

AuthorizationStatus = Literal["authorized", "held", "blocked"]


class PaymentAuthorizer(Protocol):
    def authorize(self, transaction: Transaction, decision: str) -> AuthorizationStatus:
        """Authorize, hold, or block a transaction at the payment boundary."""


@dataclass
class InMemoryPaymentAuthorizer:
    statuses: dict[str, AuthorizationStatus]

    def __init__(self) -> None:
        self.statuses = {}

    def authorize(self, transaction: Transaction, decision: str) -> AuthorizationStatus:
        status: AuthorizationStatus = {
            "approve": "authorized",
            "review": "held",
            "decline": "blocked",
        }[decision]
        self.statuses[transaction.transaction_id] = status
        return status