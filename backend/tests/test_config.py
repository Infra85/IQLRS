from pathlib import Path

from app.core.config import Settings


def test_env_paths_are_independent_of_working_directory():
    root = Path(__file__).resolve().parents[2]
    assert Settings.model_config["env_file"] == (root / ".env", root / "backend" / ".env")


def test_env_precedence_and_optional_smtp(tmp_path, monkeypatch):
    for key in ("SMTP_EMAIL", "SMTP_PASSWORD", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    defaults = Settings(_env_file=None)
    assert defaults.smtp_email == defaults.smtp_password == ""
    assert defaults.database_url == "postgresql://postgres:postgres@localhost:5432/quantumlearn"
    root_env = tmp_path / ".env"
    backend_env = tmp_path / "backend.env"
    root_env.write_text("SMTP_EMAIL=root@example.com\nSMTP_PASSWORD=test-only\n")
    backend_env.write_text("SMTP_EMAIL=backend@example.com\n")
    assert Settings(_env_file=root_env).smtp_email == "root@example.com"
    merged = Settings(_env_file=(root_env, backend_env))
    assert merged.smtp_email == "backend@example.com" and merged.smtp_password == "test-only"
    monkeypatch.setenv("SMTP_EMAIL", "process@example.com")
    assert Settings(_env_file=(root_env, backend_env)).smtp_email == "process@example.com"


def test_production_rejects_defaults_and_hides_secrets():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError) as failure:
        Settings(_env_file=None, environment='production', smtp_password='DO-NOT-PRINT-ME')
    assert 'SECRET_KEY' in str(failure.value)
    assert 'DO-NOT-PRINT-ME' not in str(failure.value)
    config = Settings(_env_file=None, environment='production', secret_key='test-only-configuration-secret-32-characters', database_url='postgresql://app:example@db/production', smtp_email='sender@example.com', resend_api_key='re_test_key', openai_api_key='example', cors_origins=['https://learn.example.com'])
    assert config.environment == 'production'


def test_production_requires_resend_api_key():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="RESEND_API_KEY"):
        Settings(
            _env_file=None,
            environment="production",
            secret_key="test-only-configuration-secret-32-characters",
            database_url="postgresql://app:example@db/production",
            smtp_email="sender@example.com",
            openai_api_key="example",
            cors_origins=["https://iqlrs.org"],
        )


def test_cors_origins_accepts_render_comma_separated_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://iqlrs.org,https://www.iqlrs.org")
    config = Settings(_env_file=None)
    assert config.cors_origins == ["https://iqlrs.org", "https://www.iqlrs.org"]


def test_cors_origins_accepts_json_array_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://iqlrs.org","https://www.iqlrs.org"]')
    config = Settings(_env_file=None)
    assert config.cors_origins == ["https://iqlrs.org", "https://www.iqlrs.org"]
