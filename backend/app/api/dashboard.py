from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user

from app.models.user import User
from app.models.gamification import UserGamification
from app.models.course import CourseEnrollment
from app.models.learning import (
    Course,
    LearningModule,
    ModuleProgress,
)
from app.models.assessment import AssessmentAttempt
from app.models.challenge import (
    CodingChallenge,
    CodeSubmission,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/me")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.user_id

    # ---------------------------------------------------------
    # 1. Get current user
    # ---------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        return {
            "error": "User not found"
        }

    # ---------------------------------------------------------
    # 2. Course progress
    # ---------------------------------------------------------

    courses_data = []

    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id)
        .all()
    )

    for enrollment in enrollments:

        course = (
            db.query(Course)
            .filter(
                Course.course_id == enrollment.course_id
            )
            .first()
        )

        if not course:
            continue

        modules = (
            db.query(LearningModule)
            .filter(
                LearningModule.course_id == course.course_id
            )
            .all()
        )

        total_modules = len(modules)

        completed_modules = 0

        for module in modules:

            progress = (
                db.query(ModuleProgress)
                .filter(
                    ModuleProgress.user_id == user_id,
                    ModuleProgress.module_id == module.module_id,
                )
                .first()
            )

            if progress and progress.status == "completed":
                completed_modules += 1

        progress_percentage = (
            round(
                (completed_modules / total_modules) * 100
            )
            if total_modules > 0
            else 0
        )

        courses_data.append(
            {
                "id": str(course.course_id),
                "name": course.title,
                "progress": progress_percentage,
            }
        )

    # ---------------------------------------------------------
    # 3. Quiz score
    # ---------------------------------------------------------

    attempts = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.user_id == user_id
        )
        .all()
    )

    scores = [
        attempt.score
        for attempt in attempts
        if attempt.score is not None
    ]

    if scores:
        quiz_score = round(
            sum(scores) / len(scores)
        )
    else:
        quiz_score = 0

    # ---------------------------------------------------------
    # 4. Coding challenges
    # ---------------------------------------------------------

    total_challenges = (
        db.query(CodingChallenge).count()
    )

    completed_challenges = (
        db.query(CodeSubmission)
        .filter(
            CodeSubmission.user_id == user_id,
            CodeSubmission.passed.is_(True),
        )
        .count()
    )

    # ---------------------------------------------------------
    # 5. Gamification
    # ---------------------------------------------------------

    gamification = (
        db.query(UserGamification)
        .filter(
            UserGamification.user_id == user_id
        )
        .first()
    )

    if gamification:
        xp = gamification.xp
        streak = gamification.current_streak
    else:
        xp = 0
        streak = 0

    # ---------------------------------------------------------
    # 6. Return dashboard data
    # ---------------------------------------------------------

    return {
        "user": {
            "id": str(user.user_id),
            "name": user.name,
            "email": user.email,
        },

        "courses": courses_data,

        "statistics": {
            "quiz_score": quiz_score,
            "challenges_completed": completed_challenges,
            "challenges_total": total_challenges,
            "streak": streak,
            "xp": xp,
        },
    }