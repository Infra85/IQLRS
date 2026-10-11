"""Additive activity drafts and immutable validation attempts."""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ChallengeWorkspace(Base):
    __tablename__ = "challenge_workspaces"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer)
    revision: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    fingerprint: Mapped[str] = mapped_column(String(64))
    circuit: Mapped[dict] = mapped_column(JSONB)
    prediction: Mapped[dict] = mapped_column(JSONB)
    execution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    __table_args__ = (UniqueConstraint("user_id", "challenge_id"),)


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[str] = mapped_column(String(80))
    module_id: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    revision: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    fingerprint: Mapped[str] = mapped_column(String(64))
    number: Mapped[int] = mapped_column(Integer)
    circuit: Mapped[dict] = mapped_column(JSONB)
    prediction: Mapped[dict] = mapped_column(JSONB)
    # Counts + ideal probabilities suffice for future feedback; no traces/shot arrays.
    simulation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict] = mapped_column(JSONB)
    passed: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[int] = mapped_column(Integer)
    hints_used: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", "revision"),
        UniqueConstraint("user_id", "challenge_id", "number"),
    )
