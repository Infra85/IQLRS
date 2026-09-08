"""Pydantic settings and app configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/IQLRS"
    openai_api_key: str = ""
    secret_key: str = "change-me-in-production"


settings = Settings()
