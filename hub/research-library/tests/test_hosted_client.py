"""The distributable client must work without loading the local service package."""

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

CLIENT_PATH = Path(__file__).parents[1] / "client" / "library_client.py"
spec = importlib.util.spec_from_file_location("standalone_hosted_client", CLIENT_PATH)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
SECRET = "private-token-never-echo"
PIN = "a" * 64
GUIDE_SHA256 = hashlib.sha256(SECRET.encode("utf-8")).hexdigest()


class Response:
    def __init__(self, body=b"", *, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, size):
        self.read_sizes.append(size)
        return self.body[:size]


class Opener:
    def __init__(self, result=None):
        self.requests = []
        self.result = result

    def open(self, request, timeout):
        packet = json.loads(request.data)
        self.requests.append((request, timeout, packet))
        if packet["method"] == "notifications/initialized":
            return Response(status=202)
        if packet["method"] == "initialize":
            result = {"protocolVersion": "2025-03-26"}
        else:
            result = self.result or {"tools": [{"name": "skill_search"}]}
        return Response(json.dumps({"jsonrpc": "2.0", "id": packet["id"],
                                    "result": result}).encode())


def transport(opener=None, **kwargs):
    return client.HostedClient("skills", "https://example.test/mcp", {"Authorization": SECRET},
                               opener=opener or Opener(), **kwargs)


def healthy(hits=None):
    return {"hits": hits or [], "semantic": True, "degraded": False,
            "diagnostics": {"channels": {"semantic": {"ok": True}}}}


def test_standalone_help_without_site_packages(tmp_path):
    distributed = tmp_path / "library_client.py"
    distributed.write_bytes(CLIENT_PATH.read_bytes())
    completed = subprocess.run([sys.executable, "-I", "-S", str(distributed), "--help"],
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0 and "smoke-test" in completed.stdout
    assert not completed.stderr


@pytest.mark.parametrize("url", [
    "http://example.test/mcp", "https://user:password@example.test/mcp",
    "https://user@example.test/mcp", "https://example.test/mcp#secret",
    "https://example.test/mcp#", "file:///private/token", "https://example.test\n/mcp",
    "https://example.test:invalid/mcp", "https:///mcp", "http://127.0.0.1.example.test/mcp",
])
def test_unsafe_endpoints_rejected_without_echo(url):
    with pytest.raises(client.ClientError) as error:
        client._valid_url(url)
    assert url not in str(error.value)
    assert "password" not in str(error.value)


@pytest.mark.parametrize("url", ["https://example.test/mcp", "http://localhost:9000/mcp",
                                 "http://127.0.0.2/mcp", "http://[::1]:9000/mcp"])
def test_tls_and_loopback_endpoints(url):
    assert client._valid_url(url) == url


@pytest.mark.parametrize("timeout", [0, 60.1, True, float("nan"), float("inf"), "10"])
def test_timeout_bounds(timeout):
    with pytest.raises(client.ClientError):
        transport(timeout=timeout)


def test_default_environment_is_service_specific_and_does_not_load_config(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text("not valid toml")
    monkeypatch.chdir(tmp_path)
    url, headers = client.connection_settings("skills", environ={"SKILL_MCP_TOKEN": SECRET})
    assert url == "https://skills-mcp.llms-explorer.com/mcp"
    assert headers == {"authorization": "Bearer " + SECRET}
    url, _ = client.connection_settings("research", environ={"RESEARCH_MCP_TOKEN": SECRET})
    assert url == "https://research-mcp.llms-explorer.com/mcp"
    with pytest.raises(client.ClientError):
        client.connection_settings("research", environ={"RESEARCH_MCP_WRITE_TOKEN": SECRET})


def test_explicit_config_selects_both_entries_and_literal_credentials(tmp_path):
    literal = "$(never-execute)${NO_INTERPOLATION}"
    (tmp_path / "config.toml").write_text(f'''
[mcp_servers.skills_mongodb]
url = "https://skills.example/mcp"
http_headers = {{ Authorization = "Bearer {literal}" }}
[mcp_servers.research-library]
url = "https://research.example/mcp"
bearer_token_env_var = "TEAM_RESEARCH"
env_http_headers = {{ "X-Team" = "TEAM_NAME" }}
role = "admin"
''')
    skills_url, headers = client.connection_settings("skills", tmp_path, environ={})
    assert skills_url == "https://skills.example/mcp"
    assert headers == {"authorization": "Bearer " + literal}
    research_url, headers = client.connection_settings("research", tmp_path, environ={
        "TEAM_RESEARCH": SECRET, "TEAM_NAME": "co-workers"})
    assert research_url == "https://research.example/mcp"
    assert headers == {"authorization": "Bearer " + SECRET, "x-team": "co-workers"}


@pytest.mark.parametrize("entry", [
    'url = "https://example.test/mcp"',
    'command = "python3"',
    'url = "https://example.test/mcp"\nenabled = false',
    'url = "https://example.test/mcp"\nbearer_token_env_var = "MISSING"',
    'url = "https://example.test/mcp"\nenv_http_headers = {Authorization = "MISSING"}',
    'url = "https://example.test/mcp"\nhttp_headers = {Authorization = 42}',
    'url = "https://example.test/mcp"\nhttp_headers = {Host = "secret"}',
    'url = "https://example.test/mcp"\nhttp_headers = {"MCP-Session-Id" = "secret"}',
    'url = "https://example.test/mcp"\nbearer_token_env_var = "TOKEN"\n'
    'http_headers = {Authorization = "secret"}',
    'url = "https://example.test/mcp"\nhttp_headers = {Authorization = "secret"}\n'
    'env_http_headers = {authorization = "TOKEN"}',
    'url = "https://example.test/mcp"\nenv_http_headers = {Authorization = "$(secret)"}',
])
def test_bad_config_rejected_without_default_credential_fallback(tmp_path, entry):
    (tmp_path / "config.toml").write_text("[mcp_servers.skills_mongodb]\n" + entry)
    with pytest.raises(client.ClientError) as error:
        client.connection_settings("skills", tmp_path, environ={
            "SKILL_MCP_TOKEN": SECRET, "TOKEN": SECRET})
    assert SECRET not in str(error.value) and "https://" not in str(error.value)


@pytest.mark.parametrize("headers", [
    {"Authorization": "Bearer\r\nsecret"}, {"bad\nheader": SECRET},
    {"Authorization": SECRET, "authorization": "second"}, {"Content-Length": "1"},
    {"Authorization": ""}, {"Authorization": "secret\u2603"},
])
def test_header_injection_and_duplicates_rejected(headers):
    with pytest.raises(client.ClientError):
        transport().headers = client._headers(headers)


def test_negotiation_initialized_notification_and_read_only_calls():
    opener = Opener({"structuredContent": healthy()})
    service = transport(opener)
    assert service.call("skill_search", {"query": "routing", "mode": "semantic"})["semantic"]
    assert [packet["method"] for _, _, packet in opener.requests] == [
        "initialize", "notifications/initialized", "tools/call"]
    request, timeout, notification = opener.requests[1]
    assert request.get_header("Mcp-protocol-version") == "2025-03-26"
    assert "id" not in notification and timeout == 30.0
    assert opener.requests[-1][0].get_header("Authorization") == SECRET
    service.call("skills_status", {})
    assert len(opener.requests) == 4


@pytest.mark.parametrize("configured", [None, "team-library-client/2.0"])
def test_descriptive_user_agent_is_sent_on_every_mcp_request(configured):
    opener = Opener()
    headers = {"Authorization": SECRET}
    if configured:
        headers["User-Agent"] = configured
    hosted = client.HostedClient("skills", "https://example.test/mcp", headers, opener=opener)
    hosted.tools()
    assert [request.get_header("User-agent") for request, _, _ in opener.requests] == [
        configured or "hosted-library-client/1.0"] * 3


def test_mcp_json_text_wrapper_and_inventory():
    opener = Opener({"content": [{"type": "text", "text": json.dumps(healthy())}]})
    assert transport(opener).call("skill_search", {}) == healthy()
    assert transport().tools() == [{"name": "skill_search"}]


@pytest.mark.parametrize("result", [
    {"isError": True, "content": [{"type": "text", "text": SECRET}]},
    {"structuredContent": [SECRET]}, {"content": [{"type": "text", "text": SECRET}]},
    {"content": [{"type": "text", "text": json.dumps([SECRET])}]},
    {"content": "secret"}, {"content": []},
])
def test_mcp_error_wrappers_do_not_echo_server_content(result):
    with pytest.raises(client.ClientError) as error:
        transport(Opener(result)).call("skill_search", {})
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("service,name", [
    ("skills", "skill_publish"), ("research", "research_concept_create"),
    ("research", "research_queue_put"), ("research", "research_finalize"),
    ("research", "research_lease_acquire"), ("skills", "research_status"),
])
def test_writer_credentials_never_enable_mutation_or_other_service(service, name):
    opener = Opener()
    hosted = client.HostedClient(service, "https://example.test/mcp", {"Authorization": SECRET},
                                 opener=opener)
    with pytest.raises(client.ClientError):
        hosted.call(name, {"role": "admin"})
    assert not opener.requests


@pytest.mark.parametrize("result", [
    {"semantic": False, "hits": [{"match_kind": "exact"}]},
    {"semantic": True, "diagnostics": {"channels": {"semantic": {"ok": False}}}},
    {"semantic": True, "diagnostics": {"channels": {}}},
    {**healthy(), "degraded": True}, {**healthy(), "semantic": 1},
    {key: value for key, value in healthy().items() if key != "degraded"},
    {**healthy(), "degraded": 0}, {**healthy(), "degraded": None},
    {**healthy(), "degraded": "false"},
])
def test_semantic_evidence_rejects_exact_or_fallback_results(result):
    with pytest.raises(client.ClientError):
        client.require_semantic(result)


def test_empty_semantic_result_is_healthy_when_channel_succeeded():
    client.require_semantic(healthy())


@pytest.mark.parametrize("kind", ["oversize", "length", "status", "invalid-json", "rpc-error",
                                  "rpc-id", "rpc-list", "network"])
def test_bounded_http_failures_have_sanitized_errors(kind):
    class Broken:
        def open(self, request, timeout):
            if kind == "network":
                raise OSError("https://user:" + SECRET + "@private.example/ " + SECRET)
            if kind == "oversize":
                return Response(b"s" * (client.MAX_RESPONSE_BYTES + 1))
            if kind == "length":
                return Response(headers={"Content-Length": str(client.MAX_RESPONSE_BYTES + 1)})
            if kind == "status":
                return Response(SECRET.encode(), status=401)
            if kind == "invalid-json":
                return Response(SECRET.encode())
            if kind == "rpc-list":
                return Response(json.dumps([SECRET]).encode())
            return Response(json.dumps({"jsonrpc": "2.0", "id": 99 if kind == "rpc-id" else 1,
                                        "result": {}, **({"error": SECRET}
                                                         if kind == "rpc-error" else {})}).encode())
    with pytest.raises(client.ClientError) as error:
        transport(Broken()).tools()
    assert SECRET not in str(error.value) and "private.example" not in str(error.value)


@contextmanager
def server(handler):
    instance = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_never_forwards_credentials(status):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            received.append((self.path, self.headers.get("Authorization")))
            self.send_response(status)
            self.send_header("Location", "/must-not-be-called?" + SECRET)
            self.end_headers()

        def do_GET(self):
            received.append((self.path, self.headers.get("Authorization")))
            self.send_response(200)
            self.end_headers()

    with server(Handler) as running:
        hosted = client.HostedClient("skills", f"http://127.0.0.1:{running.server_port}/mcp",
                                     {"Authorization": SECRET})
        with pytest.raises(client.ClientError) as error:
            hosted.tools()
    assert received == [("/mcp", SECRET)]
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("semantic", [True, False])
def test_distributed_standalone_executes_native_json_http_without_dependencies(tmp_path, semantic):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            packet = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((packet, self.headers.get("Authorization")))
            if packet["method"] == "notifications/initialized":
                self.send_response(202)
                self.end_headers()
                return
            if packet["method"] == "initialize":
                result = {"protocolVersion": client.PROTOCOL_VERSION}
            else:
                result = {"structuredContent": {**healthy(), "semantic": semantic}}
            body = json.dumps({"jsonrpc": "2.0", "id": packet["id"], "result": result}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    distributed = tmp_path / "library_client.py"
    distributed.write_bytes(CLIENT_PATH.read_bytes())
    with server(Handler) as running:
        (tmp_path / "config.toml").write_text(
            '[mcp_servers.skills_mongodb]\n'
            f'url = "http://127.0.0.1:{running.server_port}/mcp"\n'
            f'http_headers = {{ Authorization = "Bearer {SECRET}" }}\n')
        completed = subprocess.run([
            sys.executable, "-I", "-S", str(distributed), "--codex-home", str(tmp_path),
            "skills", "search", "research-library-mongodb", "--mode", "semantic",
        ], capture_output=True, text=True, check=False)
    assert completed.returncode == (0 if semantic else 2)
    assert [packet["method"] for packet, _ in requests] == [
        "initialize", "notifications/initialized", "tools/call"]
    assert all(auth == "Bearer " + SECRET for _, auth in requests)
    assert SECRET not in completed.stdout + completed.stderr
    if semantic:
        assert json.loads(completed.stdout)["semantic"] is True
    else:
        assert not completed.stdout


class SmokeService:
    def __init__(self, service):
        self.service = service
        self.calls = []

    def tools(self):
        return [{"name": "metadata"}] * (5 if self.service == "skills" else 27)

    def call(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "research_status":
            return {"private_body": SECRET}
        if name in {"skill_search", "research_search"}:
            return healthy([{"id": "skill:guide", "name": "research-library-mongodb",
                             "release_sha256": PIN, "sha256": GUIDE_SHA256,
                             "description": SECRET}])
        return {"release_sha256": PIN, "text": SECRET, "truncated": False,
                "next_offset": None, "sha256": GUIDE_SHA256, "resource_sha256": GUIDE_SHA256}


def test_smoke_tests_real_semantic_search_both_services_and_pinned_reads():
    skills, research = SmokeService("skills"), SmokeService("research")
    report = client.smoke_test(skills, research)
    assert report["verdict"] == "passed"
    assert report["native_startup_tested"] is False
    assert (report["record_writes"] == report["research_provider_calls"]
            == report["llm_research_turns"] == 0)
    assert report["skills"]["guide_sha256"] == GUIDE_SHA256
    assert SECRET not in json.dumps(report)
    assert [args["mode"] for name, args in skills.calls if name == "skill_search"] == [
        "hybrid", "semantic"]
    assert [args["mode"] for name, args in research.calls if name == "research_search"] == [
        "semantic"]
    assert skills.calls[-1] == ("skill_resource", {
        "skill_id": "skill:guide", "path": "SKILL.md", "expected_sha256": PIN,
        "max_chars": 32000})
    assert all(name in client.READ_TOOLS["skills"] for name, _ in skills.calls)
    assert all(name in client.READ_TOOLS["research"] for name, _ in research.calls)


def test_sk_smoke_requires_new_api_and_only_reads_run_inventory():
    class Runs(SmokeService):
        def tools(self):
            names = set(client.READ_TOOLS[self.service])
            if self.service == "research":
                names |= {"research_run_create", "research_run_checkpoint", "research_run_item_put",
                          "research_run_lease", "research_artifact_put", "research_artifact_index",
                          "research_compile"}
            return [{"name": name} for name in names] + super().tools()

        def call(self, name, arguments):
            if name == "research_run_list":
                self.calls.append((name, arguments))
                return {"runs": []}
            return super().call(name, arguments)

    skills, research = Runs("skills"), Runs("research")
    report = client.smoke_test(skills, research, require_sk=True)
    assert report["sk"]["run_inventory_read"]
    assert research.calls[-1] == ("research_run_list", {"limit": 1})
    assert all(name in client.READ_TOOLS["research"] for name, _ in research.calls)
    with pytest.raises(client.ClientError, match="sk run and artifact API"):
        client.smoke_test(SmokeService("skills"), SmokeService("research"), require_sk=True)


@pytest.mark.parametrize("failure", [
    "semantic", "pin", "truncated", "wrong-body", "inventory",
    "hit-sha256", "guide-sha256", "resource-sha256",
])
def test_smoke_fails_closed(failure):
    class Bad(SmokeService):
        def tools(self):
            return [] if failure == "inventory" else super().tools()

        def call(self, name, arguments):
            result = super().call(name, arguments)
            if name == "research_search" and failure == "semantic":
                result["semantic"] = False
            if name == "skill_get" and failure == "pin":
                result["release_sha256"] = "b" * 64
            if name == "skill_get" and failure == "truncated":
                result["truncated"] = True
            if name == "skill_resource" and failure == "wrong-body":
                result["text"] = "different guide"
            if name == "skill_search" and failure == "hit-sha256":
                result["hits"][0]["sha256"] = "b" * 64
            if name == "skill_get" and failure == "guide-sha256":
                result["sha256"] = "b" * 64
            if name == "skill_resource" and failure == "resource-sha256":
                result["resource_sha256"] = "b" * 64
            return result
    with pytest.raises(client.ClientError):
        client.smoke_test(Bad("skills"), Bad("research"))


def factory(monkeypatch, result=None):
    monkeypatch.setenv("SKILL_MCP_TOKEN", SECRET)
    monkeypatch.setenv("RESEARCH_MCP_TOKEN", SECRET)
    instances = []

    class Fake:
        def __init__(self, service, url, headers, **kwargs):
            self.calls = []
            self.service = service
            instances.append(self)

        def call(self, name, arguments):
            self.calls.append((name, arguments))
            return healthy() if result is None else result

    return Fake, instances


def test_named_search_scopes_and_modes(monkeypatch, capsys):
    fake, instances = factory(monkeypatch)
    assert client.main(["research", "search", "Atlas", "--mode", "keyword", "--top", "7",
                        "--topic-id", "c:atlas", "--breadth", "narrow"], client_factory=fake) == 0
    assert instances[0].calls == [("research_search", {
        "query": "Atlas", "mode": "keyword", "top": 7, "topic_id": "c:atlas",
        "breadth": "narrow"})]
    capsys.readouterr()
    assert client.main(["skills", "search", "routing", "--mode", "lexical"],
                       client_factory=fake) == 0
    assert instances[1].calls[0][0] == "skill_search"


@pytest.mark.parametrize("flags", [["--mode", "semantic"], ["--require-semantic"]])
def test_search_strict_semantic_failure_prints_no_fallback_results(monkeypatch, capsys, flags):
    fake, _ = factory(monkeypatch, {"semantic": False, "hits": [{"private": SECRET}]})
    assert client.main(["skills", "search", "guide", *flags], client_factory=fake) == 2
    captured = capsys.readouterr()
    assert not captured.out and SECRET not in captured.err


def test_call_reads_bounded_json_and_rejects_mutation_before_connect(monkeypatch, capsys):
    fake, instances = factory(monkeypatch)
    assert client.main(["call", "--service", "research", "research_status"],
                       client_factory=fake, input_stream=io.StringIO("{}")) == 0
    assert instances[0].calls == [("research_status", {})]
    capsys.readouterr()
    assert client.main(["call", "--service", "research", "research_finalize", "--arguments", "{}"],
                       client_factory=fake) == 2
    assert len(instances) == 1


@pytest.mark.parametrize("argv", [
    ["--role", SECRET, "skills", "search", "guide"],
    ["skills", "search", "guide", "--mode", SECRET],
    ["research", "search", "guide", "--breadth", "narrow"],
    ["skills", "search", "guide", "--top", "21"],
    ["call", "--service", "research", "research_status", "--arguments", SECRET],
])
def test_cli_validation_never_echoes_invalid_values(monkeypatch, capsys, argv):
    fake, _ = factory(monkeypatch)
    assert client.main(argv, client_factory=fake) == 2
    captured = capsys.readouterr()
    assert not captured.out and SECRET not in captured.err
    assert json.loads(captured.err)["error"] == "HostedClientError"
