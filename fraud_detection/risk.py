from __future__ import annotations

from dataclasses import dataclass

from .schemas import Decision, RuleMatch


@dataclass(frozen=True)
class RiskConfig:
    review_threshold: float = 0.35
    decline_threshold: float = 0.75


def aggregate_risk(model_probability: float, matches: list[RuleMatch]) -> float:
    rule_signal = max((match.severity for match in matches), default=0.0)
    return round(min(1.0, 0.7 * model_probability + 0.3 * rule_signal), 6)


def decide(risk_score: float, config: RiskConfig) -> Decision:
    if risk_score >= config.decline_threshold:
        return "decline"
    if risk_score >= config.review_threshold:
        return "review"
    return "approve"
