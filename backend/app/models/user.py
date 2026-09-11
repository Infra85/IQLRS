"""User, role models."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Authentication / email verification
    # Kept here because the current auth system uses OTP verification.
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    otp_code: Mapped[str | None] = mapped_column(
        String(6),
        nullable=True,
    )

    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    module_progress = relationship(
        "ModuleProgress",
        back_populates="user",
    )

    enrollments = relationship(
        "CourseEnrollment",
        back_populates="user",
    )

    gamification = relationship(
        "UserGamification",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    badges = relationship(
        "UserBadge",
        back_populates="user",
    )


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    users = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="roles",
    )

    role = relationship(
        "Role",
        back_populates="users",
    )

    __table_args__ = (
        Index(
            "uq_user_one_primary_role",
            "user_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )


