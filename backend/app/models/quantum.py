"""Quantum circuit and gate models."""

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuantumGate(Base):
    __tablename__ = "quantum_gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    gate_type: Mapped[str] = mapped_column(
        String(50),
        default="single_qubit",
    )

    circuit_gates = relationship(
        "CircuitGate",
        back_populates="gate",
    )


class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    num_qubits: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    gates = relationship(
        "CircuitGate",
        back_populates="circuit",
    )

    versions = relationship(
        "CircuitVersion",
        back_populates="circuit",
    )


class CircuitGate(Base):
    __tablename__ = "circuit_gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("circuits.id"),
        nullable=False,
    )

    gate_id: Mapped[int] = mapped_column(
        ForeignKey("quantum_gates.id"),
        nullable=False,
    )

    qubit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_qubit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    parameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    circuit = relationship(
        "Circuit",
        back_populates="gates",
    )

    gate = relationship(
        "QuantumGate",
        back_populates="circuit_gates",
    )


class CircuitVersion(Base):
    __tablename__ = "circuit_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("circuits.id"),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    circuit_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    circuit = relationship(
        "Circuit",
        back_populates="versions",
    )