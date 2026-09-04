"""Sign-in routes (component 15 §5).

Thin on purpose: every rule lives in ``explorer_api.auth``; this module only
moves values between cookies, request bodies and HTTP status codes.

Status-code contract, because it is security-relevant:

* ``400`` — a ceremony did not check out (bad state, stale challenge, bad
  attestation). Never says *which*, so it cannot be used as an oracle.
* ``401`` — no session, or a passkey that did not authenticate.
* ``404`` — an OAuth provider that is not configured. Same code as a typo, so
  the response does not enumerate which providers exist.
* ``409`` — a passkey sign-up claiming an address another account holds.
* ``502`` — the provider itself failed. Nothing is written.
"""

from __future__ import annotations

import hmac
from typing import Annotated, Any
from urllib.parse import urlsplit

from fastapi import (
    APIRouter, Body, Depends, HTTPException, Query, Request, Response, status,
)
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auth
from ..db import get_session
from ..models import User
from ..settings import Settings

router = APIRouter(tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# --- plumbing ----------------------------------------------------------------


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _secret(request: Request) -> str:
    return _settings(request).session_secret.get_secret_value()


def _providers(request: Request) -> dict[str, auth.OAuthProvider]:
    """The provider registry, built once per process and cached on app state
    (tests replace it with stubs before the first request)."""
    existing = getattr(request.app.state, "oauth_providers", None)
    if existing is None:
        existing = auth.build_providers(_settings(request))
        request.app.state.oauth_providers = existing
    return existing


def _rp(request: Request) -> tuple[str, list[str]]:
    """WebAuthn relying party id and the origins an assertion may carry.

    Pinned from settings outside dev. Deriving them from the request was two
    bugs in one: the relying-party id — the thing that *scopes a credential* —
    came from the attacker-controllable `Host` header, and the expected origin
    came from `request.url.scheme`, which behind a TLS-terminating tunnel is
    `http` while the browser signs `https`, so no assertion could ever verify.
    """
    settings = _settings(request)
    # Even the dev fallback must describe the SITE, not this API. A credential is
    # scoped to the origin that runs the ceremony, and `rp.id` has to be a
    # registrable-domain suffix of it. Deriving from the request gave
    # `api.llms-explorer.com` for a page on `llms-explorer.com` (not a suffix ->
    # SecurityError) and `127.0.0.1` for a page on `localhost` (likewise), so the
    # first configured site origin is the fallback, and the request only supplies
    # the last resort when no site origin is configured at all.
    site_origin = next(iter(settings.site_origins), None)
    request_origin = f"{request.url.scheme}://{request.url.netloc}"
    origin = site_origin or request_origin
    host = urlsplit(origin).hostname or request.url.hostname or "localhost"
    return settings.webauthn_relying_party(host=host, origin=origin)


def _set_session(response: Response, user: User, *, secret: str) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.sign_session(user.id, secret=secret,
                          epoch=int(user.session_epoch or 0)),
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


async def current_user(request: Request, session: SessionDep) -> User:
    """The signed-in user, or 401. Re-issues the cookie: 30-day *rolling*."""
    user = await optional_user(request, session)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sign in first")
    return user


async def optional_user(request: Request, session: SessionDep) -> User | None:
    token = request.cookies.get(auth.SESSION_COOKIE)
    if not token:
        return None
    try:
        user_id, epoch = auth.read_session(token, secret=_secret(request))
    except auth.AuthError:
        return None
    user = await auth.load_user(session, user_id)
    if user is None:
        return None
    if epoch != int(user.session_epoch or 0):
        # Signed out everywhere since this cookie was minted. A stateless
        # signature has no other way to be revoked, and "revoke a passkey" that
        # leaves the sessions it opened alive is not a revocation.
        return None
    return user


CurrentUser = Annotated[User, Depends(current_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]


def _signed_in(request: Request, user: User, status_code: int = 200) -> JSONResponse:
    response = JSONResponse(auth.public_user(user), status_code=status_code)
    _set_session(response, user, secret=_secret(request))
    return response


# --- OAuth -------------------------------------------------------------------


@router.get("/api/auth/oauth/{provider}", name="oauth_start")
async def oauth_start(provider: str, request: Request) -> RedirectResponse:
    registry = _providers(request)
    if provider not in registry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown provider")
    secret = _secret(request)
    state = auth.new_state(secret=secret)
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    response = RedirectResponse(
        registry[provider].authorization_url(redirect_uri=redirect_uri, state=state),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        auth.OAUTH_STATE_COOKIE, state, max_age=auth.CEREMONY_MAX_AGE,
        httponly=True, secure=True, samesite="lax", path="/",
    )
    return response


@router.get("/api/auth/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(provider: str, request: Request, session: SessionDep,
                         code: str | None = None, state: str | None = None) -> Response:
    registry = _providers(request)
    if provider not in registry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown provider")
    secret = _secret(request)
    cookie_state = request.cookies.get(auth.OAUTH_STATE_COOKIE)
    # Both halves must be present, equal, and *ours*. Equality alone proves
    # nothing — an attacker who can set a cookie can set the query string too.
    if not code or not state or not cookie_state or not hmac.compare_digest(state, cookie_state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "the sign-in did not check out")
    try:
        auth.verify_state(state, secret=secret)
    except auth.AuthError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "the sign-in did not check out"
        ) from exc

    try:
        profile = await registry[provider].fetch_profile(
            code=code, redirect_uri=str(request.url_for("oauth_callback", provider=provider))
        )
    except auth.OAuthError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{provider} sign-in failed") from exc

    user = await auth.resolve_oauth_user(session, profile)
    response = RedirectResponse(
        auth.POST_SIGN_IN_PATH, status_code=status.HTTP_303_SEE_OTHER
    )
    _set_session(response, user, secret=secret)
    response.delete_cookie(auth.OAUTH_STATE_COOKIE, path="/")
    return response


# --- passkeys ----------------------------------------------------------------


@router.post("/api/auth/passkey/register/options")
async def passkey_register_options(request: Request, user: OptionalUser,
                                   body: Annotated[dict[str, Any], Body()] = None) -> Response:
    email = (body or {}).get("email")
    rp_id, _origins = _rp(request)
    options, ceremony = auth.begin_passkey_registration(
        rp_id=rp_id, email=auth.normalise_email(email), user=user
    )
    response = JSONResponse(options)
    response.set_cookie(
        auth.WEBAUTHN_COOKIE, auth.sign_ceremony(ceremony, secret=_secret(request)),
        max_age=auth.CEREMONY_MAX_AGE, httponly=True, secure=True, samesite="lax", path="/",
    )
    return response


@router.post("/api/auth/passkey/register")
async def passkey_register(request: Request, session: SessionDep, user: OptionalUser,
                           body: Annotated[dict[str, Any], Body()] = None) -> Response:
    ceremony = _ceremony(request)
    credential = (body or {}).get("credential")
    if credential is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no credential")
    rp_id, origins = _rp(request)
    try:
        owner = await auth.finish_passkey_registration(
            session, credential=credential, ceremony=ceremony,
            rp_id=rp_id, origin=origins, user=user,
        )
    except auth.EmailTaken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "that email already has an account") from exc
    except auth.AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "the passkey did not check out") from exc
    response = _signed_in(request, owner)
    response.delete_cookie(auth.WEBAUTHN_COOKIE, path="/")
    return response


@router.post("/api/auth/passkey/authenticate/options")
async def passkey_authenticate_options(request: Request) -> Response:
    rp_id, _origins = _rp(request)
    options, ceremony = auth.begin_passkey_authentication(rp_id=rp_id)
    response = JSONResponse(options)
    response.set_cookie(
        auth.WEBAUTHN_COOKIE, auth.sign_ceremony(ceremony, secret=_secret(request)),
        max_age=auth.CEREMONY_MAX_AGE, httponly=True, secure=True, samesite="lax", path="/",
    )
    return response


@router.post("/api/auth/passkey/authenticate")
async def passkey_authenticate(request: Request, session: SessionDep,
                               body: Annotated[dict[str, Any], Body()] = None) -> Response:
    ceremony = _ceremony(request, unauthorized=True)
    credential = (body or {}).get("credential")
    if credential is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "that passkey did not check out")
    rp_id, origins = _rp(request)
    try:
        user = await auth.finish_passkey_authentication(
            session, credential=credential, ceremony=ceremony, rp_id=rp_id,
            origin=origins
        )
    except auth.AuthError as exc:
        # One code and one message for "unknown credential" and "bad signature"
        # alike: the difference is exactly what an attacker would probe for.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "that passkey did not check out"
        ) from exc
    response = _signed_in(request, user)
    response.delete_cookie(auth.WEBAUTHN_COOKIE, path="/")
    return response


def _ceremony(request: Request, *, unauthorized: bool = False) -> dict[str, Any]:
    code = status.HTTP_401_UNAUTHORIZED if unauthorized else status.HTTP_400_BAD_REQUEST
    token = request.cookies.get(auth.WEBAUTHN_COOKIE)
    if not token:
        raise HTTPException(code, "start the ceremony first")
    try:
        return auth.read_ceremony(token, secret=_secret(request))
    except auth.AuthError as exc:
        raise HTTPException(code, "start the ceremony first") from exc


# --- session -----------------------------------------------------------------


@router.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, session: SessionDep,
                 all_devices: Annotated[bool, Query(alias="all")] = False) -> Response:
    """Sign out. Deleting the cookie is not enough on its own.

    The session token is a stateless signature with a 30-day rolling expiry, so
    a cookie captured once (a shared machine, a proxy log, an XSS on the site)
    stayed valid for 30 days and — because `/api/me` re-issues it — indefinitely.
    `?all=true` bumps the account's session epoch, which invalidates every token
    already minted for it on every device.
    """
    if all_devices:
        user = await optional_user(request, session)
        if user is not None:
            auth.revoke_sessions(user)
            await session.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(auth.SESSION_COOKIE, path="/", httponly=True,
                           secure=True, samesite="lax")
    return response


@router.get("/api/me")
async def me(request: Request, user: CurrentUser) -> Response:
    return _signed_in(request, user)
