import asyncio
from contextlib import suppress

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.speech.provider import SpeechFailure
from app.services.speech.service import service

router = APIRouter()


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=1600)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(c) < 32 and c not in "\n\t\r" for c in value):
            raise ValueError("Text must contain readable content")
        return value


@router.get("/config")
async def speech_config():
    return {"available": service.available, "version": service.version,
            "voice": service.config.tts_voice, "max_characters": 1600}


@router.post("")
async def create_speech(payload: SpeechRequest, request: Request):
    task = asyncio.create_task(service.generate(payload.text, request.client.host if request.client else "unknown"))
    try:
        while not task.done():
            if await request.is_disconnected():
                task.cancel()
                return Response(status_code=499)
            await asyncio.sleep(0.05)
        data, key = await task
        return Response(data, media_type="audio/mpeg", headers={
            "Cache-Control": "private, no-store", "X-Narration-Key": key,
            "X-Content-Type-Options": "nosniff",
        })
    except SpeechFailure as exc:
        limited = exc.code in {"rate_limited", "daily_limit", "busy"}
        detail = "Narration is busy. Please try again shortly." if limited else "Narration is unavailable right now. You can keep reading and try again later."
        raise HTTPException(status_code=429 if limited else 503, detail=detail,
                            headers={"Retry-After": "60"} if limited else None) from None
    finally:
        if not task.done():
            task.cancel()
        with suppress(asyncio.CancelledError, SpeechFailure):
            await task
