"""Guided progress uses real assessment records and additive migrations."""

import json
from pathlib import Path
from uuid import uuid4
import pytest
from app.services.curriculum import MODULES, module_id
from app.services.lesson_journey import sequence
from app.services.learning_challenges import DEFINITIONS

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/learning_challenges.json").read_text()
)


def state(client, number=1):
    response = client.get("/api/progress/journey")
    assert response.status_code == 200, response.text
    return next(m for m in response.json()["modules"] if m["moduleId"] == number)


def update(client, key, action="complete", number=1):
    return client.put(
        f"/api/progress/lessons/{number}/journey",
        json={"step_id": key, "action": action},
    )


def activity(client, key):
    definition = DEFINITIONS[key]
    fixture = FIXTURES[key]
    payload = dict(
        module_id=definition["moduleId"],
        version=definition["version"],
        revision=str(uuid4()),
    )
    response = client.put(
        f"/api/challenges/{key}/prediction",
        json={
            **payload,
            "circuit": fixture["circuit"],
            "prediction": fixture["prediction"],
        },
    )
    assert response.status_code == 200, response.text
    if definition["kind"] == "circuit":
        response = client.post(f"/api/challenges/{key}/run", json=payload)
        assert response.status_code == 200, response.text
        assert (
            next(
                s
                for s in state(client, definition["moduleId"])["steps"]
                if s["id"] == key
            )["status"]
            == "in_progress"
        )
    response = client.post(f"/api/challenges/{key}/validate", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["result"]["passed"]


@pytest.mark.parametrize("lesson", MODULES, ids=lambda m: str(m["id"]))
def test_all_modules_full_sequence_and_resume(api, lesson):
    client, _ = api
    number = lesson["id"]
    initial = state(client, number)
    assert initial["status"] == "not_started"
    assert [s["id"] for s in initial["steps"]] == [s["id"] for s in sequence(lesson)]
    for step in initial["steps"]:
        response = update(client, step["id"], "start", number)
        assert response.status_code == 200, response.text
        assert state(client, number)["resume"]["id"] == step["id"]
        if step["kind"] in {"section", "reflection"}:
            response = update(client, step["id"], number=number)
            assert response.status_code == 200, response.text
        elif step["kind"] == "quiz":
            response = client.post(
                f"/api/progress/lessons/{number}/quiz",
                json={"answers": [q["answerIndex"] for q in lesson["questions"]]},
            )
            assert response.status_code == 200
            assert state(client, number)["status"] != "completed"
        else:
            activity(client, step["id"])
    final = state(client, number)
    assert final["status"] == "completed"
    assert final["completionPct"] == 100
    assert final["resume"] is None
    assert final["completedSteps"] == final["totalSteps"]
    assert (
        update(client, initial["steps"][0]["id"], "start", number).json()["status"]
        == "completed"
    )


def test_validation_ownership_resume_and_retry(api, sessions):
    from app.models import User
    from app.core.security import create_access_token

    client, _ = api
    assert update(client, "unknown").status_code == 422
    assert update(client, "m1-challenge").status_code == 422
    assert update(client, "knowledge-check").status_code == 422
    assert update(client, "m1-experiment-reflection").status_code == 409
    assert update(client, "concept-0", "start").status_code == 200
    assert state(client)["resume"]["id"] == "concept-0"
    assert update(client, "concept-0").status_code == 200
    assert update(client, "concept-0").json()["completedSteps"] == 1
    client.post(
        "/api/progress/lessons/1/quiz",
        json={
            "answers": [
                (q["answerIndex"] + 1) % len(q["options"])
                for q in MODULES[0]["questions"]
            ]
        },
    )
    assert (
        next(s for s in state(client)["steps"] if s["kind"] == "quiz")["status"]
        == "retry_needed"
    )
    with sessions() as db:
        other = User(
            name="Other", email="journey-other@example.com", email_verified=True
        )
        db.add(other)
        db.commit()
        token = create_access_token({"sub": str(other.user_id)})
    client.headers["Authorization"] = "Bearer " + token
    assert state(client)["status"] == "not_started"
    client.headers.pop("Authorization")
    assert client.get("/api/progress/journey").status_code == 401
    assert update(client, "objectives").status_code == 401
    assert client.get("/api/progress/lessons/1/sequence").status_code == 200
    assert client.get("/api/progress/lessons/999/sequence").status_code == 404


def test_historical_quiz_does_not_finish_journey(api, sessions):
    from app.models import ModuleProgress

    client, uid = api
    with sessions() as db:
        db.add(
            ModuleProgress(
                user_id=uid,
                module_id=module_id(1),
                status="completed",
                completion_pct=100,
            )
        )
        db.commit()
    old = client.get("/api/progress/me").json()
    row = state(client)
    assert row["status"] == "in_progress"
    assert next(s for s in row["steps"] if s["kind"] == "quiz")["status"] == "completed"
    assert 1 in state(client, 2)["pendingPrerequisites"]
    update(client, "objectives")
    assert client.get("/api/progress/me").json() == old
    recent = client.get("/api/dashboard/me").json()["recent_activity"][0]
    assert recent["href"] == "/learn/1#guided-journey"
    assert recent["title"].endswith("in progress")


def test_upgrade_populated_progress_preserves_all_existing_columns(
    api, sessions, monkeypatch
):
    from sqlalchemy import text
    from app import migrate

    client, _ = api
    client.post(
        "/api/progress/lessons/1/quiz",
        json={"answers": [q["answerIndex"] for q in MODULES[0]["questions"]]},
    )
    activity(client, "m1-experiment")
    engine = sessions.kw["bind"]
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE module_progress DROP COLUMN journey"))
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version VALUES ('0003_learning_challenges')")
        )
        before = (
            connection.execute(text("SELECT row_to_json(p) FROM module_progress p"))
            .scalars()
            .all()
        )
        attempts = (
            connection.execute(text("SELECT row_to_json(a) FROM challenge_attempts a"))
            .scalars()
            .all()
        )
    monkeypatch.setattr(migrate, "engine", engine)
    migrate.migrate()
    migrate.migrate()
    with engine.begin() as connection:
        after = (
            connection.execute(
                text("SELECT to_jsonb(p) - 'journey' FROM module_progress p")
            )
            .scalars()
            .all()
        )
        assert before == after
        assert (
            attempts
            == connection.execute(
                text("SELECT row_to_json(a) FROM challenge_attempts a")
            )
            .scalars()
            .all()
        )
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "0004_lesson_journey"
        )
    # Exercise downgrade/re-upgrade only inside this disposable schema.
    from alembic import command
    from alembic.config import Config

    with engine.begin() as connection:
        config = Config()
        config.set_main_option(
            "script_location", str(Path(__file__).parents[1] / "migrations")
        )
        config.attributes["connection"] = connection
        command.downgrade(config, "0003_learning_challenges")
        command.upgrade(config, "head")
        assert (
            before
            == connection.execute(
                text("SELECT to_jsonb(p) - 'journey' FROM module_progress p")
            )
            .scalars()
            .all()
        )
        assert (
            attempts
            == connection.execute(
                text("SELECT row_to_json(a) FROM challenge_attempts a")
            )
            .scalars()
            .all()
        )
    assert state(client)["status"] == "in_progress"
    assert update(client, "objectives").status_code == 200


def test_failed_challenge_is_retry_needed_and_success_survives_later_failure(api):
    client, _ = api
    key = "m1-challenge"
    d = DEFINITIONS[key]

    def fail_attempt():
        payload = dict(module_id=1, version=d["version"], revision=str(uuid4()))
        assert (
            client.put(
                f"/api/challenges/{key}/prediction",
                json={
                    **payload,
                    "circuit": d["starterCircuit"],
                    "prediction": FIXTURES[key]["prediction"],
                },
            ).status_code
            == 200
        )
        assert (
            client.post(f"/api/challenges/{key}/run", json=payload).status_code == 200
        )
        assert not client.post(f"/api/challenges/{key}/validate", json=payload).json()[
            "result"
        ]["passed"]

    fail_attempt()
    assert (
        next(s for s in state(client)["steps"] if s["id"] == key)["status"]
        == "retry_needed"
    )
    activity(client, key)
    fail_attempt()
    assert (
        next(s for s in state(client)["steps"] if s["id"] == key)["status"]
        == "completed"
    )
    detail = client.get(f"/api/challenges/{key}").json()
    assert detail["workspace"]["feedback"]["passed"] is False
    assert len(detail["history"]) == 3


def test_concurrent_section_updates_preserve_both_acknowledgements(api, sessions):
    from concurrent.futures import ThreadPoolExecutor
    from app.api.progress import JourneyUpdate, update_journey
    from app.models import User

    client, uid = api

    def mark(key):
        with sessions() as db:
            return update_journey(
                1, JourneyUpdate(step_id=key, action="complete"), db.get(User, uid), db
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(mark, ["objectives", "concept-0"]))
    assert all(r["moduleId"] == 1 for r in results)
    row = state(client)
    assert row["completedSteps"] == 2
    assert all(
        s["status"] == "completed"
        for s in row["steps"]
        if s["id"] in {"objectives", "concept-0"}
    )
