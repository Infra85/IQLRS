from pydantic import BaseModel, Field


class Gate(BaseModel):
    type: str
    qubit: int | None = None
    control: int | None = None
    target: int | None = None


class CircuitRequest(BaseModel):
    gates: list[Gate] = Field(max_length=500)
    num_qubits: int = Field(ge=1, le=10)
    shots: int = Field(default=1024, ge=1, le=100000)
    backend: str = "qiskit"


class CircuitResult(BaseModel):
    simulation_id: str | None = None
    counts: dict[str, int]
    statevector: list[list[float]] | None = None
    circuit_diagram: str | None = None
