"""Scientific, contract and security regressions for curriculum activities."""

import copy
import json
import math
from pathlib import Path
from uuid import uuid4
import pytest
from app.services.learning_challenges import (
    DEFINITIONS,
    execute,
    validate,
    fidelity,
    matches,
    comparison,
    canonical,
    load_definitions,
)
from app.schemas.learning_challenge import VALIDATORS, ValidationResult
from app.services.curriculum import MODULES

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/learning_challenges.json").read_text()
)


def evaluate(id, circuit=None, prediction=None):
    d = DEFINITIONS[id]
    f = FIXTURES[id]
    c = circuit or f["circuit"]
    p = prediction or f["prediction"]
    return validate(d, c, p, execute(c) if d["kind"] == "circuit" else None, 0)


@pytest.mark.parametrize("id", list(FIXTURES))
def test_all_real_scientific_reference_circuits(id):
    result = evaluate(id)
    assert result["passed"], result
    assert ValidationResult.model_validate(result).score == 100


def test_inventory_and_schema_integrity():
    assert load_definitions() == DEFINITIONS
    assert {d["moduleId"] for d in DEFINITIONS.values()} == set(range(1, 9))
    assert set(DEFINITIONS) == {
        a["id"] for m in MODULES for a in m["experiments"] + m["challenges"]
    }
    assert {r["type"] for d in DEFINITIONS.values() for r in d["rules"]} == VALIDATORS
    for d in DEFINITIONS.values():
        assert d["version"] == 1
        canonical(
            d["starterCircuit"]["gates"],
            d["starterCircuit"]["num_qubits"],
            d["starterCircuit"].get("classical_registers"),
        )


def test_global_phase_relative_phase_and_alternative_construction():
    s = 1 / math.sqrt(2)
    assert fidelity(
        [[0, s], [0, 0], [0, 0], [0, s]], [[s, 0], [0, 0], [0, 0], [s, 0]]
    ) == pytest.approx(1)
    assert fidelity(
        [[s, 0], [0, 0], [0, 0], [-s, 0]], [[s, 0], [0, 0], [0, 0], [s, 0]]
    ) == pytest.approx(0)
    c = {
        "num_qubits": 2,
        "gates": [
            {"type": "H", "qubit": 1},
            {"type": "CNOT", "control": 1, "target": 0},
        ],
        "shots": 32,
    }
    assert evaluate("m4-challenge", c)["passed"]
    c["gates"].append({"type": "Z", "qubit": 0})
    result = evaluate("m4-challenge", c)
    assert result["status"] == "near_miss"
    assert not result["checks"][1]["passed"]
    assert result["checks"][2]["passed"]


@pytest.mark.parametrize(
    "vector", [[], [[1, 0], [0]], [[float("nan"), 0], [0, 0]], [[2, 0], [0, 0]], None]
)
def test_malformed_state(vector):
    with pytest.raises(ValueError):
        fidelity(vector, [[1, 0], [0, 0]])


@pytest.mark.parametrize(
    "actual,ok",
    [
        ({"0": 0.52, "1": 0.48}, True),
        ({"0": 0.520001, "1": 0.479999}, False),
        ({"0": 1}, False),
        ({}, False),
        ({"0": float("nan")}, False),
        ({"0": 0.5}, False),
    ],
)
def test_probability_boundary_and_malformed(actual, ok):
    assert matches(actual, {"0": 0.5, "1": 0.5}, 0.02) == ok


def test_finite_shots_compare_ideal_not_sampling_noise():
    d = DEFINITIONS["m1-experiment"]
    p = {"0": 0.5, "1": 0.5}
    c = {**FIXTURES["m1-experiment"]["circuit"], "shots": 1}
    e = execute(c)
    assert max(e["simulation"]["counts"].values()) == 1
    assert comparison(d, p, e)["matches"]
    assert evaluate("m1-experiment", c)["passed"]


@pytest.mark.parametrize(
    "gates",
    [
        [{"type": "H", "qubit": 0}],
        [
            {"type": "X", "qubit": 0},
            {"type": "X", "qubit": 0},
            {"type": "X", "qubit": 0},
        ],
        [],
    ],
)
def test_gate_constraints_missing_forbidden_and_limit(gates):
    c = {"num_qubits": 1, "gates": gates, "shots": 32}
    assert not evaluate("m1-challenge", c)["checks"][1]["passed"]


def test_correlation_rejects_misleading_marginals():
    c = FIXTURES["m2-experiment"]["circuit"]
    r = evaluate("m4-challenge", c)
    assert not r["passed"] and not r["checks"][-1]["passed"]
    c = copy.deepcopy(FIXTURES["m4-challenge"]["circuit"])
    c["gates"].append({"type": "X", "qubit": 0})
    assert not evaluate("m4-challenge", c)["checks"][-1]["passed"]


def test_classical_order_wrong_oracle_and_malformed_output():
    assert evaluate("m5-challenge")["passed"]
    assert not evaluate("m5-challenge", FIXTURES["m5-experiment"]["circuit"])["passed"]
    c = copy.deepcopy(FIXTURES["m5-challenge"]["circuit"])
    c["gates"][-2]["destinations"][0]["bit"] = 1
    c["gates"][-1]["destinations"][0]["bit"] = 0
    assert not evaluate("m5-challenge", c)["passed"]
    assert not matches({"garbage": 1}, {"01": 1}, 0.02)


def test_teleportation_all_branches_not_last_shot_or_copying():
    c = copy.deepcopy(FIXTURES["m7-challenge"]["circuit"])
    assert evaluate("m7-challenge", c)["passed"]
    c["gates"][-1]["condition"]["bit"] = 1
    assert not evaluate("m7-challenge", c)["passed"]
    c = copy.deepcopy(FIXTURES["m7-challenge"]["circuit"])
    c["gates"] = c["gates"][:-2] + [{"type": "SWAP", "targets": [0, 2]}]
    assert not evaluate("m7-challenge", c)["passed"]


def test_state_target_rejects_last_shot_collapse():
    c = copy.deepcopy(FIXTURES["m4-challenge"]["circuit"])
    c["gates"].append({"type": "MEASURE_ALL"})
    assert not evaluate("m4-challenge", c)["checks"][1]["passed"]


@pytest.mark.parametrize("id", ["m3-experiment", "m5-challenge", "m7-challenge"])
def test_changed_scaffold_register_is_feedback_not_service_failure(api, id):
    client, _ = api
    c = copy.deepcopy(FIXTURES[id]["circuit"])
    c["classical_registers"] = [{"name": "renamed", "size": 2}]
    for gate in c["gates"]:
        if gate["type"] == "MEASURE" and not gate.get("destinations"):
            gate["destinations"] = [{"register": "renamed", "bit": gate["qubit"]}]
        for destination in gate.get("destinations", []):
            destination["register"] = "renamed"
        if gate.get("condition"):
            gate["condition"]["register"] = "renamed"
    response, payload = post_prediction(client, id, circuit=c)
    assert response.status_code == 200, response.text
    base = f"/api/challenges/{id}"
    assert client.post(base + "/run", json=payload).status_code == 200
    result = client.post(base + "/validate", json=payload)
    assert result.status_code == 200, result.text
    assert not result.json()["result"]["passed"]
    assert len(client.get(base).json()["history"]) == 1


def post_prediction(client, id="m4-challenge", circuit=None, **overrides):
    f = FIXTURES[id]
    d = DEFINITIONS[id]
    body = {
        "module_id": d["moduleId"],
        "version": d["version"],
        "revision": str(uuid4()),
        "circuit": circuit or f["circuit"],
        "prediction": f["prediction"],
        **overrides,
    }
    response = client.put(f"/api/challenges/{id}/prediction", json=body)
    return response, {k: body[k] for k in ["module_id", "version", "revision"]}


def test_api_lifecycle_persistence_idempotency_and_quiz_separation(api, sessions):
    from app.models import ChallengeAttempt, ModuleProgress

    client, uid = api
    bad = {"num_qubits": 2, "gates": [], "shots": 64}
    response, p = post_prediction(client, circuit=bad)
    assert response.status_code == 200, response.text
    base = "/api/challenges/m4-challenge"
    assert client.post(base + "/validate", json=p).status_code == 409
    run = client.post(base + "/run", json=p)
    assert run.status_code == 200, run.text
    assert not run.json()["comparison"]["matches"]
    assert client.post(base + "/run", json=p).json() == run.json()
    result = client.post(base + "/validate", json=p)
    assert result.status_code == 200, result.text
    assert result.json()["result"]["status"] == "incorrect"
    hint = {"module_id": 4, "version": 1, "index": 1}
    assert (
        client.post(base + "/hints", json=hint).json()
        == client.post(base + "/hints", json=hint).json()
    )
    response, p = post_prediction(client)
    assert response.status_code == 200
    assert client.post(base + "/run", json=p).status_code == 200
    good = client.post(base + "/validate", json=p)
    assert good.status_code == 200, good.text
    assert good.json()["result"]["score"] == 90
    assert (
        client.post(base + "/validate", json=p).json()["attempt"]
        == good.json()["attempt"]
    )
    detail = client.get(base + "?module=4").json()
    assert (
        detail["completed"]
        and detail["bestScore"] == 90
        and len(detail["history"]) == 2
    )
    assert detail["workspace"]["prediction"] == FIXTURES["m4-challenge"]["prediction"]
    with sessions() as db:
        assert db.query(ChallengeAttempt).filter_by(user_id=uid).count() == 2
        assert db.query(ModuleProgress).filter_by(user_id=uid).count() == 0
    assert client.get(base + "/attempts/1").json()["circuit"]["gates"] == []


@pytest.mark.parametrize(
    "override,status",
    [
        ({"module_id": 3}, 422),
        ({"version": 999}, 409),
        ({"prediction": {"00": float(2)}}, 422),
        ({"prediction": {"00": -1, "01": 0, "10": 0, "11": 2}}, 422),
        ({"passed": True}, 422),
        ({"score": 100}, 422),
        ({"hints_used": 0}, 422),
        ({"circuit": {"num_qubits": 4, "gates": []}}, 422),
        (
            {"circuit": {"num_qubits": 2, "gates": [{"type": "X", "qubit": 0}] * 65}},
            422,
        ),
        ({"circuit": {"num_qubits": 2, "gates": [{"type": "QFT", "qubit": 0}]}}, 422),
        (
            {
                "circuit": {
                    "num_qubits": 2,
                    "gates": [{"type": "CNOT", "control": 0, "target": 0}],
                }
            },
            422,
        ),
    ],
)
def test_api_input_boundaries(api, override, status):
    client, _ = api
    response, _ = post_prediction(client, **override)
    assert response.status_code == status, response.text


def test_api_unknown_auth_large_body_and_ownership(api, sessions):
    from app.models import User
    from app.core.security import create_access_token

    client, _ = api
    assert client.get("/api/challenges/nope").status_code == 404
    assert client.get("/api/challenges/m4-challenge?module=3").status_code == 422
    assert (
        client.get("/api/challenges/bell").json()["definition"]["id"] == "m4-challenge"
    )
    r, p = post_prediction(client)
    assert r.status_code == 200
    assert (
        client.post(
            "/api/challenges/m4-challenge/prediction", content="x" * 33000
        ).status_code
        == 413
    )
    with sessions() as db:
        u = User(name="Other", email="other@tests.invalid", email_verified=True)
        db.add(u)
        db.commit()
        token = create_access_token({"sub": str(u.user_id)})
    original = client.headers["Authorization"]
    client.headers["Authorization"] = "Bearer " + token
    assert client.get("/api/challenges/m4-challenge").json()["workspace"] is None
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 409
    assert client.get("/api/challenges/m4-challenge/attempts/1").status_code == 404
    client.headers["Authorization"] = "Bearer invalid"
    assert client.get("/api/challenges").status_code == 401
    del client.headers["Authorization"]
    assert client.get("/api/challenges").status_code == 401
    client.headers["Authorization"] = original


def test_simulation_failure_recoverable(api, monkeypatch):
    from app.api import learning_challenges as routes

    client, _ = api
    r, p = post_prediction(client)
    monkeypatch.setattr(
        routes,
        "execute",
        lambda _: (_ for _ in ()).throw(RuntimeError("private stack detail")),
    )
    response = client.post("/api/challenges/m4-challenge/run", json=p)
    assert response.status_code == 503
    assert "private" not in response.text
    assert client.get("/api/challenges/m4-challenge").json()["workspace"]


def test_stale_revision_and_fingerprint_conflict(api):
    client, _ = api
    _, p = post_prediction(client)
    r, _ = post_prediction(
        client, revision=p["revision"], prediction={"00": 1, "01": 0, "10": 0, "11": 0}
    )
    assert r.status_code == 409
    post_prediction(client)
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 409


def test_concurrent_validation_creates_one_attempt(api, sessions):
    from concurrent.futures import ThreadPoolExecutor
    from app.models import ChallengeAttempt

    client, uid = api
    _, p = post_prediction(client)
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(
            pool.map(
                lambda _: client.post("/api/challenges/m4-challenge/validate", json=p),
                range(2),
            )
        )
    assert [r.status_code for r in replies] == [200, 200]
    assert replies[0].json()["attempt"]["id"] == replies[1].json()["attempt"]["id"]
    with sessions() as db:
        assert db.query(ChallengeAttempt).filter_by(user_id=uid).count() == 1


def test_conceptual_completion_without_fake_simulation(api):
    client, _ = api
    r, p = post_prediction(client, "m8-challenge")
    assert r.status_code == 200, r.text
    assert client.post("/api/challenges/m8-challenge/run", json=p).status_code == 422
    r = client.post("/api/challenges/m8-challenge/validate", json=p)
    assert r.status_code == 200 and r.json()["result"]["passed"]


def test_definition_upgrade_keeps_history_but_rejects_old_revision_replay(api, monkeypatch):
    client, _ = api
    id = "m8-challenge"
    base = f"/api/challenges/{id}"
    _, payload = post_prediction(client, id)
    original = client.post(base + "/validate", json=payload).json()
    monkeypatch.setitem(DEFINITIONS, id, {**DEFINITIONS[id], "version": 2})
    detail = client.get(base).json()
    assert detail["workspace"] is None
    assert detail["completed"] and detail["bestScore"] == 100
    assert client.get(base + "/attempts/1").json()["result"] == original["result"]
    assert client.post(base + "/validate", json=payload).status_code == 409
    assert client.post(base + "/validate", json={**payload, "version": 2}).status_code == 409
    response, fresh = post_prediction(client, id)
    assert response.status_code == 200
    result = client.post(base + "/validate", json=fresh)
    assert result.status_code == 200
    assert result.json()["result"]["version"] == 2
    assert result.json()["attempt"]["number"] == 2


def test_migration_upgrade_preserves_data_and_downgrades(api, sessions, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect, select
    from app.core.database import Base
    from app.models import ChallengeAttempt, ChallengeWorkspace, AssessmentAttempt, Question, QuestionAnswer
    from app import migrate as entrypoint

    client, uid = api
    quiz = client.post("/api/progress/lessons/4/quiz", json={"answers": [0, 0, 0]})
    assert quiz.status_code == 200, quiz.text
    with sessions() as db:
        historical = db.query(AssessmentAttempt).filter_by(user_id=uid).one()
        question = Question(assessment_id=historical.assessment_id, question_text="Historical assessment prompt")
        db.add(question)
        db.flush()
        db.add(QuestionAnswer(attempt_id=historical.attempt_id, question_id=question.question_id,
                              answer_text="Historical learner answer", is_correct=False, points_earned=0))
        db.commit()
    simulation = client.post("/api/circuits/simulate", json=FIXTURES["m4-challenge"]["circuit"])
    assert simulation.status_code == 200, simulation.text
    protected = [t for t in Base.metadata.sorted_tables if not t.name.startswith("challenge_")]

    def snapshot():
        with sessions().get_bind().connect() as connection:
            return {
                t.name: sorted(json.dumps(dict(r), sort_keys=True, default=str)
                               for r in connection.execute(select(t)).mappings())
                for t in protected
            }

    before = snapshot()
    for name in ["assessment_attempts", "question_answers", "module_progress", "circuits", "circuit_versions", "simulation_runs", "simulation_results"]:
        assert before[name], f"Preservation fixture must exercise {name}"
    with sessions().get_bind().begin() as connection:
        ChallengeAttempt.__table__.drop(connection)
        ChallengeWorkspace.__table__.drop(connection)
        config = Config()
        config.set_main_option(
            "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
        )
        config.attributes["connection"] = connection
        command.stamp(config, "0002_hardware_jobs")
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        assert inspect(connection).has_table("challenge_attempts")
        command.downgrade(config, "0002_hardware_jobs")
        assert not inspect(connection).has_table("challenge_attempts")
        assert inspect(connection).has_table("hardware_jobs")
        command.upgrade(config, "head")
    monkeypatch.setattr(entrypoint, "engine", sessions.kw["bind"])
    entrypoint.migrate()
    entrypoint.migrate()
    assert snapshot() == before


def test_no_client_targets_rate_limits_and_bounded_history(api, sessions):
    from app.models import ChallengeAttempt
    from app.models.rate_limit import RateLimit

    client, uid = api
    r, _ = post_prediction(client, expected={"00": 1})
    assert r.status_code == 422
    _, p = post_prediction(client)
    hint = {"module_id": 4, "version": 1, "index": 3}
    assert (
        client.post("/api/challenges/m4-challenge/hints", json=hint).status_code == 422
    )
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 200
    with sessions() as db:
        for counter in db.query(RateLimit).all():
            counter.count = 10000
        db.commit()
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 429


def test_definition_drift_rejected(monkeypatch):
    import app.services.learning_challenges as svc

    original = json.loads(
        (Path(__file__).parents[1] / "data/challenges.json").read_text()
    )
    for mutate in [
        lambda d: d[0].update(moduleId=99),
        lambda d: d[0]["rules"][0].update(type="unknown"),
        lambda d: d[0]["starterCircuit"]["gates"].append({"type": "FAKE", "qubit": 0}),
        lambda d: d[0]["rules"][0].update(target={"0": 2}),
    ]:
        changed = copy.deepcopy(original)
        mutate(changed)
        with monkeypatch.context() as m:
            m.setattr(svc.json, "loads", lambda _: changed)
            with pytest.raises(ValueError):
                svc.load_definitions()


def test_frontend_backend_contract_fixture():
    from app.services.learning_challenges import public_definition

    fixture = json.loads(
        (
            Path(__file__).parents[2]
            / "frontend/tests/fixtures/challenge-contract.json"
        ).read_text()
    )
    for row in fixture:
        id = row["definition"]["id"]
        assert row["definition"] == public_definition(DEFINITIONS[id])
        assert row["result"] == evaluate(id)
    assert len(fixture) == len(DEFINITIONS)


def test_save_reuses_trusted_run_and_preserves_existing_history(
    api, sessions, monkeypatch
):
    from app.api import learning_challenges as routes
    from app.models import Circuit, SimulationRun

    client, uid = api
    _, p = post_prediction(client)
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 200
    monkeypatch.setattr(
        routes, "execute", lambda _: pytest.fail("Saving must not simulate again")
    )
    saved = client.post("/api/challenges/m4-challenge/save-circuit", json=p)
    assert saved.status_code == 200, saved.text
    assert (
        client.post("/api/challenges/m4-challenge/save-circuit", json=p).json()
        == saved.json()
    )
    assert (
        client.get("/api/circuits/runs/" + saved.json()["simulation_id"]).status_code
        == 200
    )
    with sessions() as db:
        assert db.query(Circuit).filter_by(user_id=uid).count() == 1
        assert db.query(SimulationRun).filter_by(user_id=uid).count() == 1


def test_equal_probability_entangled_state_does_not_pass_product_objective():
    c = copy.deepcopy(FIXTURES["m2-experiment"]["circuit"])
    c["gates"].append({"type": "CZ", "control": 0, "target": 1})
    result = evaluate("m2-experiment", c)
    assert result["status"] == "near_miss"
    assert result["checks"][1]["passed"]
    assert not result["checks"][2]["passed"]


def test_full_migration_entrypoint_from_integer_legacy_schema(sessions, monkeypatch):
    from sqlalchemy import text, inspect
    from app.core.database import Base
    from app import migrate as entrypoint
    from app.models import User
    from app.legacy_migration import legacy_id

    engine = sessions.kw["bind"]
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, name TEXT, hashed_password TEXT, email_verified BOOLEAN, otp_code TEXT, created_at TIMESTAMP)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users VALUES (1,'preserved@example.com','Preserved learner',NULL,true,NULL,now())"
            )
        )
    monkeypatch.setattr(entrypoint, "engine", engine)
    entrypoint.migrate()
    entrypoint.migrate()
    with sessions() as db:
        assert db.get(User, legacy_id("users", 1)).name == "Preserved learner"
    with engine.begin() as connection:
        assert inspect(connection).has_table("challenge_attempts")
        assert inspect(connection).has_table("hardware_jobs")
        assert (
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            == "0003_learning_challenges"
        )


def test_saved_attempt_cap_keeps_run_and_old_history(api, sessions):
    from datetime import datetime, timezone
    from app.models import ChallengeAttempt

    client, uid = api
    _, p = post_prediction(client)
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 200
    result = evaluate("m4-challenge")
    now = datetime.now(timezone.utc)
    with sessions() as db:
        db.add_all(
            [
                ChallengeAttempt(
                    user_id=uid,
                    challenge_id="m4-challenge",
                    module_id=4,
                    version=1,
                    revision=uuid4(),
                    fingerprint="0" * 64,
                    number=i + 1,
                    circuit=FIXTURES["m4-challenge"]["circuit"],
                    prediction=FIXTURES["m4-challenge"]["prediction"],
                    simulation=None,
                    result=result,
                    passed=True,
                    score=100,
                    hints_used=0,
                    created_at=now,
                    completed_at=now,
                )
                for i in range(200)
            ]
        )
        db.commit()
    response = client.post("/api/challenges/m4-challenge/validate", json=p)
    assert response.status_code == 409 and "200" in response.text
    assert client.post("/api/challenges/m4-challenge/run", json=p).status_code == 200
    assert client.get("/api/challenges/m4-challenge/attempts/1").status_code == 200
    assert len(client.get("/api/challenges/m4-challenge").json()["history"]) == 200


def test_expired_authentication_and_missing_id(api):
    from datetime import timedelta
    from app.core.security import create_access_token

    client, uid = api
    assert client.post("/api/challenges//validate", json={}).status_code == 404
    client.headers["Authorization"] = "Bearer " + create_access_token(
        {"sub": str(uid)}, expires_delta=timedelta(seconds=-1)
    )
    assert client.get("/api/challenges").status_code == 401
