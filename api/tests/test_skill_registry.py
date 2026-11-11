"""Real Postgres/account tests for immutable private skill distribution."""

from __future__ import annotations

import base64
import random

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from skill_registry.bundles import MAX_FILE_BYTES, MAX_TOTAL_BYTES, build_bundle, validate_bundle

from explorer_api import keys
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.models import SkillRelease, User
from explorer_api.routes.auth import optional_user
from explorer_api.settings import Settings

PREFIX = "/api/skill-registry"


@pytest_asyncio.fixture
async def registry(session, database_url, tmp_path):
    users = [User(email=f"skill-{label}@example.test") for label in ("owner", "reader", "other")]
    session.add_all(users)
    await session.flush()
    tokens = []
    for user in users:
        token, _ = await keys.create(session, user, ["read", "publish", "run"])
        tokens.append(token)
    read_token, _ = await keys.create(session, users[0], ["read"])
    publish_token, _ = await keys.create(session, users[0], ["publish"])
    await session.commit()
    settings = Settings(
        database_url=database_url,
        session_secret="synthetic-registry-session-secret-32",
        stripe_secret_key="sk_test_placeholder",
        stripe_webhook_secret="whsec_placeholder",
        stores_root=tmp_path / "stores",
    )
    app = create_app(settings)

    async def database():
        yield session

    app.dependency_overrides[get_session] = database
    app.dependency_overrides[optional_user] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api.test") as client:
        yield {
            "client": client,
            "users": users,
            "tokens": tokens,
            "app": app,
            "read": read_token,
            "publish": publish_token,
            "session": session,
            "root": tmp_path,
        }


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def package(state, *, version="1.0.0", body="Use exact source evidence.", namespace=None):
    root = state["root"] / ("skill-" + version)
    root.mkdir(exist_ok=True)
    (root / "SKILL.md").write_text(
        "---\nname: evidence-helper\ndescription: Find bounded research evidence\n---\n\n" + body
    )
    (root / "LICENSE").write_text("Synthetic test fixture license.\n")
    (root / "references").mkdir(exist_ok=True)
    (root / "references/notes.md").write_text("Preserve conditions and qualifiers.\n")
    return build_bundle(root, namespace or state["users"][0].id, "evidence-helper", version)


async def publish(state, blob):
    return await state["client"].post(
        PREFIX + "/releases",
        headers=auth(state["tokens"][0]),
        json={"bundle_base64": base64.b64encode(blob).decode()},
    )


@pytest.mark.asyncio
async def test_publish_replay_and_complete_bundle(registry):
    manifest, blob = package(registry)
    first = await publish(registry, blob)
    assert first.status_code == 200, first.text
    row = first.json()
    assert row["created"] is True and row["visibility"] == "private"
    assert row["manifest"] == manifest
    again = await publish(registry, blob)
    assert again.status_code == 200 and again.json()["created"] is False
    assert again.json()["id"] == row["id"]
    download = await registry["client"].get(row["bundle_url"], headers=auth(registry["tokens"][0]))
    assert download.status_code == 200 and download.content == blob
    decoded, files = validate_bundle(download.content)
    assert decoded == manifest and set(files) == {"SKILL.md", "LICENSE", "references/notes.md"}
    assert download.headers["cache-control"] == "private, no-store"
    assert download.headers["vary"] == "Authorization, Cookie"
    assert download.headers["etag"] == '"' + manifest["release_sha256"] + '"'


@pytest.mark.asyncio
async def test_existing_version_cannot_be_overwritten(registry):
    _, original = package(registry)
    assert (await publish(registry, original)).status_code == 200
    _, changed = package(registry, body="An edited instruction.")
    response = await publish(registry, changed)
    assert response.status_code == 409
    saved = await registry["session"].scalar(select(SkillRelease))
    assert saved.bundle == original


@pytest.mark.asyncio
async def test_database_itself_rejects_content_update(registry):
    _, blob = package(registry)
    await publish(registry, blob)
    with pytest.raises(DBAPIError, match="immutable"):
        await registry["session"].execute(
            update(SkillRelease).values(description="silently edited")
        )
    await registry["session"].rollback()


@pytest.mark.asyncio
async def test_team_grant_and_revoke_do_not_grant_publishing(registry):
    _, blob = package(registry)
    row = (await publish(registry, blob)).json()
    client = registry["client"]
    assert (await client.get(row["bundle_url"])).status_code == 401
    assert (
        await client.get(row["bundle_url"], headers=auth(registry["tokens"][1]))
    ).status_code == 404
    grants = row["bundle_url"].removesuffix("/bundle.zip") + "/grants"
    grant = await client.post(
        grants, headers=auth(registry["tokens"][0]), json={"user_id": registry["users"][1].id}
    )
    assert grant.status_code == 200
    assert (
        await client.get(row["bundle_url"], headers=auth(registry["tokens"][1]))
    ).content == blob
    denied = await client.post(
        grants, headers=auth(registry["tokens"][1]), json={"user_id": registry["users"][2].id}
    )
    assert denied.status_code == 404
    revoke = await client.delete(
        grants + "/" + registry["users"][1].id, headers=auth(registry["tokens"][0])
    )
    assert revoke.status_code == 204
    assert (
        await client.get(row["bundle_url"], headers=auth(registry["tokens"][1]))
    ).status_code == 404


@pytest.mark.asyncio
async def test_search_indexes_late_skill_text_and_filters_by_access(registry):
    _, blob = package(registry, body="Ordinary instruction.\n" * 300 + "late_architectural_token")
    await publish(registry, blob)
    client = registry["client"]
    result = await client.get(
        PREFIX + "/search",
        params={"query": "late_architectural_token"},
        headers=auth(registry["tokens"][0]),
    )
    assert result.status_code == 200, result.text
    assert len(result.json()["hits"]) == 1
    hidden = await client.get(
        PREFIX + "/search",
        params={"query": "late_architectural_token"},
        headers=auth(registry["tokens"][1]),
    )
    assert hidden.status_code == 200 and hidden.json()["hits"] == []


@pytest.mark.asyncio
async def test_scopes_owner_namespace_and_publication_boundary(registry):
    _, blob = package(registry)
    payload = {"bundle_base64": base64.b64encode(blob).decode()}
    client = registry["client"]
    assert (
        await client.post(PREFIX + "/releases", headers=auth(registry["read"]), json=payload)
    ).status_code == 403
    assert (
        await client.post(PREFIX + "/releases", headers=auth(registry["tokens"][1]), json=payload)
    ).status_code == 403
    assert (
        await client.post(
            PREFIX + "/releases",
            headers=auth(registry["tokens"][0]),
            json={**payload, "visibility": "public"},
        )
    ).status_code == 422
    assert (
        await client.get(
            PREFIX + "/search", params={"query": "evidence"}, headers=auth(registry["publish"])
        )
    ).status_code == 403


@pytest.mark.asyncio
async def test_bad_bundle_rejected_and_no_code_executes(registry):
    client = registry["client"]
    response = await client.post(
        PREFIX + "/releases",
        headers=auth(registry["tokens"][0]),
        json={"bundle_base64": "not-valid-base64!"},
    )
    assert response.status_code == 422
    marker = registry["root"] / "executed"
    _, blob = package(registry, body=f"Run python to create {marker}.")
    assert (await publish(registry, blob)).status_code == 200
    assert not marker.exists()


@pytest.mark.asyncio
async def test_stream_bound_and_quota(registry):
    app = registry["app"]
    app.state.settings = app.state.settings.model_copy(
        update={"skill_registry_request_bytes": 1024}
    )
    response = await registry["client"].post(
        PREFIX + "/releases", headers=auth(registry["tokens"][0]), content=b"x" * 1025
    )
    assert response.status_code == 413
    app.state.settings = app.state.settings.model_copy(
        update={"skill_registry_request_bytes": 7 * 1024 * 1024, "skill_release_limit": 1}
    )
    _, first = package(registry)
    assert (await publish(registry, first)).status_code == 200
    _, second = package(registry, version="1.0.1")
    assert (await publish(registry, second)).status_code == 413


def test_routes_mounted_in_real_factory(registry):
    paths = registry["app"].openapi()["paths"]
    assert PREFIX + "/releases" in paths and PREFIX + "/search" in paths


@pytest.mark.asyncio
async def test_private_metadata_search_and_errors_are_not_shared_cacheable(registry):
    _, blob = package(registry)
    row = (await publish(registry, blob)).json()
    client = registry["client"]
    metadata = row["bundle_url"].removesuffix("/bundle.zip")
    responses = [
        await client.get(metadata, headers=auth(registry["tokens"][0])),
        await client.get(
            PREFIX + "/search", params={"query": "evidence"}, headers=auth(registry["tokens"][0])
        ),
        await client.get(metadata),
        await client.get(metadata, headers=auth(registry["tokens"][1])),
    ]
    assert [r.status_code for r in responses] == [200, 200, 401, 404]
    for response in responses:
        assert response.headers["cache-control"] == "private, no-store"
        assert {"authorization", "cookie"} <= {
            value.strip().lower() for value in response.headers["vary"].split(",")
        }


@pytest.mark.asyncio
async def test_full_valid_resource_bundle_fits_hosted_format(registry):
    package(registry)
    root = registry["root"] / "skill-1.0.0"
    used = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    remaining = MAX_TOTAL_BYTES - used
    rng = random.Random(42)
    sequence = 0
    while remaining:
        size = min(remaining, MAX_FILE_BYTES)
        (root / f"asset-{sequence}.bin").write_bytes(rng.randbytes(size))
        remaining -= size
        sequence += 1
    manifest, blob = build_bundle(root, registry["users"][0].id, "evidence-helper", "1.0.0")
    assert sum(row["size"] for row in manifest["files"]) == MAX_TOTAL_BYTES
    assert len(blob) > MAX_TOTAL_BYTES  # ZIP metadata is part of the valid format.
    response = await publish(registry, blob)
    assert response.status_code == 200, response.text
    fetched = await registry["client"].get(
        response.json()["bundle_url"], headers=auth(registry["tokens"][0])
    )
    assert fetched.content == blob
