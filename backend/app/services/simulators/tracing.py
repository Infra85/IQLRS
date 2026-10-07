"""Bounded observation of the existing executor; never evolves state or samples RNG."""

from dataclasses import dataclass
import json

from .classical import classical_snapshot, integer

MAX_DEBUG_SHOTS = 16
MAX_CHECKPOINTS_PER_SHOT = 256
MAX_TOTAL_CHECKPOINTS = 512
MAX_BASIS_VALUES = 32768
MAX_STATEVECTOR_SNAPSHOTS = 64
MAX_DEBUG_BYTES = 2_000_000


@dataclass(frozen=True)
class TracePlan:
    shots: frozenset[int]
    operations: frozenset[int]
    include_statevector: bool


def validate_debug(raw, shots, gates, num_qubits):
    if raw is None:
        return None
    fields = {
        "enabled",
        "shot_numbers",
        "checkpoint_mode",
        "operation_indices",
        "include_statevector",
    }
    if not isinstance(raw, dict) or set(raw) - fields:
        raise ValueError("Malformed debug request or unsupported debug option")
    enabled = raw.get("enabled", False)
    amplitudes = raw.get("include_statevector", False)
    if type(enabled) is not bool or type(amplitudes) is not bool:
        raise ValueError("Debug enabled/include_statevector must be booleans")
    mode = raw.get("checkpoint_mode", "all")
    if mode not in ("all", "selected"):
        raise ValueError("Debug checkpoint_mode must be 'all' or 'selected'")
    numbers = raw.get("shot_numbers", [1])
    if not isinstance(numbers, list) or not 1 <= len(numbers) <= MAX_DEBUG_SHOTS:
        raise ValueError("Debug requires 1 to 16 selected shot numbers")
    for number in numbers:
        integer(number, "Debug shot number (one-based)", 1, shots)
    if len(set(numbers)) != len(numbers):
        raise ValueError("Debug shot numbers must be unique")
    indices = raw.get("operation_indices")
    if mode == "all" and indices is not None:
        raise ValueError("operation_indices require selected checkpoint mode")
    if mode == "selected":
        if not isinstance(indices, list) or not 1 <= len(indices) <= 254:
            raise ValueError("Selected mode requires 1 to 254 operation_indices")
        for index in indices:
            integer(index, "Debug operation index (zero-based)", 0, len(gates) - 1)
        if len(set(indices)) != len(indices):
            raise ValueError("Debug operation indices must be unique")
    if not enabled:
        return None
    selected = set(range(len(gates))) if mode == "all" else set(indices)
    # Never hide a skipped conditional or stochastic event in selected mode.
    selected.update(
        i
        for i, g in enumerate(gates)
        if g["condition"] or g["type"] in {"MEASURE", "MEASURE_ALL", "RESET"}
    )
    per_shot = len(selected) + 2  # start and end are mandatory
    total = per_shot * len(numbers)
    if per_shot > MAX_CHECKPOINTS_PER_SHOT:
        raise ValueError(
            "Debug exceeds 256 checkpoints per shot; select fewer ordinary operations"
        )
    if total > MAX_TOTAL_CHECKPOINTS:
        raise ValueError(
            "Debug exceeds 512 total checkpoints; select fewer shots or operations"
        )
    if total * (1 << num_qubits) > MAX_BASIS_VALUES:
        raise ValueError(
            "Debug exceeds 32768 basis probability values; select fewer shots or operations"
        )
    if amplitudes and total > MAX_STATEVECTOR_SNAPSHOTS:
        raise ValueError(
            "Debug exceeds 64 statevector snapshots; disable amplitudes or select fewer checkpoints"
        )
    return TracePlan(frozenset(numbers), frozenset(selected), amplitudes)


def condition_event(gate, classical, matched):
    condition = gate["condition"]
    if condition is None:
        return None
    bits = classical[condition["register"]]
    actual = (
        bits[condition["bit"]]
        if condition["bit"] is not None
        else sum(b << i for i, b in enumerate(bits))
    )
    return {"actual": actual, "expected": condition["value"], "matched": matched}


class TraceRecorder:
    def __init__(self, plan, state, classical):
        self.plan = plan
        self.checkpoints = []
        self.record("start", None, state, classical)

    def record(
        self,
        kind,
        index,
        state,
        classical,
        *,
        executed=None,
        condition=None,
        samples=None,
        outcome=None,
    ):
        quantum = {
            "probabilities": [float(abs(a) ** 2) for a in state],
            "statevector": None,
        }
        if self.plan.include_statevector:
            quantum["statevector"] = [[float(a.real), float(a.imag)] for a in state]
        self.checkpoints.append(
            {
                "kind": kind,
                "operation_index": index,
                "executed": executed,
                "quantum": quantum,
                "classical": classical_snapshot(classical),
                "condition": condition,
                "samples": samples or [],
                "outcome": outcome,
            }
        )

    def operation(self, index, gate, state, classical, executed, condition, samples):
        kind = {
            "MEASURE": "measurement",
            "MEASURE_ALL": "measurement",
            "RESET": "reset",
        }.get(gate["type"], "operation")
        if not executed or (condition is not None and kind == "operation"):
            kind = "condition"
        self.record(
            kind,
            index,
            state,
            classical,
            executed=executed,
            condition=condition,
            samples=samples,
        )


def debug_result(plan, gates, traces, num_qubits):
    # One compact operation registry shared by all checkpoints and shots.
    operations = {
        str(i): {
            k: gates[i][k]
            for k in (
                "type",
                "targets",
                "controls",
                "params",
                "condition",
                "destinations",
            )
        }
        for i in sorted(plan.operations)
    }
    result = {
        "version": 1,
        "num_qubits": num_qubits,
        "shot_numbering": "one_based",
        "operation_indexing": "zero_based",
        "operations": operations,
        "traces": traces,
    }
    # Structural budgets cap allocation; this final guard bounds serialized debug data.
    if (
        len(json.dumps(result, separators=(",", ":"), allow_nan=False).encode("utf-8"))
        > MAX_DEBUG_BYTES
    ):
        raise ValueError(
            "Debug response exceeds 2000000 bytes; select fewer shots or operations"
        )
    return result
