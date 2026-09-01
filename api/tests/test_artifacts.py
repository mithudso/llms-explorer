# api/tests/test_artifacts.py
"""`/u/<user>/<slug>.llms/<file>` — a private artifact, served like `/d/`.

Two contracts meet in this route and both are asserted here:

* **Header parity with `hub/scripts/llms_serve.py`.** The private route must be
  indistinguishable from the public `/d/` one to a client: the same
  `Content-Type`, the same `X-Markdown-Tokens` estimator (chars/4, and only on
  markdown), the same `Link: …; rel="describedby"`, and JSON served as JSON with
  neither of the markdown-only headers. A parity test reads the constants out of
  `llms_serve.py` itself so the two cannot drift silently.

* **Privacy (master §6).** `Cache-Control: private, no-store` and a cache key
  that includes the session/key (`Vary`), so nothing lands in an edge cache. A
  stranger gets **404, not 403**, because 403 would confirm the artifact exists
  and turn the path into an enumeration oracle; anonymous gets 401.

Written from the attacker's side: can I read someone else's artifact by
guessing? by presenting my own key against their user id? by walking out of the
store with `..`? does a symlink escape? does anything ever come back
edge-cacheable?
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from explorer_api import artifacts, keys, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.artifacts import router as artifacts_router
from explorer_api.routes.auth import optional_user
from explorer_api.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
LLMS_SERVE = REPO_ROOT / "hub" / "scripts" / "llms_serve.py"

INDEX_BODY = "# ada's notes\n\n> A private index.\n\n## Docs\n\n- [one](one.md): the first one.\n"
FULL_BODY = "# ada's notes\n\nSource: https://example.test/one\n\nBody text.\n" * 20
MANIFEST_BODY = '{"kind": "index", "tokens": 41}\n'


# --- fixtures ----------------------------------------------------------------


async def _user(session, email: str | None = None) -> m.User:
    user = m.User(email=email or f"u-{uuid4().hex[:10]}@example.test")
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def owner(session) -> m.User:
    return await _user(session)


@pytest_asyncio.fixture
async def stranger(session) -> m.User:
    return await _user(session)


@pytest.fixture()
def stores_root(tmp_path: Path) -> Path:
    return tmp_path / "stores"


@pytest.fixture()
def artifact_dir(stores_root: Path, owner: m.User) -> Path:
    """`<stores>/<user>/artifacts/notes.llms/` with a small llms family in it."""
    d = artifacts.artifact_dir(stores_root, owner.id, "notes")
    d.mkdir(parents=True)
    (d / "llms.txt").write_text(INDEX_BODY, encoding="utf-8")
    (d / "llms-full.txt").write_text(FULL_BODY, encoding="utf-8")
    (d / "manifest.json").write_text(MANIFEST_BODY, encoding="utf-8")
    section = d / "docs"
    section.mkdir()
    (section / "llms.txt").write_text("# section\n\n- [one](one.md)\n", encoding="utf-8")
    return d


@pytest_asyncio.fixture
async def client(session, stores_root: Path, database_url: str) -> AsyncIterator[AsyncClient]:
    """The artifact router on the real app, signed out by default.

    `signed_in_as(client, user)` flips the identity; `get_session` is pinned to
    the test's own session so a row written here is visible to the route.
    """
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
            "STORES_ROOT": str(stores_root),
        }
    )
    app = create_app(settings)
    app.include_router(artifacts_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.state.test_user = None
    app.dependency_overrides[optional_user] = lambda: app.state.test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        http.app = app  # so a test can change who is signed in
        yield http


def signed_in_as(client: AsyncClient, user: m.User | None) -> None:
    client.app.state.test_user = user


# --- the plan's four assertions ----------------------------------------------


async def test_the_owner_gets_the_file_with_the_llms_serve_headers(client, owner, artifact_dir):
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/llms.txt")

    assert r.status_code == 200
    assert r.text == INDEX_BODY
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"
    assert r.headers["x-markdown-tokens"] == str(len(INDEX_BODY.encode()) // 4)
    assert r.headers["link"] == (
        f'<http://test/u/{owner.id}/notes.llms/llms.txt>; rel="describedby"'
    )


async def test_a_signed_in_stranger_gets_404_not_403(client, owner, stranger, artifact_dir):
    signed_in_as(client, stranger)
    r = await client.get(f"/u/{owner.id}/notes.llms/llms.txt")
    assert r.status_code == 404          # 403 would confirm the artifact exists


async def test_anonymous_gets_401(client, owner, artifact_dir):
    signed_in_as(client, None)
    r = await client.get(f"/u/{owner.id}/notes.llms/llms.txt")
    assert r.status_code == 401


async def test_the_response_is_never_edge_cacheable(client, owner, artifact_dir):
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/llms-full.txt")
    cache_control = r.headers["cache-control"]
    assert "private" in cache_control and "no-store" in cache_control
    assert "public" not in cache_control
    # master §6: "cache key includes the key/session"
    vary = r.headers["vary"].lower()
    assert "cookie" in vary and "authorization" in vary


# --- header parity with llms_serve.py ---------------------------------------


def test_the_token_estimator_is_the_one_llms_serve_uses():
    source = LLMS_SERVE.read_text(encoding="utf-8")
    declared = int(re.search(r"^CHARS_PER_TOKEN\s*=\s*(\d+)", source, re.M).group(1))
    assert declared == artifacts.CHARS_PER_TOKEN
    assert artifacts.MARKDOWN_TYPE in source
    assert artifacts.JSON_TYPE in source


async def test_json_is_json_and_carries_neither_markdown_header(client, owner, artifact_dir):
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/manifest.json")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json; charset=utf-8"
    # llms_serve sends X-Markdown-Tokens and Link only for markdown.
    assert "x-markdown-tokens" not in r.headers
    assert "link" not in r.headers


async def test_a_section_index_at_any_depth_is_served(client, owner, artifact_dir):
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/docs/llms.txt")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"


# --- from the attacker's side ------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [
        "../../../../etc/passwd",
        "..%2f..%2fsecret.txt",
        "docs/../../../secret.txt",
        "llms.txt%00.png",
    ],
)
async def test_traversal_never_leaves_the_store(client, owner, artifact_dir, target):
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/{target}")
    assert r.status_code == 404


async def test_a_symlink_out_of_the_store_is_refused(client, owner, artifact_dir, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    (artifact_dir / "llms-facts.txt").symlink_to(outside)
    signed_in_as(client, owner)
    r = await client.get(f"/u/{owner.id}/notes.llms/llms-facts.txt")
    assert r.status_code == 404
    assert "secret" not in r.text


async def test_a_file_outside_the_llms_family_is_not_served(client, owner, artifact_dir):
    (artifact_dir / "notes.db").write_text("sqlite\n", encoding="utf-8")
    signed_in_as(client, owner)
    assert (await client.get(f"/u/{owner.id}/notes.llms/notes.db")).status_code == 404


async def test_a_missing_file_is_404_for_the_owner_too(client, owner, artifact_dir):
    signed_in_as(client, owner)
    assert (await client.get(f"/u/{owner.id}/notes.llms/llms-small.txt")).status_code == 404
    assert (await client.get(f"/u/{owner.id}/nope.llms/llms.txt")).status_code == 404


async def test_a_read_scoped_key_reads_its_owners_artifact(client, session, owner, artifact_dir):
    raw, _ = await keys.create(session, owner, ["read"])
    signed_in_as(client, None)
    r = await client.get(
        f"/u/{owner.id}/notes.llms/llms.txt", headers={"Authorization": f"Bearer {raw}"}
    )
    assert r.status_code == 200
    assert "no-store" in r.headers["cache-control"]


async def test_another_users_key_gets_404_not_403(client, session, owner, stranger, artifact_dir):
    raw, _ = await keys.create(session, stranger, ["read"])
    signed_in_as(client, None)
    r = await client.get(
        f"/u/{owner.id}/notes.llms/llms.txt", headers={"Authorization": f"Bearer {raw}"}
    )
    assert r.status_code == 404


async def test_a_revoked_key_is_anonymous_again(client, session, owner, artifact_dir):
    raw, row = await keys.create(session, owner, ["read"])
    await keys.revoke(session, owner, row.id)
    signed_in_as(client, None)
    r = await client.get(
        f"/u/{owner.id}/notes.llms/llms.txt", headers={"Authorization": f"Bearer {raw}"}
    )
    assert r.status_code == 401


async def test_a_bad_user_segment_does_not_reach_the_filesystem(client, owner, artifact_dir):
    signed_in_as(client, owner)
    for bad in ("..", "usr_%2e%2e", "a" * 300):
        assert (await client.get(f"/u/{bad}/notes.llms/llms.txt")).status_code in (401, 404)


async def test_head_carries_the_headers_and_no_body(client, owner, artifact_dir):
    signed_in_as(client, owner)
    r = await client.head(f"/u/{owner.id}/notes.llms/llms.txt")
    assert r.status_code == 200
    assert r.headers["x-markdown-tokens"] == str(len(INDEX_BODY.encode()) // 4)
    assert r.content == b""


async def test_a_key_without_read_scope_is_403_on_its_own_artifact(
    client, session, owner, artifact_dir
):
    """Identity is already proven here, so naming the missing scope leaks
    nothing — and it is the only thing the caller can act on."""
    raw, _ = await keys.create(session, owner, ["publish"])
    signed_in_as(client, None)
    r = await client.get(
        f"/u/{owner.id}/notes.llms/llms.txt", headers={"Authorization": f"Bearer {raw}"}
    )
    assert r.status_code == 403


async def test_a_presented_key_wins_over_the_session_cookie(
    client, session, owner, stranger, artifact_dir
):
    """A revoked key inside a signed-in tab must not silently fall back to the
    cookie and keep working."""
    raw, row = await keys.create(session, owner, ["read"])
    await keys.revoke(session, owner, row.id)
    signed_in_as(client, owner)
    r = await client.get(
        f"/u/{owner.id}/notes.llms/llms.txt", headers={"Authorization": f"Bearer {raw}"}
    )
    assert r.status_code == 401
