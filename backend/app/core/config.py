"""Pydantic settings and app configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/IQLRS"

    openai_api_key: str = ""

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