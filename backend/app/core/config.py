"""Pydantic settings and app configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/IQLRS"
    openai_api_key: str = ""
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
