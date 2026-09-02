"""HTTP surfaces, one module per area, each exporting a ``router``.

Thin by design: a route reads the request, calls the module that owns the rule
(``auth``, ``keys``, ``ledger``, ``plans``, …) and shapes the response. No
threshold, no price and no policy is written here.

:func:`include_routers` is the single wiring point ``main.create_app`` calls, and
:data:`ROUTER_MODULES` is the whole list. Both exist because the app once shipped
with **one** of eight routers mounted: every other surface — the hosted MCP
gateway, keys, usage, the Stripe webhook, artifacts, trees, proposals — answered
404 in the running process while a green test suite mounted its own router and
proved nothing about the app that ships. ``tests/test_main.py`` now asserts the
mounted path set against the deployed factory, so a surface that is written but
not wired fails the build.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import artifacts as artifact_routes
from . import auth as auth_routes
from . import billing as billing_routes
from . import keys as keys_routes
from . import mcp as mcp_routes
from . import proposals as proposal_routes
from . import skills as skill_routes
from . import subscribers as subscriber_routes
from . import trees as tree_routes
from . import usage as usage_routes

if TYPE_CHECKING:  # pragma: no cover - typing only
    from fastapi import FastAPI

#: Every surface, in the order they are mounted. `artifacts` last: its route is
#: the catch-all `/u/{user_id}/{artifact}/{relative:path}` and a greedy path
#: parameter must never shadow a more specific route.
ROUTER_MODULES = (
    auth_routes,
    keys_routes,
    usage_routes,
    billing_routes,
    mcp_routes,
    skill_routes,
    tree_routes,
    proposal_routes,
    subscriber_routes,
    artifact_routes,
)


def include_routers(app: FastAPI) -> None:
    """Register every surface on ``app``."""
    for module in ROUTER_MODULES:
        app.include_router(module.router)


__all__ = ["ROUTER_MODULES", "include_routers"]
