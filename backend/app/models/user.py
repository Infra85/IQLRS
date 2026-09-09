
"""User, role, and gamification models."""

from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
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
    DateTime,
    nullable=True,
)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    roles = relationship("UserRole", back_populates="user")
    module_progress = relationship(
        "ModuleProgress", back_populates="user"
    )
    enrollments = relationship(
        "CourseEnrollment", back_populates="user"
    )
    gamification = relationship(
        "UserGamification",
        back_populates="user",
        uselist=False,
    )

    badges = relationship(
    "UserBadge",
    back_populates="user",
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    users = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), nullable=False
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class UserGamification(Base):
    __tablename__ = "user_gamification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    xp: Mapped[int] = mapped_column(
        Integer, default=0
    )

    level: Mapped[int] = mapped_column(
        Integer, default=1
    )

    streak_days: Mapped[int] = mapped_column(
        Integer, default=0
    )

    user = relationship(
        "User",
        back_populates="gamification",
    )