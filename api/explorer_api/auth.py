"""Accounts and sessions: passkeys, OAuth, and the cookie that carries both.

Authority: component 15 §2 ("email + passkey (WebAuthn) or OAuth (GitHub,
Google); no passwords"), §5 (the route table) and §10 ("passkeys + OAuth only").

Three rules this module exists to hold:

* **A verified email is the only thing that merges two sign-ins into one
  account.** A provider that hands back an address it has not verified gets a
  *new* account, never someone else's — otherwise anyone who can set an
  unverified address on any linked provider owns every account with that email.
* **The session cookie is signed, ``HttpOnly``, ``Secure``, ``SameSite=Lax``**
  with a 30-day rolling expiry: it is re-issued on use, so an active session
  never expires under someone and an abandoned one still dies on schedule.
* **Nothing in here is state the server has to remember.** The OAuth `state`
  and the WebAuthn challenge both live in short-lived signed cookies, so a
  second API replica can finish a ceremony the first one started (master §8
  runs two).

The module is deliberately transport-free — no ``Request``-shaped arguments
past the thin helpers at the bottom — so ``routes/auth.py`` stays a wiring
layer and every rule above is unit-testable without HTTP.
"""

from __future__ import annotations

import base64
import datetime as dt
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from . import models as m
from .settings import Settings

# --- cookie names and lifetimes ----------------------------------------------

SESSION_COOKIE = "explorer_session"
OAUTH_STATE_COOKIE = "explorer_oauth_state"
WEBAUTHN_COOKIE = "explorer_webauthn"

#: 30-day rolling expiry (component 15 §6's account surface assumes a session
#: that survives a week away from the site).
SESSION_MAX_AGE = 30 * 24 * 60 * 60
#: An OAuth round-trip and a WebAuthn ceremony are both a few seconds of user
#: time. Ten minutes is generous; anything longer is a replay window.
CEREMONY_MAX_AGE = 10 * 60

SESSION_SALT = "explorer.session.v1"
OAUTH_STATE_SALT = "explorer.oauth-state.v1"
WEBAUTHN_SALT = "explorer.webauthn.v1"

RP_NAME = "LLMS-Explorer"

#: Where the browser lands after a successful OAuth callback. Relative on
#: purpose: an absolute URL taken from a request parameter is an open redirect.
POST_SIGN_IN_PATH = "/account"


class AuthError(RuntimeError):
    """Something in a sign-in ceremony did not check out."""


class OAuthError(AuthError):
    """The provider could not be talked to, or refused the code."""


class EmailTaken(AuthError):
    """A passkey sign-up claimed an address another account already holds."""


# --- signing helpers ---------------------------------------------------------


def _serializer(secret: str, salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt=salt)


def _secret(settings: Settings) -> str:
    return settings.session_secret.get_secret_value()


def sign_state(value: str, *, secret: str) -> str:
    """Sign an OAuth `state` nonce. The signature is what makes the cookie
    unforgeable — comparing a cookie to a query parameter proves only that the
    same string is in both places, which an attacker controls."""
    return _serializer(secret, OAUTH_STATE_SALT).dumps(value)


def verify_state(token: str, *, secret: str, max_age: int = CEREMONY_MAX_AGE) -> str:
    try:
        return _serializer(secret, OAUTH_STATE_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired) as exc:
        raise AuthError("the OAuth state did not verify") from exc


def new_state(*, secret: str) -> str:
    return sign_state(secrets.token_urlsafe(24), secret=secret)


def sign_session(user_id: str, *, secret: str, epoch: int = 0) -> str:
    """Mint a session token for ``user_id`` at ``epoch``.

    The epoch is what makes a stateless cookie revocable: it is compared against
    ``users.session_epoch`` on every use, so bumping that column invalidates
    every token already issued — which is what "sign out everywhere", "this
    passkey was stolen" and "close the sessions this OAuth link opened" all need.
    """
    return _serializer(secret, SESSION_SALT).dumps({"uid": user_id, "epoch": int(epoch)})


def read_session(token: str, *, secret: str,
                 max_age: int = SESSION_MAX_AGE) -> tuple[str, int]:
    """Return ``(user_id, epoch)`` a session token carries, or raise."""
    try:
        payload = _serializer(secret, SESSION_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired) as exc:
        raise AuthError("the session cookie did not verify") from exc
    uid = (payload or {}).get("uid") if isinstance(payload, Mapping) else None
    if not isinstance(uid, str) or not uid:
        raise AuthError("the session cookie carried no user")
    epoch = (payload or {}).get("epoch")
    # A token minted before the epoch existed carries none; it is treated as
    # epoch 0, which every account starts at.
    return uid, int(epoch) if isinstance(epoch, int) else 0


def revoke_sessions(user: m.User) -> int:
    """Invalidate every session token already issued for ``user``.

    Returns the new epoch. The caller commits — revoking sessions and the reason
    for revoking them (a deleted passkey, an unlinked provider) must land
    together or not at all.
    """
    user.session_epoch = int(user.session_epoch or 0) + 1
    return user.session_epoch


def sign_ceremony(payload: dict[str, Any], *, secret: str) -> str:
    return _serializer(secret, WEBAUTHN_SALT).dumps(payload)


def read_ceremony(token: str, *, secret: str,
                  max_age: int = CEREMONY_MAX_AGE) -> dict[str, Any]:
    try:
        payload = _serializer(secret, WEBAUTHN_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired) as exc:
        raise AuthError("the WebAuthn ceremony did not verify") from exc
    if not isinstance(payload, dict):
        raise AuthError("the WebAuthn ceremony was malformed")
    return payload


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def unb64url(raw: str) -> bytes:
    return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))


# --- OAuth -------------------------------------------------------------------


@dataclass(frozen=True)
class OAuthProfile:
    """What a provider tells us about the person who just signed in.

    ``email_verified`` is load-bearing: it is the difference between linking to
    an existing account and creating a new one.
    """

    provider: str
    account_id: str
    email: str | None = None
    email_verified: bool = False
    display_name: str | None = None


class OAuthProvider(Protocol):
    """The seam the tests stub. Nothing below it reaches the network."""

    name: str

    def authorization_url(self, *, redirect_uri: str, state: str) -> str: ...

    async def fetch_profile(self, *, code: str, redirect_uri: str) -> OAuthProfile: ...


@dataclass
class HttpOAuthProvider:
    """A real OAuth 2.0 authorization-code provider, over httpx."""

    name: str
    client_id: str
    client_secret: str
    authorize_endpoint: str
    token_endpoint: str
    scope: str
    timeout: float = 10.0
    extra_authorize: dict[str, str] = field(default_factory=dict)

    def authorization_url(self, *, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.scope,
            "state": state,
            "response_type": "code",
            **self.extra_authorize,
        }
        return str(httpx.URL(self.authorize_endpoint, params=params))

    async def fetch_profile(self, *, code: str, redirect_uri: str) -> OAuthProfile:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            token = await self._exchange(client, code=code, redirect_uri=redirect_uri)
            return await self._profile(client, token)

    async def _exchange(self, client: httpx.AsyncClient, *, code: str,
                        redirect_uri: str) -> str:
        try:
            response = await client.post(
                self.token_endpoint,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:  # network, TLS, timeout
            raise OAuthError(f"{self.name}: token endpoint unreachable") from exc
        if response.status_code >= 400:
            # Never echo the body: it can contain the client secret we just sent back.
            raise OAuthError(f"{self.name}: token exchange failed ({response.status_code})")
        payload = response.json()
        token = payload.get("access_token") or payload.get("id_token")
        if not token:
            raise OAuthError(f"{self.name}: no access token in the token response")
        return str(token)

    async def _profile(self, client: httpx.AsyncClient, token: str) -> OAuthProfile:
        raise OAuthError(f"{self.name}: profile lookup is not implemented")


class GitHubProvider(HttpOAuthProvider):
    async def _profile(self, client: httpx.AsyncClient, token: str) -> OAuthProfile:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        try:
            user_response = await client.get("https://api.github.com/user", headers=headers)
        except httpx.HTTPError as exc:
            raise OAuthError(f"{self.name}: profile lookup failed") from exc
        if user_response.status_code >= 400:
            raise OAuthError(f"{self.name}: profile lookup failed ({user_response.status_code})")

        try:
            user = user_response.json()
        except ValueError as exc:
            raise OAuthError(f"{self.name}: profile response was not valid JSON") from exc

        # The public profile email may be unset or unverified; the emails
        # endpoint is the only place GitHub says which address it has proven.
        email, verified = None, False
        try:
            addresses_response = await client.get(
                "https://api.github.com/user/emails", headers=headers
            )
        except httpx.HTTPError:
            addresses_response = None
        if addresses_response is not None and addresses_response.status_code < 400:
            try:
                addresses = addresses_response.json()
            except ValueError:
                addresses = []
            if isinstance(addresses, list):
                for entry in addresses:
                    if isinstance(entry, dict) and entry.get("primary") and entry.get("verified"):
                        email, verified = entry.get("email"), True
                        break
        account_id = user.get("id")
        if account_id is None:
            raise OAuthError(f"{self.name}: profile response had no account id")
        return OAuthProfile(
            provider=self.name,
            account_id=str(account_id),
            email=email,
            email_verified=verified,
            display_name=user.get("name") or user.get("login"),
        )


class GoogleProvider(HttpOAuthProvider):
    async def _profile(self, client: httpx.AsyncClient, token: str) -> OAuthProfile:
        try:
            response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as exc:
            raise OAuthError(f"{self.name}: profile lookup failed") from exc
        if response.status_code >= 400:
            raise OAuthError(f"{self.name}: profile lookup failed ({response.status_code})")
        try:
            info = response.json()
        except ValueError as exc:
            raise OAuthError(f"{self.name}: profile response was not valid JSON") from exc
        account_id = info.get("sub")
        if account_id is None:
            raise OAuthError(f"{self.name}: profile response had no account id")
        return OAuthProfile(
            provider=self.name,
            account_id=str(account_id),
            email=info.get("email"),
            email_verified=bool(info.get("email_verified")),
            display_name=info.get("name"),
        )


def build_providers(settings: Settings) -> dict[str, OAuthProvider]:
    """Only the providers whose credentials are actually configured.

    An unconfigured provider is simply absent, so the route 404s rather than
    bouncing the user to a broken consent screen.
    """
    providers: dict[str, OAuthProvider] = {}
    if settings.oauth_github_id and settings.oauth_github_secret:
        providers["github"] = GitHubProvider(
            name="github",
            client_id=settings.oauth_github_id,
            client_secret=settings.oauth_github_secret.get_secret_value(),
            authorize_endpoint="https://github.com/login/oauth/authorize",
            token_endpoint="https://github.com/login/oauth/access_token",
            scope="read:user user:email",
        )
    if settings.oauth_google_id and settings.oauth_google_secret:
        providers["google"] = GoogleProvider(
            name="google",
            client_id=settings.oauth_google_id,
            client_secret=settings.oauth_google_secret.get_secret_value(),
            authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            scope="openid email profile",
            extra_authorize={"access_type": "online", "prompt": "select_account"},
        )
    return providers


# --- users -------------------------------------------------------------------


def normalise_email(email: object) -> str | None:
    if not isinstance(email, str):
        return None
    normalised = email.strip().lower()
    return normalised or None


async def _user_by_email(session: AsyncSession, email: str) -> m.User | None:
    """The account that has **proved** ``email``, or ``None``.

    ``email_verified`` in the filter is the whole security property of this
    module's first rule. Without it an account whose address was merely
    *claimed* — a passkey sign-up types one into an unauthenticated request
    body — was a row a later, genuinely verified OAuth sign-in merged into,
    which handed the claimant the victim's account, keys, usage and artifacts.
    """
    return (
        await session.execute(
            select(m.User).where(
                m.User.email == email, m.User.email_verified.is_(True)
            )
        )
    ).scalar_one_or_none()


async def resolve_oauth_user(session: AsyncSession, profile: OAuthProfile) -> m.User:
    """Find or create the account this profile belongs to.

    Order matters, and it is the security-relevant part:

    1. an existing link for ``(provider, account_id)`` — the strongest claim,
       and the only one that survives the person changing their email;
    2. otherwise a **verified** address matching an existing account, which is
       what makes "sign in with GitHub" and "sign in with Google" one account;
    3. otherwise a new account.
    """
    now = dt.datetime.now(dt.UTC)
    link = (
        await session.execute(
            select(m.OAuthAccount).where(
                m.OAuthAccount.provider == profile.provider,
                m.OAuthAccount.provider_account_id == profile.account_id,
            )
        )
    ).scalar_one_or_none()
    email = normalise_email(profile.email)

    if link is not None:
        link.last_used_at = now
        link.email = email or link.email
        link.email_verified = profile.email_verified
        user = (
            await session.execute(select(m.User).where(m.User.id == link.user_id))
        ).scalar_one()
        _adopt_verified_email(user, email, profile.email_verified)
        await session.commit()
        return user

    user: m.User | None = None
    if email and profile.email_verified:
        user = await _user_by_email(session, email)

    if user is None:
        user = m.User(
            email=email if profile.email_verified else None,
            email_verified=bool(email) and profile.email_verified,
            display_name=profile.display_name,
        )
        session.add(user)
        await session.flush()
    else:
        _adopt_verified_email(user, email, profile.email_verified)

    session.add(
        m.OAuthAccount(
            user_id=user.id,
            provider=profile.provider,
            provider_account_id=profile.account_id,
            email=email,
            email_verified=profile.email_verified,
            last_used_at=now,
        )
    )
    try:
        await session.commit()
    except IntegrityError:
        # Two first sign-ins raced. The loser re-reads what the winner wrote
        # rather than handing the caller a second account.
        await session.rollback()
        raced = (
            await session.execute(
                select(m.OAuthAccount).where(
                    m.OAuthAccount.provider == profile.provider,
                    m.OAuthAccount.provider_account_id == profile.account_id,
                )
            )
        ).scalar_one_or_none()
        if raced is None:
            raise
        return (
            await session.execute(select(m.User).where(m.User.id == raced.user_id))
        ).scalar_one()
    return user


def _adopt_verified_email(user: m.User, email: str | None, verified: bool) -> None:
    """Fill in an address only when the provider says it proved it.

    This is also the only path by which a ``pending_email`` becomes real: the
    account claimed the address at passkey sign-up, and a provider has now
    proved that the person holding the account holds the address too.
    """
    if not (email and verified):
        return
    if not user.email:
        user.email = email
        user.email_verified = True
    elif user.email == email and not user.email_verified:
        user.email_verified = True
    if user.pending_email == email:
        user.pending_email = None


async def load_user(session: AsyncSession, user_id: str) -> m.User | None:
    user = (
        await session.execute(select(m.User).where(m.User.id == user_id))
    ).scalar_one_or_none()
    if user is None or user.deleted_at is not None:
        return None
    return user


def public_user(user: m.User) -> dict[str, Any]:
    """The `/api/me` shape. No secret, no internal column."""
    return {
        "id": user.id,
        "email": user.email,
        "email_verified": user.email_verified,
        #: What the account claimed at sign-up and nothing has proved. Shown so
        #: the UI can ask the owner to verify it; never treated as an identity.
        "pending_email": user.pending_email,
        "display_name": user.display_name,
        "plan": user.plan_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# --- passkeys ----------------------------------------------------------------


def begin_passkey_registration(*, rp_id: str, email: str | None,
                               user: m.User | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(options_json, ceremony_payload)`` for a registration ceremony.

    ``ceremony_payload`` goes into a short-lived signed cookie; the server keeps
    no ceremony state of its own, so either replica can finish it.
    """
    handle = secrets.token_bytes(32)
    label = (user.email if user else None) or email or f"user-{b64url(handle)[:8]}"
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=handle,
        user_name=label,
        user_display_name=(user.display_name if user else None) or label,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    payload = {
        "purpose": "register",
        "challenge": b64url(options.challenge),
        "email": email,
        "user_id": user.id if user else None,
    }
    return _options_dict(options), payload


async def finish_passkey_registration(
    session: AsyncSession, *, credential: Any, ceremony: dict[str, Any],
    rp_id: str, origin: str | list[str], user: m.User | None,
) -> m.User:
    """Verify the attestation, then create or extend the account behind it."""
    if ceremony.get("purpose") != "register":
        raise AuthError("that ceremony was not a registration")
    try:
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=unb64url(str(ceremony.get("challenge", ""))),
            expected_rp_id=rp_id,
            expected_origin=origin,
        )
    except Exception as exc:  # py_webauthn raises a family of parse/verify errors
        raise AuthError(f"the passkey registration did not verify: {exc}") from exc

    # The cookie, not the request body, says whose ceremony this was.
    owner = user
    if owner is not None and ceremony.get("user_id") not in (None, owner.id):
        raise AuthError("that ceremony belongs to a different session")
    if owner is None and ceremony.get("user_id"):
        owner = await load_user(session, str(ceremony["user_id"]))

    if owner is None:
        email = normalise_email(ceremony.get("email"))
        if email and await _user_by_email(session, email) is not None:
            # A passkey has not *proved* the address, so it can never take over
            # an account that holds it.
            raise EmailTaken(email)
        # The address goes in `pending_email`, never `email`: it arrived in an
        # unauthenticated request body and nothing has proved it. Writing it to
        # `users.email` made this row a merge target for the real owner's next
        # verified OAuth sign-in — the pre-hijack this column exists to close.
        owner = m.User(email=None, email_verified=False, pending_email=email)
        session.add(owner)
        await session.flush()

    session.add(
        m.Passkey(
            user_id=owner.id,
            credential_id=bytes(verified.credential_id),
            public_key=bytes(verified.credential_public_key),
            sign_count=int(verified.sign_count),
            aaguid=str(verified.aaguid) if verified.aaguid else None,
            last_used_at=dt.datetime.now(dt.UTC),
        )
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AuthError("that passkey is already registered") from exc
    return owner


def begin_passkey_authentication(*, rp_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    options = generate_authentication_options(
        rp_id=rp_id, user_verification=UserVerificationRequirement.PREFERRED
    )
    return _options_dict(options), {
        "purpose": "authenticate",
        "challenge": b64url(options.challenge),
    }


async def finish_passkey_authentication(
    session: AsyncSession, *, credential: Any, ceremony: dict[str, Any],
    rp_id: str, origin: str | list[str],
) -> m.User:
    if ceremony.get("purpose") != "authenticate":
        raise AuthError("that ceremony was not an authentication")
    raw_id = _raw_credential_id(credential)
    stored = (
        await session.execute(
            select(m.Passkey).where(m.Passkey.credential_id == raw_id)
        )
    ).scalar_one_or_none()
    if stored is None:
        # Same message either way: whether a credential is registered here is
        # not something an unauthenticated caller gets to learn.
        raise AuthError("that passkey is not registered")
    try:
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=unb64url(str(ceremony.get("challenge", ""))),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=bytes(stored.public_key),
            credential_current_sign_count=int(stored.sign_count),
        )
    except Exception as exc:
        raise AuthError("that passkey did not verify") from exc

    user = await load_user(session, stored.user_id)
    if user is None:
        raise AuthError("that passkey has no account")
    stored.sign_count = int(verified.new_sign_count)
    stored.last_used_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return user


def _raw_credential_id(credential: Any) -> bytes:
    raw = None
    if isinstance(credential, Mapping):
        raw = credential.get("rawId") or credential.get("id")
    if not isinstance(raw, str) or not raw:
        raise AuthError("the credential carried no id")
    try:
        return unb64url(raw)
    except Exception as exc:
        raise AuthError("the credential id was not base64url") from exc


def _options_dict(options: Any) -> dict[str, Any]:
    import json

    return json.loads(options_to_json(options))


__all__ = [
    "CEREMONY_MAX_AGE",
    "OAUTH_STATE_COOKIE",
    "SESSION_COOKIE",
    "SESSION_MAX_AGE",
    "WEBAUTHN_COOKIE",
    "AuthError",
    "EmailTaken",
    "GitHubProvider",
    "GoogleProvider",
    "HttpOAuthProvider",
    "OAuthError",
    "OAuthProfile",
    "OAuthProvider",
    "begin_passkey_authentication",
    "begin_passkey_registration",
    "build_providers",
    "finish_passkey_authentication",
    "finish_passkey_registration",
    "load_user",
    "new_state",
    "public_user",
    "read_ceremony",
    "read_session",
    "resolve_oauth_user",
    "revoke_sessions",
    "sign_ceremony",
    "sign_session",
    "sign_state",
    "verify_state",
]
