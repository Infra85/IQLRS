"""Registration uses a real isolated database and never contacts SMTP."""

import smtplib
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth
from app.core import email
from app.core.config import Settings
from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User

PAYLOAD = {"email": "learner@example.com", "password": "test-registration-password", "name": "Learner"}


@pytest.fixture
def setup(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    User.__table__.create(engine)
    sessions = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(email, "settings", Settings(_env_file=None, smtp_email="sender@example.com", smtp_password="test-only-password"))
    smtp = MagicMock()
    monkeypatch.setattr(email.smtplib, "SMTP", smtp)
    with TestClient(app) as client:
        yield client, sessions, smtp
    engine.dispose()


def register(client, **changes):
    return client.post("/api/auth/register", json={**PAYLOAD, **changes})


def seed(sessions, verified=False):
    with sessions() as db:
        user = User(email=PAYLOAD["email"], name="Original", hashed_password=hash_password(PAYLOAD["password"]), email_verified=verified,
                    otp_code="123456", otp_expires_at=datetime.utcnow() + timedelta(minutes=5))
        db.add(user)
        db.commit()
        return user.id


def test_valid_registration_requires_otp_before_login(setup, monkeypatch):
    client, sessions, smtp = setup
    sender = MagicMock()
    monkeypatch.setattr(auth, "send_otp_email", sender)
    response = register(client)
    assert response.status_code == 201
    with sessions() as db:
        user = db.query(User).one()
        assert response.json() == {"message": "User registered successfully", "user_id": user.id}
        assert not user.email_verified and user.hashed_password != PAYLOAD["password"]
        code = user.otp_code
        assert len(code) == 6 and code.isdigit()
        assert user.otp_expires_at > datetime.utcnow()
        sender.assert_called_once_with(PAYLOAD["email"], code)
    login = {"email": PAYLOAD["email"], "password": PAYLOAD["password"]}
    assert client.post("/api/auth/login", json=login).status_code == 403
    assert client.post("/api/auth/verify-otp", params={"email": PAYLOAD["email"], "otp": "bad"}).status_code == 400
    assert client.post("/api/auth/verify-otp", params={"email": PAYLOAD["email"], "otp": code}).status_code == 200
    assert client.post("/api/auth/login", json=login).status_code == 200
    with sessions() as db:
        user = db.query(User).one()
        assert user.email_verified and user.otp_code is None and user.otp_expires_at is None


@pytest.mark.parametrize("field", ["smtp_email", "smtp_password"])
def test_missing_smtp_rolls_back_and_can_retry(setup, monkeypatch, field):
    client, sessions, smtp = setup
    original = getattr(email.settings, field)
    monkeypatch.setattr(email.settings, field, " ")
    response = register(client)
    assert response.status_code == 503
    assert "SMTP_EMAIL and SMTP_PASSWORD" in response.json()["detail"]
    smtp.assert_not_called()
    with sessions() as db:
        assert db.query(User).count() == 0
    monkeypatch.setattr(email.settings, field, original)
    assert register(client).status_code == 201
    with sessions() as db:
        assert db.query(User).count() == 1


@pytest.mark.parametrize("error,detail", [
    (smtplib.SMTPAuthenticationError(535, b"PRIVATE-PROVIDER-DETAIL"), "SMTP authentication failed"),
    (smtplib.SMTPRecipientsRefused({"private@example.com": (550, b"PRIVATE-PROVIDER-DETAIL")}), "could not be sent"),
    (TimeoutError("PRIVATE-PROVIDER-DETAIL"), "could not be sent"),
    (smtplib.SMTPNotSupportedError("PRIVATE-PROVIDER-DETAIL"), "could not be sent"),
])
def test_smtp_failures_are_actionable_and_redacted(setup, caplog, error, detail):
    client, sessions, smtp = setup
    smtp.return_value.__enter__.return_value.login.side_effect = error
    response = register(client)
    assert response.status_code == 503
    assert detail in response.json()["detail"]
    assert "PRIVATE-PROVIDER-DETAIL" not in response.text + caplog.text
    assert "test-only-password" not in response.text + caplog.text
    assert caplog.records
    with sessions() as db:
        assert db.query(User).count() == 0


def test_smtp_success_uses_tls_login_and_email(setup):
    client, sessions, smtp = setup
    assert register(client).status_code == 201
    smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
    server = smtp.return_value.__enter__.return_value
    assert server.starttls.call_args.kwargs["context"].check_hostname
    server.login.assert_called_once_with("sender@example.com", "test-only-password")
    message = server.send_message.call_args.args[0]
    with sessions() as db:
        assert db.query(User).one().otp_code in message.get_content()
    assert message["To"] == PAYLOAD["email"]


@pytest.mark.parametrize("verified, password", [(True, PAYLOAD["password"]), (False, "wrong-password")])
def test_duplicate_account_cannot_be_overwritten(setup, verified, password):
    client, sessions, smtp = setup
    seed(sessions, verified)
    response = register(client, password=password)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
    smtp.assert_not_called()
    with sessions() as db:
        user = db.query(User).one()
        assert user.name == "Original" and user.otp_code == "123456"
        assert user.email_verified == verified


def test_unverified_retry_preserves_account_and_rolls_back_failed_otp(setup, monkeypatch):
    client, sessions, smtp = setup
    user_id = seed(sessions)
    monkeypatch.setattr(auth.secrets, "randbelow", lambda limit: 654321)
    server = smtp.return_value.__enter__.return_value
    server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"rejected")
    assert register(client, name="Replacement").status_code == 503
    with sessions() as db:
        user = db.query(User).one()
        assert user.id == user_id and user.otp_code == "123456"
        old_expiry = user.otp_expires_at
    server.login.side_effect = None
    response = register(client, name="Replacement")
    assert response.status_code == 201 and response.json()["user_id"] == user_id
    with sessions() as db:
        user = db.query(User).one()
        assert user.name == "Original" and not user.email_verified
        assert user.otp_code == "754321" and user.otp_expires_at > old_expiry
    assert client.post("/api/auth/verify-otp", params={"email": PAYLOAD["email"], "otp": "123456"}).status_code == 400


@pytest.mark.parametrize("field,value", [("smtp_email", "invalid\naddress"), ("smtp_password", "non-ascii-\u2603")])
def test_invalid_smtp_configuration_is_rejected_before_connecting(setup, monkeypatch, field, value):
    client, sessions, smtp = setup
    monkeypatch.setattr(email.settings, field, value)
    response = register(client)
    assert response.status_code == 503
    assert "not configured correctly" in response.json()["detail"]
    smtp.assert_not_called()
    with sessions() as db:
        assert db.query(User).count() == 0


def test_unique_constraint_race_returns_duplicate_error(setup, monkeypatch):
    from fastapi import HTTPException
    from app.schemas.auth import RegisterRequest

    client, sessions, smtp = setup
    seed(sessions)
    with sessions() as db:
        original_query = db.query
        missed = MagicMock()
        missed.filter.return_value.with_for_update.return_value.first.return_value = None
        calls = 0

        def query(*args):
            nonlocal calls
            calls += 1
            # Simulate another registration committing after the initial lookup.
            return missed if calls == 1 else original_query(*args)

        monkeypatch.setattr(db, "query", query)
        with pytest.raises(HTTPException) as failure:
            auth.register(RegisterRequest(**PAYLOAD), db)
        assert failure.value.status_code == 400
        assert failure.value.detail == "Email already registered"
        assert original_query(User).count() == 1
    smtp.assert_not_called()
