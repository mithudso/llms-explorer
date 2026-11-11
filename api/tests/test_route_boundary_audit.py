"""Malformed public inputs remain client errors and browser API methods work."""
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from starlette.requests import Request

from explorer_api import auth, gateway
from explorer_api.main import create_app
from explorer_api.routes import auth as auth_routes
from explorer_api.routes.mcp import _read_message
from explorer_api.settings import Settings


@pytest.mark.parametrize("payload", [b"\xff", b"\xfe\xff\x00", b"not-json"])
async def test_mcp_rejects_invalid_json_encodings_as_bad_requests(payload):
    class Body:
        async def body(self):
            return payload

    with pytest.raises(gateway.BadRequest):
        await _read_message(Body())


async def test_unicode_oauth_state_is_a_client_refusal_before_provider_call():
    secret = "s" * 32
    cookie = auth.new_state(secret=secret)
    app = SimpleNamespace(state=SimpleNamespace(
        settings=SimpleNamespace(session_secret=SecretStr(secret)),
        oauth_providers={"github": object()},
    ))
    request = Request({"type": "http", "app": app,
                       "headers": [(b"cookie", f"{auth.OAUTH_STATE_COOKIE}={cookie}".encode())]})
    with pytest.raises(HTTPException) as raised:
        await auth_routes.oauth_callback("github", request, None, code="irrelevant", state="é")
    assert raised.value.status_code == 400


async def test_allowed_site_can_preflight_put_for_byok_save():
    settings = Settings.load({
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        "SITE_ORIGINS": "https://reader.example.test",
        "ALLOWED_HOSTS": "api.example.test",
    })
    app = create_app(settings)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                base_url="https://api.example.test") as client:
        response = await client.options("/api/account/anthropic-key", headers={
            "Origin": "https://reader.example.test",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://reader.example.test"
    assert "PUT" in response.headers["access-control-allow-methods"]


async def test_database_refusal_logs_only_safe_request_metadata(caplog):
    import logging

    from sqlalchemy.exc import DBAPIError

    settings = Settings.load({
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
    })
    app = create_app(settings)

    @app.get("/audit-database-failure")
    async def failing_query():
        raise DBAPIError("INSERT INTO subscribers(email) VALUES (:email)",
                         {"email": "private-marker@example.test"},
                         RuntimeError("private-driver-marker"))

    with caplog.at_level(logging.WARNING, logger="explorer_api"):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="http://test") as client:
            response = await client.get("/audit-database-failure")
    assert response.status_code == 503
    assert "database unavailable" in caplog.text
    assert "private-marker" not in caplog.text
    assert "private-driver-marker" not in caplog.text
    assert "INSERT INTO" not in caplog.text
