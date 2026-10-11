from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

from app.api import circuits, ai, auth, progress, speech, hardware, learning_challenges
from app.api.dashboard import router as dashboard_router

app = FastAPI(
    title=" IQLRS API",
    description="Backend API for Intelligent Quantum Learning and Reseach System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

app.include_router(hardware.router, prefix="/api/hardware", tags=["hardware"])
app.include_router(speech.router, prefix="/api/speech", tags=["speech"])
app.include_router(circuits.router, prefix="/api/circuits", tags=["circuits"])

app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(progress.router)
app.include_router(learning_challenges.router)

app.include_router(dashboard_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "IQLRS-API"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT user_id, otp_attempts FROM users LIMIT 1"))
        db.execute(text("SELECT key FROM request_limits LIMIT 1"))
        if settings.hardware_execution_enabled:
            db.execute(text("SELECT id FROM hardware_jobs LIMIT 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable or migrations missing") from None
    return {"status": "ready"}


@app.middleware("http")
async def bound_challenge_body(request, call_next):
    if request.url.path.startswith("/api/challenges") and request.method in {"POST", "PUT"}:
        from starlette.responses import JSONResponse
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 32768:
                return JSONResponse({"detail": "Activity request exceeds 32 KiB."}, status_code=413)
        request._body = bytes(body)
    return await call_next(request)
