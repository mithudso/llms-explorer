# api/tests/test_main.py
import pytest
from explorer_api.main import create_app
from explorer_api.settings import MissingSettings, Settings
from fastapi.testclient import TestClient


@pytest.fixture()
def settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    return Settings.load()


def test_health_answers_with_the_environment(settings):
    with TestClient(create_app(settings)) as client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "environment": "dev"}


def test_health_never_leaks_a_secret(settings):
    with TestClient(create_app(settings)) as client:
        body = client.get("/health").text
    assert "sk_test_x" not in body and "hunter2" not in body


def test_the_app_refuses_to_start_without_its_environment(monkeypatch):
    for var in ("DATABASE_URL", "SESSION_SECRET", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(MissingSettings):
        create_app()


def test_the_lifespan_wires_a_session_factory_and_disposes_the_engine(settings):
    """db.py is reachable from a request: `get_session` reads app.state."""
    app = create_app(settings)
    with TestClient(app):
        assert app.state.session_factory is not None
        engine = app.state.engine
    assert engine.pool.checkedout() == 0     # disposed on shutdown, nothing leaked
