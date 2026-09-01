"""`/api/tree` and `/api/trees/…` — the public tree, and a private fork of it.

Thin by design: the shape of a request and the choice of status code live here;
every rule about what a fork *is* lives in `explorer_api.trees`, and the
allowance it spends is `explorer_api.ledger.check_quota`. No tier number is
written in this file.

Status-code contract, because two of these are security decisions:

* ``402`` — the plan's private-tree allowance is spent. The body is 15 §5's
  structured refusal (`code`, `tier`, `limit`, `remaining`, `upgrade_url`), so
  the client can say what to buy instead of guessing.
* ``404`` — no such tree *for you*. Someone else's tree answers identically to
  one that does not exist, so `/api/trees/<slug>/validate` cannot be used to
  find out which slugs other accounts have forked.
* ``409`` — that slug is already forked. Re-forking would silently overwrite
  the edits already in the private copy, so it is refused rather than applied.
* ``422`` — a slug that is not a safe path component. Rejected before it can
  reach the filesystem.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models as m, trees
from ..db import get_session
from ..settings import Settings
from .auth import current_user, optional_user

router = APIRouter(prefix="/api", tags=["trees"])

CurrentUser = Annotated[m.User, Depends(current_user)]
OptionalUser = Annotated[m.User | None, Depends(optional_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(_settings)]


class ForkRequest(BaseModel):
    """`POST /api/trees/fork` body. Everything optional: the common case is
    "give me my tree"."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(default=trees.DEFAULT_SLUG)


class TreePublic(BaseModel):
    """A private tree's listing row — never its contents."""

    id: str
    slug: str
    forked_from_sha: str
    path: str
    created_at: dt.datetime
    updated_at: dt.datetime
    node_count: int


class TreeContent(BaseModel):
    """`GET /api/tree` — the nodes, plus what they were forked from."""

    tree: str
    sha: str
    forked_from_sha: str | None = None
    slug: str | None = None
    node_count: int
    nodes: list[dict[str, Any]]


class ValidationOut(BaseModel):
    slug: str
    ok: bool
    node_count: int
    problems: list[str]
    #: Findings about this machine rather than the tree (a node naming a skill
    #: that is not installed here). Reported, never fatal.
    warnings: list[str]


def _quota_error(exc: trees.QuotaExceeded) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=exc.verdict.as_error(),
    )


def _no_such_tree(slug: str) -> HTTPException:
    # Same answer for "not yours" and "does not exist" — anything else is an
    # enumeration oracle over other accounts' slugs.
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail=f"no tree {slug!r}")


@router.post(
    "/trees/fork",
    response_model=TreePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Fork the public concept tree into this account",
)
async def fork_tree(
    body: ForkRequest,
    user: CurrentUser,
    session: DbSession,
    settings: SettingsDep,
) -> TreePublic:
    try:
        row = await trees.fork(session, user, settings=settings, slug=body.slug)
    except trees.InvalidSlug as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except trees.TreeExists as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except trees.QuotaExceeded as exc:
        raise _quota_error(exc) from exc
    await session.commit()
    return TreePublic(
        **trees.public_view(row, node_count=len(trees.load_nodes(settings, row)))
    )


@router.get(
    "/tree",
    response_model=TreeContent,
    summary="The public concept tree, or this account's fork of it",
)
async def read_tree(
    session: DbSession,
    settings: SettingsDep,
    user: OptionalUser = None,
    tree: Literal["public", "me"] = trees.PUBLIC,
    slug: str = trees.DEFAULT_SLUG,
) -> TreeContent:
    if tree == trees.PUBLIC:
        path = trees.public_tree_path()
        nodes = trees.read_nodes(path)
        return TreeContent(tree=trees.PUBLIC, sha=trees.sha_of(path),
                           node_count=len(nodes), nodes=nodes)

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sign in first",
                            headers={"WWW-Authenticate": "Session"})
    row = await trees.get(session, user, slug)
    if row is None:
        raise _no_such_tree(slug)
    try:
        nodes = trees.load_nodes(settings, row)
    except trees.TreeNotFound as exc:
        # The row exists but the file does not — a restore that missed the
        # store. Still a 404 to the caller; there is nothing to read.
        raise _no_such_tree(slug) from exc
    return TreeContent(
        tree=trees.MINE,
        slug=row.slug,
        sha=trees.sha_of(trees.resolve_path(settings, row)),
        forked_from_sha=row.forked_from_sha,
        node_count=len(nodes),
        nodes=nodes,
    )


@router.post(
    "/trees/{slug}/validate",
    response_model=ValidationOut,
    summary="Run the hub's concept-tree validator over this account's fork",
)
async def validate_tree(
    slug: str,
    user: CurrentUser,
    session: DbSession,
    settings: SettingsDep,
) -> ValidationOut:
    row = await trees.get(session, user, slug)
    if row is None:
        raise _no_such_tree(slug)
    try:
        report = trees.validate(settings, row)
    except trees.TreeNotFound as exc:
        raise _no_such_tree(slug) from exc
    return ValidationOut(slug=row.slug, **report.as_dict())


__all__ = ["ForkRequest", "TreeContent", "TreePublic", "ValidationOut", "router"]
