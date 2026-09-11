"""Learning progress API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.learning import LearningModule, ModuleProgress


router = APIRouter(
    prefix="/api/progress",
    tags=["Progress"],
)


@router.get("/me")
def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get learning progress for the logged-in user."""

    progress_records = (
        db.query(ModuleProgress)
        .filter(ModuleProgress.user_id == current_user.user_id)
        .all()
    )

    result = []

    for progress in progress_records:
        module = (
            db.query(LearningModule)
            .filter(LearningModule.module_id == progress.module_id)
            .first()
        )

        result.append(
            {
                "module_id": str(progress.module_id),
                "module_title": module.title if module else None,
                "status": progress.status,
                "completion_pct": progress.completion_pct,
            }
        )

    return {
        "user_id": str(current_user.user_id),
        "progress": result,
    }


@router.get("/{user_id}")
def get_progress(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get learning progress for a specific user."""

    # Users can only access their own progress.
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this user's progress.",
        )

    progress_records = (
        db.query(ModuleProgress)
        .filter(ModuleProgress.user_id == user_id)
        .all()
    )

    result = []

    for progress in progress_records:
        module = (
            db.query(LearningModule)
            .filter(LearningModule.module_id == progress.module_id)
            .first()
        )

        result.append(
            {
                "module_id": str(progress.module_id),
                "module_title": module.title if module else None,
                "status": progress.status,
                "completion_pct": progress.completion_pct,
            }
        )

    return {
        "user_id": str(user_id),
        "progress": result,
    }


@router.post("/{user_id}/update")
def update_progress(
    user_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update learning progress for a module."""

    # Users can only update their own progress.
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this user's progress.",
        )

    module_id = payload.get("module_id")

    if not module_id:
        raise HTTPException(
            status_code=400,
            detail="module_id is required.",
        )

    try:
        module_id = UUID(str(module_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid module_id.",
        )

    # Make sure the module exists.
    module = (
        db.query(LearningModule)
        .filter(LearningModule.module_id == module_id)
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=404,
            detail="Learning module not found.",
        )

    progress = (
        db.query(ModuleProgress)
        .filter(
            ModuleProgress.user_id == user_id,
            ModuleProgress.module_id == module_id,
        )
        .first()
    )

    completion_pct = payload.get("completion_pct")
    status_value = payload.get("status")

    if completion_pct is not None:
        try:
            completion_pct = int(completion_pct)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="completion_pct must be a number.",
            )

        if completion_pct < 0 or completion_pct > 100:
            raise HTTPException(
                status_code=400,
                detail="completion_pct must be between 0 and 100.",
            )

    if progress:
        # Update existing progress.
        if completion_pct is not None:
            progress.completion_pct = completion_pct

        if status_value is not None:
            progress.status = status_value

    else:
        # Create new progress record.
        progress = ModuleProgress(
            user_id=user_id,
            module_id=module_id,
            status=status_value or "in_progress",
            completion_pct=completion_pct if completion_pct is not None else 0,
        )

        db.add(progress)

    db.commit()
    db.refresh(progress)

    return {
        "message": "Progress updated successfully.",
        "progress": {
            "module_id": str(progress.module_id),
            "status": progress.status,
            "completion_pct": progress.completion_pct,
        },
    }