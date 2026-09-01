# api/tests/test_gateway.py
"""The hosted MCP gateway: the only door between the public internet and the hub.

The hub's own MCP server is unauthenticated by design — `hub/docs/MCP.md` says
"localhost trust model; never expose off-box without adding auth". This gateway
*is* that auth, so every test here is written from the attacker's side:

* a tool master D5 keeps off the hosted surface must be unreachable **however**
  the key is scoped — scope creep must not be able to reach it,
* one user's docset namespace must be invisible and untouchable from another's
  key, in the arguments going out *and* in the reply coming back,
* a `read` key must not be able to spend money,
* a metered call must write exactly one ledger row — not zero (free work) and
  not two (double billing),
* a filesystem path handed to `hub_index_docset` must not be able to walk out of
  the caller's own store: the hub indexes any file it can read, so an unconfined
  `mirror_path` is a local-file-read primitive.

The hub is faked. A test that talked to a real `hub_mcp_server.py` would be
testing the hub, and would need the owner's box; the contract this file pins is
the gateway's: what reaches the hub, and what never does.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from explorer_api import gateway as gw
from explorer_api import keys, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.mcp import get_catalogue, get_hub_client
from explorer_api.routes.mcp import router as mcp_router
from explorer_api.settings import Settings

#: A docset in the shared catalogue — no `u_…` prefix, so anyone may read it.
PUBLIC_DOCSET = "codeclaudecom__codeclaudecom"
#: Somebody else's private docset. It is in the hub's registry and must never
#: be readable, listable or deletable through another user's key.
FOREIGN_DOCSET = "u_bob__notes"

#: Every tool the hub actually registers (`hub/mcp-server/hub_mcp_server.py`).
#: The fake advertises all of them so `tools/list` filtering is tested against
#: the real surface rather than against a list the gateway also owns.
HUB_TOOLS = (
    "hub_search_codebase", "hub_ask", "hub_search_symbols", "hub_route",
    "hub_index_docset", "hub_query_docset", "hub_list_docsets", "hub_delete_docset",
    "hub_docset_index", "hub_llms_full_list", "hub_llms_full_read",
    "hub_concept_tree", "hub_concept_lookup", "hub_concept_frontier",
    "hub_concept_queue", "hub_distill_run", "hub_memory_search", "hub_memory_stats",
)


def _text(payload: str) -> dict[str, Any]:
    """An MCP `tools/call` result, as FastMCP shapes a string-returning tool."""
    return {"content": [{"type": "text", "text": payload}], "isError": False}


class FakeHub:
    """Stands in for `hub_mcp_server.py --http` on 127.0.0.1."""

    def __init__(self, entries: list[dict] | None = None) -> None:
        self.entries: list[dict] = entries if entries is not None else [
            {"docset": PUBLIC_DOCSET, "pages": 12, "chunks": 340},
            {"docset": f"{PUBLIC_DOCSET}__facts", "pages": 12, "chunks": 90},
            {"docset": FOREIGN_DOCSET, "pages": 3, "chunks": 20},
        ]
        self.calls: list[tuple[str, dict]] = []
        self.raise_on_call: Exception | None = None

    async def list_tools(self) -> list[dict]:
        return [
            {"name": name, "description": name, "inputSchema": {"type": "object"}}
            for name in HUB_TOOLS
        ]

    async def call_tool(self, name: str, arguments: dict, *, timeout: float | None = None):
        self.calls.append((name, dict(arguments)))
        if self.raise_on_call is not None:
            raise self.raise_on_call
        if name == "hub_list_docsets":
            return _text(json.dumps(self.entries))
        if name == "hub_index_docset":
            self.entries.append({"docset": arguments.get("name", ""), "chunks": 7})
            return _text(json.dumps({"docset": arguments.get("name"), "chunks": 7}))
        return _text(f"ok:{name}")


@dataclass(frozen=True)
class Caller:
    """A key, its owner and the namespace that key may write in."""

    raw: str
    user: m.User
    namespace: str


@pytest_asyncio.fixture
async def hub() -> FakeHub:
    return FakeHub()


@pytest_asyncio.fixture
async def stores_root(tmp_path):
    root = tmp_path / "stores"
    root.mkdir()
    return root


class GatewayClient:
    """`POST /mcp`, spoken as an MCP client would speak it."""

    def __init__(self, http: AsyncClient, hub: FakeHub) -> None:
        self.http, self.hub = http, hub
        self._id = 0

    def _headers(self, key: Caller | str | None) -> dict[str, str]:
        raw = key.raw if isinstance(key, Caller) else key
        return {"Authorization": f"Bearer {raw}"} if raw else {}

    async def rpc(self, method: str, params: dict | None = None, *,
                  key: Caller | str | None = None) -> httpx.Response:
        self._id += 1
        body: dict[str, Any] = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            body["params"] = params
        return await self.http.post("/mcp", json=body, headers=self._headers(key))

    async def call(self, tool: str, arguments: dict | None = None, *,
                   key: Caller | str | None = None) -> httpx.Response:
        return await self.rpc("tools/call",
                              {"name": tool, "arguments": arguments or {}}, key=key)


@pytest_asyncio.fixture
async def gateway(session, hub, stores_root, database_url: str) -> AsyncIterator[GatewayClient]:
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
    # Wiring the router into `main.create_app` belongs to the task that owns
    # `main.py`; mounting it here keeps this task to its three files.
    app.include_router(mcp_router)
    catalogue = gw.Catalogue(hub)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_hub_client] = lambda: hub
    app.dependency_overrides[get_catalogue] = lambda: catalogue

    gw.reset_rate_limits()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield GatewayClient(http, hub)


async def _caller(session, scopes: list[str], plan_id: str = "pro") -> Caller:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", plan_id=plan_id)
    session.add(user)
    await session.flush()
    raw, _row = await keys.create(session, user, scopes)
    await session.flush()
    return Caller(raw=raw, user=user, namespace=gw.namespace_for(user))


@pytest_asyncio.fixture
async def key_all_scopes(session) -> Caller:
    return await _caller(session, ["read", "run", "publish"])


@pytest_asyncio.fixture
async def key_a(session) -> Caller:
    return await _caller(session, ["read", "run"])


@pytest_asyncio.fixture
async def key_read(session) -> Caller:
    return await _caller(session, ["read"])


@pytest_asyncio.fixture
async def key_run(session) -> Caller:
    """A `run` key on the free plan — one index is included there (15 §5)."""
    return await _caller(session, ["read", "run"], plan_id="free")


# --- the plan's four acceptance tests ---------------------------------------


async def test_absent_tools_are_not_reachable_however_the_key_is_scoped(
    gateway, key_all_scopes
):
    """Master D5: these are local-only. No scope, however wide, reaches them."""
    for tool in ("hub_ask", "hub_distill_run", "hub_memory_search", "hub_memory_stats"):
        r = await gateway.call(tool, {}, key=key_all_scopes)
        assert r.status_code == 404, tool
        assert "not hosted" in r.text, tool
    assert gateway.hub.calls == []          # nothing was forwarded


def test_the_absent_list_is_decision_d5_verbatim():
    """A tool cannot be reachable by being *added* to the policy table either.

    `resolve_policy` refuses absent tools by name before it looks anything up,
    so this asserts the data the two halves share: D5's names are absent, and
    absent means they are in no policy row.
    """
    for tool in ("hub_ask", "hub_distill_run", "hub_memory_search", "hub_memory_stats"):
        assert tool in gw.ABSENT_TOOLS
    assert set(gw.TOOL_POLICY) & gw.ABSENT_TOOLS == set()


async def test_a_user_cannot_touch_another_users_docset(gateway, key_a):
    r = await gateway.call("hub_query_docset",
                           {"docset": FOREIGN_DOCSET, "question": "x"}, key=key_a)
    assert r.status_code == 403
    assert (await gateway.call("hub_query_docset",
                               {"docset": PUBLIC_DOCSET, "question": "x"},
                               key=key_a)).status_code == 200
    forwarded = [name for name, _ in gateway.hub.calls if name == "hub_query_docset"]
    assert len(forwarded) == 1              # the refused one never left the gateway


async def test_a_metered_tool_writes_exactly_one_ledger_row(gateway, key_run, session):
    r = await gateway.call(
        "hub_index_docset",
        {"mirror_path": "mirror.md", "name": f"{key_run.namespace}x"},
        key=key_run,
    )
    assert r.status_code == 200, r.text
    rows = (await session.execute(select(m.LedgerEntry))).scalars().all()
    assert len(rows) == 1 and rows[0].component == "13"
    assert isinstance(rows[0].price_usd, Decimal)


async def test_read_scope_cannot_run(gateway, key_read):
    r = await gateway.call("hub_index_docset",
                           {"mirror_path": "m.md", "name": f"{key_read.namespace}x"},
                           key=key_read)
    assert r.status_code == 403
    assert gateway.hub.calls == []


# --- namespacing, both directions -------------------------------------------


async def test_a_foreign_namespace_cannot_be_created_or_deleted(gateway, key_a):
    for tool, args in (
        ("hub_index_docset", {"mirror_path": "m.md", "name": FOREIGN_DOCSET}),
        ("hub_delete_docset", {"docset": FOREIGN_DOCSET, "confirm": True}),
        ("hub_delete_docset", {"docset": PUBLIC_DOCSET, "confirm": True}),
        ("hub_docset_index", {"docset": FOREIGN_DOCSET}),
    ):
        r = await gateway.call(tool, args, key=key_a)
        assert r.status_code == 403, (tool, args, r.text)
    assert gateway.hub.calls == []


async def test_the_facts_twin_of_a_foreign_docset_is_refused_too(gateway, key_a):
    r = await gateway.call("hub_query_docset",
                           {"docset": f"{FOREIGN_DOCSET}__facts", "question": "x"},
                           key=key_a)
    assert r.status_code == 403


async def test_list_docsets_never_returns_another_users_namespace(gateway, key_a):
    r = await gateway.call("hub_list_docsets", {}, key=key_a)
    assert r.status_code == 200
    listed = json.loads(r.json()["result"]["content"][0]["text"])
    names = {entry["docset"] for entry in listed}
    assert PUBLIC_DOCSET in names
    assert FOREIGN_DOCSET not in names
    assert FOREIGN_DOCSET not in r.text


async def test_a_user_sees_their_own_docsets_in_the_listing(gateway, key_a):
    gateway.hub.entries.append({"docset": f"{key_a.namespace}mine", "pages": 1})
    r = await gateway.call("hub_list_docsets", {}, key=key_a)
    names = {e["docset"] for e in json.loads(r.json()["result"]["content"][0]["text"])}
    assert f"{key_a.namespace}mine" in names


# --- the filesystem is not part of the API ----------------------------------


async def test_a_mirror_path_cannot_walk_out_of_the_callers_store(gateway, key_run):
    for path in ("../../etc/passwd", "/etc/passwd", "sub/../../escape.md"):
        r = await gateway.call("hub_index_docset",
                               {"mirror_path": path, "name": f"{key_run.namespace}x"},
                               key=key_run)
        assert r.status_code == 403, path
    assert gateway.hub.calls == []


async def test_a_relative_mirror_path_is_rewritten_into_the_callers_store(
    gateway, key_run, stores_root
):
    await gateway.call("hub_index_docset",
                       {"mirror_path": "m.md", "name": f"{key_run.namespace}x"},
                       key=key_run)
    _name, args = next(c for c in gateway.hub.calls if c[0] == "hub_index_docset")
    expected = stores_root / key_run.user.id / "m.md"
    assert args["mirror_path"] == str(expected)


# --- scopes and keys ---------------------------------------------------------


async def test_a_read_tool_needs_a_key_but_a_public_one_does_not(gateway, key_read):
    assert (await gateway.call("hub_concept_frontier", {})).status_code == 200
    anonymous = await gateway.call("hub_query_docset",
                                   {"docset": PUBLIC_DOCSET, "question": "x",
                                    "mode": "keyword"})
    assert anonymous.status_code == 401
    signed_in = await gateway.call("hub_query_docset",
                                   {"docset": PUBLIC_DOCSET, "question": "x",
                                    "mode": "keyword"}, key=key_read)
    assert signed_in.status_code == 200


async def test_a_revoked_key_stops_working_at_the_gateway(gateway, session, key_a):
    row = (await session.execute(
        select(m.ApiKey).where(m.ApiKey.user_id == key_a.user.id)
    )).scalar_one()
    await keys.revoke(session, key_a.user, row.id)
    r = await gateway.call("hub_query_docset",
                           {"docset": PUBLIC_DOCSET, "question": "x"}, key=key_a)
    assert r.status_code == 401


async def test_a_garbage_key_is_401_and_never_a_traceback(gateway):
    r = await gateway.call("hub_query_docset",
                           {"docset": PUBLIC_DOCSET, "question": "x"},
                           key="llmsx_not_a_key")
    assert r.status_code == 401
    assert "Traceback" not in r.text


# --- discovery ---------------------------------------------------------------


async def test_tools_list_never_advertises_an_absent_tool(gateway, key_all_scopes):
    r = await gateway.rpc("tools/list", {}, key=key_all_scopes)
    assert r.status_code == 200
    names = {tool["name"] for tool in r.json()["result"]["tools"]}
    assert names & set(gw.ABSENT_TOOLS) == set()
    assert "hub_list_docsets" in names and "hub_index_docset" in names


async def test_tools_list_for_a_read_key_hides_the_run_tools(gateway, key_read):
    names = {t["name"] for t in (await gateway.rpc("tools/list", {},
                                                   key=key_read)).json()["result"]["tools"]}
    assert "hub_index_docset" not in names and "hub_delete_docset" not in names
    assert "hub_list_docsets" in names


async def test_an_unknown_tool_looks_exactly_like_an_absent_one(gateway, key_all_scopes):
    unknown = await gateway.call("hub_not_a_tool", {}, key=key_all_scopes)
    absent = await gateway.call("hub_ask", {}, key=key_all_scopes)
    assert unknown.status_code == absent.status_code == 404
    assert unknown.json()["error"]["message"].replace("hub_not_a_tool", "T") == \
        absent.json()["error"]["message"].replace("hub_ask", "T")


async def test_initialize_is_answered_by_the_gateway_not_the_hub(gateway):
    r = await gateway.rpc("initialize", {"protocolVersion": "2025-06-18",
                                         "capabilities": {}, "clientInfo": {"name": "t"}})
    assert r.status_code == 200
    assert r.json()["result"]["serverInfo"]["name"]
    assert r.headers.get("mcp-session-id")
    assert gateway.hub.calls == []


# --- quotas and metering -----------------------------------------------------


async def test_a_free_plans_semantic_query_is_402_with_somewhere_to_go(gateway, session):
    free = await _caller(session, ["read", "run"], plan_id="free")
    r = await gateway.call("hub_query_docset",
                           {"docset": PUBLIC_DOCSET, "question": "x",
                            "mode": "semantic"}, key=free)
    assert r.status_code == 402
    assert r.json()["error"]["data"]["upgrade_url"]
    # The catalogue read is the gateway's own; the caller's tool never ran.
    assert [name for name, _ in gateway.hub.calls if name == "hub_query_docset"] == []


async def test_the_free_index_quota_stops_the_second_index(gateway, key_run):
    first = await gateway.call("hub_index_docset",
                               {"mirror_path": "a.md", "name": f"{key_run.namespace}a"},
                               key=key_run)
    assert first.status_code == 200
    second = await gateway.call("hub_index_docset",
                                {"mirror_path": "b.md", "name": f"{key_run.namespace}b"},
                                key=key_run)
    assert second.status_code == 402
    assert second.json()["error"]["data"]["upgrade_url"]


async def test_a_keyword_query_is_counted_but_not_charged(gateway, key_read, session):
    r = await gateway.call("hub_query_docset",
                           {"docset": PUBLIC_DOCSET, "question": "x", "mode": "keyword"},
                           key=key_read)
    assert r.status_code == 200
    row = (await session.execute(select(m.LedgerEntry))).scalar_one()
    assert row.billable is False and row.price_usd == Decimal("0")


async def test_a_refused_call_never_writes_a_ledger_row(gateway, key_run, session):
    await gateway.call("hub_index_docset",
                       {"mirror_path": "../escape.md", "name": f"{key_run.namespace}x"},
                       key=key_run)
    assert (await session.execute(select(m.LedgerEntry))).scalars().all() == []


# --- the hub's failures are not the caller's problem -------------------------


async def test_a_hub_failure_is_502_and_leaks_nothing(gateway, key_a):
    """Even an exception the client contract does not promise stays a 502."""
    gateway.hub.raise_on_call = ConnectionError("refused to 127.0.0.1:8787 as mitch")
    r = await gateway.call("hub_docset_index", {"docset": PUBLIC_DOCSET}, key=key_a)
    assert r.status_code == 502
    assert "127.0.0.1" not in r.text and "Traceback" not in r.text
    assert "mitch" not in r.text


async def test_third_party_full_text_is_never_served_hosted(gateway, key_a):
    """Master D8: the directory links to the source's own URL, it never republishes."""
    r = await gateway.call("hub_llms_full_read", {"key": "stripe", "page": ""}, key=key_a)
    assert r.status_code == 403
    assert "D8" in r.text
    assert gateway.hub.calls == []


async def test_the_catalogue_listing_itself_stays_public(gateway):
    r = await gateway.call("hub_llms_full_list", {"query": "stripe"})
    assert r.status_code == 200


# --- the unauthenticated surface is rate limited -----------------------------


async def test_anonymous_public_calls_are_rate_limited(gateway, monkeypatch):
    monkeypatch.setattr(gw, "ANON_RATE_LIMIT", 2)
    gw.reset_rate_limits()
    assert (await gateway.call("hub_concept_frontier", {})).status_code == 200
    assert (await gateway.call("hub_concept_frontier", {})).status_code == 200
    limited = await gateway.call("hub_concept_frontier", {})
    assert limited.status_code == 429
    assert limited.headers.get("retry-after")


# --- malformed input ---------------------------------------------------------


@pytest.mark.parametrize("body", [
    {"jsonrpc": "1.0", "id": 1, "method": "tools/call"},
    {"jsonrpc": "2.0", "id": 1},
    [{"jsonrpc": "2.0", "id": 1, "method": "ping"}],
    "not json at all",
])
async def test_a_malformed_envelope_is_400_not_500(gateway, body):
    if isinstance(body, str):
        r = await gateway.http.post("/mcp", content=body,
                                    headers={"Content-Type": "application/json"})
    else:
        r = await gateway.http.post("/mcp", json=body)
    assert r.status_code == 400


async def test_arguments_must_be_an_object(gateway, key_a):
    r = await gateway.rpc("tools/call", {"name": "hub_list_docsets", "arguments": []},
                          key=key_a)
    assert r.status_code == 400


# --- the REST twin is the same door, not a second one ------------------------


async def test_the_rest_twin_enforces_the_same_policy(gateway, key_read, key_a):
    """13 §5's `/api/mcp/<tool>` shares the code path, so it shares the rules."""
    headers = {"Authorization": f"Bearer {key_read.raw}"}
    absent = await gateway.http.post("/api/mcp/hub_ask", json={}, headers=headers)
    assert absent.status_code == 404 and "not hosted" in absent.text

    scoped = await gateway.http.post(
        "/api/mcp/hub_index_docset",
        json={"mirror_path": "m.md", "name": f"{key_read.namespace}x"},
        headers=headers,
    )
    assert scoped.status_code == 403

    foreign = await gateway.http.post(
        "/api/mcp/hub_query_docset", json={"docset": FOREIGN_DOCSET, "question": "x"},
        headers={"Authorization": f"Bearer {key_a.raw}"},
    )
    assert foreign.status_code == 403
    assert gateway.hub.calls == []


async def test_the_rest_twin_returns_the_bare_tool_result(gateway, key_a):
    r = await gateway.http.post("/api/mcp/hub_list_docsets", json={},
                                headers={"Authorization": f"Bearer {key_a.raw}"})
    assert r.status_code == 200
    assert "content" in r.json()          # the MCP result, not a JSON-RPC envelope


async def test_get_mcp_offers_no_stream_to_hang_on(gateway):
    r = await gateway.http.get("/mcp")
    assert r.status_code == 405 and r.headers.get("allow") == "POST"


# --- the client that actually talks to the hub -------------------------------


def _sse(payload: dict) -> httpx.Response:
    body = f"event: message\ndata: {json.dumps(payload)}\n\n"
    return httpx.Response(200, content=body,
                          headers={"Content-Type": "text/event-stream"})


async def test_the_http_hub_client_initialises_then_calls(stores_root):
    """The real client speaks Streamable HTTP: initialize → notify → call."""
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append({"method": body.get("method"),
                     "session": request.headers.get("mcp-session-id")})
        if body.get("method") == "initialize":
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": body["id"],
                      "result": {"protocolVersion": gw.MCP_PROTOCOL_VERSION,
                                 "capabilities": {}, "serverInfo": {"name": "hub"}}},
                headers={"Mcp-Session-Id": "sess-1"},
            )
        if body.get("id") is None:
            return httpx.Response(202)
        return _sse({"jsonrpc": "2.0", "id": body["id"], "result": _text("pong")})

    client = gw.HttpHubClient("http://127.0.0.1:8787",
                              transport=httpx.MockTransport(handler))
    try:
        result = await client.call_tool("hub_list_docsets", {})
    finally:
        await client.aclose()
    assert result["content"][0]["text"] == "pong"
    assert [s["method"] for s in seen] == ["initialize", "notifications/initialized",
                                           "tools/call"]
    assert seen[-1]["session"] == "sess-1"


async def test_the_http_hub_client_turns_a_transport_error_into_hub_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = gw.HttpHubClient("http://127.0.0.1:8787",
                              transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(gw.HubUnavailable):
            await client.call_tool("hub_list_docsets", {})
    finally:
        await client.aclose()
