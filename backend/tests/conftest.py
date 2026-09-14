"""Integration tests use an isolated schema in an explicitly configured PostgreSQL DB."""
import os
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
import app.models


@pytest.fixture
def sessions():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run real PostgreSQL integration checks")
    schema = "test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()
    with admin.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}_legacy_v1" CASCADE'))
    admin.dispose()


@pytest.fixture
def api(sessions):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import User
    from app.core.security import create_access_token
    from app.services.curriculum import seed_curriculum
    with sessions() as db:
        seed_curriculum(db)
        user = User(name="Integration learner", email="integration@example.com", email_verified=True)
        db.add(user)
        db.commit()
        token = create_access_token({"sub": str(user.user_id)})
        uid = user.user_id
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client, uid
    app.dependency_overrides.clear()
