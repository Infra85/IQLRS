from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import circuits, code, ai, auth, progress, collaborate

app = FastAPI(
    title=" IQLRS API",
    description="Backend API for Intelligent Quantum Learning and Reseach System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(circuits.router, prefix="/api/circuits", tags=["circuits"])
app.include_router(code.router, prefix="/api/code", tags=["code"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(collaborate.router, prefix="/api/collaborate", tags=["collaborate"])


@app.get("/")
def root():
    return {"status": "ok", "service": "IQLRS-API"}
