from fastapi import APIRouter

router = APIRouter()


@router.get("/{user_id}")
async def get_progress(user_id: str):
    """Get learning progress for a user."""
    # TODO: Fetch from database
    return {"status": "not_implemented"}


@router.post("/{user_id}/update")
async def update_progress(user_id: str, payload: dict):
    """Update learning progress after module/quiz completion."""
    # TODO: Update database
    return {"status": "not_implemented"}
