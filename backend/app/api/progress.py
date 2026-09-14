"""Learning progress API."""

from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.assessment import AssessmentAttempt
from app.models.course import CourseEnrollment
from app.services.curriculum import MODULES, COURSE_ID, module_id, assessment_id
from app.services.curriculum import module_id as module_id_for_lesson

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.learning import LearningModule, ModuleProgress


class QuizSubmission(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=100)


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


@router.post("/lessons/{number}/quiz")
def submit_quiz(number: int, payload: QuizSubmission, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lesson = next((m for m in MODULES if m["id"] == number), None)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    if len(payload.answers) != len(lesson["questions"]) or any(a < 0 or a >= len(q["options"]) for a, q in zip(payload.answers, lesson["questions"])):
        raise HTTPException(422, "Submit one valid answer for each question")
    mid = module_id(number)
    if not db.get(LearningModule, mid):
        raise HTTPException(503, "Curriculum unavailable. Run database migrations.")
    # Serialize updates for this user across workers; avoid duplicate progress/enrollment.
    db.query(User).filter_by(user_id=current_user.user_id).with_for_update().one()
    now = datetime.now(timezone.utc)
    score = sum(a == q["answerIndex"] for a, q in zip(payload.answers, lesson["questions"]))
    total = len(lesson["questions"])
    db.add(AssessmentAttempt(assessment_id=assessment_id(number), user_id=current_user.user_id, score=score, max_score=total, percentage=100*score/total, status="submitted", submitted_at=now))
    progress = db.query(ModuleProgress).filter_by(user_id=current_user.user_id, module_id=mid).first()
    if not progress:
        progress = ModuleProgress(user_id=current_user.user_id, module_id=mid, started_at=now, completion_pct=0)
        db.add(progress)
    progress.completion_pct = max(progress.completion_pct, round(100*score/total))
    progress.status = "completed" if progress.completion_pct == 100 else "in_progress"
    progress.last_accessed_at = now
    if progress.status == "completed" and not progress.completed_at:
        progress.completed_at = now
    if not db.query(CourseEnrollment).filter_by(user_id=current_user.user_id, course_id=COURSE_ID).first():
        db.add(CourseEnrollment(user_id=current_user.user_id, course_id=COURSE_ID))
    db.commit()
    return {"score": score, "total": total, "completion_pct": progress.completion_pct, "status": progress.status}


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

    if status_value not in {None, "not_started", "in_progress", "completed"}:
        raise HTTPException(422, "Invalid progress status")
    if module_id in {module_id_for_lesson(m["id"]) for m in MODULES}:
        raise HTTPException(400, "Complete the lesson quiz to update bundled curriculum progress.")

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