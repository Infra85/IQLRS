from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register(payload: dict):
    """Register a new user."""
    # TODO: Create user in database
    return {"status": "not_implemented"}


@router.post("/login")
async def login(payload: dict):
    """Authenticate a user."""
    # TODO: Verify credentials, return token
    return {"status": "not_implemented"}
