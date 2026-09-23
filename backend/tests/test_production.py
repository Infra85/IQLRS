from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import Circuit, SimulationRun, SimulationResult, User, AIConversation, AIMessage
from app.core.security import create_access_token
from app.services.curriculum import MODULES


def test_simulation_persistence_dashboard_and_isolation(api, sessions):
    client, uid = api
    before = client.get('/api/dashboard/me').json()
    assert before['statistics']['simulations'] == 0
    circuit = {'gates': [{'type': 'H', 'qubit': 0}, {'type': 'CNOT', 'control': 0, 'target': 1}], 'num_qubits': 2, 'shots': 256}
    response = client.post('/api/circuits/simulate', json=circuit)
    assert response.status_code == 200, response.text
    saved = client.get('/api/circuits/runs/' + response.json()['simulation_id'])
    assert saved.status_code == 200
    assert sum(saved.json()['counts'].values()) == 256
    assert saved.json()['circuit']['gates'][0]['type'] == 'H'
    after = client.get('/api/dashboard/me').json()
    assert after['statistics']['simulations'] == 1 and after['recent_activity']
    with sessions() as db:
        assert db.query(Circuit).count() == db.query(SimulationRun).count() == db.query(SimulationResult).count() == 1
        other = User(email='other@example.com', name='Other', email_verified=True)
        db.add(other)
        db.commit()
        other_token = create_access_token({'sub': str(other.user_id)})
    assert client.get('/api/circuits/runs/' + response.json()['simulation_id'], headers={'Authorization': 'Bearer '+other_token}).status_code == 404
    assert client.get('/api/dashboard/me', headers={'Authorization': 'Bearer '+other_token}).json()['statistics']['simulations'] == 0
    assert client.post('/api/circuits/simulate', json={**circuit, 'shots': 0}).status_code == 422
    assert client.post('/api/circuits/simulate', json={**circuit, 'gates': [{'type': 'INVALID'}]}).status_code == 400
    assert client.get('/api/dashboard/me').json()['statistics']['simulations'] == 1
    assert client.post('/api/circuits/simulate', json=circuit, headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_save_failure_rolls_back(api, sessions, monkeypatch):
    from sqlalchemy.orm import Session
    client, uid = api
    original = Session.commit
    def fail(self):
        if any(isinstance(row, SimulationResult) for row in self.new):
            raise RuntimeError('private-database-details')
        return original(self)
    monkeypatch.setattr(Session, 'commit', fail)
    response = client.post('/api/circuits/simulate', json={'gates': [], 'num_qubits': 1})
    assert response.status_code == 503 and 'private' not in response.text
    monkeypatch.setattr(Session, 'commit', original)
    with sessions() as db:
        assert db.query(Circuit).count() == db.query(SimulationRun).count() == 0


def test_quiz_updates_dashboard(api):
    client, uid = api
    answers = [q['answerIndex'] for q in MODULES[0]['questions']]
    response = client.post('/api/progress/lessons/1/quiz', json={'answers': answers})
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'completed'
    dashboard = client.get('/api/dashboard/me').json()
    assert dashboard['statistics']['modules_completed'] == 1
    assert dashboard['statistics']['quiz_score'] == 100
    assert dashboard['courses'][0]['progress'] == 12
    assert client.get('/api/progress/me').json()['progress'][0]['status'] == 'completed'
    assert client.post('/api/progress/lessons/1/quiz', json={'answers': [999]}).status_code == 422
    client.post('/api/progress/lessons/1/quiz', json={'answers': answers})
    assert client.get('/api/dashboard/me').json()['statistics']['modules_completed'] == 1


def test_ai_saved_conversation_and_failure(api, sessions, monkeypatch):
    from app.api import ai
    from openai import APIConnectionError
    import httpx
    client, uid = api
    tutor = MagicMock()
    tutor.chat = AsyncMock(return_value='A Hadamard gate creates equal amplitudes from |0>.')
    tutor.client.close = AsyncMock()
    monkeypatch.setattr(ai.settings, 'openai_api_key', 'test-provider-key')
    monkeypatch.setattr(ai, 'get_ai_tutor', lambda: tutor)
    response = client.post('/api/ai/chat', json={'message': 'Explain H'})
    assert response.status_code == 200, response.text
    cid = response.json()['conversation_id']
    assert len(client.get('/api/ai/conversations/'+cid).json()) == 2
    response = client.post('/api/ai/chat', json={'message': 'And X?', 'conversation_id': cid})
    assert response.status_code == 200
    assert len(tutor.chat.call_args.args[1]['conversation']) == 2
    assert client.post('/api/ai/chat', json={'message': ' ', 'conversation_id': cid}).status_code == 422
    assert client.post('/api/ai/chat', json={'message': 'hello', 'conversation_id': str(uuid4())}).status_code == 404
    tutor.chat.side_effect = APIConnectionError(request=httpx.Request('POST', 'https://api.openai.com'))
    response = client.post('/api/ai/chat', json={'message': 'Another question'})
    assert response.status_code == 502
    with sessions() as db:
        assert db.query(AIConversation).count() == 1
        assert db.query(AIMessage).count() == 4


def test_ai_missing_config_and_cors(api, monkeypatch):
    from app.core.config import settings
    client, uid = api
    monkeypatch.setattr(settings, 'openai_api_key', '')
    assert client.post('/api/ai/chat', json={'message': 'Explain H'}).status_code == 503
    response = client.options('/api/circuits/simulate', headers={'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'authorization,content-type'})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'
    assert client.options('/api/circuits/simulate', headers={'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'POST'}).status_code == 400
    assert client.get('/health/ready').status_code == 200
    assert client.post('/api/code/execute', json={}).status_code == 404


def test_legacy_migration_preserves_user_and_results(sessions):
    from sqlalchemy import text
    from app.core.database import Base
    from app.legacy_migration import migrate_legacy, legacy_id
    from app.core.security import hash_password
    engine = sessions.kw['bind']
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, name TEXT, hashed_password TEXT, email_verified BOOLEAN, otp_code TEXT, created_at TIMESTAMP)'))
        connection.execute(text('CREATE TABLE circuits (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), name TEXT, num_qubits INTEGER, created_at TIMESTAMP)'))
        connection.execute(text('CREATE TABLE simulation_runs (id INTEGER PRIMARY KEY, circuit_id INTEGER REFERENCES circuits(id), user_id INTEGER REFERENCES users(id), simulator TEXT, shots INTEGER, status TEXT, execution_time FLOAT, created_at TIMESTAMP)'))
        connection.execute(text('CREATE TABLE simulation_results (id INTEGER PRIMARY KEY, simulation_id INTEGER REFERENCES simulation_runs(id), measurement_counts JSON, state_vector JSON)'))
        hashed = hash_password('legacy-password-123')
        connection.execute(text("INSERT INTO users VALUES (1, 'legacy@example.com', 'Legacy', :password, true, '123456', now())"), {'password': hashed})
        connection.execute(text("INSERT INTO circuits VALUES (1, 1, 'Original circuit', 1, now())"))
        connection.execute(text("INSERT INTO simulation_runs VALUES (1, 1, 1, 'qiskit', 64, 'completed', 0.5, now())"))
        connection.execute(text("INSERT INTO simulation_results VALUES (1, 1, :counts, :state)"), {"counts": '{"0":64}', "state": '{"amplitudes":[[1,0],[0,0]]}'})
        migrate_legacy(connection)
    with sessions() as db:
        user = db.get(User, legacy_id('users', 1))
        assert user.password_hash == hashed and user.email_verified and user.otp_code is None
        run = db.get(SimulationRun, legacy_id('simulation_runs', 1))
        assert run.user_id == user.user_id and run.execution_time_ms == 500
        assert run.result.measurement_counts == {'0': 64}
        assert db.get(Circuit, legacy_id('circuits', 1)).name == 'Original circuit'
        assert db.query(User).count() == 2


def test_shared_auth_rate_limit(api):
    client, uid = api
    for _ in range(30):
        assert client.post('/api/auth/login', json={'email':'absent@example.com', 'password':'incorrect'}).status_code == 401
    response = client.post('/api/auth/login', json={'email':'absent@example.com', 'password':'incorrect'})
    assert response.status_code == 429 and response.headers['retry-after'] == '300'


def test_guest_simulation_stays_available_without_persisting(api, sessions):
    client, uid = api
    client.headers.pop('Authorization')
    response = client.post('/api/circuits/simulate', json={'gates': [], 'num_qubits': 1, 'shots':64})
    assert response.status_code == 200 and response.json()['counts'] == {'0':64}
    assert response.json()['simulation_id'] is None
    with sessions() as db:
        assert db.query(SimulationRun).count() == 0


def test_production_cors_preflight_allows_authenticated_headers():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient
    from app.main import app

    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    assert cors.kwargs["allow_headers"] == ["Authorization", "Content-Type"]
    isolated = FastAPI()
    isolated.add_api_route("/api/circuits/simulate", lambda: {"ok": True}, methods=["POST"])
    isolated.add_middleware(CORSMiddleware, allow_origins=["https://iqlrs.org"],
                            allow_credentials=cors.kwargs["allow_credentials"],
                            allow_methods=cors.kwargs["allow_methods"],
                            allow_headers=cors.kwargs["allow_headers"])
    response = TestClient(isolated).options(
        "/api/circuits/simulate",
        headers={"Origin": "https://iqlrs.org", "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "authorization,content-type"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://iqlrs.org"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
