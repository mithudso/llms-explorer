"""Regression cases for authentication trust boundaries and safe diagnostics."""

from __future__ import annotations

import logging

import httpx
import pytest
from sqlalchemy import func, select

from explorer_api import auth, models as m
from test_auth import SoftAuthenticator, app, client, settings, sign_in

# Reuse the existing real API/PostgreSQL fixtures instead of duplicating wiring.
__all__ = ["app", "client", "settings"]


@pytest.mark.parametrize("all_devices", [False, True])
async def test_registration_cannot_attach_to_logged_out_account(client, session, all_devices):
    await sign_in(client)
    owner_id = (await client.get("/api/me")).json()["id"]
    options = (await client.post("/api/auth/passkey/register/options", json={})).json()
    credential = SoftAuthenticator().register(options)

    assert (await client.post("/api/auth/logout", params={"all": all_devices})).status_code == 204
    result = await client.post("/api/auth/passkey/register", json={"credential": credential})

    assert result.status_code == 400
    assert (await client.get("/api/me")).status_code == 401
    count = (await session.execute(
        select(func.count()).select_from(m.Passkey).where(m.Passkey.user_id == owner_id)
    )).scalar_one()
    assert count == 0


def provider():
    return auth.HttpOAuthProvider(
        name="test-provider", client_id="public-id", client_secret="private-client-secret",
        authorize_endpoint="https://provider.test/authorize",
        token_endpoint="https://provider.test/token", scope="profile",
    )


@pytest.mark.parametrize("body", [
    "private-provider-body-not-json", "[]", "null", '"not-an-object"',
    '{"refresh_token":"private-provider-refresh-token"}', '{"access_token":123}',
])
async def test_malformed_token_response_is_a_safe_oauth_failure(body, caplog):
    caplog.set_level(logging.INFO, logger="explorer_api.auth")
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    async with httpx.AsyncClient(transport=transport) as http:
        with pytest.raises(auth.OAuthError) as failure:
            await provider()._exchange(http, code="private-auth-code", redirect_uri="https://api.test/")
    output = str(failure.value) + caplog.text
    for secret in ["private-provider-body", "private-provider-refresh-token",
                   "private-client-secret", "private-auth-code"]:
        assert secret not in output
    assert any(record.levelno == logging.WARNING for record in caplog.records)


async def test_valid_token_response_keeps_its_value_and_logs_no_secret(caplog):
    caplog.set_level(logging.INFO, logger="explorer_api.auth")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"access_token": "private-access-token"})
    )
    async with httpx.AsyncClient(transport=transport) as http:
        token = await provider()._exchange(http, code="private-auth-code",
                                           redirect_uri="https://api.test/")
    assert token == "private-access-token"
    assert "oauth_token_exchange_succeeded" in caplog.text
    assert "private-access-token" not in caplog.text
    assert "private-auth-code" not in caplog.text
    assert "private-client-secret" not in caplog.text


@pytest.mark.parametrize("kind", [auth.GitHubProvider, auth.GoogleProvider])
@pytest.mark.parametrize("body", ["private-profile-body-not-json", "[]", "null"])
async def test_malformed_profile_is_a_safe_oauth_failure(kind, body, caplog):
    caplog.set_level(logging.INFO, logger="explorer_api.auth")
    service = kind(**provider().__dict__)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    async with httpx.AsyncClient(transport=transport) as http:
        with pytest.raises(auth.OAuthError) as failure:
            await service._profile(http, "private-access-token")
    assert "private-profile-body" not in str(failure.value) + caplog.text
    assert "private-access-token" not in caplog.text
    assert "oauth_response_invalid" in caplog.text


async def test_authentication_transitions_have_safe_audit_events(client, caplog):
    caplog.set_level(logging.INFO, logger="explorer_api.auth")
    await sign_in(client)
    options = (await client.post("/api/auth/passkey/register/options", json={})).json()
    result = await client.post("/api/auth/passkey/register", json={
        "credential": SoftAuthenticator().register(options),
    })
    assert result.status_code == 200
    assert (await client.post("/api/auth/logout", params={"all": True})).status_code == 204
    assert "auth_oauth_account_resolved" in caplog.text
    assert "auth_passkey_registered" in caplog.text
    assert "auth_session_revocation_requested" in caplog.text
    assert "ada@example.test" not in caplog.text
    assert auth.SESSION_COOKIE not in caplog.text
    assert auth.WEBAUTHN_COOKIE not in caplog.text
