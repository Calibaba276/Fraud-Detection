from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    pass


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(128), index=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True, default="")
    transaction_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_score: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(16))
    model_probability: Mapped[float] = mapped_column(Float)
    rule_matches: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    workflow_status: Mapped[str] = mapped_column(String(32), default="approved")
    next_action: Mapped[str] = mapped_column(String(32), default="none")
    user_message: Mapped[str] = mapped_column(String(512), default="")
    authorization_status: Mapped[str] = mapped_column(String(16), default="authorized")
    model_version: Mapped[str] = mapped_column(String(64), default="unknown")
    processing_ms: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def create_store(url: str = "sqlite:///fraud_detection.db"):
    engine = create_engine(url, future=True, poolclass=NullPool if url.startswith("sqlite") else None)
    Base.metadata.create_all(engine)
    if engine.dialect.name == "sqlite":
        existing = {column["name"] for column in inspect(engine).get_columns("predictions")}
        additions = {
            "account_id": "VARCHAR(128) DEFAULT ''",
            "transaction_data": "JSON",
            "workflow_status": "VARCHAR(32) DEFAULT 'approved'",
            "next_action": "VARCHAR(32) DEFAULT 'none'",
            "user_message": "VARCHAR(512) DEFAULT ''",
            "authorization_status": "VARCHAR(16) DEFAULT 'authorized'",
            "model_version": "VARCHAR(64) DEFAULT 'unknown'",
            "processing_ms": "FLOAT DEFAULT 0",
        }
        with engine.begin() as connection:
            for name, definition in additions.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE predictions ADD COLUMN {name} {definition}"))
    return sessionmaker(bind=engine, expire_on_commit=False)


def record_prediction(session_factory, result, transaction) -> None:
    with session_factory() as session:
        session.add(Prediction(transaction_id=result.transaction_id, account_id=transaction.account_id, transaction_data=transaction.model_dump(mode="json"), risk_score=result.risk_score, decision=result.decision, model_probability=result.model_probability, rule_matches=[match.model_dump() for match in result.rule_matches], workflow_status=result.workflow_status, next_action=result.next_action, user_message=result.user_message, authorization_status=result.authorization_status, model_version=result.model_version, processing_ms=result.processing_ms))
        session.commit()


def get_prediction(session_factory, transaction_id: str):
    with session_factory() as session:
        return session.scalar(select(Prediction).where(Prediction.transaction_id == transaction_id).order_by(Prediction.created_at.desc()))


def get_recent_predictions(session_factory, limit: int = 500):
    with session_factory() as session:
        return list(session.scalars(select(Prediction).order_by(Prediction.id.desc()).limit(limit)))


def get_account_history(session_factory, account_id: str, before: datetime | None = None) -> list[dict[str, Any]]:
    with session_factory() as session:
        query = select(Prediction.transaction_data).where(Prediction.account_id == account_id)
        if before is not None:
            query = query.where(Prediction.created_at < before)
        return [row[0] for row in session.execute(query).all() if row[0]]


def update_workflow_status(session_factory, transaction_id: str, result) -> None:
    with session_factory() as session:
        prediction = session.scalar(select(Prediction).where(Prediction.transaction_id == transaction_id).order_by(Prediction.created_at.desc()))
        if prediction:
            prediction.workflow_status = result.workflow_status
            prediction.next_action = result.next_action
            prediction.user_message = result.user_message
            prediction.authorization_status = result.authorization_status
            session.commit()
