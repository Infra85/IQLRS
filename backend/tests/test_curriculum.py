"""Schema, stable identity, safe bundle upgrades and every lesson's quiz API."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.schemas.curriculum import validate_curriculum
from app.services.curriculum import (
    MODULES,
    PREVIOUS,
    COURSE_ID,
    module_id,
    assessment_id,
    seed_curriculum,
    content_fingerprint,
)

# Frozen public identities from the pre-Phase-1 baseline (not recomputed expectations).
MODULE_IDS = [
    "21fb6ff6-20bf-5ec7-9ff3-5ae9feb201cd",
    "0ca89265-a088-5cc7-a9e7-ee45c7532f07",
    "71866d40-2083-51da-a04c-00f4c6ce1d70",
    "9ec6a1c6-37cc-59cf-abf7-9ffbe0cc3ed1",
    "49d52e9a-afaf-50c7-afe4-e3f2665ca1d0",
    "908d7c3b-b605-5b1c-8f73-ad7c36699a88",
    "e80407bd-f43c-500b-922d-41be8c827107",
    "fcf73081-3044-5fca-8dde-db2c4ecb878a",
]
ASSESSMENT_IDS = [
    "dd504d03-7e8e-57fc-b70e-2440b4fd59a4",
    "cff5cb97-3e7a-5180-b4cb-b23784e945f5",
    "f007c2eb-971a-5b9a-ae07-59d29b7c516e",
    "466fd281-aa59-552b-a7d7-ab40870b1fae",
    "8d04885c-1bb1-5d64-9c60-781c6cc9583f",
    "02a5241f-6174-5d1f-a5ca-dfd9c5c018b6",
    "b8f0ceb2-5d56-5b62-b712-37fdf2d22310",
    "7c5633a5-4861-53e5-9745-3c044bade7ed",
]
OLD = json.loads((Path(__file__).parent / "fixtures/curriculum_v1.json").read_text())


def test_bundle_and_stable_ids():
    assert validate_curriculum(MODULES) is MODULES
    assert [m["id"] for m in MODULES] == list(range(1, 9))
    assert [str(module_id(i)) for i in range(1, 9)] == MODULE_IDS
    assert [str(assessment_id(i)) for i in range(1, 9)] == ASSESSMENT_IDS
    for old, new in zip(OLD, MODULES):
        assert content_fingerprint(old) == PREVIOUS[str(old["id"])]["sha256"]
        assert set(old) <= set(new)
        assert old["tryInBuilder"] == new["tryInBuilder"]
        assert old.get("builderLink") == new.get("builderLink")
        assert len(new["questions"]) >= len(old["questions"])


@pytest.mark.parametrize(
    "field",
    [
        "difficulty",
        "estimatedMinutes",
        "prerequisites",
        "learningObjectives",
        "mathematicalLevel",
        "references",
        "experiments",
        "challenges",
        "sections",
        "questions",
        "objectives",
        "introduction",
        "workedExample",
        "keyTakeaways",
    ],
)
def test_required_fields(field):
    data = deepcopy(MODULES)
    del data[0][field]
    with pytest.raises(ValueError):
        validate_curriculum(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m[0].update(id=2),
        lambda m: m[0].update(prerequisites=[99]),
        lambda m: m[0].update(prerequisites=[2]),
        lambda m: m[0].update(estimatedMinutes=True),
        lambda m: m[0].update(difficulty="expert"),
        lambda m: m[0].update(references=[]),
        lambda m: m[0]["references"][0].update(url="javascript:alert(1)"),
        lambda m: m[0].update(learningObjectives=[]),
        lambda m: m[0].update(experiments=[]),
        lambda m: m[0]["challenges"][0].update(moduleId=2),
        lambda m: m[0]["challenges"][0].update(assessmentQuestionIndices=[99]),
        lambda m: m[0]["challenges"][0].update(id=m[0]["experiments"][0]["id"]),
        lambda m: m[0]["questions"][0].update(answerIndex=True),
        lambda m: m[0]["questions"][0].update(answerIndex=-1),
        lambda m: m[0]["questions"][0].update(answerIndex=4),
        lambda m: m[0]["questions"][0].update(options=["same", "same"]),
        lambda m: m[0]["questions"][0].update(explanation=" "),
    ],
)
def test_invalid_content_is_rejected(mutate):
    data = deepcopy(MODULES)
    mutate(data)
    with pytest.raises(ValueError):
        validate_curriculum(data)


def test_future_additive_fields_are_preserved():
    data = deepcopy(MODULES)
    data[0]["future"] = {"description": "static metadata"}
    assert validate_curriculum(data)[0]["future"] == data[0]["future"]


def install_previous(db):
    from app.models import LearningModule

    seed_curriculum(db)
    for old in OLD:
        row = db.get(LearningModule, module_id(old["id"]))
        row.content = json.dumps(old, indent=4)
        row.difficulty = "beginner"
        row.estimated_minutes = None
    db.commit()


def test_upgrade_preserves_progress_attempts_and_ids(sessions):
    from app.models import (
        LearningModule,
        Assessment,
        AssessmentAttempt,
        ModuleProgress,
        User,
    )

    with sessions() as db:
        install_previous(db)
        user = User(name="Existing learner", email="old@example.test")
        db.add(user)
        db.flush()
        progress = ModuleProgress(
            user_id=user.user_id,
            module_id=module_id(5),
            status="completed",
            completion_pct=100,
        )
        attempt = AssessmentAttempt(
            user_id=user.user_id,
            assessment_id=assessment_id(5),
            score=2,
            max_score=3,
            percentage=200 / 3,
            status="submitted",
        )
        db.add_all([progress, attempt])
        db.commit()
        pid, aid = progress.progress_id, attempt.attempt_id
        seed_curriculum(db)
        db.commit()
        timestamps = [
            db.get(LearningModule, module_id(i)).updated_at for i in range(1, 9)
        ]
        seed_curriculum(db)
        db.commit()
        assert db.query(LearningModule).count() == db.query(Assessment).count() == 8
        for lesson in MODULES:
            row = db.get(LearningModule, module_id(lesson["id"]))
            assert json.loads(row.content) == lesson
            assert row.difficulty == lesson["difficulty"]
            assert row.estimated_minutes == lesson["estimatedMinutes"]
        assert timestamps == [
            db.get(LearningModule, module_id(i)).updated_at for i in range(1, 9)
        ]
        assert db.get(ModuleProgress, pid).completion_pct == 100
        old_attempt = db.get(AssessmentAttempt, aid)
        assert (
            old_attempt.score,
            old_attempt.max_score,
            old_attempt.assessment_id,
        ) == (2, 3, assessment_id(5))


@pytest.mark.parametrize(
    "customization",
    ["content", "malformed", "title", "metadata", "assessment", "questions", "author"],
)
def test_upgrade_does_not_overwrite_customizations(sessions, customization):
    from app.models import (
        LearningModule,
        Assessment,
        Course,
        User,
        Question,
        QuestionOption,
    )

    with sessions() as db:
        install_previous(db)
        row = db.get(LearningModule, module_id(1))
        assessment = db.get(Assessment, assessment_id(1))
        if customization == "content":
            custom = deepcopy(OLD[0])
            custom["introduction"] = "An instructor edit"
            row.content = json.dumps(custom)
        elif customization == "malformed":
            row.content = "not JSON"
        elif customization == "title":
            row.title = "An instructor title"
        elif customization == "metadata":
            row.estimated_minutes = 90
        elif customization == "assessment":
            assessment.max_score = 20
        elif customization == "questions":
            question = Question(
                assessment_id=assessment.assessment_id, question_text="Custom question"
            )
            db.add(question)
            db.flush()
            db.add(
                QuestionOption(
                    question_id=question.question_id,
                    option_text="Custom option",
                    is_correct=True,
                )
            )
        else:
            author = User(name="Instructor", email="author@example.test")
            db.add(author)
            db.flush()
            db.get(Course, COURSE_ID).created_by = author.user_id
        db.commit()
        before = (row.content, row.title, row.estimated_minutes, assessment.max_score)
        seed_curriculum(db)
        db.commit()
        assert (
            row.content,
            row.title,
            row.estimated_minutes,
            assessment.max_score,
        ) == before
        if customization == "questions":
            assert db.query(QuestionOption).one().option_text == "Custom option"


@pytest.mark.parametrize("number", range(1, 9))
def test_every_lesson_scores_and_persists(api, sessions, number):
    from app.models import AssessmentAttempt

    client, uid = api
    questions = MODULES[number - 1]["questions"]
    correct = [q["answerIndex"] for q in questions]
    wrong = [(q["answerIndex"] + 1) % len(q["options"]) for q in questions]
    assert (
        client.post(
            f"/api/progress/lessons/{number}/quiz", json={"answers": correct[:-1]}
        ).status_code
        == 422
    )
    for answers, expected in [(wrong, 0), (correct, len(correct)), (wrong, 0)]:
        response = client.post(
            f"/api/progress/lessons/{number}/quiz", json={"answers": answers}
        )
        assert response.status_code == 200, response.text
        with sessions() as db:
            attempt = (
                db.query(AssessmentAttempt)
                .filter_by(user_id=uid)
                .order_by(AssessmentAttempt.submitted_at.desc())
                .first()
            )
            assert (attempt.score, attempt.max_score) == (expected, len(correct))
    progress = client.get("/api/progress/me").json()["progress"]
    assert progress[0]["completion_pct"] == 100
