import base64
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from skill_registry import remote_worker
from skill_registry.bundles import build_bundle, release_hash, validate_bundle
from skill_registry.client import Remote
from skill_registry.jobs import Jobs
from skill_registry.remote_worker import run_remote
from skill_registry.service import Service
from skill_registry.util import sha


@pytest.mark.parametrize("kind", ["document", "skill"])
@pytest.mark.parametrize("edit_after_verification", [False, True])
def test_hosted_transport_runs_bounded_owner_local_worker_and_reports_candidate(
        kind, edit_after_verification, skill, tmp_path, monkeypatch):
    source = "Original prose."
    manifest, archive = build_bundle(skill, "usr_owner", "example", "1.0.0")
    snapshot = ({"format": "text/v1", "text": source} if kind == "document" else {
        "format": "skill-release/v1", "manifest": manifest,
        "bundle_base64": base64.b64encode(archive).decode()})
    input_hash = (sha(source.encode()) if kind == "document" else release_hash(dict(
        manifest, namespace="local", name="optimization-input", version="0.0.0")))
    completed = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path.endswith("/claim"):
                reply = {"id": "job_fixture", "status": "running", "lease_token": "synthetic-lease-" * 3,
                         "input_snapshot": snapshot, "input_sha256": input_hash,
                         "artifact_type": kind, "timeout_seconds": 30, "max_iterations": 1,
                         "source_release_sha256": manifest["release_sha256"] if kind == "skill" else None}
            elif self.path.endswith("/heartbeat"):
                reply = {"id": "job_fixture", "status": "running"}
            else:
                completed.append(payload)
                reply = {"id": "job_fixture", "status": "done" if payload["exit_code"] == 0 else "failed"}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(reply).encode())

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"id":"job_fixture","status":"running"}')

        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    script = tmp_path / "configured_worker.py"
    script.write_text("from pathlib import Path\nimport sys\np=Path(sys.argv[1])\n" + (
        "p.write_text('A concrete revised sentence.')\n" if kind == "document" else
        "(p.parent/'references/guide.md').write_text('A revised condition.')\n"))
    service = Service(tmp_path / "state", {"roots": []})
    service.remote = lambda: Remote(f"http://127.0.0.1:{server.server_port}", "synthetic-token",
                                     service.state / "releases")
    if edit_after_verification:
        original_run = remote_worker.run_one
        def changed(*args, **kwargs):
            result = original_run(*args, **kwargs)
            candidate = service.state / "runs" / result["id"] / "candidate"
            path = candidate / ("artifact.txt" if kind == "document" else "references/guide.md")
            path.write_text("Edited after verification")
            return result
        monkeypatch.setattr(remote_worker, "run_one", changed)
    try:
        result = run_remote(service, "job_fixture", [sys.executable, str(script), "{target}"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    if edit_after_verification:
        assert result["remote"]["status"] == "failed"
        assert completed[0]["exit_code"] == 1
        assert "candidate_text" not in completed[0] and "candidate_bundle_base64" not in completed[0]
        return
    assert result["remote"]["status"] == "done", result
    assert result["local_result"]["changed"]
    assert not result["local_result"]["converged"]
    assert completed[0]["input_sha256"] == input_hash
    if kind == "document":
        assert completed[0]["candidate_text"] == "A concrete revised sentence."
    else:
        _, files = validate_bundle(base64.b64decode(completed[0]["candidate_bundle_base64"]))
        assert files["references/guide.md"] == b"A revised condition."
        assert (skill / "references/guide.md").read_text() == "Retain version and scope.\n"
    binding = next((service.state / "remote-runs").glob("*/binding.json"))
    assert "lease_token" not in json.loads(binding.read_text())


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_remote_cli_signal_cancels_local_and_reports_remote(signum, tmp_path):
    source = "Keep this source unchanged."
    posted = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            posted.append((self.path, payload))
            reply = {"id": "job_fixture", "status": "running"}
            if self.path.endswith("/claim"):
                reply.update(lease_token="synthetic-lease-" * 3, input_sha256=sha(source.encode()),
                    input_snapshot={"format": "text/v1", "text": source}, artifact_type="document",
                    timeout_seconds=60, max_iterations=1)
            elif self.path.endswith("/cancel"):
                reply["status"] = "cancelled"
            else:
                assert self.path.endswith("/heartbeat"), self.path
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(reply).encode())

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    state = tmp_path / "state"
    pid_file = tmp_path / "child.pid"
    script = tmp_path / "worker.py"
    script.write_text("import os, pathlib, sys, time\n"
                      "pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))\n"
                      "time.sleep(60)\n")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"roots": [], "remote_url": f"http://127.0.0.1:{server.server_port}",
                                 "worker_command": [sys.executable, str(script), str(pid_file)]}))
    process = subprocess.Popen([sys.executable, "-m", "skill_registry.cli", "--state", str(state),
        "remote-work", "job_fixture"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env={**os.environ, "SKILL_REGISTRY_CONFIG": str(config), "SKILL_REGISTRY_TOKEN": "synthetic-token"})
    child_pid = None
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        assert pid_file.exists(), process.communicate(timeout=2)
        child_pid = int(pid_file.read_text())
        process.send_signal(signum)
        stdout, stderr = process.communicate(timeout=8)
        assert process.returncode == 128 + signum, stderr
        result = json.loads(stdout)
        assert result["remote"]["status"] == "cancelled"
        assert Jobs(state).get(result["local_job_id"])["status"] == "cancelled"
        assert any(path.endswith("/cancel") for path, _ in posted)
        assert not any(path.endswith("/complete") for path, _ in posted)
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        binding = next((state / "remote-runs").glob("*/binding.json"))
        assert "lease_token" not in json.loads(binding.read_text())
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if child_pid:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        server.shutdown()
        server.server_close()
        thread.join()
