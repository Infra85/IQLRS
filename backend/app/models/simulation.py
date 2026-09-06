"""Quantum simulation models."""

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("circuits.id"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    simulator: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    shots: Mapped[int] = mapped_column(
        Integer,
        default=1024,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
    )

    execution_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    results = relationship(
        "SimulationResult",
        back_populates="simulation",
    )


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    simulation_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_runs.id"),
        nullable=False,
    )

    measurement_counts: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    probabilities: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    state_vector: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    bloch_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    simulation = relationship(
        "SimulationRun",
        back_populates="results",
    )