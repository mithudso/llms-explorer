import json

import pytest
from starlette.testclient import TestClient
from test_protocol import READ, WRITE, rpc
from test_store_core import Database

from research_library_service.mcp_server import create_server, http_app
from research_library_service.service import Service
from research_library_service.store import LibraryStore


def content(response):
    assert response.status_code == 200
    result = response.json()["result"]
    assert not result.get("isError"), result
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def test_new_capabilities_are_denied_before_database_initialization():
    service = Service(config={}, bridge={})
    for operation in ("run_create", "run_checkpoint", "run_item_put", "run_lease",
                      "artifact_put", "artifact_index", "compile", "run_provision"):
        with pytest.raises(PermissionError):
            service.dispatch(operation, {}, role="read")
    assert service._store is None and service._runs is None
    for operation in ("_archive_artifact", "index_artifacts", "drop_collection"):
        with pytest.raises(ValueError):
            service.dispatch(operation, {}, role="write")
    assert service._store is None


def test_native_mcp_runs_artifacts_and_client_labels_remain_unqualified():
    store = LibraryStore(Database())
    service = Service(store=store, config={}, bridge={})
    application = http_app(create_server(service), READ, WRITE, allowed_hosts=["testserver"])
    with TestClient(application) as client:
        tools = rpc(client, READ, "tools/list").json()["result"]["tools"]
        definitions = {row["name"]: row for row in tools}
        assert definitions["research_run_get"]["annotations"]["readOnlyHint"]
        assert not definitions["research_compile"]["annotations"]["readOnlyHint"]
        assert "_archive_artifact" not in definitions
        assert store.database.list_collection_names() == []
        denied = rpc(client, READ, "tools/call", {"name": "research_run_create", "arguments": {
            "mode": "full-suite", "subject": "Fixture", "prompt": "A scoped fixture",
            "owner": "fixture", "request_id": "fixture-create"}})
        assert denied.json()["result"]["isError"]
        assert store.database.list_collection_names() == []
        created = content(rpc(client, WRITE, "tools/call", {
            "name": "research_run_create", "arguments": {
                "mode": "full-suite", "subject": "Fixture", "prompt": "A scoped fixture",
                "owner": "fixture", "options": {"threshold": 3.0},
                "request_id": "fixture-create"}}))
        run, token = created["run"], created["lease_token"]
        assert created["lease"]["owner"] == "mcp:fixture"
        assert service.runs.run_versions.find_one({"run_id": run["_id"]})["actor"] == "mcp-writer"
        saved = content(rpc(client, WRITE, "tools/call", {
            "name": "research_artifact_put", "arguments": {
                "run_id": run["_id"], "name": "report.json", "kind": "gate-result",
                "text": "Unicode fixture: café 🧪", "metadata": {"verdict": "SUPPORTED"},
                "expected_revision": run["revision"], "lease_token": token,
                "owner": "fixture", "request_id": "fixture-artifact"}}))
        artifact = saved["artifact"]
        assert artifact["trusted_provenance"] is False
        assert artifact["qualification"]["status"] == "unverified"
        page = content(rpc(client, READ, "tools/call", {
            "name": "research_artifact_get", "arguments": {"artifact_id": artifact["_id"]}}))
        assert page["text"] == "Unicode fixture: café 🧪"
        listed = content(rpc(client, READ, "tools/call", {
            "name": "research_run_list", "arguments": {"mode": "full-suite", "limit": 1}}))
        assert len(listed["runs"]) == 1
        assert token not in json.dumps(listed)
        assert not store.concepts.count_documents({})
        assert not store.queue.count_documents({})
