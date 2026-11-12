from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from starlette.testclient import TestClient

from research_library_service.mcp_server import AUTH, BearerAuth, create_server, http_app
from research_library_service.service import MAX_REQUEST_BYTES, Service

READ = "reader-" + "r" * 48
WRITE = "writer-" + "w" * 48


class Store:
    def __init__(self):
        self.calls = []

    def status(self):
        return {"ready": True}

    def concept_get(self, concept_id, revision=None):
        time.sleep(0.005)
        principal = AUTH.get()
        return {"id": concept_id, "role_seen": principal.role}

    def source_lookup(self, url):
        return {"found": True, "source_id": "src:1234567890abcdef", "url": url,
                "source": {"revision": 3, "deleted": False},
                "snapshot_available": True, "role_seen": AUTH.get().role}

    def concept_create(self, name, slug=None, description="", aliases=None, terms=None,
                       request_id="", actor="agent"):
        time.sleep(0.005)
        principal = AUTH.get()
        self.calls.append((name, actor, principal.role))
        return {"id": "c:created", "actor": actor, "role_seen": principal.role}

    def lease_acquire(self, concept_ids, owner, ttl_seconds=900, run_id="", request_id="",
                      actor="agent"):
        self.calls.append((owner, run_id, actor))
        return {"owner": owner, "tokens": {"c:example": "private-lease-proof"}}


def rpc(client, token, method, params=None):
    return client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {},
    }, headers={"Authorization": "Bearer " + token,
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18"})


@pytest.fixture
def application():
    store = Store()
    server = create_server(Service(store=store, config={}, bridge={}))
    return http_app(server, READ, WRITE, allowed_hosts=["testserver"]), store


def test_native_protocol_tools_annotations_and_actual_roles(application):
    app, store = application
    with TestClient(app) as client:
        unauthorized = rpc(client, "existing-skill-reader-" + "x" * 40, "tools/list")
        assert unauthorized.status_code == 401
        assert "no-store" in unauthorized.headers["cache-control"]
        initialized = rpc(client, READ, "initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "research-test", "version": "1"},
        })
        assert initialized.status_code == 200 and "error" not in initialized.json()
        listed = rpc(client, READ, "tools/list")
        tools = {t["name"]: t for t in listed.json()["result"]["tools"]}
        assert {"research_search", "research_frontier", "research_incomplete",
                "research_lease_acquire", "research_claim_mutate", "research_relation_mutate",
                "research_finalize", "research_publication_status",
                "research_source_lookup"} <= tools.keys()
        lookup_schema = tools["research_source_lookup"]
        assert lookup_schema["annotations"]["readOnlyHint"] is True
        assert lookup_schema["inputSchema"]["required"] == ["url"]
        assert tools["research_search"]["annotations"]["readOnlyHint"] is True
        assert tools["research_concept_create"]["annotations"]["readOnlyHint"] is False
        assert "research_coordinate" not in tools
        forbidden = rpc(client, READ, "tools/call", {
            "name": "research_concept_create", "arguments": {"name": "forbidden"},
        }).json()["result"]
        assert forbidden["isError"] is True and store.calls == []
        result = rpc(client, WRITE, "tools/call", {
            "name": "research_concept_create", "arguments": {"name": "allowed"},
        }).json()["result"]
        assert not result.get("isError")
        assert result["structuredContent"]["role_seen"] == "write"
        assert result["structuredContent"]["actor"] == "mcp-writer"
        assert store.calls == [("allowed", "mcp-writer", "write")]
        assert "no-store" in listed.headers["cache-control"]


def test_reader_can_lookup_exact_source_metadata_without_body_or_write(application):
    app, store = application
    with TestClient(app) as client:
        result = rpc(client, READ, "tools/call", {
            "name": "research_source_lookup", "arguments": {"url": "https://example.org/ref"},
        }).json()["result"]
        assert not result.get("isError")
        metadata = result["structuredContent"]
        assert metadata["found"] and metadata["snapshot_available"]
        assert metadata["source"]["revision"] == 3 and metadata["role_seen"] == "read"
        assert "text" not in metadata and store.calls == []


def test_remote_lease_owner_cannot_impersonate_local_legacy_holder(application):
    app, store = application
    with TestClient(app) as client:
        result = rpc(client, WRITE, "tools/call", {
            "name": "research_lease_acquire", "arguments": {
                "concept_ids": ["c:example"], "owner": "legacy:protected-run",
                "run_id": "protected-run",
            },
        }).json()["result"]
        assert result["structuredContent"]["owner"] == "mcp:legacy:protected-run"
        assert store.calls == [("mcp:legacy:protected-run", "protected-run", "mcp-writer")]


def test_finalize_owner_namespace_is_applied_before_trusted_callback():
    calls = []

    def publish(store, concept_id, expected_revision, lease_token, owner, actor, request_id=""):
        calls.append((owner, actor))
        return {"job_id": "publication-1"}

    server = create_server(Service(store=Store(), config={}, bridge={"publish": publish}))
    with TestClient(http_app(server, READ, WRITE, allowed_hosts=["testserver"])) as client:
        result = rpc(client, WRITE, "tools/call", {
            "name": "research_finalize", "arguments": {
                "concept_id": "c:example", "expected_revision": 1,
                "lease_token": "opaque", "owner": "agent",
            },
        }).json()["result"]
        assert not result.get("isError") and calls == [("mcp:agent", "mcp-writer")]


def test_parallel_requests_cannot_leak_write_capability_to_readers(application):
    app, store = application
    with TestClient(app) as client:
        def call(i):
            token = WRITE if i % 2 else READ
            method = "research_concept_create" if i % 2 else "research_concept_get"
            args = {"name": str(i)} if i % 2 else {"concept_id": "c:example"}
            value = rpc(client, token, "tools/call", {
                "name": method, "arguments": args,
            }).json()["result"]
            assert not value.get("isError")
            return value["structuredContent"]["role_seen"]
        with ThreadPoolExecutor(max_workers=6) as executor:
            actual = list(executor.map(call, range(12)))
        assert actual == ["write" if i % 2 else "read" for i in range(12)]
        assert len(store.calls) == 6


def test_malformed_operators_are_rejected_before_backend_call(application):
    app, store = application
    with TestClient(app) as client:
        result = rpc(client, WRITE, "tools/call", {
            "name": "research_concept_update",
            "arguments": {"concept_id": "c:x", "patch": {"$set": {"state": "complete"}},
                          "expected_revision": 1, "lease_token": "opaque"},
        }).json()["result"]
        assert result["isError"] is True and store.calls == []


def test_sdk_rejects_unapproved_host_and_browser_origin(application):
    app, _ = application
    with TestClient(app) as client:
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        headers = {"Authorization": "Bearer " + READ,
                   "Accept": "application/json, text/event-stream"}
        response = client.post("/mcp", json=body, headers={**headers, "Host": "attacker.example"})
        assert response.status_code in {400, 403, 421}
        response = client.post("/mcp", json=body,
                               headers={**headers, "Origin": "https://attacker.example"})
        assert response.status_code in {400, 403, 421}


@pytest.mark.parametrize("read,write", [("short", ""), (READ, READ), ("x" * 31, WRITE),
                                         ("x" * 32 + "\x01", WRITE)])
def test_invalid_or_shared_capability_tokens_are_rejected(read, write):
    with pytest.raises(ValueError):
        BearerAuth(None, read, write)


def test_unauthenticated_request_body_is_never_read():
    async def app(scope, receive, send):
        raise AssertionError("Untrusted request must not reach MCP")
    async def receive():
        raise AssertionError("Untrusted body must not be read")
    sent = []
    async def send(message):
        sent.append(message)
    asyncio.run(BearerAuth(app, READ, WRITE)(
        {"type": "http", "headers": []}, receive, send))
    assert sent[0]["status"] == 401


def test_authorized_request_body_is_bounded_before_json_parsing():
    async def app(scope, receive, send):
        raise AssertionError("Oversized body must not reach MCP")
    chunks = iter([
        {"type": "http.request", "body": b"x" * MAX_REQUEST_BYTES, "more_body": True},
        {"type": "http.request", "body": b"x", "more_body": False},
    ])
    async def receive():
        return next(chunks)
    sent = []
    async def send(message):
        sent.append(message)
    asyncio.run(BearerAuth(app, READ, WRITE)(
        {"type": "http", "headers": [(b"authorization", ("Bearer " + WRITE).encode())]},
        receive, send))
    assert sent[0]["status"] == 413


def test_real_stdio_defaults_to_read_and_returns_structured_metadata(tmp_path):
    runner = tmp_path / "server.py"
    runner.write_text(
        "from research_library_service.mcp_server import create_server\n"
        "from research_library_service.service import Service\n"
        "class Store:\n"
        " def status(self): return {'from_store':True}\n"
        "create_server(Service(store=Store(),config={},bridge={})).run(transport='stdio')\n")

    async def scenario():
        async with stdio_client(StdioServerParameters(
                command=sys.executable, args=[str(runner)], cwd=str(tmp_path))) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                status = await session.call_tool("research_status", {})
                assert status.model_dump(by_alias=True)["structuredContent"]["from_store"]
                rejected = await session.call_tool("research_concept_create", {"name": "x"})
                assert rejected.model_dump(by_alias=True)["isError"]
    asyncio.run(asyncio.wait_for(scenario(), timeout=15))


def test_server_refuses_public_bind_and_does_not_reuse_old_skill_token():
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("RESEARCH_LIBRARY_")}
    environment["SKILL_MCP_TOKEN"] = "old-skill-reader-" + "x" * 48
    command = [sys.executable, "-m", "research_library_service.mcp_server",
               "--transport", "streamable-http"]
    result = subprocess.run(command + ["--host", "0.0.0.0"], env=environment,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2 and "--allow-remote" in result.stderr
    result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "capability tokens" in result.stderr and environment["SKILL_MCP_TOKEN"] not in result.stderr
