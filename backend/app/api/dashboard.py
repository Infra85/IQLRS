"""Authenticated dashboard derived from persisted learning and simulations."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User, Course, CourseEnrollment, ModuleProgress, AssessmentAttempt, SimulationRun, Circuit

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/me")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = current_user.user_id
    progress = db.query(ModuleProgress).filter_by(user_id=uid).all()
    attempts = db.query(AssessmentAttempt).filter_by(user_id=uid, status="submitted").all()
    runs = db.query(SimulationRun).filter_by(user_id=uid, status="completed")
    courses = []
    for course in db.query(Course).join(CourseEnrollment).filter(CourseEnrollment.user_id == uid).all():
        ids = {m.module_id for m in course.modules}
        completed = sum(p.status == "completed" for p in progress if p.module_id in ids)
        courses.append({"id": str(course.course_id), "name": course.title, "progress": round(100*completed/len(ids)) if ids else 0})
    recent = [{"title": f"Circuit simulation · {r.shots} shots", "at": r.completed_at, "href": "/builder"}
              for r in runs.order_by(SimulationRun.completed_at.desc()).limit(10)]
    for p in progress:
        if p.last_accessed_at:
            recent.append({"title": f"{p.module.title} · {p.status.replace('_', ' ')}", "at": p.last_accessed_at, "href": "/learn"})
    recent.sort(key=lambda item: item["at"], reverse=True)
    dates = {r[0].date() for r in runs.with_entities(SimulationRun.completed_at) if r[0]}
    dates |= {a.submitted_at.date() for a in attempts if a.submitted_at}
    day = datetime.now(timezone.utc).date()
    if day not in dates:
        day -= timedelta(days=1)
    streak = 0
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    return {"user": {"id": str(uid), "name": current_user.name, "email": current_user.email},
            "courses": courses, "recent_activity": recent[:10], "statistics": {
                "simulations": runs.count(), "circuits": db.query(Circuit).filter_by(user_id=uid).count(),
                "modules_completed": sum(p.status == "completed" for p in progress),
                "modules_started": len(progress), "quiz_attempts": len(attempts),
                "quiz_score": round(sum(a.percentage for a in attempts)/len(attempts)) if attempts else 0,
                "streak": streak}}
