from fastapi import APIRouter, HTTPException

from app.schemas.circuit import CircuitRequest, CircuitResult
from app.services.simulators.qiskit_runner import run_circuit

router = APIRouter()

SUPPORTED_BACKENDS = {"qiskit"}


@router.post("/simulate", response_model=CircuitResult)
async def simulate_circuit(circuit: CircuitRequest):
    """Accept a circuit definition and return simulation results."""
    backend = (circuit.backend or "qiskit").strip().lower()
    if backend not in SUPPORTED_BACKENDS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported backend '{circuit.backend}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_BACKENDS))}"
            ),
        )

    try:
        return run_circuit(circuit.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
