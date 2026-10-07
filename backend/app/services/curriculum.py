"""Stable identifiers for the bundled curriculum; never overwrite user content."""

import json
import hashlib
import logging
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.schemas.curriculum import validate_curriculum

DATA = Path(__file__).resolve().parents[2] / "data"
MODULES = validate_curriculum(json.loads((DATA / "modules.json").read_text()))
PREVIOUS = json.loads((DATA / "curriculum_previous.json").read_text())
COURSE_ID = uuid5(NAMESPACE_URL, "https://iqlrs/curriculum/foundations")
AUTHOR_ID = uuid5(NAMESPACE_URL, "https://iqlrs/curriculum/author")


def module_id(number):
    return uuid5(NAMESPACE_URL, f"https://iqlrs/curriculum/modules/{number}")


def assessment_id(number):
    return uuid5(NAMESPACE_URL, f"https://iqlrs/curriculum/quizzes/{number}")


def content_fingerprint(content):
    """Canonical JSON hash tolerates formatting differences, but no content edits."""
    canonical = json.dumps(
        content, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def upgrade_bundled_content(db):
    """Upgrade only the exact previous publisher-owned bundle; retain all activity.

    Called by the existing migration/seed transaction. Unknown or edited rows are
    left intact and reported, never treated as permission to overwrite content.
    """
    from app.models import Course, LearningModule, Assessment

    course = db.get(Course, COURSE_ID)
    if not course or course.created_by != AUTHOR_ID:
        logging.getLogger(__name__).warning(
            "Preserved curriculum with unrecognized course ownership; review manually"
        )
        return
    for lesson in MODULES:
        row = db.get(LearningModule, module_id(lesson["id"]))
        if not row:
            continue
        try:
            stored = json.loads(row.content or "null")
        except (ValueError, TypeError):
            stored = None
        if stored == lesson:
            continue
        previous = PREVIOUS[str(lesson["id"])]
        assessment = db.get(Assessment, assessment_id(lesson["id"]))
        if (
            row.course_id == COURSE_ID
            and row.module_order == lesson["id"]
            and row.title == previous["title"]
            and row.description is None
            and row.difficulty == "beginner"
            and row.estimated_minutes is None
            and content_fingerprint(stored) == previous["sha256"]
            and assessment
            and assessment.module_id == row.module_id
            and assessment.max_score == previous["questionCount"]
            and assessment.passing_score == previous["questionCount"]
            and assessment.title == "Knowledge check"
            and assessment.description is None
            and assessment.assessment_type == "quiz"
            and not assessment.questions
        ):
            row.content = json.dumps(lesson)
            row.title = lesson["title"]
            row.difficulty = lesson["difficulty"]
            row.estimated_minutes = lesson["estimatedMinutes"]
            assessment.max_score = len(lesson["questions"])
            assessment.passing_score = len(lesson["questions"])
        else:
            logging.getLogger(__name__).warning(
                "Preserved customized or unrecognized curriculum module %s; review manually",
                lesson["id"],
            )


def seed_curriculum(db):
    from app.models import User, Course, LearningModule, Assessment

    if not db.get(User, AUTHOR_ID):
        db.add(
            User(
                user_id=AUTHOR_ID,
                name="IQLRS Curriculum",
                email="curriculum@iqlrs.invalid",
                email_verified=False,
            )
        )
        db.flush()
    if not db.get(Course, COURSE_ID):
        db.add(
            Course(
                course_id=COURSE_ID,
                title="Quantum computing foundations",
                created_by=AUTHOR_ID,
                is_published=True,
            )
        )
        db.flush()
    for lesson in MODULES:
        mid, aid = module_id(lesson["id"]), assessment_id(lesson["id"])
        if not db.get(LearningModule, mid):
            db.add(
                LearningModule(
                    module_id=mid,
                    course_id=COURSE_ID,
                    title=lesson["title"],
                    content=json.dumps(lesson),
                    module_order=lesson["id"],
                    difficulty=lesson["difficulty"],
                    estimated_minutes=lesson["estimatedMinutes"],
                )
            )
            db.flush()
        if not db.get(Assessment, aid):
            db.add(
                Assessment(
                    assessment_id=aid,
                    module_id=mid,
                    title="Knowledge check",
                    max_score=len(lesson["questions"]),
                    passing_score=len(lesson["questions"]),
                )
            )
    db.flush()
    upgrade_bundled_content(db)
    db.flush()
