"""Qiskit simulation runner.

Builds a QuantumCircuit from the shared CircuitRequest JSON and runs it on
Aer when Qiskit is installed and the runtime is compatible. Falls back to
the pure-Python statevector engine otherwise so /simulate still returns
real results (Qiskit 2.x currently segfaults on Python 3.14).
"""

from __future__ import annotations

import sys
from typing import Any

from app.services.simulators.engine import (
    run_statevector,
    validate_and_normalize_gates,
)


def _qiskit_usable() -> bool:
    if sys.version_info >= (3, 14):
        return False
    try:
        import qiskit  # noqa: F401
        import qiskit_aer  # noqa: F401
    except ImportError:
        return False
    return True


def _run_with_qiskit(circuit_data: dict[str, Any]) -> dict[str, Any]:
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator

    num_qubits = int(circuit_data["num_qubits"])
    shots = int(circuit_data.get("shots") or 1024)
    gates = validate_and_normalize_gates(circuit_data)

    qc = QuantumCircuit(num_qubits)
    for gate in gates:
        gate_type = gate["type"]
        if gate_type == "I":
            qc.id(gate["qubit"])
        elif gate_type == "H":
            qc.h(gate["qubit"])
        elif gate_type == "X":
            qc.x(gate["qubit"])
        elif gate_type == "Y":
            qc.y(gate["qubit"])
        elif gate_type == "Z":
            qc.z(gate["qubit"])
        elif gate_type == "CNOT":
            qc.cx(gate["control"], gate["target"])

    statevector = Statevector.from_instruction(qc)
    pairs = [[float(amp.real), float(amp.imag)] for amp in statevector.data]

    measured = qc.copy()
    measured.measure_all()
    simulator = AerSimulator()
    job = simulator.run(transpile(measured, simulator), shots=shots)
    raw_counts = job.result().get_counts()
    counts = {
        str(bitstring).replace(" ", ""): int(n) for bitstring, n in raw_counts.items()
    }

    return {
        "counts": counts,
        "statevector": pairs,
        "circuit_diagram": str(qc.draw(output="text")),
    }


def run_circuit(circuit_data: dict) -> dict:
    """Execute a quantum circuit using Qiskit Aer, with a local fallback."""
    if _qiskit_usable():
        return _run_with_qiskit(circuit_data)
    return run_statevector(circuit_data)
