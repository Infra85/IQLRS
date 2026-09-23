"""Versioned, transactional PostgreSQL migration entrypoint: python -m app.migrate."""
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.database import Base, engine
import app.models  # noqa: F401
from app.services.curriculum import seed_curriculum


def migrate():
    with engine.begin() as connection:
        if connection.dialect.name != "postgresql":
            raise RuntimeError("IQLRS production migrations require PostgreSQL")
        connection.execute(text("SELECT pg_advisory_xact_lock(741852963)"))
        inspector = inspect(connection)
        if inspector.has_table("users") and "user_id" not in {c['name'] for c in inspector.get_columns('users')}:
            from app.legacy_migration import migrate_legacy
            migrate_legacy(connection)
        Base.metadata.create_all(connection)
        connection.execute(text("ALTER TABLE users ALTER COLUMN otp_code TYPE VARCHAR(64)"))
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0"))
        # Previously stored plaintext codes must no longer be accepted.
        connection.execute(text("UPDATE users SET otp_code = NULL, otp_expires_at = NULL WHERE length(otp_code) = 6"))
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"))
        with Session(bind=connection) as db:
            seed_curriculum(db)
            db.flush()
        connection.execute(text("INSERT INTO schema_migrations(version) VALUES (1) ON CONFLICT DO NOTHING"))
    print("Database migrated to version 1; curriculum ready.")


if __name__ == "__main__":
    migrate()
