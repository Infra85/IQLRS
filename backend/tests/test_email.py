"""Transactional email transport tests."""

from unittest.mock import MagicMock

import httpx
import pytest

from app.core import email
from app.core.config import Settings


def test_resend_transport_posts_otp_without_smtp(monkeypatch):
    configured = Settings(_env_file=None, smtp_email="sender@example.com", resend_api_key="re_test_key")
    monkeypatch.setattr(email, "settings", configured)
    client = MagicMock()
    response = MagicMock()
    client.return_value.__enter__.return_value = client
    client.post.return_value = response
    monkeypatch.setattr(email.httpx, "Client", client)
    smtp = MagicMock(side_effect=AssertionError("SMTP must not be used with Resend configured"))
    monkeypatch.setattr(email.smtplib, "SMTP", smtp)

    email.send_otp_email("learner@example.com", "123456")

    client.assert_called_once_with(timeout=10.0)
    request = client.post.call_args
    assert request.args[0] == "https://api.resend.com/emails"
    assert request.kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    assert request.kwargs["json"]["subject"] == "Verify your IQLRS account"
    assert "123456" in request.kwargs["json"]["text"]
    assert "IQLRS" in request.kwargs["json"]["text"]
    smtp.assert_not_called()


def test_resend_failure_is_redacted(monkeypatch, caplog):
    configured = Settings(_env_file=None, smtp_email="sender@example.com", resend_api_key="re_secret_key")
    monkeypatch.setattr(email, "settings", configured)
    client = MagicMock()
    client.return_value.__enter__.return_value = client
    client.post.side_effect = httpx.RequestError("provider secret re_secret_key", request=MagicMock())
    monkeypatch.setattr(email.httpx, "Client", client)

    with pytest.raises(email.EmailDeliveryError, match="Verification email could not be sent"):
        email.send_otp_email("learner@example.com", "654321")

    assert "re_secret_key" not in caplog.text
    assert "654321" not in caplog.text


def test_production_never_uses_smtp(monkeypatch):
    configured = Settings(_env_file=None, smtp_email="sender@example.com", resend_api_key="")
    configured.environment = "production"
    monkeypatch.setattr(email, "settings", configured)
    smtp = MagicMock(side_effect=AssertionError("SMTP must never be used in production"))
    monkeypatch.setattr(email.smtplib, "SMTP", smtp)

    with pytest.raises(email.EmailDeliveryError, match="RESEND_API_KEY"):
        email.send_otp_email("learner@example.com", "123456")
    smtp.assert_not_called()


def test_resend_http_error_is_diagnosable_without_secrets(monkeypatch, caplog):
    configured = Settings(_env_file=None, smtp_email="sender@example.com", resend_api_key="re_secret_key")
    monkeypatch.setattr(email, "settings", configured)
    client = MagicMock()
    client.return_value.__enter__.return_value = client
    response = MagicMock(status_code=422)
    request = httpx.Request("POST", "https://api.resend.com/emails")
    client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "provider details re_secret_key", request=request, response=response
    )
    monkeypatch.setattr(email.httpx, "Client", client)

    with pytest.raises(email.EmailDeliveryError, match="Verification email could not be sent"):
        email.send_otp_email("learner@example.com", "987654")

    assert "Resend returned HTTP 422" in caplog.text
    assert "re_secret_key" not in caplog.text
    assert "987654" not in caplog.text
