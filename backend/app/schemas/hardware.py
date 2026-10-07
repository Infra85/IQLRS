from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator
from app.schemas.circuit import CircuitRequest


class HardwareCircuitRequest(CircuitRequest):
    execution_mode: Literal["HARDWARE"] = "HARDWARE"


class HardwareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    execution_mode: Literal["HARDWARE"] = "HARDWARE"
    provider: Literal["ibm", "braket"]
    device_id: str = Field(min_length=1, max_length=512)
    circuit: HardwareCircuitRequest
    confirmed: StrictBool = False

    @model_validator(mode="after")
    def bounded_payload(self):
        if len(self.circuit.model_dump_json()) > 131072:
            raise ValueError("Hardware circuit payload exceeds 128 KiB")
        if any(len(g.type) > 32 for g in self.circuit.gates):
            raise ValueError("Gate names must contain at most 32 characters")
        return self
