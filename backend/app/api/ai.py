from fastapi import APIRouter

from app.schemas.ai import ChatRequest, DebugRequest

router = APIRouter()


@router.post("/chat")
async def ai_chat(payload: ChatRequest):
    """Send a message to the AI tutor and get a response."""
    # TODO: Forward to AI service with quantum context
    return {"status": "not_implemented"}


@router.post("/debug")
async def ai_debug(payload: DebugRequest):
    """Analyze circuit/code for errors and suggest fixes."""
    # TODO: AI-based debugging
    return {"status": "not_implemented"}
