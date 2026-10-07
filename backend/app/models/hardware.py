"""Durable hardware reservation, ownership, metadata and measured results."""

from datetime import datetime, timezone
from uuid import UUID as UUIDValue, uuid4
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def now():
    return datetime.now(timezone.utc)


class HardwareJob(Base):
    __tablename__ = "hardware_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("shots > 0"),
    )
    id: Mapped[UUIDValue] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUIDValue] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(80))
    fingerprint: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(20))
    provider_job_id: Mapped[str | None] = mapped_column(String(512))
    device_id: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(24), default="VALIDATING")
    shots: Mapped[int] = mapped_column(Integer)
    circuit: Mapped[dict] = mapped_column(JSONB)
    execution_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB)
    failure: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
