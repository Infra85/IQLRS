from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    DebugRequest,
    DebugResponse,
)
from app.services.ai_tutor import AITutor


router = APIRouter()


def get_ai_tutor() -> AITutor:
    return AITutor()


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest):
    """Send a message to the AI quantum tutor."""

    try:
        tutor = get_ai_tutor()

        reply = await tutor.chat(
            message=payload.message,
            context=payload.context,
        )

        return ChatResponse(reply=reply)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI Tutor error: {str(exc)}",
        )


@router.post("/debug", response_model=DebugResponse)
async def ai_debug(payload: DebugRequest):
    """Analyze quantum code and suggest a fix."""

    try:
        tutor = get_ai_tutor()

        result = await tutor.debug_code(
            code=payload.code,
            error=payload.error,
        )

        return DebugResponse(
            explanation=result["explanation"],
            suggested_fix=result["suggested_fix"],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI Debugger error: {str(exc)}",
        )
