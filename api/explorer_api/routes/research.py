"""`/api/research` — start a research run for a concept from the `/tree/` page.

Thin by design: who may start a run and which concept is fair game are
checked here; the run itself lives in :mod:`explorer_api.research`.

* **Only moderators start runs.** A run spends model and web-search budget on
  the owner's machine, and the button sits on a public page. A signed-in
  non-moderator gets a 403; a signed-out visitor gets the usual 401.
* **Cookie POSTs need `X-Requested-With: XMLHttpRequest`**, the same CSRF
  guard `routes/skills.py` uses: a cross-site form cannot set the header.
* **The concept must be one the public tree names**, and the prompt carries the
  tree's spelling, never the caller's.
* **One run per concept, at most** :data:`~explorer_api.research.MAX_RUNNING`
  **at once.** A second click returns the run already going.
* **A concept already checked out by another run is refused** (409): see
  :mod:`explorer_api.checkouts` for what holds a concept.
* **Reading a run's status is public and read-only**: the panel shows
  "research in progress" to everyone, and the view holds no user, path or log.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import checkouts, gateway as gw, models as m, moderation, research
from ..db import get_session
from .auth import CurrentUser

router = APIRouter(prefix="/api/research", tags=["research"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept: str = Field(min_length=1, max_length=research.SAFE_NAME_MAX)


def _known(concept: str) -> tuple[str, str | None]:
    nodes, _sha = moderation.read_tree(moderation.public_tree_path())
    found = research.find_concept(nodes, concept)
    if found is None:
        raise gw.InvalidParams("that concept is not in the public tree")
    name, parent = found
    if not research.safe_name(name) or (parent is not None and not research.safe_name(parent)):
        raise gw.InvalidParams("that concept name cannot be researched automatically")
    return name, parent


@router.post("", status_code=202, summary="Start a research run for a concept")
async def start(body: ResearchRequest, request: Request, user: CurrentUser,
                session: SessionDep) -> dict[str, Any]:
    if request.headers.get("x-requested-with", "").lower() != "xmlhttprequest":
        raise gw.Forbidden("research runs require X-Requested-With: XMLHttpRequest")
    if not moderation.is_moderator(user):
        raise gw.Forbidden("only a moderator can start a research run")
    concept, parent = _known(body.concept)
    holder = checkouts.held_by(concept)
    if holder:
        raise gw.Conflict(f"already being researched by {holder}")

    # Check-and-insert under one advisory lock, so two clicks cannot both see
    # "no run" and both launch, nor push past MAX_RUNNING together.
    await research.lock(session)
    await research.expire_stale(session)
    current = await research.latest_for(session, concept)
    if current is not None and current.status in research.ACTIVE:
        await session.commit()
        return research.public_view(current)
    if await research.active_count(session) >= research.MAX_RUNNING:
        await session.commit()
        raise gw.RateLimited(
            f"{research.MAX_RUNNING} research runs are already going; try again when one finishes",
            retry_after=600)

    binary = research.claude_binary()
    if binary is None:
        raise gw.HubUnavailable("the research runner is not installed on this server")

    job = m.Job(user_id=user.id, kind="research", status="queued",
                params={"concept": concept, "parent": parent, "mode": "dr", "source": "tree",
                        "boot": research.BOOT})
    session.add(job)
    await session.commit()
    await session.refresh(job)

    launcher: research.Launcher = getattr(request.app.state, "research_launcher", research.launch)
    launcher(request.app.state.session_factory, job.id,
             research.research_argv(concept, parent, binary))
    return research.public_view(job)


@router.get("", summary="The latest research run for a concept")
async def status(concept: str, session: SessionDep) -> dict[str, Any]:
    # Read-only: public_view reports an orphaned run as failed without a write.
    if not research.safe_name(concept):
        raise gw.InvalidParams("invalid concept name")
    job = await research.latest_for(session, concept.strip())
    view = research.public_view(job) if job else None
    holder = checkouts.held_by(concept)
    if holder is None and view and view["status"] in research.ACTIVE:
        holder = "a website research run"
    return {"run": view, "checked_out": holder}


@router.get("/queue", summary="Everything being researched now, and what is queued")
async def queue(session: SessionDep) -> dict[str, Any]:
    """The monitor behind /queue/ and the llmsx explorer queue screen.

    Public and read-only, like `status`: concept names are already public in
    the tree, and no path, user or log leaves the server.
    """
    runs, _held = checkouts.snapshot()
    jobs = await research.recent(session, limit=20)
    return {
        "generated_at": checkouts.now_iso(),
        "runs": [{**r, "pending_count": len(r["pending"]), "pending": r["pending"][:12]}
                 for r in runs],
        "website": [research.public_view(j) for j in jobs],
        "queue": checkouts.research_queue(research.repo_root()),
    }


__all__ = ["router"]
