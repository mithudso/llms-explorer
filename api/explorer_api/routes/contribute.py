"""`POST /api/contribute` — community contribution to the concept tree (component 05 §2.2.B).

One endpoint, one atomic server-side flow, session-cookie authenticated:
1. Validate: signed in, concept (1–200 chars), text (≤4000 chars), concept not in tree
2. Run the bounded concept-abstract-mini skill
3. Persist output as an artifact
4. Build and submit the merge-back proposal via moderation

A failure at skill invocation (provider error) or lint rejection is the only
two branches the client needs to distinguish; everything else is the existing
`gw.GatewayRefusal` → structured-error path.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import artifacts, gateway as gw, moderation
from ..db import get_session
from ..models import Artifact
from ..routes.auth import CurrentUser
from . import skills

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass

router = APIRouter(prefix="/api", tags=["contribute"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# --- request and response ----


class ContributeRequest(BaseModel):
    """Request body for `POST /api/contribute`."""

    model_config = ConfigDict(extra="forbid")

    concept: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=skills.MAX_INPUT_CHARS)
    parent: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=200)


class ContributeResponse(BaseModel):
    """Response from a successful `POST /api/contribute`."""

    proposal: dict[str, Any]
    pass_output: str


# --- slugification ----------------------------------------------------------


def _slugify(concept: str) -> str:
    """Convert a concept name to a valid artifact slug.

    Slugs must match `SAFE_RE`: one leading alphanumeric, then up to 200 more
    of alphanumeric, dot, underscore or dash.
    """
    # Lowercase, replace spaces and non-safe characters with dashes
    slug = concept.lower()
    slug = re.sub(r"[^a-z0-9._-]", "-", slug)
    # Collapse multiple dashes
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing dashes
    slug = slug.strip("-")
    # Ensure it's not empty and starts with alphanumeric
    if not slug or not slug[0].isalnum():
        slug = "concept-" + slug if slug else "concept"
    return slug[:200]


# --- the endpoint ----


@router.post("/contribute", summary="Contribute a new concept to the tree", status_code=201)
async def contribute(
    body: ContributeRequest,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> ContributeResponse:
    """Submit a new concept to the community tree.

    Validates the concept name, runs the abstract-mini skill, creates an artifact,
    and queues a proposal for moderation. On lint rejection (a real outcome, not
    an error), returns 201 with the findings attached to the proposal.
    """
    # --- 1. Validate input -----------------------------------------------

    concept = body.concept.strip()
    if not concept or len(concept) > 200:
        raise gw.InvalidParams("concept must be 1–200 characters")

    text = body.text.strip()
    if not text or len(text) > skills.MAX_INPUT_CHARS:
        raise gw.InvalidParams(
            f"text must be 1–{skills.MAX_INPUT_CHARS} characters"
        )

    parent = (body.parent or "").strip() if body.parent else None
    if parent and len(parent) > 200:
        raise gw.InvalidParams("parent must be at most 200 characters")

    # Check that concept is not already in the tree
    nodes, current_sha = moderation.read_tree(moderation.public_tree_path())
    index = {n.get("concept"): n for n in nodes if n.get("concept")}
    if concept in index:
        raise gw.InvalidParams(f"concept '{concept}' already exists in the tree")

    # Verify parent exists if supplied
    if parent and parent not in index:
        raise gw.InvalidParams(f"parent concept '{parent}' does not exist")

    # Check plan allows this operation (reuse skill's check)
    principal = gw.Principal(user=user, scopes=frozenset({"run"}))
    await skills._check_plan(session, principal, text)

    # --- 2. Run the skill ------------------------------------------------

    slug = _slugify(concept)
    llm_factory = skills.get_llm_client_factory(request)
    llm = llm_factory(user)

    skill_policy = skills.SKILL_POLICY["concept-abstract-mini"]
    run_request = skills.RunRequest(input=text, concept=concept)
    try:
        pass_output, in_tokens, out_tokens = await skills._run_passes(
            llm, skill_policy, run_request
        )
    except gw.GatewayRefusal:
        raise
    except Exception as exc:  # noqa: BLE001
        raise skills.LlmUnavailable("the model provider did not answer") from exc

    # Create a job record
    from ..models import Job
    job = Job(
        user_id=user.id,
        kind=skill_policy.job_kind,
        status="done",
        params={
            "skill": skill_policy.name,
            "passes": skill_policy.passes,
            "bounded": True,
        },
    )
    job.started_at = dt.datetime.now(dt.UTC)
    job.finished_at = dt.datetime.now(dt.UTC)
    job.cost_tokens = in_tokens + out_tokens
    session.add(job)
    await session.flush()

    # --- 3. Persist the artifact -----------------------------------------

    stores_root = request.app.state.settings.stores_root
    relative = "llms.txt"
    artifact_path = artifacts.write(stores_root, user.id, slug, relative, pass_output)

    # Create the artifact database row
    artifact = Artifact(
        owner_user_id=user.id,
        visibility="private",
        kind="concept-pack",
        slug=slug,
        path=str(artifact_path),
        manifest_json={},
        lint_summary_json={},
        job_id=job.id,
    )
    session.add(artifact)
    await session.flush()

    # --- 4. Build and submit the proposal --------------------------------

    # Count concepts mentioned in the output (rough heuristic)
    concepts_count = pass_output.count("##") if pass_output else 0

    patch = {
        "ops": [
            {
                "op": "add",
                "node": {
                    "concept": concept,
                    "parent": parent,
                    "slug": slug,
                    "llmsFile": f"/u/{user.id}/{slug}.llms/llms.txt",
                    "state": "researched",
                    "sourcesCount": 1,
                    "conceptsCount": concepts_count,
                    "researchedAt": dt.date.today().isoformat(),
                },
            }
        ]
    }

    summary = (body.summary or "").strip()
    if not summary:
        # Use first 200 chars of output as summary
        summary = (pass_output[:200] + "...") if len(pass_output) > 200 else pass_output

    proposal, lint_report = await moderation.submit(
        session,
        user,
        tree_sha=current_sha,
        patch=patch,
        artifact_ids=[artifact.id],
        summary=summary,
    )
    await session.commit()

    # --- 5. Return the response ------------------------------------------

    # Both passing and lint-rejected proposals return 201; only system errors are non-201.
    return ContributeResponse(
        proposal=moderation.public_view(proposal),
        pass_output=pass_output,
    )


__all__ = ["router"]
