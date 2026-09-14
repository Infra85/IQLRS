"""Stable identifiers for the bundled curriculum; never overwrite user content."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

MODULES = json.loads((Path(__file__).resolve().parents[2] / "data/modules.json").read_text())
COURSE_ID = uuid5(NAMESPACE_URL, "https://iqlrs/curriculum/foundations")
AUTHOR_ID = uuid5(NAMESPACE_URL, "https://iqlrs/curriculum/author")


def module_id(number):
    return uuid5(NAMESPACE_URL, f"https://iqlrs/curriculum/modules/{number}")


def assessment_id(number):
    return uuid5(NAMESPACE_URL, f"https://iqlrs/curriculum/quizzes/{number}")


def seed_curriculum(db):
    from app.models import User, Course, LearningModule, Assessment
    if not db.get(User, AUTHOR_ID):
        db.add(User(user_id=AUTHOR_ID, name="IQLRS Curriculum", email="curriculum@iqlrs.invalid", email_verified=False))
        db.flush()
    if not db.get(Course, COURSE_ID):
        db.add(Course(course_id=COURSE_ID, title="Quantum computing foundations", created_by=AUTHOR_ID, is_published=True))
        db.flush()
    for lesson in MODULES:
        mid, aid = module_id(lesson['id']), assessment_id(lesson['id'])
        if not db.get(LearningModule, mid):
            db.add(LearningModule(module_id=mid, course_id=COURSE_ID, title=lesson['title'], content=json.dumps(lesson), module_order=lesson['id']))
            db.flush()
        if not db.get(Assessment, aid):
            db.add(Assessment(assessment_id=aid, module_id=mid, title="Knowledge check", max_score=len(lesson['questions']), passing_score=len(lesson['questions'])))
    db.flush()
