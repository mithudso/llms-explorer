# api/tests/test_auth.py
"""Sign-in: OAuth, passkeys, and the session cookie that carries both.

Written from the attacker's side, as the plan's self-review asks: can a second
sign-in fork my account in two? can an *unverified* address from one provider
take over an account proven by another? does a stolen `state` let a callback be
replayed? does logging out actually end the session?

Everything here is offline. The OAuth providers are stubs that return a fixed
profile — no token endpoint is ever called — and the passkey ceremonies run
against a software authenticator built from `cryptography` in this file, so the
WebAuthn path is genuinely exercised rather than mocked away.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass

import cbor2
import httpx
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from explorer_api import auth, models as m
from explorer_api.main import create_app
from explorer_api.settings import Settings

RP_ID = "api.test"
ORIGIN = f"https://{RP_ID}"


def b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def unb64u(raw: str) -> bytes:
    return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))


# --- stub OAuth provider -----------------------------------------------------


@dataclass
class StubProvider:
    """An OAuth provider that answers from memory. Never opens a socket."""

    name: str
    profile: auth.OAuthProfile
    seen_codes: list[str] | None = None

    def authorization_url(self, *, redirect_uri: str, state: str) -> str:
        return f"https://stub.invalid/{self.name}/authorize?state={state}&r={redirect_uri}"

    async def fetch_profile(self, *, code: str, redirect_uri: str) -> auth.OAuthProfile:
        if self.seen_codes is not None:
            self.seen_codes.append(code)
        if code == "bad-code":
            raise auth.OAuthError("the provider rejected the code")
        return self.profile


def profile(provider: str, account_id: str, email: str | None, verified: bool):
    return auth.OAuthProfile(
        provider=provider,
        account_id=account_id,
        email=email,
        email_verified=verified,
        display_name=f"{provider}-{account_id}",
    )


# --- app / client ------------------------------------------------------------


@pytest.fixture()
def settings(database_url: str, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SESSION_SECRET", "k" * 48)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    return Settings.load()


@pytest_asyncio.fixture
async def app(settings: Settings, database_url: str):
    """The real app, wired to the test database, with stub OAuth providers."""
    application = create_app(settings)
    engine = create_async_engine(database_url, future=True)
    application.state.engine = engine
    application.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    application.state.oauth_providers = {
        "github": StubProvider("github", profile("github", "gh-1", "ada@example.test", True)),
        "google": StubProvider("google", profile("google", "go-1", "ada@example.test", True)),
    }
    try:
        yield application
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=ORIGIN, follow_redirects=False
    ) as c:
        yield c


async def sign_in(client: httpx.AsyncClient, provider: str = "github") -> httpx.Response:
    """Walk the whole OAuth dance the way a browser would."""
    start = await client.get(f"/api/auth/oauth/{provider}")
    assert start.status_code in (302, 303, 307), start.text
    state = client.cookies[auth.OAUTH_STATE_COOKIE]
    return await client.get(
        f"/api/auth/oauth/{provider}/callback", params={"code": "ok", "state": state}
    )


async def count_users(session) -> int:
    return (await session.execute(select(func.count()).select_from(m.User))).scalar_one()


# --- the plan's assertions ---------------------------------------------------


async def test_first_sign_in_creates_a_user_and_the_second_reuses_it(client, session):
    first = await sign_in(client)
    assert first.status_code in (302, 303, 307)
    assert await count_users(session) == 1

    me = (await client.get("/api/me")).json()
    assert me["email"] == "ada@example.test"

    client.cookies.clear()
    await sign_in(client)
    assert await count_users(session) == 1, "a second sign-in forked the account"
    assert (await client.get("/api/me")).json()["id"] == me["id"]


async def test_two_providers_with_one_verified_email_are_one_user(client, session):
    await sign_in(client, "github")
    first_id = (await client.get("/api/me")).json()["id"]

    client.cookies.clear()
    await sign_in(client, "google")
    second_id = (await client.get("/api/me")).json()["id"]

    assert first_id == second_id
    assert await count_users(session) == 1
    links = (await session.execute(select(m.OAuthAccount))).scalars().all()
    assert {link.provider for link in links} == {"github", "google"}


async def test_the_session_cookie_is_httponly_secure_and_lax(client):
    response = await sign_in(client)
    raw = response.headers["set-cookie"]
    assert raw.startswith(f"{auth.SESSION_COOKIE}=")
    lowered = raw.lower()
    assert "httponly" in lowered
    assert "secure" in lowered
    assert "samesite=lax" in lowered
    assert f"max-age={auth.SESSION_MAX_AGE}" in lowered  # 30-day rolling expiry
    assert "path=/" in lowered


async def test_me_is_401_without_a_session(client):
    response = await client.get("/api/me")
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


# --- the attacker's side -----------------------------------------------------


async def test_an_unverified_email_never_takes_over_a_verified_account(app, client, session):
    """github proved ada@; a *different* google account merely claims it."""
    await sign_in(client, "github")
    victim = (await client.get("/api/me")).json()["id"]

    app.state.oauth_providers["google"] = StubProvider(
        "google", profile("google", "impostor", "ada@example.test", False)
    )
    client.cookies.clear()
    await sign_in(client, "google")
    attacker = (await client.get("/api/me")).json()["id"]

    assert attacker != victim
    assert await count_users(session) == 2


async def test_a_callback_without_a_matching_state_is_refused(client):
    await client.get("/api/auth/oauth/github")
    forged = await client.get(
        "/api/auth/oauth/github/callback", params={"code": "ok", "state": "not-the-state"}
    )
    assert forged.status_code == 400
    assert auth.SESSION_COOKIE not in forged.cookies

    client.cookies.clear()  # no state cookie at all — a bare replayed callback
    bare = await client.get(
        "/api/auth/oauth/github/callback", params={"code": "ok", "state": "anything"}
    )
    assert bare.status_code == 400


async def test_a_state_cookie_signed_with_another_key_is_refused(client):
    await client.get("/api/auth/oauth/github")
    forged_state = auth.sign_state("evil", secret="a-completely-different-secret-value!!")
    client.cookies.set(auth.OAUTH_STATE_COOKIE, forged_state, domain=RP_ID, path="/")
    response = await client.get(
        "/api/auth/oauth/github/callback", params={"code": "ok", "state": forged_state}
    )
    assert response.status_code == 400


async def test_an_unknown_provider_is_404(client):
    assert (await client.get("/api/auth/oauth/facebook")).status_code == 404


async def test_a_provider_failure_does_not_create_an_account(client, session):
    await client.get("/api/auth/oauth/github")
    state = client.cookies[auth.OAUTH_STATE_COOKIE]
    response = await client.get(
        "/api/auth/oauth/github/callback", params={"code": "bad-code", "state": state}
    )
    assert response.status_code == 502
    assert await count_users(session) == 0


async def test_a_tampered_session_cookie_is_not_a_session(client):
    await sign_in(client)
    good = client.cookies[auth.SESSION_COOKIE]
    client.cookies.set(auth.SESSION_COOKIE, good[:-1] + ("x" if good[-1] != "x" else "y"),
                       domain=RP_ID, path="/")
    assert (await client.get("/api/me")).status_code == 401


async def test_logout_ends_the_session(client):
    await sign_in(client)
    assert (await client.get("/api/me")).status_code == 200
    out = await client.post("/api/auth/logout")
    assert out.status_code in (200, 204)
    assert (await client.get("/api/me")).status_code == 401


async def test_a_deleted_user_cannot_keep_using_their_cookie(client, session):
    await sign_in(client)
    user = (await session.execute(select(m.User))).scalar_one()
    await session.delete(user)
    await session.commit()
    assert (await client.get("/api/me")).status_code == 401


async def test_the_session_rolls_forward_on_use(client):
    await sign_in(client)
    response = await client.get("/api/me")
    assert response.status_code == 200
    assert auth.SESSION_COOKIE in response.headers.get("set-cookie", "")


# --- passkeys ----------------------------------------------------------------


class SoftAuthenticator:
    """A minimal ES256 platform authenticator. Enough to be verified for real."""

    def __init__(self, rp_id: str = RP_ID, origin: str = ORIGIN) -> None:
        self.rp_id = rp_id
        self.origin = origin
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.sign_count = 0

    @property
    def _rp_id_hash(self) -> bytes:
        return hashlib.sha256(self.rp_id.encode()).digest()

    def _client_data(self, kind: str, challenge: str) -> bytes:
        return json.dumps(
            {"type": kind, "challenge": challenge, "origin": self.origin, "crossOrigin": False}
        ).encode()

    def _cose_key(self) -> bytes:
        numbers = self.key.public_key().public_numbers()
        return cbor2.dumps({
            1: 2, 3: -7, -1: 1,
            -2: numbers.x.to_bytes(32, "big"),
            -3: numbers.y.to_bytes(32, "big"),
        })

    def register(self, options: dict) -> dict:
        challenge = options["challenge"]
        auth_data = (
            self._rp_id_hash
            + bytes([0x45])                       # UP | UV | AT
            + self.sign_count.to_bytes(4, "big")
            + b"\x00" * 16                        # aaguid
            + len(self.credential_id).to_bytes(2, "big")
            + self.credential_id
            + self._cose_key()
        )
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {
            "id": b64u(self.credential_id),
            "rawId": b64u(self.credential_id),
            "type": "public-key",
            "clientExtensionResults": {},
            "response": {
                "clientDataJSON": b64u(self._client_data("webauthn.create", challenge)),
                "attestationObject": b64u(attestation),
            },
        }

    def authenticate(self, options: dict) -> dict:
        self.sign_count += 1
        client_data = self._client_data("webauthn.get", options["challenge"])
        auth_data = (
            self._rp_id_hash + bytes([0x05]) + self.sign_count.to_bytes(4, "big")
        )
        signature = self.key.sign(
            auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256())
        )
        return {
            "id": b64u(self.credential_id),
            "rawId": b64u(self.credential_id),
            "type": "public-key",
            "clientExtensionResults": {},
            "response": {
                "clientDataJSON": b64u(client_data),
                "authenticatorData": b64u(auth_data),
                "signature": b64u(signature),
                "userHandle": b64u(b"handle"),
            },
        }


async def register_passkey(client: httpx.AsyncClient, device: SoftAuthenticator,
                           email: str | None = "grace@example.test") -> httpx.Response:
    options = (await client.post(
        "/api/auth/passkey/register/options", json={"email": email}
    )).json()
    return await client.post(
        "/api/auth/passkey/register", json={"credential": device.register(options)}
    )


async def test_a_passkey_registers_then_signs_in(client, session):
    device = SoftAuthenticator()
    created = await register_passkey(client, device)
    assert created.status_code == 200, created.text
    assert await count_users(session) == 1
    user_id = (await client.get("/api/me")).json()["id"]

    stored = (await session.execute(select(m.Passkey))).scalar_one()
    assert stored.credential_id == device.credential_id
    assert stored.user_id == user_id

    client.cookies.clear()
    assert (await client.get("/api/me")).status_code == 401
    options = (await client.post("/api/auth/passkey/authenticate/options", json={})).json()
    signed_in = await client.post(
        "/api/auth/passkey/authenticate", json={"credential": device.authenticate(options)}
    )
    assert signed_in.status_code == 200, signed_in.text
    assert (await client.get("/api/me")).json()["id"] == user_id


async def test_a_passkey_signature_from_another_key_is_refused(client, session):
    device = SoftAuthenticator()
    await register_passkey(client, device)
    client.cookies.clear()

    impostor = SoftAuthenticator()
    impostor.credential_id = device.credential_id      # same id, different private key
    options = (await client.post("/api/auth/passkey/authenticate/options", json={})).json()
    response = await client.post(
        "/api/auth/passkey/authenticate", json={"credential": impostor.authenticate(options)}
    )
    assert response.status_code == 401
    assert auth.SESSION_COOKIE not in response.cookies


async def test_a_registration_replayed_against_a_fresh_challenge_is_refused(client):
    device = SoftAuthenticator()
    stale = (await client.post(
        "/api/auth/passkey/register/options", json={"email": "eve@example.test"}
    )).json()
    captured = device.register(stale)
    # A new ceremony rotates the challenge cookie; the captured response is now stale.
    await client.post("/api/auth/passkey/register/options", json={"email": "eve@example.test"})
    replay = await client.post("/api/auth/passkey/register", json={"credential": captured})
    assert replay.status_code == 400


async def test_an_unknown_credential_cannot_sign_in(client):
    device = SoftAuthenticator()
    await register_passkey(client, device)
    client.cookies.clear()
    stranger = SoftAuthenticator()
    options = (await client.post("/api/auth/passkey/authenticate/options", json={})).json()
    response = await client.post(
        "/api/auth/passkey/authenticate", json={"credential": stranger.authenticate(options)}
    )
    assert response.status_code == 401


async def test_a_passkey_cannot_claim_an_address_another_account_holds(client, session):
    await sign_in(client)                     # ada@example.test, verified by github
    client.cookies.clear()
    conflict = await register_passkey(client, SoftAuthenticator(), email="ada@example.test")
    assert conflict.status_code == 409
    assert await count_users(session) == 1


async def test_a_signed_in_user_adds_a_second_passkey_to_the_same_account(client, session):
    await sign_in(client)
    user_id = (await client.get("/api/me")).json()["id"]
    added = await register_passkey(client, SoftAuthenticator(), email=None)
    assert added.status_code == 200, added.text
    assert await count_users(session) == 1
    keys = (await session.execute(select(m.Passkey))).scalars().all()
    assert [k.user_id for k in keys] == [user_id]


# --- nothing sensitive leaks -------------------------------------------------


async def test_no_response_carries_the_session_secret(client):
    response = await sign_in(client)
    body = response.text + json.dumps(dict(response.headers))
    assert "k" * 48 not in body
