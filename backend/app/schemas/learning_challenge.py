"""Bounded educational contract built on the existing circuit format."""

import math
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.circuit import CircuitRequest, Gate

VALIDATORS = {
    "constraints",
    "state_equivalence",
    "probability",
    "correlation",
    "classical_output",
    "teleportation",
    "conceptual",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Rule(StrictModel):
    type: Literal[
        "constraints",
        "state_equivalence",
        "probability",
        "correlation",
        "classical_output",
        "teleportation",
        "conceptual",
    ]
    message: str
    target: dict[str, float] | list[list[float]] | None = None
    tolerance: float = Field(default=1e-8, ge=0, le=0.1)
    required: list[Gate] = Field(default_factory=list)
    allowed: list[str] | None = None
    maxGates: int = Field(default=64, ge=0, le=64)
    prefix: list[Gate] = Field(default_factory=list)


class PredictionDefinition(StrictModel):
    kind: Literal["distribution", "answer"]
    labels: list[str]
    displayLabels: dict[str, str]
    expected: dict[str, float]
    tolerance: float = Field(ge=0, le=0.1)
    prompt: str


class ChallengeDefinition(StrictModel):
    id: str
    moduleId: int
    version: int = Field(ge=1)
    kind: Literal["circuit", "conceptual"]
    title: str
    objective: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    instructions: str
    initialState: str
    reflection: str
    starterCircuit: CircuitRequest
    rules: list[Rule] = Field(min_length=1)
    hints: list[str] = Field(min_length=1, max_length=5)
    successFeedback: str
    failureFeedback: str
    solutionExplanation: str
    prediction: PredictionDefinition


class ActivityCircuit(CircuitRequest):
    num_qubits: int = Field(ge=1, le=3, strict=True)
    gates: list[Gate] = Field(max_length=64)
    shots: int = Field(default=1024, ge=1, le=2048, strict=True)

    @model_validator(mode="after")
    def bounded(self):
        if self.backend != "qiskit" or self.debug is not None or self.shot_record_limit:
            raise ValueError(
                "Learning activities use local simulation without debug payloads"
            )
        if (
            self.classical_registers
            and sum(r.size for r in self.classical_registers) > 3
        ):
            raise ValueError("Learning activities support at most three classical bits")
        if len(self.model_dump_json()) > 24000:
            raise ValueError("Circuit is too large")
        return self


class CommitPrediction(StrictModel):
    module_id: int = Field(strict=True, ge=1)
    version: int = Field(strict=True, ge=1)
    revision: UUID
    circuit: ActivityCircuit
    prediction: dict[str, float] = Field(max_length=16)

    @model_validator(mode="after")
    def bounded(self):
        if any(len(k) > 32 or not math.isfinite(v) for k, v in self.prediction.items()):
            raise ValueError("Prediction must contain finite numbers and short labels")
        return self


class RevisionRequest(StrictModel):
    module_id: int = Field(strict=True, ge=1)
    version: int = Field(strict=True, ge=1)
    revision: UUID


class Check(StrictModel):
    id: str
    passed: bool
    message: str


class Feedback(StrictModel):
    summary: str
    details: list[str]
    explanation: str


class ValidationResult(StrictModel):
    status: Literal["success", "near_miss", "incorrect", "invalid_circuit"]
    passed: bool
    score: int = Field(ge=0, le=100)
    checks: list[Check]
    expectation: dict
    feedback: Feedback
    hintsUsed: int
    challengeId: str
    moduleId: int
    version: int
