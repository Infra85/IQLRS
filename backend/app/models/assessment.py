"""Assessment and question models."""

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id"),
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
    )

    questions = relationship(
        "Question",
        back_populates="assessment",
    )

    attempts = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"),
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[str] = mapped_column(
        String(50),
        default="multiple_choice",
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    assessment = relationship(
        "Assessment",
        back_populates="questions",
    )

    options = relationship(
        "QuestionOption",
        back_populates="question",
    )

    answers = relationship(
        "QuestionAnswer",
        back_populates="question",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    option_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        default=False,
    )

    question = relationship(
        "Question",
        back_populates="options",
    )


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completed: Mapped[bool] = mapped_column(
        default=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    assessment = relationship(
        "Assessment",
        back_populates="attempts",
    )

    answers = relationship(
        "QuestionAnswer",
        back_populates="attempt",
    )


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_attempts.id"),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    selected_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_options.id"),
        nullable=True,
    )

    answer_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_correct: Mapped[bool] = mapped_column(
        default=False,
    )

    attempt = relationship(
        "AssessmentAttempt",
        back_populates="answers",
    )

    question = relationship(
        "Question",
        back_populates="answers",
    )