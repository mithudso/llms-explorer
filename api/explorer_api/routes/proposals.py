"""`/api/proposals` — submit a merge-back diff, read the queue, decide (05 §5).

Thin by design: this module shapes requests and maps
:class:`~explorer_api.moderation.ModerationError` onto status codes; every rule
about what a proposal *is* — the gate, the ladder, who may decide, how the
public tree is written — lives in `explorer_api.moderation`.

Three status choices are deliberate:

* **A failed lint gate is a 201, not a 4xx.** The proposal is a real record and
  the contributor is meant to read its verdict (05 §2); returning it with
  ``status: "rejected"`` and the findings attached is what makes the auto-
  rejection reviewable instead of a dead-end error.
* **Someone else's proposal is a 404, not a 403** — a 403 would confirm the id
  exists, which turns this surface into an enumeration oracle.
* **A stale sha is a 409 carrying the current sha**, so the client can rebase
  without a second round trip.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import moderation
from ..db import get_session
from ..models import User
from .auth import current_user

router = APIRouter(prefix="/api/proposals", tags=["proposals"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(current_user)]

MAX_ARTIFACTS = 20

#: Spelled numerically: Starlette renamed its constant and deprecated the old
#: name, and this service must lint clean on both spellings.
HTTP_422 = 422


class ProposalCreate(BaseModel):
    """`POST /api/proposals` body."""

    model_config = ConfigDict(extra="forbid")

    #: The public tree sha the diff was taken against (05 §4 / master §4).
    tree_sha: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    patch: dict[str, Any]
    #: The caller's own artifacts, linted before the proposal is queued.
    artifact_ids: list[str] = Field(default_factory=list, max_length=MAX_ARTIFACTS)
    summary: str | None = Field(default=None, max_length=moderation.MAX_SUMMARY_LEN)


class Decision(BaseModel):
    """The moderator's note, which becomes part of the record (05 §2)."""

    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=2000)


class ProposalPublic(BaseModel):
    """A proposal as its author and a moderator may see it."""

    id: str
    user_id: str
    tree_id: str | None
    tree_sha: str
    patch: dict[str, Any]
    summary: str | None
    status: str
    lint: dict[str, Any]
    moderator_user_id: str | None
    decided_at: dt.datetime | None
    created_at: dt.datetime


#: Every failure mode of the module, and the code it means over HTTP.
_STATUS_FOR: tuple[tuple[type[Exception], int], ...] = (
    (moderation.NotAModerator, status.HTTP_403_FORBIDDEN),
    (moderation.ProposalNotFound, status.HTTP_404_NOT_FOUND),
    (moderation.UnknownArtifact, status.HTTP_404_NOT_FOUND),
    (moderation.AlreadyDecided, status.HTTP_409_CONFLICT),
    (moderation.StaleTree, status.HTTP_409_CONFLICT),      # TreeMoved subclasses it
    (moderation.SteeringDetected, HTTP_422),
    (moderation.BrokenTree, HTTP_422),
    (moderation.InvalidPatch, HTTP_422),
)


def _http(exc: moderation.ModerationError) -> HTTPException:
    for kind, code in _STATUS_FOR:
        if isinstance(exc, kind):
            return HTTPException(status_code=code, detail=str(exc))
    # An unmapped ModerationError is an operator fault (a missing public tree),
    # not the caller's; 500 keeps it out of the client's error handling.
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
    )


@router.post(
    "",
    response_model=ProposalPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Propose a merge back into the public tree",
)
async def create_proposal(
    body: ProposalCreate, user: CurrentUser, session: SessionDep
) -> ProposalPublic:
    try:
        proposal, _ = await moderation.submit(
            session,
            user,
            tree_sha=body.tree_sha,
            patch=body.patch,
            artifact_ids=body.artifact_ids,
            summary=body.summary,
        )
    except moderation.ModerationError as exc:
        await session.rollback()
        raise _http(exc) from exc
    await session.commit()
    return ProposalPublic(**moderation.public_view(proposal))


@router.get("", response_model=list[ProposalPublic], summary="List proposals")
async def list_proposals(
    user: CurrentUser,
    session: SessionDep,
    scope: Literal["mine", "queue"] = "mine",
) -> list[ProposalPublic]:
    """``scope=mine`` (default) is the caller's own; ``scope=queue`` is the
    pending moderation queue and is moderator-only."""
    try:
        rows = (
            await moderation.queue(session, user)
            if scope == "queue"
            else await moderation.list_for_user(session, user)
        )
    except moderation.ModerationError as exc:
        raise _http(exc) from exc
    return [ProposalPublic(**moderation.public_view(row)) for row in rows]


@router.get("/{proposal_id}", response_model=ProposalPublic, summary="Read one proposal")
async def read_proposal(
    proposal_id: str, user: CurrentUser, session: SessionDep
) -> ProposalPublic:
    proposal = await moderation.get_for_user(session, user, proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no such proposal"
        )
    return ProposalPublic(**moderation.public_view(proposal))


async def _decide(
    *,
    accept: bool,
    proposal_id: str,
    body: Decision | None,
    user: User,
    session: AsyncSession,
) -> ProposalPublic:
    try:
        proposal = await moderation.decide(
            session,
            user,
            proposal_id,
            accept=accept,
            note=(body.note if body else None),
        )
    except moderation.ModerationError as exc:
        await session.rollback()
        raise _http(exc) from exc
    await session.commit()
    return ProposalPublic(**moderation.public_view(proposal))


@router.post(
    "/{proposal_id}/accept",
    response_model=ProposalPublic,
    summary="Accept a proposal and merge it into the public tree",
)
async def accept_proposal(
    proposal_id: str,
    user: CurrentUser,
    session: SessionDep,
    body: Decision | None = None,
) -> ProposalPublic:
    return await _decide(accept=True, proposal_id=proposal_id, body=body,
                         user=user, session=session)


@router.post(
    "/{proposal_id}/reject",
    response_model=ProposalPublic,
    summary="Reject a proposal, with the reason kept on the record",
)
async def reject_proposal(
    proposal_id: str,
    user: CurrentUser,
    session: SessionDep,
    body: Decision | None = None,
) -> ProposalPublic:
    return await _decide(accept=False, proposal_id=proposal_id, body=body,
                         user=user, session=session)


__all__ = ["Decision", "ProposalCreate", "ProposalPublic", "router"]
