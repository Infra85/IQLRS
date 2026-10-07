from typing import Literal

from pydantic import BaseModel, Field, StrictInt, StrictFloat, StrictBool, ConfigDict


class ClassicalRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
    size: StrictInt = Field(ge=1, le=32)


class ClassicalBit(BaseModel):
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)
    register_name: str = Field(alias="register")
    bit: StrictInt = Field(ge=0)


class ClassicalCondition(BaseModel):
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)
    register_name: str = Field(alias="register")
    bit: StrictInt | None = None
    operator: str
    value: StrictInt


class Gate(BaseModel):
    type: str
    destinations: list[ClassicalBit] | None = None
    condition: ClassicalCondition | None = None
    qubit: StrictInt | None = None
    control: StrictInt | None = None
    target: StrictInt | None = None

    targets: list[StrictInt] | None = None
    controls: list[StrictInt] | None = None
    params: dict[str, StrictInt | StrictFloat] | None = None


class DebugRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: StrictBool = False
    shot_numbers: list[StrictInt] = Field(
        default_factory=lambda: [1], min_length=1, max_length=16
    )
    checkpoint_mode: Literal["all", "selected"] = "all"
    operation_indices: list[StrictInt] | None = Field(default=None, max_length=254)
    include_statevector: StrictBool = False


class QuantumCheckpoint(BaseModel):
    probabilities: list[float]
    statevector: list[list[float]] | None = None


class ConditionEvaluation(BaseModel):
    actual: int
    expected: int
    matched: bool


class MeasurementSample(BaseModel):
    qubit: int
    destination: ClassicalBit | None = None
    outcome: int
    probabilities_before: list[float]


class ExecutionCheckpoint(BaseModel):
    kind: Literal["start", "end", "operation", "measurement", "condition", "reset"]
    operation_index: int | None = None
    executed: bool | None = None
    quantum: QuantumCheckpoint
    classical: dict[str, str]
    condition: ConditionEvaluation | None = None
    samples: list[MeasurementSample] = Field(default_factory=list)
    outcome: str | None = None


class TraceOperation(BaseModel):
    type: str
    targets: list[int]
    controls: list[int]
    params: dict[str, float | int]
    condition: ClassicalCondition | None = None
    destinations: list[ClassicalBit] | None = None


class ShotTrace(BaseModel):
    shot: int
    checkpoints: list[ExecutionCheckpoint]


class DebugResult(BaseModel):
    version: Literal[1]
    num_qubits: int
    shot_numbering: Literal["one_based"]
    operation_indexing: Literal["zero_based"]
    operations: dict[str, TraceOperation]
    traces: list[ShotTrace]


class CircuitRequest(BaseModel):
    gates: list[Gate] = Field(max_length=500)
    num_qubits: StrictInt = Field(ge=1, le=10)
    shots: StrictInt = Field(default=1024, ge=1, le=100000)
    backend: str = "qiskit"
    debug: DebugRequest | None = None
    classical_registers: list[ClassicalRegister] | None = Field(
        default=None, min_length=1, max_length=8
    )
    seed: StrictInt | None = Field(default=None, ge=0, le=2**63 - 1)
    shot_record_limit: StrictInt = Field(default=0, ge=0, le=256)


class CircuitResult(BaseModel):
    debug: DebugResult | None = None
    simulation_id: str | None = None
    counts: dict[str, int]
    statevector: list[list[float]] | None = None
    circuit_diagram: str | None = None

    measurements: list[dict] = Field(default_factory=list)
    measurement_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    classical_registers: list[ClassicalRegister] = Field(default_factory=list)
    classical_bit_order: list[ClassicalBit] = Field(default_factory=list)
    classical_counts: dict[str, int] = Field(default_factory=dict)
    last_classical: dict[str, str] = Field(default_factory=dict)
    shot_results: list[dict] = Field(default_factory=list)
