"""The FastAPI application factory.

Deliberately thin: it resolves settings (failing fast when the environment is
incomplete), exposes ``GET /health``, and leaves every real surface to the
route modules added by later tasks.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .db import create_engine, create_session_factory
from .routes import include_routers
from .settings import Settings

log = logging.getLogger("explorer_api")

#: The site links here when the API itself is what is broken (00-platform-design
#: §"if the tunnel or the API is down").
STATUS_PAGE = "https://llms-explorer.com/status/"

#: JSON-RPC application code for "the service is degraded". `/mcp` speaks
#: JSON-RPC, so even a 503 has to come back in an envelope a strict client parses.
RPC_UNAVAILABLE = -32005
RPC_INTERNAL = -32603


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app.

    ``settings`` is injectable so tests never depend on process environment
    ordering; with no argument the environment is read and a missing required
    variable raises :class:`~explorer_api.settings.MissingSettings` **here**,
    before a worker ever binds a port.
    """
    settings = settings or Settings.load()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # `create_engine` does not connect; the first query does. So a bad
        # DATABASE_URL surfaces on the first request, not as a boot crash that
        # takes /health down with it.
        app.state.engine = create_engine(settings)
        app.state.session_factory = create_session_factory(app.state.engine)
        try:
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(
        title="explorer-api",
        version=__version__,
        description="Accounts, metering, hosted MCP and governance for LLMS-Explorer.",
        lifespan=lifespan,
    )
    app.state.settings = settings

    # `Host` is an attacker-controlled header and several decisions used to be
    # read off it (the WebAuthn relying party, every absolute URL the app
    # builds). Restricting it here is what makes those safe to derive at all.
    app.add_middleware(TrustedHostMiddleware,
                       allowed_hosts=list(settings.allowed_hosts))
    # The site is a different origin and calls with `credentials: "include"`, so
    # without this every account page is blocked by the browser. An explicit
    # list, never `*` (invalid with credentials) and never a regex (which would
    # match `llms-explorer.com.evil.net`).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.site_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["authorization", "content-type", "accept"],
        max_age=600,
    )

    # Every surface lives in `routes/`; the package's explicit list is the only
    # place a new one has to be named.
    include_routers(app)

    @app.exception_handler(DBAPIError)
    async def _database_is_down(request: Request, exc: DBAPIError) -> JSONResponse:
        """A dead database is a 503 with a status page, never a bare 500.

        Without this an MCP client gets `Internal Server Error` as *plain text*,
        which is not a JSON-RPC envelope and which no monitor can distinguish
        from an application bug.
        """
        log.warning("database unavailable for %s %s", request.method,
                    request.url.path, exc_info=exc)
        return _unavailable(request, "the service is temporarily unavailable")

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        """Liveness only — deliberately touches nothing. See `/ready`."""
        # Never echo anything from the secret half of the settings.
        return {"status": "ok", "environment": settings.environment}

    @app.get("/ready", tags=["ops"])
    async def ready(request: Request) -> JSONResponse:
        """Readiness: the probe an external monitor should watch.

        `/health` answers 200 even with the database gone, which is exactly the
        outage nobody was paged for. This one runs `SELECT 1`.
        """
        try:
            factory = request.app.state.session_factory
            async with factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 - any failure is "not ready"
            log.warning("readiness probe failed", exc_info=exc)
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "database": "down",
                         "status_page": STATUS_PAGE},
            )
        return JSONResponse({"status": "ready", "environment": settings.environment})

    return app


def _unavailable(request: Request, message: str) -> JSONResponse:
    """503 in whichever envelope the caller is speaking."""
    body: dict[str, object] = {"detail": message, "status_page": STATUS_PAGE}
    if request.url.path == "/mcp" or request.url.path.startswith("/api/mcp/"):
        body = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": RPC_UNAVAILABLE, "message": message,
                      "data": {"code": "unavailable", "status_page": STATUS_PAGE}},
        }
    return JSONResponse(status_code=503, content=body)


def __getattr__(name: str) -> FastAPI:
    """Let ``uvicorn explorer_api.main:app`` work without importing at module load.

    Building the app at import time would raise ``MissingSettings`` during
    collection in any tool that merely imports this module (pytest, ruff's
    plugins, a docs build). Resolving it lazily keeps the fail-fast behaviour
    exactly where it belongs: at process start.
    """
    if name == "app":
        return create_app()
    raise AttributeError(name)
