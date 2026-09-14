from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4000)
    context: dict | None = None


    @field_validator("message")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Enter a message")
        return value.strip()


class ChatResponse(BaseModel):
    conversation_id: UUID
    reply: str


class DebugRequest(BaseModel):
    code: str = Field(min_length=1, max_length=12000)
    error: str = Field(max_length=4000)
    framework: str = "qiskit"


class DebugResponse(BaseModel):
    explanation: str
    suggested_fix: str
