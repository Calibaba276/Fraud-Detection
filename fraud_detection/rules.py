from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .schemas import RuleMatch, Transaction


def load_rule_config(path: str | Path = "rules.yaml") -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class RuleEngine:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def evaluate(self, transaction: Transaction, context: dict[str, Any] | None = None) -> list[RuleMatch]:
        context = context or {}
        matches: list[RuleMatch] = []
        amount_config = self.config["abnormal_amount"]
        if amount_config["enabled"] and transaction.amount > transaction.avg_monthly_spend * amount_config["ratio"]:
            matches.append(RuleMatch(rule_id="abnormal_amount", reason="Amount exceeds configured spend ratio", severity=amount_config["severity"]))
        activity = self.config["excessive_activity"]
        if activity["enabled"] and context.get("velocity_1h", 0) >= activity["max_transactions"]:
            matches.append(RuleMatch(rule_id="excessive_activity", reason="Account activity exceeds configured hourly limit", severity=activity["severity"]))
        blocklists = self.config["blocklists"]
        if blocklists["enabled"] and (transaction.merchant_id in blocklists["merchants"] or transaction.device_id in blocklists["devices"] or transaction.ip_address in blocklists["ip_addresses"]):
            matches.append(RuleMatch(rule_id="blocklist", reason="Entity is present on a configured blocklist", severity=blocklists["severity"]))
        travel = self.config["impossible_travel"]
        distance = context.get("distance_km", 0)
        minutes = context.get("minutes_since_last_location", 0)
        impossible_travel = context.get("impossible_travel", False) or (distance >= travel.get("minimum_distance_km", float("inf")) and minutes < travel.get("minimum_minutes", 0))
        if travel["enabled"] and impossible_travel:
            matches.append(RuleMatch(rule_id="impossible_travel", reason="Recent account activity implies impossible travel", severity=travel["severity"]))
        return matches
