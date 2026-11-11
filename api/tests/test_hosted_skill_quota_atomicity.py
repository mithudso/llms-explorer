"""Daily model allowances are reserved before provider work across both entrypoints."""
import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.requests import Request

from explorer_api import gateway, models as m, plans
from explorer_api.routes import contribute, skills


async def test_two_inflight_skill_requests_cannot_share_last_daily_slot(engine, monkeypatch):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as seed:
        user = m.User(email="quota@example.test", plan_id="free",
                      anthropic_api_key_ciphertext="test-ciphertext")
        seed.add(user)
        await seed.flush()
        limit = plans.get("free").quota("lint_per_day")
        seed.add_all(m.Job(user_id=user.id, kind="notes", status="done")
                     for _ in range(limit - 1))
        await seed.commit()
        user_id = user.id

    async def identity(_request, session, _authorization):
        return await session.get(m.User, user_id), True, None

    monkeypatch.setattr(skills.auth_routes, "resolve_identity_from_session_or_key", identity)
    entered = asyncio.Event()
    second_entered = asyncio.Event()
    release = asyncio.Event()

    class Provider:
        calls = 0

        async def complete(self, **_kwargs):
            self.calls += 1
            entered.set()
            if self.calls == 2:
                second_entered.set()
            await release.wait()
            return skills.Completion("result", 1, 1)

    provider = Provider()
    request = Request({"type": "http", "headers": [(b"x-requested-with", b"XMLHttpRequest")]})

    async def run():
        async with factory() as session:
            return await skills.run_skill(
                "notes-to-llms", skills.RunRequest(input="notes"), request, session,
                lambda _user: provider, None,
            )

    first = asyncio.create_task(run())
    second = None
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        second = asyncio.create_task(run())
        reached_provider = asyncio.create_task(second_entered.wait())
        try:
            done, _ = await asyncio.wait({second, reached_provider}, timeout=5,
                                         return_when=asyncio.FIRST_COMPLETED)
            assert done, "second request must either refuse or reach the provider"
        finally:
            reached_provider.cancel()
            await asyncio.gather(reached_provider, return_exceptions=True)
    finally:
        release.set()
        results = await asyncio.gather(first, *([second] if second else []))
    assert provider.calls == 1
    statuses = sorted(getattr(result, "status_code", 200) for result in results)
    assert statuses == [200, gateway.QuotaExceeded.status_code]
    async with factory() as check:
        count = (await check.execute(select(func.count()).select_from(m.Job).where(
            m.Job.user_id == user_id))).scalar_one()
    assert count == limit


async def test_failed_contribution_keeps_its_attempt_and_consumes_the_slot(
    session, tmp_path, monkeypatch,
):
    user = m.User(email="failed-contribution@example.test", plan_id="free",
                  anthropic_api_key_ciphertext="test-ciphertext")
    session.add(user)
    await session.flush()
    tree = tmp_path / "public-tree.json"
    tree.write_text("[]\n")
    monkeypatch.setattr(contribute.moderation, "public_tree_path", lambda: tree)

    class Provider:
        async def complete(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(skills, "get_llm_client_factory", lambda _request: lambda _user: Provider())
    app = SimpleNamespace(state=SimpleNamespace(settings=SimpleNamespace(stores_root=tmp_path)))
    request = Request({"type": "http", "app": app, "headers": []})
    with pytest.raises(gateway.GatewayRefusal):
        await contribute.contribute(contribute.ContributeRequest(concept="new", text="corpus"),
                                    request, session, user)
    rows = (await session.execute(select(m.Job).where(m.Job.user_id == user.id))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "failed"
    assert rows[0].started_at is not None
    assert rows[0].finished_at is not None


async def test_unpaired_surrogate_is_a_client_input_refusal():
    principal = gateway.Principal(user=m.User(anthropic_api_key_ciphertext="fake"))
    with pytest.raises(gateway.InvalidParams):
        await skills._check_plan(None, principal, "\ud800")
