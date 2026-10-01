"""Statevector and stochastic-trajectory simulator.

Little endian: amplitude index i encodes q0 in bit 0. Labels/counts are
q(n-1)...q0, even though the builder draws q0 at the top. Measurement/reset
return one conditional pure trajectory, never an ensemble statevector.
"""

from __future__ import annotations

import cmath
import math
import random
from typing import Any

SQRT2_INV = 1 / math.sqrt(2)
SINGLE_QUBIT_GATES = {
    "I": ((1, 0), (0, 1)),
    "H": ((SQRT2_INV, SQRT2_INV), (SQRT2_INV, -SQRT2_INV)),
    "X": ((0, 1), (1, 0)),
    "Y": ((0, -1j), (1j, 0)),
    "Z": ((1, 0), (0, -1)),
    "S": ((1, 0), (0, 1j)),
    "T": ((1, 0), (0, cmath.exp(1j * math.pi / 4))),
    "SDG": ((1, 0), (0, -1j)),
    "TDG": ((1, 0), (0, cmath.exp(-1j * math.pi / 4))),
}
ROTATIONS = {"RX", "RY", "RZ"}
CONTROLLED = {"CNOT": "X", **{"C" + g: g for g in (*SINGLE_QUBIT_GATES, *ROTATIONS)}}
GATE_ALIASES = {"CX": "CNOT", "ID": "I", "IDENTITY": "I", "HADAMARD": "H"}


def normalize_gate_type(gate_type: str) -> str:
    key = gate_type.strip().upper()
    return GATE_ALIASES.get(key, key)


def _integer(value, label, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer between {low} and {high}")
    return value


def validate_and_normalize_gates(circuit_data: dict[str, Any]) -> list[dict[str, Any]]:
    n = _integer(circuit_data.get("num_qubits"), "num_qubits", 1, 10)
    raw_gates = circuit_data.get("gates", [])
    if not isinstance(raw_gates, list) or len(raw_gates) > 500:
        raise ValueError("gates must be a list of at most 500 operations")
    normalized = []
    for raw in raw_gates:
        if not isinstance(raw, dict) or not isinstance(raw.get("type"), str):
            raise ValueError("Gate requires a string type")
        kind = normalize_gate_type(raw["type"])
        base = CONTROLLED.get(kind, kind)
        if (
            base not in SINGLE_QUBIT_GATES
            and base not in ROTATIONS
            and kind not in {"SWAP", "MEASURE", "MEASURE_ALL", "RESET"}
        ):
            raise ValueError(f"Unsupported gate type '{kind}'")
        controls = raw.get("controls")
        if controls is not None and raw.get("control") is not None:
            raise ValueError("Use control or controls, not both")
        if controls is None:
            controls = [raw["control"]] if raw.get("control") is not None else []
        if not isinstance(controls, list):
            raise ValueError("controls must be a list")
        targets = raw.get("targets")
        legacy = [raw[k] for k in ("qubit", "target") if raw.get(k) is not None]
        if targets is not None and legacy:
            raise ValueError("Use targets or qubit/target, not both")
        if targets is None:
            targets = legacy
        if kind == "SWAP" and raw.get("control") is not None:
            targets = controls + targets  # legacy pair fields accepted by builder
            controls = []
        if not isinstance(targets, list):
            raise ValueError("targets must be a list")
        if kind == "MEASURE_ALL":
            if targets:
                raise ValueError("MEASURE_ALL does not accept targets")
            targets = list(range(n))
        required = 2 if kind == "SWAP" else n if kind == "MEASURE_ALL" else 1
        if len(targets) != required:
            raise ValueError(f"{kind} requires {required} target qubit(s)")
        if kind in CONTROLLED and not controls:
            raise ValueError(f"{kind} requires control qubit(s)")
        if controls and base not in SINGLE_QUBIT_GATES and base not in ROTATIONS:
            raise ValueError(f"{kind} cannot have controls")
        indices = controls + targets
        for q in indices:
            _integer(q, f"{kind} qubit index", 0, n - 1)
        if len(set(indices)) != len(indices):
            raise ValueError(
                "Control and target indices must be distinct (no duplicates)"
            )
        params = raw.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        if base in ROTATIONS:
            theta = params.get("theta")
            try:
                finite = type(theta) in (int, float) and math.isfinite(theta)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(
                    f"{kind} requires a finite numeric params.theta in radians"
                )
            if set(params) != {"theta"}:
                raise ValueError(f"{kind} only accepts params.theta")
        elif params:
            raise ValueError(f"{kind} does not accept parameters")
        normalized.append(
            {
                "type": kind,
                "base": base,
                "targets": targets,
                "controls": controls,
                "params": params,
            }
        )
    return normalized


def gate_matrix(kind, params):
    if kind in SINGLE_QUBIT_GATES:
        return SINGLE_QUBIT_GATES[kind]
    half = params["theta"] / 2
    c, s = math.cos(half), math.sin(half)
    if kind == "RX":
        return ((c, -1j * s), (-1j * s, c))
    if kind == "RY":
        return ((c, -s), (s, c))
    return ((cmath.exp(-1j * half), 0), (0, cmath.exp(1j * half)))


def _apply_single(state, qubit, matrix, controls=()):
    """Apply an arbitrary 2x2 matrix in place, conditional on all controls=1."""
    (a, b), (c, d) = matrix
    mask = 1 << qubit
    control_mask = sum(1 << q for q in controls)
    for start in range(0, len(state), mask * 2):
        for i in range(start, start + mask):
            if i & control_mask != control_mask:
                continue
            j = i | mask
            x, y = state[i], state[j]
            state[i], state[j] = a * x + b * y, c * x + d * y
    return state


def _measure(state, qubit, rng):
    mask = 1 << qubit
    weights = [
        sum(abs(a) ** 2 for i, a in enumerate(state) if bool(i & mask) == bool(bit))
        for bit in (0, 1)
    ]
    outcome = int(rng.random() * sum(weights) >= weights[0])
    scale = math.sqrt(weights[outcome])
    for i in range(len(state)):
        state[i] = state[i] / scale if bool(i & mask) == bool(outcome) else 0j
    return outcome


def _execute(state, operations, rng):
    measurements = []
    for index, gate, matrix in operations:
        kind, targets = gate["type"], gate["targets"]
        if kind in {"MEASURE", "MEASURE_ALL", "RESET"}:
            outcomes = {q: _measure(state, q, rng) for q in targets}
            if kind == "RESET":
                if outcomes[targets[0]]:
                    _apply_single(state, targets[0], SINGLE_QUBIT_GATES["X"])
            else:
                ordered = sorted(targets, reverse=True)
                measurements.append(
                    {
                        "operation": index,
                        "qubits": ordered,
                        "bits": "".join(str(outcomes[q]) for q in ordered),
                    }
                )
        elif kind == "SWAP":
            a, b = (1 << q for q in targets)
            for i in range(len(state)):
                if not i & a and i & b:
                    j = i ^ a ^ b
                    state[i], state[j] = state[j], state[i]
        else:
            _apply_single(state, targets[0], matrix, gate["controls"])
    return measurements


def render_diagram(num_qubits, gates):
    rows = [f"q{q}: ─" for q in range(num_qubits)]
    for gate in gates:
        label = gate["type"]
        if gate["params"]:
            label += f"({gate['params']['theta']:.4g})"
        width = len(label) + 4
        for q in range(num_qubits):
            cell = (
                "●"
                if q in gate["controls"]
                else f"[{label}]"
                if q in gate["targets"]
                else ""
            )
            rows[q] += cell.center(width, "─")
    return "\n".join(rows)


def run_statevector(circuit_data: dict[str, Any], *, rng=None) -> dict[str, Any]:
    gates = validate_and_normalize_gates(circuit_data)
    n = circuit_data["num_qubits"]
    shots = _integer(circuit_data.get("shots", 1024), "shots", 1, 100000)
    rng = rng if rng is not None else random
    operations = [
        (
            i,
            g,
            gate_matrix(g["base"], g["params"])
            if g["base"] in SINGLE_QUBIT_GATES or g["base"] in ROTATIONS
            else None,
        )
        for i, g in enumerate(gates)
    ]
    split = next(
        (
            i
            for i, g in enumerate(gates)
            if g["type"] in {"MEASURE", "MEASURE_ALL", "RESET"}
        ),
        len(gates),
    )
    dynamic = split < len(gates)
    # Bound repeated trajectory work without changing the established qubit limit.
    if dynamic and shots * (len(gates) - split + 1) * (1 << n) > 20_000_000:
        raise ValueError(
            "Circuit exceeds trajectory work limit; reduce shots, qubits, or operations"
        )
    prefix = [0j] * (1 << n)
    prefix[0] = 1 + 0j
    _execute(prefix, operations[:split], rng)
    counts, measurements = {}, []
    measurement_counts = {}
    state = prefix
    for _ in range(shots if dynamic else 1):
        if dynamic:
            state = prefix.copy()
            measurements = _execute(state, operations[split:], rng)
            for record in measurements:
                bucket = measurement_counts.setdefault(str(record["operation"]), {})
                bits = record["bits"]
                bucket[bits] = bucket.get(bits, 0) + 1
        picks = rng.choices(
            range(len(state)),
            weights=[abs(a) ** 2 for a in state],
            k=1 if dynamic else shots,
        )
        for index in picks:
            bits = format(index, f"0{n}b")
            counts[bits] = counts.get(bits, 0) + 1
    return {
        "counts": counts,
        "statevector": [[float(a.real), float(a.imag)] for a in state],
        "circuit_diagram": render_diagram(n, gates),
        "measurements": measurements,
        "measurement_counts": measurement_counts,
        "metadata": {
            "engine": "statevector-v2",
            "shots": shots,
            "statevector_scope": "last_shot" if dynamic else "unitary",
            "bit_order": "q(n-1)...q0",
        },
    }
