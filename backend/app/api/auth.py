from fastapi import APIRouter

from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter()


@router.post("/register")
async def register(payload: RegisterRequest):
    """Register a new user."""
    # TODO: Create user in database
    return {"status": "not_implemented"}


@router.post("/login")
async def login(payload: LoginRequest):
    """Authenticate a user."""
    # TODO: Verify credentials, return token
    return {"status": "not_implemented"}
