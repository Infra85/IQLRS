"""Provider-neutral contracts. No SDK import or simulator execution in this layer."""

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.services.simulators.engine import validate_and_normalize_gates
from app.services.simulators.classical import validate_registers

TERMINAL = {"COMPLETED", "FAILED", "CANCELED"}


class HardwareError(ValueError):
    """Safe, application-owned message; never wrap SDK exception text."""


@dataclass
class Compiled:
    program: Any
    metadata: dict


class HardwareProvider(ABC):
    @abstractmethod
    def devices(self) -> list[dict]: ...

    def device(self, device_id: str) -> dict:
        for device in self.devices():
            if device["device_id"] == device_id:
                return device
        raise HardwareError("Selected hardware device is unavailable")

    @abstractmethod
    def compile(self, device_id: str, circuit: dict) -> Compiled: ...

    @abstractmethod
    def submit(
        self, device_id: str, compiled: Compiled, shots: int, key: str
    ) -> str: ...

    @abstractmethod
    def status(self, job_id: str) -> dict: ...

    @abstractmethod
    def result(self, job_id: str, metadata: dict, shots: int) -> dict: ...

    @abstractmethod
    def cancel(self, job_id: str) -> None: ...


def prepare(circuit):
    if (circuit.get("debug") or {}).get("enabled"):
        raise HardwareError("Hardware cannot provide internal state checkpoints")
    if circuit.get("seed") is not None or circuit.get("shot_record_limit", 0):
        raise HardwareError(
            "Hardware does not support local random seeds or simulator shot histories"
        )
    try:
        ops = validate_and_normalize_gates(circuit)
        regs = validate_registers(circuit, circuit["num_qubits"])
    except ValueError as exc:
        raise HardwareError(str(exc)) from None
    # Legacy simulator counts use a final quantum readout, even after explicit M.
    classical = any(op["classical_mode"] for op in ops)
    if not classical or not any(op["destinations"] for op in ops):
        if classical:
            raise HardwareError(
                "Classical hardware circuits require explicit measurements"
            )
        regs = [{"name": "c", "size": circuit["num_qubits"]}]
        ops = ops + [
            {
                "type": "MEASURE_ALL",
                "targets": list(range(circuit["num_qubits"])),
                "controls": [],
                "params": {},
                "condition": None,
                "destinations": [
                    {"register": "c", "bit": q} for q in range(circuit["num_qubits"])
                ],
            }
        ]
    if any(op["condition"] and op["destinations"] for op in ops):
        raise HardwareError(
            "Conditional measurement writes cannot preserve IQLRS unwritten-bit semantics"
        )
    measured = {
        (d["register"], d["bit"]) for op in ops for d in op["destinations"] or []
    }
    order = [
        {"register": r["name"], "bit": bit}
        for r in regs
        for bit in reversed(range(r["size"]))
        if (r["name"], bit) in measured
    ]
    return ops, regs, order


def checked_counts(counts, width, shots):
    if not isinstance(counts, dict) or not counts or len(counts) > shots:
        raise HardwareError("Provider returned invalid measurement counts")
    if any(
        not isinstance(k, str)
        or len(k) != width
        or set(k) - {"0", "1"}
        or type(v) is not int
        or v < 0
        for k, v in counts.items()
    ):
        raise HardwareError("Provider returned invalid bitstrings or counts")
    if sum(counts.values()) != shots:
        raise HardwareError("Provider shot count does not match the submitted workload")
    return counts


def register_counts(samples, order, shots):
    """Join register samples by shot, never multiply marginal distributions."""
    counts = Counter()
    for i in range(shots):
        try:
            counts[
                "".join(samples[d["register"]][i][-1 - d["bit"]] for d in order)
            ] += 1
        except (KeyError, IndexError, TypeError):
            raise HardwareError(
                "Provider measurement registers are incomplete"
            ) from None
    return checked_counts(dict(counts), len(order), shots)


def provider_failure(exc):
    """Map allowlisted SDK codes/types without reflecting messages, URLs or secrets."""
    code = ""
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = response.get("Error", {}).get("Code", "")
    status = getattr(exc, "status_code", None)
    kind = type(exc).__name__
    if code in {
        "AccessDeniedException",
        "UnrecognizedClientException",
        "ExpiredTokenException",
    } or status in (401, 403):
        return 503, "Provider authentication failed or account lacks permission", True
    if code in {"ServiceQuotaExceededException"}:
        return 429, "Provider quota exceeded", True
    if code in {"ThrottlingException", "TooManyRequestsException"} or status == 429:
        return 429, "Provider rate limit reached", True
    if code in {"ValidationException", "ResourceNotFoundException"}:
        return 400, "Device or circuit is not accepted by the provider", True
    if kind in {"TranspilerError", "CircuitTooWideForTarget", "IBMInputValueError"}:
        return (
            400,
            "Selected backend cannot compile or execute the requested circuit",
            True,
        )
    if (
        kind in {"RuntimeInvalidStateError", "ConflictException"}
        or code == "ConflictException"
    ):
        return 409, "Operation is not supported for this provider job state", True
    if "Timeout" in kind:
        return 504, "Provider timeout; job acceptance may be uncertain", False
    return (
        502,
        "Hardware provider request failed; check availability, account permissions or quota",
        False,
    )
