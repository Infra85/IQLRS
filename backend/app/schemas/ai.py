from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    context: dict | None = None


class ChatResponse(BaseModel):
    reply: str


class DebugRequest(BaseModel):
    code: str
    error: str
    framework: str = "qiskit"


class DebugResponse(BaseModel):
    explanation: str
    suggested_fix: str
