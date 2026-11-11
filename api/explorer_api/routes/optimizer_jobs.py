"""Create/lease/report generic optimization jobs; execute only on owner-local workers."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from skill_registry.bundles import MAX_ARCHIVE_BYTES

from .. import optimizer_jobs as broker
from .skill_registry import BoundedRoute, Session, Viewer, principal, release


class OptimizerRoute(BoundedRoute):
    body_limit_setting = "optimizer_job_request_bytes"

    def maximum_body_bytes(self, request):
        if request.url.path.endswith("/complete"):
            return request.app.state.settings.skill_registry_request_bytes
        return super().maximum_body_bytes(request)


router = APIRouter(prefix="/api/jobs", tags=["jobs"], route_class=OptimizerRoute)
SHA = "^[a-f0-9]{64}$"


class ReleaseRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    namespace: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=100)
    release_sha256: str = Field(pattern=SHA)


class CreateJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_type: Literal["skill", "code", "document", "query", "prompt", "agent"]
    input_text: str | None = Field(default=None, min_length=1, max_length=262144)
    release_ref: ReleaseRef | None = None
    input_sha256: str = Field(default="", pattern="^(?:[a-f0-9]{64})?$")
    timeout_seconds: int = Field(default=600, ge=1, le=3600)
    max_iterations: int = Field(default=3, ge=1, le=5)
    retry_of: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def one_input(self):
        if (self.input_text is None) == (self.release_ref is None):
            raise ValueError("supply exactly one input_text or release_ref")
        if self.release_ref and self.artifact_type != "skill":
            raise ValueError("release_ref is only for complete skill releases")
        return self


class ClaimJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    worker: str = Field(min_length=1, max_length=100)
    lease_seconds: int = Field(default=60, ge=1, le=3600)


class Heartbeat(ClaimJob):
    lease_token: str = Field(pattern="^[A-Za-z0-9_-]{32,200}$")


class ReportedCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    exit_code: int = Field(ge=-65535, le=65535)


class CompleteJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    worker: str = Field(min_length=1, max_length=100)
    lease_token: str = Field(pattern="^[A-Za-z0-9_-]{32,200}$")
    input_sha256: str = Field(pattern=SHA)
    exit_code: int = Field(ge=-65535, le=65535)
    candidate_text: str | None = Field(default=None, max_length=262144)
    candidate_bundle_base64: str | None = Field(
        default=None, max_length=4 * ((MAX_ARCHIVE_BYTES + 2) // 3)
    )
    checks: list[ReportedCheck] = Field(default_factory=list, max_length=20)
    convergence_status: str = Field(default="UNREPORTED", max_length=64)
    summary: str = Field(default="", max_length=8000)


def failure(error):
    return HTTPException(error.status, error.detail)


@router.post("")
async def create_job(body: CreateJob, request: Request, session: Session, viewer: Viewer):
    owner = await principal(request, session, viewer, ("read", "run"), mutate=True)
    source = None
    if body.release_ref:
        ref = body.release_ref
        source = await release(session, owner, ref.namespace, ref.name, ref.version, owned=True)
    try:
        row, created = await broker.create(
            session, owner, body.model_dump(), request.app.state.settings, source_release=source
        )
        await session.commit()
        return {**broker.describe(row), "created": created}
    except broker.BrokerError as exc:
        raise failure(exc) from exc


@router.get("/{job_id}")
async def status_job(job_id: str, request: Request, session: Session, viewer: Viewer):
    owner = await principal(request, session, viewer, "read")
    try:
        return broker.describe(await broker.get(session, owner, job_id))
    except broker.BrokerError as exc:
        raise failure(exc) from exc


@router.post("/{job_id}/claim")
async def claim_job(
    job_id: str, body: ClaimJob, request: Request, session: Session, viewer: Viewer
):
    owner = await principal(request, session, viewer, ("read", "run"), mutate=True)
    try:
        row = await broker.get(session, owner, job_id, lock=True)
        token = await broker.claim(session, row, body.worker, body.lease_seconds)
        await session.commit()
        if token is None:
            raise HTTPException(409, "worker lease expired; job held for explicit recovery")
        return broker.describe(row, include_input=True, lease_token=token)
    except broker.BrokerError as exc:
        raise failure(exc) from exc


@router.post("/{job_id}/heartbeat")
async def heartbeat_job(
    job_id: str, body: Heartbeat, request: Request, session: Session, viewer: Viewer
):
    owner = await principal(request, session, viewer, ("read", "run"), mutate=True)
    try:
        row = await broker.get(session, owner, job_id, lock=True)
        await broker.heartbeat(session, row, body.worker, body.lease_token, body.lease_seconds)
        await session.commit()
        return broker.describe(row)
    except broker.BrokerError as exc:
        raise failure(exc) from exc


@router.post("/{job_id}/complete")
async def complete_job(
    job_id: str, body: CompleteJob, request: Request, session: Session, viewer: Viewer
):
    owner = await principal(request, session, viewer, ("read", "run"), mutate=True)
    try:
        row = await broker.get(session, owner, job_id, lock=True)
        await broker.complete(session, row, body.model_dump(), request.app.state.settings)
        await session.commit()
        return broker.describe(row)
    except broker.BrokerError as exc:
        raise failure(exc) from exc


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request, session: Session, viewer: Viewer):
    owner = await principal(request, session, viewer, ("read", "run"), mutate=True)
    try:
        row = await broker.get(session, owner, job_id, lock=True)
        await broker.cancel(session, row)
        await session.commit()
        return broker.describe(row)
    except broker.BrokerError as exc:
        raise failure(exc) from exc
