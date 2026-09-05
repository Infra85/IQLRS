from fastapi import APIRouter

from app.schemas.circuit import CircuitRequest

router = APIRouter()


@router.post("/simulate")
async def simulate_circuit(circuit: CircuitRequest):
    """Accept a circuit definition and return simulation results."""
    # TODO: Parse circuit, dispatch to selected simulator backend
    return {"status": "not_implemented", "backend": circuit.backend}
