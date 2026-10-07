from pydantic import BaseModel, Field, StrictInt, StrictFloat


class Gate(BaseModel):
    type: str
    qubit: StrictInt | None = None
    control: StrictInt | None = None
    target: StrictInt | None = None

    targets: list[StrictInt] | None = None
    controls: list[StrictInt] | None = None
    params: dict[str, StrictInt | StrictFloat] | None = None


class CircuitRequest(BaseModel):
    gates: list[Gate] = Field(max_length=500)
    num_qubits: StrictInt = Field(ge=1, le=10)
    shots: StrictInt = Field(default=1024, ge=1, le=100000)
    backend: str = "qiskit"


class CircuitResult(BaseModel):
    simulation_id: str | None = None
    counts: dict[str, int]
    statevector: list[list[float]] | None = None
    circuit_diagram: str | None = None

    measurements: list[dict] = Field(default_factory=list)
    measurement_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
