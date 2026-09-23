from fastapi import APIRouter

from app.schemas.code import CodeExecuteRequest

router = APIRouter()


@router.post("/execute")
async def execute_code(payload: CodeExecuteRequest):
    """Execute user-submitted quantum code in a sandbox."""
    # TODO: Sandbox execution with selected framework
    return {"status": "not_implemented", "framework": payload.framework}
