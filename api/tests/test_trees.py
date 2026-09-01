# api/tests/test_trees.py
"""Private tree forks (plan Task 9).

The plan's four checks come first — fork records the source sha, a second fork
past the plan's quota is a 402 that says what to buy, `?tree=me` diverges from
`?tree=public` once the private copy is edited, and `validate` reports a
dangling parent.

The rest are written from the attacker's side, because a tree is a *file* on
the box and the two ways that goes wrong are both here:

* a slug that escapes ``stores_root`` (``../..``) would let a signed-in user
  name any path on the machine,
* another user's tree must be neither readable nor forkable-over, and a
  re-fork must never silently overwrite the edits already in a private tree.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from explorer_api import models as m, trees
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes import auth as auth_routes
from explorer_api.routes.trees import router as trees_router
from explorer_api.settings import Settings


async def _user(session, plan_id: str = "free") -> m.User:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", plan_id=plan_id)
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest.fixture
def settings(database_url: str, tmp_path: Path) -> Settings:
    return Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
            "STORES_ROOT": str(tmp_path / "stores"),
        }
    )


def _client_for(settings: Settings, session, user: m.User | None) -> AsyncClient:
    """The trees router on the real app, signed in as ``user`` (or nobody).

    ``get_session`` is pinned to the test's own session so an assertion made
    straight afterwards sees the rows the route wrote. Identity is Task 3's
    cookie dependency, overridden rather than forged, so the route keeps using
    the real one in production.
    """
    app = create_app(settings)
    # Wiring the router into `main.create_app` belongs to the task that owns
    # `main.py`; mounting it here keeps this task to its three files.
    app.include_router(trees_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    if user is None:

        async def _anonymous():
            from fastapi import HTTPException

            raise HTTPException(401, "sign in first")

        app.dependency_overrides[auth_routes.current_user] = _anonymous
        app.dependency_overrides[auth_routes.optional_user] = lambda: None
    else:
        app.dependency_overrides[auth_routes.current_user] = lambda: user
        app.dependency_overrides[auth_routes.optional_user] = lambda: user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture
async def client(settings, session, user) -> AsyncIterator[AsyncClient]:
    async with _client_for(settings, session, user) as http:
        yield http


@pytest_asyncio.fixture
async def anonymous(settings, session) -> AsyncIterator[AsyncClient]:
    async with _client_for(settings, session, None) as http:
        yield http


async def _tree_row(session, user: m.User, slug: str = "me") -> m.Tree:
    return (
        await session.execute(
            select(m.Tree).where(m.Tree.user_id == user.id, m.Tree.slug == slug)
        )
    ).scalar_one()


# --- the plan's four checks --------------------------------------------------


async def test_fork_copies_the_public_tree_and_records_its_sha(client, session, user,
                                                               settings):
    r = await client.post("/api/trees/fork", json={})
    assert r.status_code == 201, r.text
    body = r.json()

    assert body["forked_from_sha"] == trees.public_sha()
    assert len(body["forked_from_sha"]) == 64          # sha256 of the file, not a guess

    row = await _tree_row(session, user)
    assert row.forked_from_sha == body["forked_from_sha"]
    # A file copy, not a patch model (master §4): the bytes are the public tree's.
    path = trees.resolve_path(settings, row)
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8")) == trees.public_nodes()
    assert body["node_count"] == len(trees.public_nodes())


async def test_a_second_fork_past_quota_is_402_with_an_upgrade_url(client):
    assert (await client.post("/api/trees/fork", json={})).status_code == 201
    r = await client.post("/api/trees/fork", json={"slug": "spare"})
    assert r.status_code == 402
    detail = r.json()["detail"]
    assert detail["feature"] == "private_trees" and detail["tier"] == "free"
    assert detail["limit"] == 1 and detail["remaining"] == 0
    assert "starter" in detail["upgrade_url"]           # free → 1, starter → 3 (15 §5)


async def test_me_diverges_from_public_once_the_private_copy_is_edited(
    client, session, user, settings
):
    await client.post("/api/trees/fork", json={})
    public = (await client.get("/api/tree", params={"tree": "public"})).json()
    assert (await client.get("/api/tree", params={"tree": "me"})).json()["nodes"] == \
        public["nodes"]

    row = await _tree_row(session, user)
    nodes = trees.load_nodes(settings, row)
    nodes.append({"concept": "My Private Concept", "parentConcept": None,
                  "childConcepts": []})
    trees.save_nodes(settings, row, nodes)

    mine = (await client.get("/api/tree", params={"tree": "me"})).json()
    assert mine["nodes"] != public["nodes"]
    assert len(mine["nodes"]) == len(public["nodes"]) + 1
    # The public tree is untouched by anything a user does to their fork.
    assert (await client.get("/api/tree", params={"tree": "public"})).json() == public


async def test_validate_reports_a_dangling_parent(client, session, user, settings):
    await client.post("/api/trees/fork", json={})
    assert (await client.post("/api/trees/me/validate")).json()["ok"] is True

    row = await _tree_row(session, user)
    nodes = trees.load_nodes(settings, row)
    nodes.append({"concept": "Orphan", "parentConcept": "No Such Parent",
                  "childConcepts": []})
    trees.save_nodes(settings, row, nodes)

    body = (await client.post("/api/trees/me/validate")).json()
    assert body["ok"] is False
    assert any("No Such Parent" in p for p in body["problems"])
    # Skill-link findings are environment-dependent (the skills are installed on
    # the box, not in CI), so they are reported separately and never fail a tree.
    assert not any("skillId" in p for p in body["problems"])


# --- the private copy stays private and stays put ----------------------------


async def test_a_slug_cannot_escape_the_stores_root(client):
    for slug in ("../../etc", "..", "a/b", "", "Me!", "x" * 65):
        r = await client.post("/api/trees/fork", json={"slug": slug})
        assert r.status_code == 422, f"{slug!r} was accepted"


async def test_a_fork_lands_under_the_stores_root_for_its_owner(client, session, user,
                                                                settings):
    await client.post("/api/trees/fork", json={})
    path = trees.resolve_path(settings, await _tree_row(session, user))
    assert settings.stores_root in path.parents
    assert user.id in path.parts                      # one directory per account


async def test_re_forking_the_same_slug_refuses_rather_than_overwriting(
    client, session, user, settings
):
    await client.post("/api/trees/fork", json={})
    row = await _tree_row(session, user)
    trees.save_nodes(settings, row, [{"concept": "Kept", "parentConcept": None,
                                      "childConcepts": []}])

    r = await client.post("/api/trees/fork", json={})
    assert r.status_code == 409
    assert trees.load_nodes(settings, row) == [{"concept": "Kept",
                                                "parentConcept": None,
                                                "childConcepts": []}]


async def test_another_users_tree_is_invisible(settings, session, user):
    async with _client_for(settings, session, user) as mine:
        await mine.post("/api/trees/fork", json={})
        row = await _tree_row(session, user)
        trees.save_nodes(settings, row, [{"concept": "Mine", "parentConcept": None,
                                          "childConcepts": []}])

    stranger = await _user(session)
    async with _client_for(settings, session, stranger) as theirs:
        # Same slug, different account: no read, and no 500 from a missing file.
        assert (await theirs.get("/api/tree", params={"tree": "me"})).status_code == 404
        assert (await theirs.post("/api/trees/me/validate")).status_code == 404
        # Forking is allowed and gets its own copy — it does not adopt Mine.
        assert (await theirs.post("/api/trees/fork", json={})).status_code == 201
        got = (await theirs.get("/api/tree", params={"tree": "me"})).json()["nodes"]
        assert got == trees.public_nodes()


async def test_the_public_tree_is_readable_signed_out_and_the_private_one_is_not(
    anonymous,
):
    assert (await anonymous.get("/api/tree", params={"tree": "public"})).status_code == 200
    assert (await anonymous.get("/api/tree", params={"tree": "me"})).status_code == 401
    assert (await anonymous.post("/api/trees/fork", json={})).status_code == 401


async def test_a_paid_plan_gets_its_own_higher_allowance(settings, session):
    starter = await _user(session, plan_id="starter")
    async with _client_for(settings, session, starter) as http:
        for slug in ("me", "second", "third"):
            assert (await http.post("/api/trees/fork",
                                    json={"slug": slug})).status_code == 201
        assert (await http.post("/api/trees/fork",
                                json={"slug": "fourth"})).status_code == 402


async def test_validate_on_a_tree_that_was_never_forked_is_404(client):
    assert (await client.post("/api/trees/me/validate")).status_code == 404
    assert (await client.get("/api/tree", params={"tree": "me"})).status_code == 404


# --- the module's own contract ----------------------------------------------


def test_the_public_sha_is_the_hash_of_the_file_on_disk():
    import hashlib

    path = trees.public_tree_path()
    assert trees.public_sha() == hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_public_tree_never_moves_under_a_user_directory(settings):
    assert settings.stores_root not in trees.public_tree_path().parents
