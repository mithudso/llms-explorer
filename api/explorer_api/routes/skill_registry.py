"""Authenticated, immutable skill releases using the existing account boundary.

Local and hosted clients share the same bundle validator. Uploaded files are
data. This service never imports or executes a supplied skill or script.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from skill_registry.bundles import MAX_ARCHIVE_BYTES, validate_bundle

from ..db import get_session
from ..models import SkillRelease, SkillReleaseGrant, User
from .artifacts import _identity
from .auth import optional_user

log = logging.getLogger(__name__)
PREFIX = "/api/skill-registry"
Session = Annotated[AsyncSession, Depends(get_session)]
Viewer = Annotated[User | None, Depends(optional_user)]


class BoundedRoute(APIRoute):
    """Cap streamed bodies before FastAPI parses JSON, including chunked input."""

    body_limit_setting = "skill_registry_request_bytes"

    def maximum_body_bytes(self, request: Request) -> int:
        return getattr(request.app.state.settings, self.body_limit_setting)

    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            if request.method == "POST":
                maximum = self.maximum_body_bytes(request)
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > maximum:
                        raise HTTPException(413, "skill registry request is too large")
                    body.extend(chunk)
                request._body = bytes(body)
            return await original(request)

        return bounded


router = APIRouter(prefix=PREFIX, tags=["skill-registry"], route_class=BoundedRoute)


class PublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bundle_base64: str = Field(min_length=1, max_length=4 * ((MAX_ARCHIVE_BYTES + 2) // 3))
    # Public uploads require the platform's moderation adapter. Private and
    # explicitly granted team reads are the implemented first release.
    visibility: str = Field(default="private", pattern="^private$")


class GrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=100)


async def principal(request, session, viewer, scope, *, mutate=False):
    caller = await _identity(request, session, viewer)
    if caller is None:
        raise HTTPException(
            401,
            "present a skill registry account key or sign in",
            headers={"WWW-Authenticate": 'Bearer realm="skill-registry"'},
        )
    user_id, scopes = caller
    required = {scope} if isinstance(scope, str) else set(scope)
    missing = required - scopes
    if missing:
        raise HTTPException(403, "this key lacks required scopes: " + ", ".join(sorted(missing)))
    if (
        mutate
        and not request.headers.get("authorization", "").lower().startswith("bearer ")
        and request.headers.get("x-requested-with", "").lower() != "xmlhttprequest"
    ):
        raise HTTPException(403, "session writes require X-Requested-With: XMLHttpRequest")
    return user_id


def accessible(user_id):
    granted = exists().where(
        SkillReleaseGrant.release_id == SkillRelease.id, SkillReleaseGrant.user_id == user_id
    )
    return or_(SkillRelease.user_id == user_id, granted)


def describe(row):
    return {
        "id": row.id,
        "namespace": row.user_id,
        "name": row.name,
        "version": row.version,
        "description": row.description,
        "release_sha256": row.release_sha256,
        "visibility": "private",
        "size_bytes": row.size_bytes,
        "created_at": row.created_at.isoformat(),
        "manifest": row.manifest,
        "bundle_url": f"{PREFIX}/releases/{row.user_id}/{row.name}/{row.version}/bundle.zip",
    }


async def release(session, user_id, namespace, name, version, *, owned=False):
    statement = select(SkillRelease).where(
        SkillRelease.user_id == namespace,
        SkillRelease.name == name,
        SkillRelease.version == version,
        SkillRelease.user_id == user_id if owned else accessible(user_id),
    )
    row = await session.scalar(statement)
    if row is None:
        raise HTTPException(404, "no such skill release")
    return row


@router.post("/releases")
async def publish(body: PublishRequest, request: Request, session: Session, viewer: Viewer):
    owner = await principal(request, session, viewer, "publish", mutate=True)
    try:
        blob = base64.b64decode(body.bundle_base64, validate=True)
        if len(blob) > MAX_ARCHIVE_BYTES:
            raise ValueError("bundle exceeds hosted release limit")
        manifest, files = await asyncio.to_thread(validate_bundle, blob)
        entrypoint = files[manifest["entrypoint"]].decode("utf-8")
    except (ValueError, binascii.Error, OSError) as exc:
        log.info("skill_release_rejected error_type=%s", type(exc).__name__)
        raise HTTPException(422, "invalid or unsafe skill bundle") from exc
    if manifest["namespace"] != owner:
        raise HTTPException(403, "the bundle namespace must match its publishing account")
    # Serializes per-account quota checks and duplicate publication. No file/
    # database dual write: the bounded ZIP and metadata commit together.
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    prior = await session.scalar(
        select(SkillRelease).where(
            SkillRelease.user_id == owner,
            SkillRelease.name == manifest["name"],
            SkillRelease.version == manifest["version"],
        )
    )
    if prior is not None:
        if prior.release_sha256 != manifest["release_sha256"]:
            raise HTTPException(409, "skill release versions are immutable; publish a new version")
        return {**describe(prior), "created": False}
    used = (
        await session.execute(
            select(func.count(), func.coalesce(func.sum(SkillRelease.size_bytes), 0)).where(
                SkillRelease.user_id == owner
            )
        )
    ).one()
    settings = request.app.state.settings
    if (
        used[0] >= settings.skill_release_limit
        or used[1] + len(blob) > settings.skill_storage_limit_bytes
    ):
        raise HTTPException(413, "skill release storage limit reached")
    row = SkillRelease(
        user_id=owner,
        name=manifest["name"],
        version=manifest["version"],
        description=manifest["description"],
        release_sha256=manifest["release_sha256"],
        manifest=manifest,
        bundle=blob,
        size_bytes=len(blob),
        search_text=" ".join((manifest["name"], manifest["description"], entrypoint[:262144])),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    log.info("skill_release_published release_id=%s bytes=%s", row.id, len(blob))
    return {**describe(row), "created": True}


@router.get("/search")
async def search(
    request: Request,
    session: Session,
    viewer: Viewer,
    query: str = Query(min_length=1, max_length=1000),
    top: int = Query(default=10, ge=1, le=20),
):
    owner = await principal(request, session, viewer, "read")
    vector = func.to_tsvector("simple", SkillRelease.search_text)
    terms = func.plainto_tsquery("simple", query)
    rows = (
        await session.scalars(
            select(SkillRelease)
            .where(accessible(owner), vector.op("@@")(terms))
            .order_by(
                func.ts_rank(vector, terms).desc(), SkillRelease.created_at.desc(), SkillRelease.id
            )
            .limit(top)
        )
    ).all()
    return {"method": "postgres-lexical", "hits": [describe(r) for r in rows]}


@router.get("/releases/{namespace}/{name}/{version}")
async def get_release(
    namespace: str, name: str, version: str, request: Request, session: Session, viewer: Viewer
):
    owner = await principal(request, session, viewer, "read")
    return describe(await release(session, owner, namespace, name, version))


@router.get("/releases/{namespace}/{name}/{version}/bundle.zip")
async def download(
    namespace: str, name: str, version: str, request: Request, session: Session, viewer: Viewer
):
    owner = await principal(request, session, viewer, "read")
    row = await release(session, owner, namespace, name, version)
    return Response(
        row.bundle,
        media_type="application/zip",
        headers={
            "Cache-Control": "private, no-store",
            "Vary": "Authorization, Cookie",
            "X-Content-Type-Options": "nosniff",
            "ETag": f'"{row.release_sha256}"',
            "Content-Disposition": f'attachment; filename="{row.name}-{row.version}.zip"',
        },
    )


@router.post("/releases/{namespace}/{name}/{version}/grants")
async def grant(
    namespace: str,
    name: str,
    version: str,
    body: GrantRequest,
    request: Request,
    session: Session,
    viewer: Viewer,
):
    owner = await principal(request, session, viewer, "publish", mutate=True)
    row = await release(session, owner, namespace, name, version, owned=True)
    if await session.get(User, body.user_id) is None:
        raise HTTPException(404, "no such account")
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    prior = await session.scalar(
        select(SkillReleaseGrant).where(
            SkillReleaseGrant.release_id == row.id, SkillReleaseGrant.user_id == body.user_id
        )
    )
    if prior is None:
        session.add(SkillReleaseGrant(release_id=row.id, user_id=body.user_id))
        await session.commit()
    return {"release_id": row.id, "user_id": body.user_id, "access": "read"}


@router.delete("/releases/{namespace}/{name}/{version}/grants/{user_id}")
async def revoke_grant(
    namespace: str,
    name: str,
    version: str,
    user_id: str,
    request: Request,
    session: Session,
    viewer: Viewer,
):
    owner = await principal(request, session, viewer, "publish", mutate=True)
    row = await release(session, owner, namespace, name, version, owned=True)
    prior = await session.scalar(
        select(SkillReleaseGrant).where(
            SkillReleaseGrant.release_id == row.id, SkillReleaseGrant.user_id == user_id
        )
    )
    if prior is not None:
        await session.delete(prior)
        await session.commit()
    return Response(status_code=204)
