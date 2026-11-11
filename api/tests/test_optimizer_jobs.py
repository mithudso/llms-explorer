"""Actual Postgres/account/lease tests for the generic owner-local worker broker."""

from __future__ import annotations

import base64
import datetime as dt
import random

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from skill_registry.bundles import build_bundle

from explorer_api import keys
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.models import Job, JobEvent, SkillRelease, User
from explorer_api.routes.auth import optional_user
from explorer_api.settings import Settings


@pytest_asyncio.fixture
async def broker(session, database_url, tmp_path):
    users = [User(email=f"optimizer-{name}@example.test") for name in ("owner", "other")]
    session.add_all(users)
    await session.flush()
    tokens = [(await keys.create(session, user, ["read", "run", "publish"]))[0] for user in users]
    readonly = (await keys.create(session, users[0], ["read"]))[0]
    await session.commit()
    settings = Settings(
        database_url=database_url,
        session_secret="synthetic-broker-session-secret-32",
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
            "readonly": readonly,
            "session": session,
            "app": app,
            "root": tmp_path,
        }


def auth(token):
    return {"Authorization": "Bearer " + token}


async def create(state, **values):
    return await state["client"].post(
        "/api/jobs",
        headers=auth(state["tokens"][0]),
        json={"artifact_type": "document", "input_text": "A useful draft.", **values},
    )


async def claim(state, job_id, **values):
    return await state["client"].post(
        f"/api/jobs/{job_id}/claim",
        headers=auth(state["tokens"][0]),
        json={"worker": "owner-local-worker", **values},
    )


@pytest.mark.asyncio
async def test_create_idempotency_private_status_and_no_execution(broker):
    response = await create(broker)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] and body["status"] == "queued"
    assert not body["published"]
    assert "input_snapshot" not in body and "lease_token" not in body
    again = await create(broker)
    assert again.json()["id"] == body["id"] and not again.json()["created"]
    assert await broker["session"].scalar(select(func.count()).select_from(Job)) == 1
    status = await broker["client"].get("/api/jobs/" + body["id"], headers=auth(broker["readonly"]))
    assert status.status_code == 200
    assert status.json()["result"] is None


@pytest.mark.asyncio
async def test_account_and_scope_boundaries_are_non_enumerating(broker):
    created = (await create(broker)).json()
    other = auth(broker["tokens"][1])
    client = broker["client"]
    assert (await client.get("/api/jobs/" + created["id"], headers=other)).status_code == 404
    assert (await client.get("/api/jobs/absent", headers=other)).status_code == 404
    assert (
        await client.post(
            "/api/jobs/" + created["id"] + "/claim", headers=other, json={"worker": "other"}
        )
    ).status_code == 404
    assert (
        await client.post(
            "/api/jobs",
            headers=auth(broker["readonly"]),
            json={"artifact_type": "query", "input_text": "SELECT 1"},
        )
    ).status_code == 403
    assert (await client.get("/api/jobs/" + created["id"])).status_code == 401


@pytest.mark.asyncio
async def test_actual_lease_and_completion_keep_claims_separate(broker):
    created = (await create(broker)).json()
    response = await claim(broker, created["id"])
    assert response.status_code == 200, response.text
    leased = response.json()
    assert leased["input_snapshot"] == {"format": "text/v1", "text": "A useful draft."}
    assert len(leased["lease_token"]) >= 32
    assert (await claim(broker, created["id"])).status_code == 409
    completed = await broker["client"].post(
        f"/api/jobs/{created['id']}/complete",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "input_sha256": created["input_sha256"],
            "exit_code": 0,
            "candidate_text": "A precise revised draft.",
            "checks": [{"name": "native-eval", "exit_code": 0}],
            "convergence_status": "CLEAN",
        },
    )
    assert completed.status_code == 200, completed.text
    result = completed.json()["result"]
    assert completed.json()["status"] == "done"
    assert result["changed"] and result["server_checks_passed"]
    assert result["worker_checks_reported_passed"]
    assert result["reported_convergence"] == "CLEAN"
    assert not result["converged"] and not result["execution_independently_verified"]
    assert not result["published"]
    assert await broker["session"].scalar(select(func.count()).select_from(SkillRelease)) == 0
    row = await broker["session"].get(Job, created["id"])
    assert row.params["lease_token_hash"] is None
    assert await broker["session"].scalar(select(func.count()).select_from(JobEvent)) == 3


@pytest.mark.asyncio
async def test_wrong_worker_token_and_input_cannot_complete(broker):
    created = (await create(broker)).json()
    leased = (await claim(broker, created["id"])).json()
    valid = {
        "worker": "owner-local-worker",
        "lease_token": leased["lease_token"],
        "input_sha256": created["input_sha256"],
        "exit_code": 0,
        "candidate_text": "Changed.",
    }
    for bad in ({"worker": "another"}, {"lease_token": "x" * 43}, {"input_sha256": "0" * 64}):
        response = await broker["client"].post(
            f"/api/jobs/{created['id']}/complete",
            headers=auth(broker["tokens"][0]),
            json={**valid, **bad},
        )
        assert response.status_code == 409
    status = await broker["client"].get(
        f"/api/jobs/{created['id']}", headers=auth(broker["tokens"][0])
    )
    assert status.json()["status"] == "running"


@pytest.mark.asyncio
async def test_heartbeat_cannot_extend_absolute_deadline(broker):
    created = (await create(broker, timeout_seconds=10)).json()
    leased = (await claim(broker, created["id"], lease_seconds=2)).json()
    response = await broker["client"].post(
        f"/api/jobs/{created['id']}/heartbeat",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "lease_seconds": 3600,
        },
    )
    assert response.status_code == 200
    row = await broker["session"].get(Job, created["id"])
    assert row.lease_expires <= row.started_at + dt.timedelta(seconds=10)


@pytest.mark.asyncio
async def test_expired_execution_is_held_not_automatically_replayed(broker):
    created = (await create(broker)).json()
    await claim(broker, created["id"])
    row = await broker["session"].get(Job, created["id"])
    row.lease_expires = dt.datetime.now(dt.UTC) - dt.timedelta(seconds=1)
    await broker["session"].commit()
    assert (await claim(broker, created["id"])).status_code == 409
    await broker["session"].refresh(row)
    assert row.status == "held" and row.params["lease_token_hash"] is None
    assert row.attempts == 1


@pytest.mark.asyncio
async def test_cancel_revokes_worker_lease(broker):
    created = (await create(broker)).json()
    leased = (await claim(broker, created["id"])).json()
    response = await broker["client"].post(
        f"/api/jobs/{created['id']}/cancel", headers=auth(broker["tokens"][0])
    )
    assert response.status_code == 200 and response.json()["status"] == "cancelled"
    done = await broker["client"].post(
        f"/api/jobs/{created['id']}/complete",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "input_sha256": created["input_sha256"],
            "exit_code": 1,
        },
    )
    assert done.status_code == 409


@pytest.mark.asyncio
async def test_job_quota_and_streamed_body_bound(broker):
    settings = broker["app"].state.settings
    settings = settings.model_copy(update={"optimizer_max_active_jobs": 1})
    broker["app"].state.settings = settings
    assert (await create(broker)).status_code == 200
    assert (await create(broker, input_text="Another input.")).status_code == 429
    broker["app"].state.settings = settings.model_copy(update={"optimizer_job_request_bytes": 50})

    async def chunks():
        yield b'{"artifact_type":"document","input_text":"'
        yield b"x" * 100
        yield b'"}'

    response = await broker["client"].post(
        "/api/jobs", headers=auth(broker["tokens"][0]), content=chunks()
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_release_job_keeps_complete_tree_and_never_changes_release(broker):
    root = broker["root"] / "skill"
    root.mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: example\ndescription: Review evidence\n---\nOriginal instructions.\n"
    )
    (root / "references").mkdir()
    (root / "references/conditions.md").write_text("Original condition.")
    owner = broker["users"][0].id
    manifest, blob = build_bundle(root, owner, "example", "1.0.0")
    response = await broker["client"].post(
        "/api/skill-registry/releases",
        headers=auth(broker["tokens"][0]),
        json={"bundle_base64": base64.b64encode(blob).decode()},
    )
    assert response.status_code == 200, response.text
    reference = {
        "namespace": owner,
        "name": "example",
        "version": "1.0.0",
        "release_sha256": manifest["release_sha256"],
    }
    created_response = await create(
        broker, artifact_type="skill", input_text=None, release_ref=reference
    )
    assert created_response.status_code == 200, created_response.text
    created = created_response.json()
    leased = (await claim(broker, created["id"])).json()
    assert leased["input_snapshot"]["bundle_base64"] == base64.b64encode(blob).decode()
    (root / "references/conditions.md").write_text("Revised condition.")
    _, changed = build_bundle(root, owner, "example", "1.0.0")
    completed = await broker["client"].post(
        f"/api/jobs/{created['id']}/complete",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "input_sha256": created["input_sha256"],
            "exit_code": 0,
            "candidate_bundle_base64": base64.b64encode(changed).decode(),
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["result"]["changed"]
    source = await broker["session"].scalar(select(SkillRelease))
    assert source.bundle == blob and source.release_sha256 == manifest["release_sha256"]


@pytest.mark.asyncio
async def test_legacy_jobs_are_not_claimed_by_new_adapter(broker):
    legacy = Job(
        user_id=broker["users"][0].id, kind="optimize", status="queued", params={"legacy": True}
    )
    broker["session"].add(legacy)
    await broker["session"].commit()
    assert (await claim(broker, legacy.id)).status_code == 404
    await broker["session"].refresh(legacy)
    assert legacy.status == "queued" and legacy.params == {"legacy": True}


@pytest.mark.asyncio
async def test_shared_release_read_grant_does_not_authorize_optimization(broker):
    root = broker["root"] / "shared-skill"
    root.mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: example\ndescription: Example skill\n---\nRead original evidence.\n"
    )
    owner = broker["users"][0].id
    manifest, blob = build_bundle(root, owner, "example", "1.0.0")
    client = broker["client"]
    assert (
        await client.post(
            "/api/skill-registry/releases",
            headers=auth(broker["tokens"][0]),
            json={"bundle_base64": base64.b64encode(blob).decode()},
        )
    ).status_code == 200
    grant_path = f"/api/skill-registry/releases/{owner}/example/1.0.0/grants"
    assert (
        await client.post(
            grant_path, headers=auth(broker["tokens"][0]), json={"user_id": broker["users"][1].id}
        )
    ).status_code == 200
    response = await client.post(
        "/api/jobs",
        headers=auth(broker["tokens"][1]),
        json={
            "artifact_type": "skill",
            "release_ref": {
                "namespace": owner,
                "name": "example",
                "version": "1.0.0",
                "release_sha256": manifest["release_sha256"],
            },
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_cannot_choose_a_server_command_or_self_declare_verified_convergence(broker):
    response = await create(broker, worker_command=["untrusted-program"])
    assert response.status_code == 422

    assert await broker["session"].scalar(select(func.count()).select_from(Job)) == 0
    created = (await create(broker)).json()
    leased = (await claim(broker, created["id"])).json()
    response = await broker["client"].post(
        f"/api/jobs/{created['id']}/complete",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "input_sha256": created["input_sha256"],
            "exit_code": 0,
            "candidate_text": "Changed.",
            "converged": True,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_unicode_is_a_client_error_not_server_failure(broker):
    response = await broker["client"].post(
        "/api/jobs",
        headers={**auth(broker["tokens"][0]), "Content-Type": "application/json"},
        content=b'{"artifact_type":"document","input_text":"\\ud800"}',
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_only_key_cannot_read_or_create_input_returning_broker_calls(broker):
    token, _ = await keys.create(broker["session"], broker["users"][0], ["run"])
    await broker["session"].commit()
    created = (await create(broker)).json()
    response = await broker["client"].post(
        "/api/jobs",
        headers=auth(token),
        json={"artifact_type": "document", "input_text": "A useful draft."},
    )
    assert response.status_code == 403
    for action in ("claim", "cancel"):
        response = await broker["client"].post(
            f"/api/jobs/{created['id']}/{action}",
            headers=auth(token),
            json={"worker": "run-only"} if action == "claim" else None,
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_maximum_expanded_skill_bundle_can_complete_with_archive_overhead(broker):
    root = broker["root"] / "large-skill"
    root.mkdir()
    text = (
        b"---\nname: large\ndescription: Bounded large fixture\n---\nKeep all approved resources.\n"
    )
    (root / "SKILL.md").write_bytes(text)
    rng = random.Random(7)
    for index, size in enumerate((2 * 1024 * 1024, 2 * 1024 * 1024, 1024 * 1024 - len(text))):
        (root / f"asset-{index}.bin").write_bytes(rng.randbytes(size))
    owner = broker["users"][0].id
    manifest, blob = build_bundle(root, owner, "large", "1.0.0")
    assert len(blob) > 5 * 1024 * 1024
    assert (
        await broker["client"].post(
            "/api/skill-registry/releases",
            headers=auth(broker["tokens"][0]),
            json={"bundle_base64": base64.b64encode(blob).decode()},
        )
    ).status_code == 200
    created_response = await create(
        broker,
        artifact_type="skill",
        input_text=None,
        release_ref={
            "namespace": owner,
            "name": "large",
            "version": "1.0.0",
            "release_sha256": manifest["release_sha256"],
        },
    )
    assert created_response.status_code == 200
    created = created_response.json()
    leased = (await claim(broker, created["id"])).json()
    completed = await broker["client"].post(
        f"/api/jobs/{created['id']}/complete",
        headers=auth(broker["tokens"][0]),
        json={
            "worker": "owner-local-worker",
            "lease_token": leased["lease_token"],
            "input_sha256": created["input_sha256"],
            "exit_code": 0,
            "candidate_bundle_base64": base64.b64encode(blob).decode(),
        },
    )
    assert completed.status_code == 200, completed.text[:1000]
    assert completed.json()["status"] == "done"
