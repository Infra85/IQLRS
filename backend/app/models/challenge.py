"""Coding challenge and code submission models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CodingChallenge(Base):
    __tablename__ = "coding_challenges"

    challenge_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    module_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("learning_modules.module_id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    framework: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    starter_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expected_output: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    test_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="beginner",
        nullable=False,
    )

    max_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    module = relationship(
        "LearningModule",
        back_populates="coding_challenges",
    )

    submissions = relationship(
        "CodeSubmission",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    submission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    challenge_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("coding_challenges.challenge_id"),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    framework: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    execution_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    passed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    challenge = relationship(
        "CodingChallenge",
        back_populates="submissions",
    )

    user = relationship(
        "User",
    )