"""Assessment and question models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id: Mapped[UUID] = mapped_column(
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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessment_type: Mapped[str] = mapped_column(
        String(50),
        default="quiz",
        nullable=False,
    )

    max_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    passing_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    questions = relationship(
        "Question",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    attempts = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class Question(Base):
    __tablename__ = "questions"

    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assessments.assessment_id"),
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[str] = mapped_column(
        String(50),
        default="multiple_choice",
        nullable=False,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    assessment = relationship(
        "Assessment",
        back_populates="questions",
    )

    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    answers = relationship(
        "QuestionAnswer",
        back_populates="question",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    option_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.question_id"),
        nullable=False,
    )

    option_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    question = relationship(
        "Question",
        back_populates="options",
    )


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    attempt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assessments.assessment_id"),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    percentage: Mapped[float] = mapped_column(
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="in_progress",
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assessment = relationship(
        "Assessment",
        back_populates="attempts",
    )

    answers = relationship(
        "QuestionAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    answer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    attempt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assessment_attempts.attempt_id"),
        nullable=False,
    )

    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.question_id"),
        nullable=False,
    )

    selected_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("question_options.option_id"),
        nullable=True,
    )

    answer_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_correct: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    points_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    attempt = relationship(
        "AssessmentAttempt",
        back_populates="answers",
    )

    question = relationship(
        "Question",
        back_populates="answers",
    )