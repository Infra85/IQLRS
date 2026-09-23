"""Pure-Python statevector simulator for the circuit JSON schema.

Used as the always-available engine and as a fallback when Qiskit is not
installed. Little-endian convention matches Qiskit: qubit 0 is the least
significant bit (rightmost in bitstring labels).
"""

from __future__ import annotations

import math
import random
from typing import Any

SQRT2_INV = 1.0 / math.sqrt(2.0)

SINGLE_QUBIT_GATES: dict[str, tuple[tuple[complex, complex], tuple[complex, complex]]] = {
    "I": ((1, 0), (0, 1)),
    "H": ((SQRT2_INV, SQRT2_INV), (SQRT2_INV, -SQRT2_INV)),
    "X": ((0, 1), (1, 0)),
    "Y": ((0, -1j), (1j, 0)),
    "Z": ((1, 0), (0, -1)),
}

TWO_QUBIT_GATES = {"CNOT"}

GATE_ALIASES = {
    "CX": "CNOT",
    "ID": "I",
    "IDENTITY": "I",
    "HADAMARD": "H",
}


def normalize_gate_type(gate_type: str) -> str:
    key = gate_type.strip().upper()
    return GATE_ALIASES.get(key, key)


def validate_and_normalize_gates(circuit_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a list of normalized gate dicts, raising ValueError on bad input."""
    num_qubits = int(circuit_data["num_qubits"])
    if num_qubits < 1 or num_qubits > 10:
        raise ValueError("num_qubits must be between 1 and 10")

    normalized: list[dict[str, Any]] = []
    for raw in circuit_data.get("gates") or []:
        gate_type = normalize_gate_type(str(raw.get("type", "")))
        if not gate_type:
            raise ValueError("Gate is missing a type")

        if gate_type in SINGLE_QUBIT_GATES:
            qubit = raw.get("qubit")
            if qubit is None:
                raise ValueError(f"{gate_type} gate requires 'qubit'")
            qubit = int(qubit)
            if qubit < 0 or qubit >= num_qubits:
                raise ValueError(f"{gate_type} qubit {qubit} is out of range")
            normalized.append({"type": gate_type, "qubit": qubit})
        elif gate_type in TWO_QUBIT_GATES:
            control = raw.get("control")
            target = raw.get("target")
            if control is None or target is None:
                raise ValueError(f"{gate_type} gate requires 'control' and 'target'")
            control = int(control)
            target = int(target)
            if control < 0 or control >= num_qubits:
                raise ValueError(f"{gate_type} control {control} is out of range")
            if target < 0 or target >= num_qubits:
                raise ValueError(f"{gate_type} target {target} is out of range")
            if control == target:
                raise ValueError(f"{gate_type} control and target must differ")
            normalized.append(
                {"type": gate_type, "control": control, "target": target}
            )
        else:
            supported = ", ".join(sorted(set(SINGLE_QUBIT_GATES) | TWO_QUBIT_GATES))
            raise ValueError(
                f"Unsupported gate type '{raw.get('type')}'. Supported: {supported}"
            )
    return normalized


def _apply_single(state: list[complex], qubit: int, matrix) -> list[complex]:
    (a, b), (c, d) = matrix
    new = [0j] * len(state)
    mask = 1 << qubit
    for i in range(len(state)):
        if i & mask:
            continue
        j = i | mask
        amp0 = state[i]
        amp1 = state[j]
        new[i] = a * amp0 + b * amp1
        new[j] = c * amp0 + d * amp1
    return new


def _apply_cnot(state: list[complex], control: int, target: int) -> list[complex]:
    new = [0j] * len(state)
    control_mask = 1 << control
    target_mask = 1 << target
    for i, amp in enumerate(state):
        if amp == 0:
            continue
        if i & control_mask:
            new[i ^ target_mask] += amp
        else:
            new[i] += amp
    return new


def render_diagram(num_qubits: int, gates: list[dict[str, Any]]) -> str:
    """Compact ASCII circuit diagram."""
    if not gates:
        return "\n".join(f"q{q}: ─" for q in range(num_qubits))

    columns: list[list[str]] = []
    for gate in gates:
        col = ["─────"] * num_qubits
        if gate["type"] == "CNOT":
            control = gate["control"]
            target = gate["target"]
            lo, hi = min(control, target), max(control, target)
            for q in range(lo + 1, hi):
                col[q] = "──│──"
            col[control] = "──●──"
            col[target] = "──⊕──"
        else:
            label = gate["type"][:3]
            col[gate["qubit"]] = f"─[{label}]─" if len(label) == 1 else f"[{label}]".center(5, "─")
        columns.append(col)

    lines = []
    for q in range(num_qubits):
        wire = "".join(col[q] for col in columns)
        lines.append(f"q{q}: ─{wire}─")
    return "\n".join(lines)


def _complex_pairs(state: list[complex]) -> list[list[float]]:
    return [[float(amp.real), float(amp.imag)] for amp in state]


def _sample_counts(state: list[complex], num_qubits: int, shots: int) -> dict[str, int]:
    weights = [abs(amp) ** 2 for amp in state]
    total = sum(weights)
    if total == 0:
        raise ValueError("Statevector has zero norm")
    probs = [w / total for w in weights]
    picks = random.choices(range(len(state)), weights=probs, k=shots)
    counts: dict[str, int] = {}
    width = num_qubits
    for index in picks:
        key = format(index, f"0{width}b")
        counts[key] = counts.get(key, 0) + 1
    return counts


def run_statevector(circuit_data: dict[str, Any]) -> dict[str, Any]:
    num_qubits = int(circuit_data["num_qubits"])
    shots = int(circuit_data.get("shots") or 1024)
    if shots < 1:
        raise ValueError("shots must be at least 1")

    gates = validate_and_normalize_gates(circuit_data)
    state: list[complex] = [0j] * (1 << num_qubits)
    state[0] = 1 + 0j

    for gate in gates:
        if gate["type"] == "CNOT":
            state = _apply_cnot(state, gate["control"], gate["target"])
        else:
            state = _apply_single(
                state, gate["qubit"], SINGLE_QUBIT_GATES[gate["type"]]
            )

    return {
        "counts": _sample_counts(state, num_qubits, shots),
        "statevector": _complex_pairs(state),
        "circuit_diagram": render_diagram(num_qubits, gates),
    }
