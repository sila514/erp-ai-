"""
Test altyapısı: Docker/Postgres gerekmeden hızlı çalışması için varsayılan
olarak in-memory SQLite kullanılır (bkz. app/core/types.py::GUID -
dialect-agnostic UUID tipi bu yüzden eklendi). CI'da TEST_DATABASE_URL
gerçek bir Postgres'e işaret eder (bkz. .github/workflows/ci.yml) - şema
orada ayrıca `alembic upgrade head` ile de doğrulanır.

Redis, gerçek bir sunucu olmadan test edilebilsin diye fakeredis ile
mock'lanır (bkz. fake_redis fixture).
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("ENV", "test")

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
_is_sqlite = TEST_DATABASE_URL.startswith("sqlite")

_engine_kwargs = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(TEST_DATABASE_URL, **_engine_kwargs)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.core.database import Base, get_db  # noqa: E402
from app.core import events as events_module  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_schema():
    """Her testten önce şemayı temiz baştan kurar - testler birbirinden tam izole olur."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fake_redis(monkeypatch):
    """`app.core.events.get_redis_client()`'ın döndürdüğü client'ı fakeredis ile değiştirir."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(events_module, "_redis_client", fake)
    return fake


@pytest.fixture()
def client(db, fake_redis):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, username: str, password: str, role: str = "admin") -> dict:
    """Yardımcı: kullanıcı kaydeder, giriş yapar, Authorization header döndürür."""
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "role": role,
        },
    )
    resp = client.post("/api/auth/login", data={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
