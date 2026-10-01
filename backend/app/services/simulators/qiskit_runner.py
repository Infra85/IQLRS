"""Compatibility entry point for the historical 'qiskit' backend name.

Use the shared engine on every Python version so measurement trajectories and
validation have identical semantics regardless of optional native packages.
"""

from app.services.simulators.engine import run_statevector


def run_circuit(circuit_data: dict) -> dict:
    return run_statevector(circuit_data)
