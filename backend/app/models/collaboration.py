"""Project, contribution, and shared resource models."""

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


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    name: Mapped[str] = mapped_column(String(200))

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    owner = relationship("User")

    members = relationship(
        "ProjectMember",
        back_populates="project",
    )

    contributions = relationship(
        "Contribution",
        back_populates="project",
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    project_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    project = relationship(
        "Project",
        back_populates="members",
    )

    user = relationship("User")


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
    )

    title: Mapped[str] = mapped_column(String(200))

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    contribution_type: Mapped[str] = mapped_column(
        String(50),
        default="other",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    project = relationship(
        "Project",
        back_populates="contributions",
    )

    members = relationship(
        "ContributionMember",
        back_populates="contribution",
    )


class ContributionMember(Base):
    __tablename__ = "contribution_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    contribution_id: Mapped[int] = mapped_column(
        ForeignKey("contributions.id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    contribution_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    contribution = relationship(
        "Contribution",
        back_populates="members",
    )

    user = relationship("User")


class SharedResource(Base):
    __tablename__ = "shared_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    share_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    kind: Mapped[str] = mapped_column(
        String(30),
    )

    title: Mapped[str] = mapped_column(
        String(200),
        default="",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    owner = relationship("User")