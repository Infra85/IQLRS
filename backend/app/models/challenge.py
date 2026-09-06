"""Coding challenge and code submission models."""

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CodingChallenge(Base):
    __tablename__ = "coding_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    module_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_modules.id"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="beginner",
    )

    starter_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expected_output: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    test_cases: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    module = relationship(
        "LearningModule",
        back_populates="coding_challenges",
    )

    submissions = relationship(
        "CodeSubmission",
        back_populates="challenge",
    )


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("coding_challenges.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    code: Mapped[str] = mapped_column(Text)

    language: Mapped[str] = mapped_column(
        String(30),
        default="python",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
    )

    score: Mapped[int | None] = mapped_column(
        Integer,
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

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    challenge = relationship(
        "CodingChallenge",
        back_populates="submissions",
    )

    user = relationship("User")