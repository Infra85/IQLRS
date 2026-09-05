from pydantic import BaseModel, Field


class Gate(BaseModel):
    type: str
    qubit: int | None = None
    control: int | None = None
    target: int | None = None


class CircuitRequest(BaseModel):
    gates: list[Gate]
    num_qubits: int = Field(ge=1, le=10)
    shots: int = 1024
    backend: str = "qiskit"


class CircuitResult(BaseModel):
    counts: dict[str, int]
    statevector: list[list[float]] | None = None
    circuit_diagram: str | None = None
