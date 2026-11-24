import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient
from test_protocol import READ, WRITE, rpc
from test_store_core import Database

from research_library_service import cli, writer_request
from research_library_service.mcp_server import BearerAuth, create_server, http_app
from research_library_service.service import Service
from research_library_service.store import LibraryStore

PROVISION = "test-issuer-" + "p" * 48


@pytest.fixture
def enrollment():
    clock = [1000.0]
    store = LibraryStore(Database(), clock=lambda: clock[0])
    service = Service(store=store, config={}, bridge={})
    app = http_app(create_server(service), READ, WRITE, allowed_hosts=["testserver"],
                   provision_token=PROVISION, service=service)
    with TestClient(app) as client:
        yield service, client, clock


def call(client, token, name, args):
    response = rpc(client, token, "tools/call", {"name": name, "arguments": args})
    assert response.status_code == 200
    return response.json()["result"]


def headers(token):
    return {"Authorization": "Bearer " + token}


def test_recipient_cli_exclusive_private_file_and_standalone(tmp_path, capsys):
    path = tmp_path / "private"
    assert cli.main(["writer-prepare", "--token-file", str(path)]) == 0
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    token = path.read_text().strip()
    out = json.loads(capsys.readouterr().out)
    assert out == {"credential_id": hashlib.sha256(token.encode()).hexdigest()}
    assert cli.main(["writer-prepare", "--token-file", str(path)]) != 0
    assert path.read_text().strip() == token and token not in capsys.readouterr().err
    link = tmp_path / "link"
    link.symlink_to(path)
    command = [sys.executable, "-IS", str(Path(writer_request.__file__)), "--token-file"]
    second = tmp_path / "second"
    run = subprocess.run([*command, second], capture_output=True, text=True, check=True)
    assert list(json.loads(run.stdout)) == ["credential_id"] and not run.stderr
    assert subprocess.run([*command, link], capture_output=True).returncode != 0
    assert path.read_text().strip() == token


def test_remote_grant_writer_actor_revocation_and_denials(enrollment, tmp_path):
    service, client, _ = enrollment
    path = tmp_path / "recipient"
    args = {"name": "lab", **writer_request.prepare_writer(path)}
    token = path.read_text().strip()
    for denied in [READ, WRITE]:
        assert client.post("/v1/writers", headers=headers(denied), json=args).status_code == 403
        assert call(client, denied, "research_writer_grant", args)["isError"]
    assert service.store.database.list_collection_names() == []
    assert rpc(client, token, "tools/list").status_code == 401
    assert call(client, PROVISION, "research_status", {})["isError"]
    assert call(client, PROVISION, "research_concept_create", {"name": "fixture"})["isError"]
    for override in [{"Origin": "https://example.invalid"}, {"Host": "example.invalid"}]:
        assert client.post("/v1/writers", headers={**headers(PROVISION), **override},
                           json=args).status_code in {403, 421}
    response = client.post("/v1/writers", headers=headers(PROVISION), json=args)
    assert response.status_code == 201 and token not in response.text
    assert call(client, PROVISION, "research_writer_grant", args)["structuredContent"] == response.json()
    # The enrollment fingerprint is safe to share and cannot authenticate a request.
    assert rpc(client, args["credential_id"], "tools/list").status_code == 401
    created = call(client, token, "research_run_create", {
        "mode": "full-suite", "subject": "Graph paths", "prompt": "Compare paths",
        "owner": "fixture", "request_id": "named-writer-run"})
    assert not created.get("isError")
    receipt = service.store.receipts.find_one({"request_id": "named-writer-run"})
    assert receipt["actor"] == "mcp-writer:lab"
    assert call(client, token, "research_writer_grant", args)["isError"]
    assert client.delete("/v1/writers/" + args["credential_id"],
                         headers=headers(token)).status_code == 403
    revoked = call(client, PROVISION, "research_writer_revoke",
                   {"credential_id": args["credential_id"]})["structuredContent"]
    assert revoked["revoked"] and rpc(client, token, "tools/list").status_code == 401
    assert client.post("/v1/writers", headers=headers(PROVISION), json=args).status_code == 409
    docs = list(service.writers.rows.find({}))
    assert len(docs) == 1 and token not in str(docs) and docs[0]["revoked_by"] == "mcp-provisioner"


def test_expiry_duplicate_name_replacement_and_local_cli(enrollment, tmp_path, capsys):
    service, client, clock = enrollment
    path = tmp_path / "recipient"
    fingerprint = writer_request.prepare_writer(path)["credential_id"]
    grant = ["writer-grant", "trial", fingerprint, "--valid-days", "1"]
    for local_role in ["read", "write"]:
        assert cli.main(["--role", local_role, *grant], service=service) != 0
        capsys.readouterr()
    assert cli.main(grant, service=service) == 0
    start = json.loads(capsys.readouterr().out)
    clock[0] += 10
    assert cli.main(grant, service=service) == 0
    assert json.loads(capsys.readouterr().out) == start
    token = path.read_text().strip()
    assert rpc(client, token, "tools/list").status_code == 200
    args = {"name": "trial", **writer_request.prepare_writer(tmp_path / "replacement")}
    assert client.post("/v1/writers", headers=headers(PROVISION), json=args).status_code == 409
    clock[0] = start["expires_at"]
    assert rpc(client, token, "tools/list").status_code == 401
    assert client.post("/v1/writers", headers=headers(PROVISION), json=args).status_code == 201
    assert cli.main(grant, service=service) != 0
    assert client.delete("/v1/writers/" + args["credential_id"], headers=headers(PROVISION)).status_code == 200
    assert cli.main(["writer-revoke", fingerprint], service=service) == 0
    assert rpc(client, token, "tools/list").status_code == 401


def test_invalid_grants_and_shared_provision_token(enrollment):
    _, client, _ = enrollment
    args = {"name": "trial", "credential_id": "0" * 64}
    for change in [{"credential_id": "wrong"}, {"name": "admin role"}, {"valid_days": 0},
                   {"valid_days": 91}, {"valid_days": True}, {"actor": "spoofed"}]:
        assert client.post("/v1/writers", headers=headers(PROVISION),
                           json={**args, **change}).status_code == 400
    with pytest.raises(ValueError):
        BearerAuth(None, READ, WRITE, provision_token=WRITE)


def test_managed_only_deployment_and_verification_outage(enrollment, tmp_path):
    service, _, _ = enrollment
    path = tmp_path / "managed-only"
    grant = writer_request.prepare_writer(path)
    service.dispatch("writer_grant", {"name": "solo", **grant}, role="admin")
    token = path.read_text().strip()
    server = create_server(service)
    app = http_app(server, allowed_hosts=["testserver"], service=service, named_writers=True)
    with TestClient(app) as client:
        assert rpc(client, token, "tools/list").status_code == 200
        assert rpc(client, READ, "tools/list").status_code == 401
        service.store.database.fail = lambda name, op: name.endswith("writer_credentials")
        assert rpc(client, token, "tools/list").status_code == 503
        assert rpc(client, grant["credential_id"], "tools/list").status_code == 401
    # Older reader-only hosts do not begin accepting managed writers after a deploy.
    with TestClient(http_app(create_server(service), READ, allowed_hosts=["testserver"])) as client:
        assert rpc(client, token, "tools/list").status_code == 401
        assert rpc(client, READ, "tools/list").status_code == 200


@pytest.mark.parametrize("path", ["/v1/writers", "/mcp"])
@pytest.mark.parametrize("duplicate", ["Authorization", "Host", "Origin"])
def test_ambiguous_security_headers_rejected_on_both_routes(enrollment, path, duplicate):
    _, client, _ = enrollment
    values = {"Authorization": "Bearer " + PROVISION, "Host": "testserver", "Origin": ""}
    request_headers = list(values.items()) + [(duplicate, values[duplicate])]
    response = client.post(path, headers=request_headers, json={})
    assert response.status_code == 400 and response.json()["error"] == "ambiguous security header"
