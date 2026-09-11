"""Quantum circuit, gate, version, and simulation models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Circuit(Base):
    __tablename__ = "circuits"

    circuit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
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
        nullable=False,
    )

    num_classical_bits: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(30),
        default="builder",
        nullable=False,
    )

    framework: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    circuit_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
    )

    gates = relationship(
        "CircuitGate",
        back_populates="circuit",
        cascade="all, delete-orphan",
    )

    versions = relationship(
        "CircuitVersion",
        back_populates="circuit",
        cascade="all, delete-orphan",
    )

    simulation_runs = relationship(
        "SimulationRun",
        back_populates="circuit",
        cascade="all, delete-orphan",
    )


class QuantumGate(Base):
    __tablename__ = "quantum_gates"

    gate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

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

    num_qubits: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    matrix: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    circuit_gates = relationship(
        "CircuitGate",
        back_populates="gate",
    )


class CircuitGate(Base):
    __tablename__ = "circuit_gates"

    circuit_gate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    circuit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("circuits.circuit_id"),
        nullable=False,
    )

    gate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("quantum_gates.gate_id"),
        nullable=False,
    )

    qubit_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    control_qubit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    target_qubit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    gate_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    parameters: Mapped[dict | None] = mapped_column(
        JSONB,
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

    version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    circuit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("circuits.circuit_id"),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(30),
        default="builder",
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    circuit_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    circuit = relationship(
        "Circuit",
        back_populates="versions",
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    simulation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    circuit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("circuits.circuit_id"),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    backend: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    shots: Mapped[int] = mapped_column(
        Integer,
        default=1024,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    circuit = relationship(
        "Circuit",
        back_populates="simulation_runs",
    )

    user = relationship(
        "User",
    )

    result = relationship(
        "SimulationResult",
        back_populates="simulation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    simulation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("simulation_runs.simulation_id"),
        nullable=False,
        unique=True,
    )

    measurement_counts: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    probabilities: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    state_vector: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    bloch_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    circuit_diagram: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    simulation = relationship(
        "SimulationRun",
        back_populates="result",
    )