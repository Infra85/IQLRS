"""Course, learning module, progress, and recommendation models."""

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    modules = relationship(
        "LearningModule",
        back_populates="course",
    )

    enrollments = relationship(
        "CourseEnrollment",
        back_populates="course",
    )


class LearningModule(Base):
    __tablename__ = "learning_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    module_order: Mapped[int] = mapped_column(
        Integer, default=1
    )

    course = relationship(
        "Course",
        back_populates="modules",
    )

    progress = relationship(
        "ModuleProgress",
        back_populates="module",
    )

    coding_challenges = relationship(
        "CodingChallenge",
        back_populates="module",
    )


class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id"),
        nullable=False,
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer, default=0
    )

    completed: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    score: Mapped[int] = mapped_column(
        Integer, default=0
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="module_progress",
    )

    module = relationship(
        "LearningModule",
        back_populates="progress",
    )


class LearningRecommendation(Base):
    __tablename__ = "learning_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    module_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_modules.id"),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )