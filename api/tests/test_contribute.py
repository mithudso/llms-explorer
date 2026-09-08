"""Tests for `POST /api/contribute`."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from explorer_api import models as m, moderation
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.auth import current_user
from explorer_api.routes.contribute import router as contribute_router
from explorer_api.routes import skills as skills_module
from explorer_api.routes.skills import Completion
from explorer_api.settings import Settings


class FakeLlm:
    """Stands in for Anthropic. Records what it was asked, never calls out."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.reply = "# Test Concept\n\n- A fact about the concept.\n"

    async def complete(self, *, system: str, prompt: str,
                       max_tokens: int) -> Completion:
        self.calls.append({"system": system, "prompt": prompt,
                           "max_tokens": max_tokens})
        return Completion(text=self.reply, input_tokens=120, output_tokens=340)


@pytest.fixture
def llm() -> FakeLlm:
    return FakeLlm()


async def _user(session: AsyncSession) -> m.User:
    """Create a test user."""
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test")
    # _check_plan refuses with MissingApiKey unless the user has stored a key.
    # The ciphertext is never decrypted here; the LLM client is stubbed below.
    user.anthropic_api_key_ciphertext = "gAAAAA...test-ciphertext..."
    user.anthropic_api_key_hint = "test"
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> m.User:
    """A test user."""
    return await _user(session)


@pytest_asyncio.fixture
async def client(
    session: AsyncSession, user: m.User, database_url: str, llm: FakeLlm,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AsyncClient]:
    """Authenticated test client for the contribute endpoint."""
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
        }
    )
    app = create_app(settings)
    app.include_router(contribute_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[current_user] = lambda: user
    monkeypatch.setattr(skills_module, "get_llm_client_factory",
                        lambda _request: (lambda _user: llm))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


class TestContributeEndpoint:
    """Tests for the contribute endpoint."""

    async def test_happy_path_creates_artifact_and_proposal(
        self, client: AsyncClient, user: m.User, session: AsyncSession
    ) -> None:
        """Happy path: artifact written, proposal created, pending."""
        # Ensure the tree file exists - create it with proper JSON
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        if not tree_path.exists():
            tree_path.write_text(json.dumps([]))

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "Test Concept",
                "text": "This is a test corpus about the concept.",
                "parent": None,
                "summary": "A brief test summary",
            },
        )

        # Should succeed with 201
        assert response.status_code == 201, response.text
        data = response.json()

        # Check proposal was created
        assert "proposal" in data
        proposal = data["proposal"]
        assert proposal["status"] in ("proposed", "rejected")
        assert proposal["user_id"] == user.id
        assert "patch" in proposal

        # Check patch structure
        patch = proposal["patch"]
        assert "ops" in patch
        assert len(patch["ops"]) == 1
        op = patch["ops"][0]
        assert op["op"] == "add"
        assert op["node"]["concept"] == "Test Concept"
        assert op["node"]["slug"] == "test-concept"
        assert op["node"]["state"] == "researched"

        # Check pass output is present
        assert "pass_output" in data
        assert len(data["pass_output"]) > 0

    async def test_name_collision_returns_400(
        self, client: AsyncClient, user: m.User
    ) -> None:
        """Attempting to add an existing concept returns 422."""
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a tree with an existing concept
        existing_node = {
            "concept": "Existing Concept",
            "slug": "existing-concept",
            "parent": None,
        }
        tree_path.write_text(json.dumps([existing_node]))

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "Existing Concept",
                "text": "This will collide.",
            },
        )

        # A duplicate concept is a gateway InvalidParams refusal, which
        # gateway.py maps to 400. FastAPI's 422 covers body validation only.
        assert response.status_code == 400, response.text

    async def test_overcap_input_returns_422(
        self, client: AsyncClient, user: m.User
    ) -> None:
        """Input exceeding MAX_INPUT_CHARS returns 422."""
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        if not tree_path.exists():
            tree_path.write_text(json.dumps([]))

        # Text exceeds the limit
        oversized_text = "x" * (4001)

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "Test",
                "text": oversized_text,
            },
        )

        assert response.status_code == 422, response.text

    async def test_unauthenticated_returns_401(self, database_url: str) -> None:
        """Request without session cookie returns 401."""
        settings = Settings.load(
            {
                "DATABASE_URL": "postgresql+asyncpg://test@localhost/test",
                "SESSION_SECRET": "s" * 32,
                "STRIPE_SECRET_KEY": "sk_test_x",
                "STRIPE_WEBHOOK_SECRET": "whsec_x",
            }
        )
        app = create_app(settings)
        app.include_router(contribute_router)
        # ASGITransport does not run the lifespan, so wire the state the auth
        # dependency reads. Without it the request raises AttributeError on
        # state.session_factory before it can refuse with 401.
        engine = create_async_engine(database_url, future=True)
        app.state.engine = engine
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            response = await http.post(
                "/api/contribute",
                json={
                    "concept": "Test Concept",
                    "text": "Test text",
                },
            )

        assert response.status_code == 401, response.text

    async def test_concept_validation_too_short(
        self, client: AsyncClient, user: m.User
    ) -> None:
        """Concept with 0 chars returns 422."""
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        if not tree_path.exists():
            tree_path.write_text(json.dumps([]))

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "",
                "text": "Test text",
            },
        )

        assert response.status_code == 422, response.text

    async def test_concept_validation_too_long(
        self, client: AsyncClient, user: m.User
    ) -> None:
        """Concept with >200 chars returns 422."""
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        if not tree_path.exists():
            tree_path.write_text(json.dumps([]))

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "x" * 201,
                "text": "Test text",
            },
        )

        assert response.status_code == 422, response.text

    async def test_nonexistent_parent_returns_400(
        self, client: AsyncClient, user: m.User
    ) -> None:
        """Specifying a nonexistent parent returns 422."""
        tree_path = moderation.public_tree_path()
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        if not tree_path.exists():
            tree_path.write_text(json.dumps([]))

        response = await client.post(
            "/api/contribute",
            json={
                "concept": "New Concept",
                "text": "Test text",
                "parent": "Nonexistent Parent",
            },
        )

        # InvalidParams again: the parent is well-formed but does not exist.
        assert response.status_code == 400, response.text


__all__ = ["TestContributeEndpoint"]
