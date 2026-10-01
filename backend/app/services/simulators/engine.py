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

from .classical import (
    integer as _integer,
    validate_registers,
    validate_reference,
    validate_condition,
    condition_matches,
    classical_snapshot,
    measured_bitstring,
)

from .tracing import validate_debug, TraceRecorder, condition_event, debug_result

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


def validate_and_normalize_gates(circuit_data: dict[str, Any]) -> list[dict[str, Any]]:
    n = _integer(circuit_data.get("num_qubits"), "num_qubits", 1, 10)
    raw_gates = circuit_data.get("gates", [])
    if not isinstance(raw_gates, list) or len(raw_gates) > 500:
        raise ValueError("gates must be a list of at most 500 operations")
    registers = validate_registers(circuit_data, n)
    sizes = {r["name"]: r["size"] for r in registers}
    classical_mode = circuit_data.get("classical_registers") is not None or any(
        isinstance(g, dict)
        and (g.get("destinations") is not None or g.get("condition") is not None)
        for g in raw_gates
    )
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
        if not isinstance(targets, list):
            raise ValueError("targets must be a list")
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
        if kind == "MEASURE":
            required = len(targets) if targets else 1
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
        destinations = raw.get("destinations")
        measuring = kind in {"MEASURE", "MEASURE_ALL"}
        if measuring:
            if destinations is None:
                if classical_mode:
                    raise ValueError(f"{kind} requires classical destinations")
                destinations = [{"register": "c", "bit": q} for q in targets]
            if not isinstance(destinations, list) or len(destinations) != len(targets):
                raise ValueError(
                    "Measurement requires one classical destination per target"
                )
            destinations = [validate_reference(ref, sizes) for ref in destinations]
            if len({(r["register"], r["bit"]) for r in destinations}) != len(
                destinations
            ):
                raise ValueError(
                    "Duplicate classical destinations in one measurement are prohibited"
                )
        elif destinations is not None:
            raise ValueError(
                "Only measurement operations accept classical destinations"
            )
        condition = validate_condition(raw.get("condition"), sizes)
        normalized.append(
            {
                "type": kind,
                "base": base,
                "targets": targets,
                "controls": controls,
                "params": params,
                "destinations": destinations,
                "condition": condition,
                "classical_mode": classical_mode,
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


def _measure(state, qubit, rng, samples=None, destination=None):
    mask = 1 << qubit
    weights = [0.0, 0.0]
    for i, amplitude in enumerate(state):
        weights[bool(i & mask)] += abs(amplitude) ** 2
    outcome = int(rng.random() * sum(weights) >= weights[0])
    if samples is not None:
        total = sum(weights)
        samples.append(
            {
                "qubit": qubit,
                "destination": destination,
                "outcome": outcome,
                "probabilities_before": [w / total for w in weights],
            }
        )
    scale = math.sqrt(weights[outcome])
    for i in range(len(state)):
        state[i] = state[i] / scale if bool(i & mask) == bool(outcome) else 0j
    return outcome


def _execute(state, operations, rng, classical, written, trace=None):
    measurements = []
    for index, gate, matrix in operations:
        capture = trace is not None and index in trace.plan.operations
        matched = condition_matches(gate["condition"], classical)
        evaluation = condition_event(gate, classical, matched) if capture else None
        if not matched:
            if capture:
                trace.operation(index, gate, state, classical, False, evaluation, None)
            continue
        samples = [] if capture else None
        kind, targets = gate["type"], gate["targets"]
        if kind in {"MEASURE", "MEASURE_ALL", "RESET"}:
            if capture:
                destinations = gate["destinations"] or [None] * len(targets)
                outcomes = {
                    q: _measure(state, q, rng, samples, destination)
                    for q, destination in zip(targets, destinations)
                }
            else:
                outcomes = {q: _measure(state, q, rng) for q in targets}
            if kind == "RESET":
                if outcomes[targets[0]]:
                    _apply_single(state, targets[0], SINGLE_QUBIT_GATES["X"])
            else:
                mapping = dict(zip(targets, gate["destinations"]))
                for q, destination in mapping.items():
                    name, bit = destination["register"], destination["bit"]
                    classical[name][bit] = outcomes[q]
                    written.add((name, bit))
                ordered = sorted(targets, reverse=True)
                record = {
                    "operation": index,
                    "qubits": ordered,
                    "bits": "".join(str(outcomes[q]) for q in ordered),
                }
                if gate["classical_mode"]:
                    record["destinations"] = [mapping[q] for q in ordered]
                measurements.append(record)
        elif kind == "SWAP":
            a, b = (1 << q for q in targets)
            for i in range(len(state)):
                if not i & a and i & b:
                    j = i ^ a ^ b
                    state[i], state[j] = state[j], state[i]
        else:
            _apply_single(state, targets[0], matrix, gate["controls"])
        if capture:
            trace.operation(index, gate, state, classical, True, evaluation, samples)
    return measurements


def render_diagram(num_qubits, gates):
    rows = [f"q{q}: ─" for q in range(num_qubits)]
    for gate in gates:
        label = gate["type"]
        if gate["params"]:
            label += f"({gate['params']['theta']:.4g})"
        if gate["classical_mode"] and gate["destinations"]:
            label += " -> " + ",".join(
                f"{r['register']}[{r['bit']}]" for r in gate["destinations"]
            )
        if gate["condition"]:
            cond = gate["condition"]
            ref = cond["register"] + (
                f"[{cond['bit']}]" if cond["bit"] is not None else ""
            )
            label += f" IF {ref} == {cond['value']}"
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


def _terminal_readout(state, n, rng):
    # Preserve the exposed pre-readout state, using the same collapse primitive.
    measured = state.copy()
    outcomes = [_measure(measured, q, rng) for q in range(n)]
    return "".join(str(bit) for bit in reversed(outcomes))


def run_statevector(circuit_data: dict[str, Any], *, rng=None) -> dict[str, Any]:
    gates = validate_and_normalize_gates(circuit_data)
    n = circuit_data["num_qubits"]
    shots = _integer(circuit_data.get("shots", 1024), "shots", 1, 100000)
    limit = _integer(
        circuit_data.get("shot_record_limit", 0), "shot_record_limit", 0, 256
    )
    seed = circuit_data.get("seed")
    if seed is not None:
        _integer(seed, "seed", 0, (1 << 63) - 1)
    plan = validate_debug(circuit_data.get("debug"), shots, gates, n)
    rng = rng if rng is not None else random.Random(seed)
    registers = validate_registers(circuit_data, n)
    measured = {
        (r["register"], r["bit"]) for g in gates for r in (g["destinations"] or [])
    }
    order = [
        {"register": r["name"], "bit": bit}
        for r in registers
        for bit in reversed(range(r["size"]))
        if (r["name"], bit) in measured
    ]
    classical_mode = any(g["classical_mode"] for g in gates)
    classical_counts_mode = classical_mode and bool(order)
    # Every shot executes the full sequence. Bound both work and returned history.
    cost = sum(
        len(g["targets"]) if g["type"] in {"MEASURE", "MEASURE_ALL"} else 1
        for g in gates
    )
    cost += 1 if classical_counts_mode else n + 1
    if shots * cost * (1 << n) > 20_000_000:
        raise ValueError(
            "Circuit exceeds trajectory work limit; reduce shots, qubits, or operations"
        )
    history_size = sum(len(g["targets"]) for g in gates if g["destinations"])
    if min(limit, shots) * history_size > 20000:
        raise ValueError(
            "Shot history exceeds 20000 measurement values; reduce shot_record_limit"
        )
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
    counts, measurement_counts, classical_counts, shot_results = {}, {}, {}, []
    traces = [] if plan else None
    for shot in range(shots):
        state = [0j] * (1 << n)
        state[0] = 1 + 0j
        classical = {r["name"]: [0] * r["size"] for r in registers}
        written = set()
        trace = (
            TraceRecorder(plan, state, classical)
            if plan and shot + 1 in plan.shots
            else None
        )
        if trace is None:
            measurements = _execute(state, operations, rng, classical, written)
        else:
            measurements = _execute(state, operations, rng, classical, written, trace)
        for record in measurements:
            bucket = measurement_counts.setdefault(str(record["operation"]), {})
            bits = record["bits"]
            bucket[bits] = bucket.get(bits, 0) + 1
        classical_bits = measured_bitstring(classical, written, order)
        if order:
            classical_counts[classical_bits] = (
                classical_counts.get(classical_bits, 0) + 1
            )
        outcome = (
            classical_bits
            if classical_counts_mode
            else _terminal_readout(state, n, rng)
        )
        counts[outcome] = counts.get(outcome, 0) + 1
        if trace is not None:
            trace.record("end", None, state, classical, outcome=outcome)
            traces.append({"shot": shot + 1, "checkpoints": trace.checkpoints})
        if shot < limit:
            # Histories always include destination mappings, including implicit legacy c.
            history = []
            for record in measurements:
                gate = gates[record["operation"]]
                mapping = dict(zip(gate["targets"], gate["destinations"]))
                history.append(
                    {**record, "destinations": [mapping[q] for q in record["qubits"]]}
                )
            shot_results.append(
                {
                    "shot": shot + 1,
                    "outcome": outcome,
                    "classical": classical_snapshot(classical),
                    "measurements": history,
                }
            )
    dynamic = any(g["type"] in {"MEASURE", "MEASURE_ALL", "RESET"} for g in gates)
    result = {
        "counts": counts,
        "statevector": [[float(a.real), float(a.imag)] for a in state],
        "circuit_diagram": render_diagram(n, gates),
        "measurements": measurements,
        "measurement_counts": measurement_counts,
        "classical_registers": registers,
        "classical_bit_order": order,
        "classical_counts": classical_counts,
        "last_classical": classical_snapshot(classical),
        "shot_results": shot_results,
        "metadata": {
            "engine": "statevector-v2",
            "execution_version": 2,
            "shots": shots,
            "seed": seed,
            "counts_kind": "classical" if classical_counts_mode else "quantum",
            "shot_records_returned": len(shot_results),
            "shot_records_truncated": len(shot_results) < shots,
            "statevector_scope": "last_shot" if dynamic else "unitary",
            "bit_order": "q(n-1)...q0",
        },
    }
    if plan is not None:
        result["debug"] = debug_result(plan, gates, traces, n)
    return result
