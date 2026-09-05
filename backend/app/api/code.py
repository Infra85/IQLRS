from fastapi import APIRouter

router = APIRouter()


@router.post("/execute")
async def execute_code(payload: dict):
    """Execute user-submitted quantum code in a sandbox."""
    # TODO: Sandbox execution with selected framework
    return {"status": "not_implemented"}
