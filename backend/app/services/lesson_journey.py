"""Orchestrate existing lessons and assessments; never duplicate their grading."""

from app.services.curriculum import MODULES, module_id, assessment_id
from app.services.learning_challenges import DEFINITIONS
from app.models.learning import ModuleProgress
from app.models.learning_challenge import ChallengeAttempt, ChallengeWorkspace
from app.models.assessment import AssessmentAttempt


def sequence(lesson):
    number = lesson["id"]
    steps = []

    def reading(key, title, kind="section", **extra):
        steps.append(
            dict(id=key, title=title, kind=kind, href=f"/learn/{number}#{key}", **extra)
        )

    reading("objectives", "Learning objectives")
    for index, section in enumerate(lesson["sections"]):
        reading(f"concept-{index}", section["title"])
    reading("example", "Worked example and takeaways")
    for activity in lesson["experiments"]:
        steps.append(
            dict(
                id=activity["id"],
                title=activity["title"],
                kind="experiment",
                href=f"/builder?module={number}&challenge={activity['id']}",
            )
        )
        reading(
            f"{activity['id']}-reflection",
            "Compare and explain",
            "reflection",
            activityId=activity["id"],
            explanation=DEFINITIONS[activity["id"]]["reflection"],
        )
    reading("knowledge-check", "Knowledge check", "quiz")
    for activity in lesson["challenges"]:
        steps.append(
            dict(
                id=activity["id"],
                title=activity["title"],
                kind="challenge",
                href=f"/builder?module={number}&challenge={activity['id']}",
            )
        )
    return steps


def journey(db, uid, lesson):
    number = lesson["id"]
    progress = (
        db.query(ModuleProgress)
        .filter_by(user_id=uid, module_id=module_id(number))
        .first()
    )
    saved = (progress.journey if progress else None) or {}
    # Reading identities are scoped to the authored curriculum version.
    if saved.get("version") != lesson["curriculumVersion"]:
        saved = {}
    attempts = db.query(ChallengeAttempt).filter_by(user_id=uid, module_id=number).all()
    workspaces = {
        w.challenge_id: w.revision
        for w in db.query(ChallengeWorkspace).filter_by(user_id=uid).all()
    }
    quizzes = (
        db.query(AssessmentAttempt)
        .filter_by(user_id=uid, assessment_id=assessment_id(number), status="submitted")
        .all()
    )
    steps = sequence(lesson)
    for step in steps:
        key = step["id"]
        status = "not_started"
        if key in saved.get("started", []) or key in workspaces:
            status = "in_progress"
        if step["kind"] in {"section", "reflection"}:
            if key in saved.get("completed", []):
                status = "completed"
        elif step["kind"] == "quiz":
            # Existing perfect quiz records remain valid, even if old answers were not stored.
            if any(a.percentage == 100 for a in quizzes) or (
                progress and progress.completion_pct == 100
            ):
                status = "completed"
            elif quizzes:
                status = "retry_needed"
        else:
            rows = [a for a in attempts if a.challenge_id == key]
            if any(a.passed for a in rows):
                status = "completed"
            elif rows:
                latest = max(rows, key=lambda a: a.number)
                status = (
                    "in_progress"
                    if key in workspaces and workspaces[key] != latest.revision
                    else "retry_needed"
                )
        step["status"] = status
    incomplete = [s for s in steps if s["status"] != "completed"]
    resume = next((s for s in incomplete if s["id"] == saved.get("current")), None)
    resume = resume or (incomplete[0] if incomplete else None)
    completed = len(steps) - len(incomplete)
    return dict(
        moduleId=number,
        title=lesson["title"],
        steps=steps,
        status="completed"
        if not incomplete
        else "in_progress"
        if completed or any(s["status"] != "not_started" for s in steps)
        else "not_started",
        completedSteps=completed,
        totalSteps=len(steps),
        completionPct=round(100 * completed / len(steps)),
        resume=resume,
        next=incomplete[0] if incomplete else None,
        prerequisites=lesson["prerequisites"],
        updatedAt=progress.last_accessed_at.isoformat()
        if progress and progress.last_accessed_at
        else None,
    )


def journeys(db, uid):
    rows = [journey(db, uid, lesson) for lesson in MODULES]
    by_id = {r["moduleId"]: r for r in rows}
    for row in rows:
        row["pendingPrerequisites"] = [
            n for n in row["prerequisites"] if by_id[n]["status"] != "completed"
        ]
        following = next(
            (
                r
                for r in rows
                if r["status"] != "completed"
                and all(by_id[n]["status"] == "completed" for n in r["prerequisites"])
            ),
            None,
        )
        row["nextModule"] = following["moduleId"] if following else None
    return rows
