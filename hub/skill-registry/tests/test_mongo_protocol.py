import asyncio
import os
import subprocess
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from starlette.testclient import TestClient

from skill_registry.mongo_mcp import create_server, http_app

TOKEN = "a-test-bearer-token-with-at-least-32-characters"


class Store:
    def status(self):
        return {"skills": 1, "indexes_ready": True}

    def search(self, query, top=5, mode="hybrid"):
        if not 1 <= top <= 20:
            raise ValueError("Invalid top")
        return {"hits": [{"id": "db-only", "name": "example", "sha256": "a" * 64}],
                "mode": mode}

    def catalog(self, after="", limit=200):
        return {"skills": [{"id": "db-only", "name": "example", "sha256": "a" * 64,
                            "release_sha256": "b" * 64}], "has_more": False, "next_after": None}

    def load(self, skill_id, expected_sha256, offset=0, max_chars=16000):
        if expected_sha256 != "a" * 64:
            raise ValueError("Stale hash")
        return {"text": "DB-only workflow"[offset:offset + max_chars], "sha256": "a" * 64}

    def resource(self, skill_id, path, expected_sha256, offset=0, max_chars=16000):
        if path != "references/check.md":
            raise ValueError("Resource not found")
        return {"text": "Read from DB", "resource_sha256": "b" * 64}


def request(client, method, params=None, token=TOKEN):
    return client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method,
        "params": params or {}}, headers={"Authorization": "Bearer " + token,
        "Accept": "application/json, text/event-stream"})


def test_http_auth_readonly_tools_and_database_reads():
    with TestClient(http_app(create_server(Store()), TOKEN), base_url="http://localhost") as client:
        assert client.post("/mcp", json={}).status_code == 401
        rejected = request(client, "tools/list", token="wrong")
        assert rejected.status_code == 401
        assert TOKEN not in rejected.text
        assert rejected.headers["cache-control"] == "no-store"
        initialized = request(client, "initialize", {"protocolVersion": "2025-06-18",
            "capabilities": {}, "clientInfo": {"name": "independent", "version": "1"}})
        assert initialized.status_code == 200
        tools = request(client, "tools/list").json()["result"]["tools"]
        assert {tool["name"] for tool in tools} == {
            "skill_search", "skill_catalog", "skill_get", "skill_resource", "skills_status"}
        assert all(tool["annotations"]["readOnlyHint"] for tool in tools)
        result = request(client, "tools/call", {"name": "skill_search", "arguments": {
            "query": "example", "mode": "semantic"}})
        assert result.json()["result"]["structuredContent"]["mode"] == "semantic"
        assert result.headers["cache-control"] == "no-store"
        metadata = request(client, "tools/call", {"name": "skill_catalog", "arguments": {}})
        assert metadata.json()["result"]["structuredContent"]["skills"][0]["id"] == "db-only"
        loaded = request(client, "tools/call", {"name": "skill_get", "arguments": {
            "skill_id": "db-only", "expected_sha256": "a" * 64, "max_chars": 7}})
        assert loaded.json()["result"]["structuredContent"]["text"] == "DB-only"
        stale = request(client, "tools/call", {"name": "skill_get", "arguments": {
            "skill_id": "db-only", "expected_sha256": "bad"}})
        assert stale.json()["result"]["isError"]
        resource = request(client, "tools/call", {"name": "skill_resource", "arguments": {
            "skill_id": "db-only", "path": "references/check.md", "expected_sha256": "a" * 64}})
        assert resource.json()["result"]["structuredContent"]["text"] == "Read from DB"


def test_http_rejects_weak_token_and_untrusted_host():
    with pytest.raises(ValueError, match="32 characters"):
        http_app(create_server(Store()), "short")
    with TestClient(http_app(create_server(Store()), TOKEN), base_url="http://evil.test") as client:
        assert request(client, "tools/list").status_code == 421


def test_real_stdio_reads_without_local_skill_files(tmp_path):
    # This second process has a database-interface fixture and no skill tree.
    # Actual Atlas acceptance is separate from this deterministic protocol gate.
    runner = tmp_path / "server.py"
    runner.write_text("from skill_registry.mongo_mcp import create_server\n"
        "class Store:\n"
        " def search(self,query,top=5,mode='hybrid'):\n"
        "  return {'hits':[{'id':'db-only','sha256':'a'*64}]}\n"
        " def load(self,skill_id,expected_sha256,offset=0,max_chars=16000):\n"
        "  return {'text':'Workflow supplied from database'}\n"
        "create_server(Store()).run(transport='stdio')\n")

    async def scenario():
        async with stdio_client(StdioServerParameters(command=sys.executable,
            args=[str(runner)], cwd=str(tmp_path), env=dict(os.environ))) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                found = await session.call_tool("skill_search", {"query": "task"})
                hit = found.model_dump(by_alias=True)["structuredContent"]["hits"][0]
                loaded = await session.call_tool("skill_get", {
                    "skill_id": hit["id"], "expected_sha256": hit["sha256"]})
                assert loaded.model_dump(by_alias=True)["structuredContent"]["text"].endswith("database")
    asyncio.run(scenario())


def test_cli_mongo_help_does_not_connect():
    result = subprocess.run([sys.executable, "-m", "skill_registry.cli", "mongo", "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert "provision" in result.stdout and "watch" in result.stdout
    assert "Traceback" not in result.stderr


def test_explicit_environment_preserves_existing_values_and_literal_dollars(tmp_path, monkeypatch):
    from skill_registry.environment import load_environment
    path = tmp_path / "runtime.env"
    path.write_text("SKILL_EXAMPLE_LITERAL='${SHOULD_NOT_EXPAND}'\nSKILL_EXAMPLE_SET=file\n")
    monkeypatch.setenv("SKILL_EXAMPLE_SET", "process")
    monkeypatch.delenv("SKILL_EXAMPLE_LITERAL", raising=False)
    load_environment(path)
    assert os.environ["SKILL_EXAMPLE_LITERAL"] == "${SHOULD_NOT_EXPAND}"
    assert os.environ["SKILL_EXAMPLE_SET"] == "process"


def test_mongo_watch_validates_interval_without_entering_loop(monkeypatch, capsys, tmp_path):
    from skill_registry import cli
    monkeypatch.setattr(cli.Service, "mongo", lambda self: Store())
    monkeypatch.setattr(sys, "argv", ["skill-registry", "--state", str(tmp_path / "state"),
                                      "mongo", "watch", "--interval", "1"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert "watch interval" in capsys.readouterr().err
