"""Typed settings, loaded from the environment, that fail fast and loudly.

Rules this module exists to enforce (Global Constraints of the step-3 plan):

* Secrets come from the **environment**, never from a file in the repo. A
  ``.env`` sitting next to the app is deliberately NOT read — an operator
  sources it into the environment first (see ``.env.example``).
* A missing required variable fails at startup with **every** missing name in
  the message, not just the first one.
* Nothing sensitive is ever ``repr``-able: secrets are ``SecretStr``, so a
  traceback, a log line or a debugger never carries the plaintext.
* ``hub_mcp_url`` stays on loopback. The hub MCP server never faces the tunnel
  (``hub/docs/MCP.md``), so a non-loopback host is a configuration error.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "prod"]

#: Variables with no default and no safe fallback. Missing any of these is a
#: startup failure, reported together.
REQUIRED_VARS: tuple[str, ...] = (
    "DATABASE_URL",
    "SESSION_SECRET",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
)

#: Hosts the hub MCP gateway is allowed to talk to. Anything else would put the
#: hub's unauthenticated tool surface on a routable address.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})

DEFAULT_HUB_MCP_URL = "http://127.0.0.1:8787"
DEFAULT_STORES_ROOT = Path.home() / ".llms-explorer" / "stores"
MIN_SESSION_SECRET_LEN = 32

#: The site is a different origin from the API (`site/src/components/AccountNav.astro`
#: publishes `https://api.llms-explorer.com`) and every account island fetches with
#: `credentials: "include"`. That combination needs CORS with an **explicit** origin
#: list: `allow_origins=["*"]` is invalid with credentials, and a regex would match
#: `llms-explorer.com.evil.net`. `SameSite=Lax` is no defence between siblings of one
#: registrable domain, so this list is what stands between a subdomain and the session.
DEFAULT_SITE_ORIGINS = ("https://llms-explorer.com", "https://www.llms-explorer.com")

#: Hosts the app answers to at all. The WebAuthn relying-party id used to be read
#: straight off the `Host` header, which made a credential-scoping decision
#: attacker-controlled; pinning the host list is the other half of pinning the RP.
DEFAULT_ALLOWED_HOSTS = ("api.llms-explorer.com", "llms-explorer.com", "localhost",
                         "127.0.0.1", "testserver", "test", "api.test", "*.test")


def normalize_database_url(value: str) -> str:
    """Coerce a Postgres DSN to the async SQLAlchemy dialect used here.

    The app and Alembic both require an async driver. The repo is wired to
    ``asyncpg`` and the helper tests boot a temporary Postgres cluster with the
    equivalent ``postgresql+asyncpg://...`` DSN. A plain driver-less DSN is
    convenient for admin tooling but not for SQLAlchemy async, so we normalize it
    once here instead of leaving every caller to remember the detail.

    Neon and other managed Postgres providers often append parameters like
    ``sslmode=require`` and ``channel_binding=require`` for psycopg-compatible
    clients. ``asyncpg`` accepts ``ssl=require`` instead, so we translate the
    common psycopg keys to the asyncpg equivalent and drop the rest.
    """
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"postgresql", "postgresql+asyncpg", "postgresql+psycopg2"}:
        return url

    scheme = "postgresql+asyncpg"
    if parsed.netloc and "://" not in url:
        # Defensive fallback for malformed inputs: keep the original string.
        return url

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode:
        query["ssl"] = sslmode

    normalized = parsed._replace(scheme=scheme, query=urlencode(query, doseq=True))
    return urlunparse(normalized)


class MissingSettings(RuntimeError):
    """Raised when required environment variables are absent — names them all."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = list(missing)
        joined = ", ".join(self.missing)
        super().__init__(
            f"explorer-api cannot start: {len(self.missing)} required environment "
            f"variable(s) are not set: {joined}. "
            "Set them in the environment (see api/.env.example); they are never "
            "read from a file in the repo."
        )


class Settings(BaseSettings):
    """Everything the service needs to run, resolved once at startup."""

    model_config = SettingsConfigDict(
        env_file=None,          # secrets come from the environment, never a repo file
        extra="ignore",
        frozen=True,
    )

    # --- required -----------------------------------------------------------
    database_url: SecretStr
    session_secret: SecretStr
    stripe_secret_key: SecretStr
    stripe_webhook_secret: SecretStr

    @field_validator("database_url", mode="before")
    @classmethod
    def _database_url_is_async_compatible(cls, value: object) -> object:
        if isinstance(value, str):
            return SecretStr(normalize_database_url(value))
        if isinstance(value, SecretStr):
            return SecretStr(normalize_database_url(value.get_secret_value()))
        return value

    # --- optional until the surface that needs them is used (Task 3) ---------
    oauth_github_id: str | None = None
    oauth_github_secret: SecretStr | None = None
    oauth_google_id: str | None = None
    oauth_google_secret: SecretStr | None = None

    # --- defaulted ----------------------------------------------------------
    hub_mcp_url: str = Field(default=DEFAULT_HUB_MCP_URL)
    stores_root: Path = Field(default=DEFAULT_STORES_ROOT)
    environment: Environment = "dev"
    #: Comma-separated in the environment; a list here.
    site_origins: tuple[str, ...] = Field(default=DEFAULT_SITE_ORIGINS)
    allowed_hosts: tuple[str, ...] = Field(default=DEFAULT_ALLOWED_HOSTS)
    #: WebAuthn relying party. Pinned in prod: an RP id taken from the request is
    #: a security parameter an attacker sets. Empty in dev means "derive it from
    #: the request", which is what makes localhost and a preview domain work.
    webauthn_rp_id: str | None = None
    webauthn_origins: tuple[str, ...] = Field(default=())
    #: The subscribers confirm/unsubscribe links are mailed, so they must be
    #: absolute; this is the origin they are built against. Unset in dev means
    #: `notify.py` logs instead of sending (see its module docstring).
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str = "no-reply@llms-explorer.com"
    api_public_url: str = Field(default="http://127.0.0.1:8790")

    @field_validator("site_origins", "allowed_hosts", "webauthn_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value

    @field_validator("site_origins", "webauthn_origins")
    @classmethod
    def _origins_are_absolute(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for origin in value:
            parsed = urlparse(origin)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(
                    f"{origin!r} is not an absolute origin (scheme://host[:port])"
                )
            if origin.rstrip("/") != origin or parsed.path:
                raise ValueError(f"{origin!r} must be a bare origin, with no path")
        return value

    def webauthn_relying_party(self, *, host: str, origin: str) -> tuple[str, list[str]]:
        """``(rp_id, expected_origins)`` for a ceremony, pinned where configured.

        In ``prod`` the configured values win outright, so the `Host` header
        cannot move the credential scope and a TLS-terminating tunnel (which
        makes uvicorn see ``http``) cannot break the origin check. In ``dev``
        the request is the fallback, which is what keeps localhost working.
        """
        rp_id = self.webauthn_rp_id or (host if self.environment == "dev" else None)
        if not rp_id:
            raise ValueError(
                "WEBAUTHN_RP_ID must be set outside dev: deriving the relying-party "
                "id from the Host header lets a caller choose the credential scope."
            )
        origins = list(self.webauthn_origins)
        if not origins:
            if self.environment != "dev":
                raise ValueError(
                    "WEBAUTHN_ORIGINS must be set outside dev: behind a "
                    "TLS-terminating tunnel the request scheme is http, so an "
                    "origin derived from it never matches what the browser signed."
                )
            origins = [origin]
        return rp_id, origins

    @field_validator("session_secret")
    @classmethod
    def _session_secret_is_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SESSION_SECRET_LEN:
            raise ValueError(
                f"SESSION_SECRET must be at least {MIN_SESSION_SECRET_LEN} characters"
            )
        return value

    @field_validator("stores_root")
    @classmethod
    def _stores_root_is_absolute(cls, value: Path) -> Path:
        # ``~/...`` is the natural thing to write in a shell env; expand it here
        # so every caller downstream gets a real absolute path.
        return value.expanduser()

    @field_validator("hub_mcp_url")
    @classmethod
    def _hub_stays_on_loopback(cls, value: str) -> str:
        host = urlparse(value).hostname
        if host not in LOOPBACK_HOSTS:
            raise ValueError(
                f"HUB_MCP_URL must stay on loopback (got host {host!r}). The hub MCP "
                "server is unauthenticated and must never face the tunnel."
            )
        return value

    @classmethod
    def load(cls, env: dict[str, str] | None = None) -> Settings:
        """Build settings from ``env`` (default ``os.environ``).

        Collects *every* missing required variable before raising, so one
        restart tells the operator the whole story.
        """
        source = os.environ if env is None else env
        missing = [var for var in REQUIRED_VARS if not (source.get(var) or "").strip()]
        if missing:
            raise MissingSettings(missing)
        values = {
            key.lower(): value
            for key, value in source.items()
            if key.lower() in cls.model_fields and value.strip()
        }
        return cls(**values)
