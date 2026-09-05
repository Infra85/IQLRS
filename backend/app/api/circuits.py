from fastapi import APIRouter

router = APIRouter()


@router.post("/simulate")
async def simulate_circuit(circuit: dict):
    """Accept a circuit definition and return simulation results."""
    # TODO: Parse circuit, dispatch to selected simulator backend
    return {"status": "not_implemented"}
