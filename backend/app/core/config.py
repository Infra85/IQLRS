"""Pydantic settings and app configuration."""

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[2] / ".env",
        ),
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/quantumlearn"

    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    openai_api_key: str = ""
    ai_model: str = "gpt-4.1-mini"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_reply_to: str = ""
    smtp_ssl: bool = False

    @model_validator(mode="after")
    def production_configuration(self):
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        if self.environment == "production":
            if len(self.secret_key) < 32 or self.secret_key == "change-me-in-production":
                raise ValueError("Production SECRET_KEY must be a random secret of at least 32 characters")
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg2://")) or "postgres:postgres@" in self.database_url:
                raise ValueError("Production DATABASE_URL must use PostgreSQL with dedicated credentials")
            if not self.smtp_email.strip() or not self.smtp_password.strip() or not self.smtp_host.strip():
                raise ValueError("Production requires SMTP_EMAIL, SMTP_PASSWORD, and SMTP_HOST")
            if not self.cors_origins or any(not o.startswith("https://") or "*" in o or "localhost" in o for o in self.cors_origins):
                raise ValueError("Production CORS_ORIGINS must contain explicit HTTPS frontend origins")
            if not self.openai_api_key.strip() or not self.ai_model.strip():
                raise ValueError("Production AI requires OPENAI_API_KEY and AI_MODEL")
        return self


    # Speech credentials stay on the backend. Provider/model/voice are operator settings.
    tts_provider: str = "openai"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "marin"
    tts_cache_path: str = ".cache/narration.sqlite3"
    tts_cache_max_bytes: int = Field(default=134217728, ge=1048576)
    tts_cache_ttl_seconds: int = Field(default=604800, ge=60)
    tts_daily_char_limit: int = Field(default=250000, ge=1)
    tts_requests_per_minute: int = Field(default=40, ge=1)
    tts_max_concurrent: int = Field(default=2, ge=1, le=16)

    secret_key: str = "change-me-in-production"

    smtp_email: str = ""

    smtp_password: str = ""


settings = Settings()
