import asyncio
import json
import os
import signal
import subprocess
import sys
import time

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from skill_registry.jobs import Jobs


def test_real_stdio_lookup_load_package_and_job_protocol(skill, roots, tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"roots": roots}))
    state = tmp_path / "state"

    async def scenario():
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "skill_registry.mcp_server"],
                                       env={**os.environ, "SKILL_REGISTRY_HOME": str(state),
                                            "SKILL_REGISTRY_CONFIG": str(config)})
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = {t.name: t for t in (await session.list_tools()).tools}
                assert tools["skills_status"].annotations.readOnlyHint
                assert not tools["skill_lookup"].annotations.readOnlyHint
                assert not tools["skill_remote_publish"].annotations.readOnlyHint
                lookup = await session.call_tool("skill_lookup", {"query": "evidence"})
                assert not lookup.isError
                hit = lookup.structuredContent["hits"][0]
                loaded = await session.call_tool("skill_load", {"skill_id": hit["id"], "max_chars": 20})
                assert loaded.structuredContent["current"]
                assert len(loaded.structuredContent["text"]) == 20
                package = await session.call_tool("skill_package", {
                    "skill_id": hit["id"], "namespace": "local", "name": "example", "version": "1.0.0"})
                assert not package.isError
                assert not package.structuredContent["published"]
                submitted = await session.call_tool("optimizer_submit", {
                    "artifact_type": "document", "input_text": "Rewrite this vague statement."})
                assert submitted.structuredContent["status"] == "queued"
                cancelled = await session.call_tool("optimizer_cancel", {"job_id": submitted.structuredContent["id"]})
                assert cancelled.structuredContent["status"] == "cancelled"
                rejected = await session.call_tool("skill_lookup", {"query": "x", "top": 100})
                assert rejected.isError
    asyncio.run(scenario())


def test_cli_refresh_lookup_and_input_failure(skill, tmp_path):
    command = [sys.executable, "-m", "skill_registry.cli", "--state", str(tmp_path / "state"),
               "--root", str(skill.parent)]
    refreshed = subprocess.run([*command, "refresh"], capture_output=True, text=True)
    assert refreshed.returncode == 0, refreshed.stderr
    assert json.loads(refreshed.stdout)["counts"]["skills"] == 1
    searched = subprocess.run([*command, "lookup", "evidence"], capture_output=True, text=True)
    assert searched.returncode == 0
    assert json.loads(searched.stdout)["hits"][0]["name"] == "example"
    failed = subprocess.run([*command, "lookup", "x", "--top", "100"], capture_output=True, text=True)
    assert failed.returncode == 2
    assert "top must be" in failed.stderr and "Traceback" not in failed.stderr


def test_cli_root_override_retains_configured_worker_and_verification(skill, tmp_path):
    worker = tmp_path / "configured_worker.py"
    worker.write_text("pass\n")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"roots": [], "remote_url": "https://registry.example.test",
        "worker_command": [sys.executable, str(worker)],
        "check_commands": [[sys.executable, "-c", "raise SystemExit(7)"]]}))
    command = [sys.executable, "-m", "skill_registry.cli", "--state", str(tmp_path / "state"),
               "--root", str(skill.parent)]
    env = {**os.environ, "SKILL_REGISTRY_CONFIG": str(config)}
    submitted = subprocess.run([*command, "optimize", "document", "--text", "Original"],
                               capture_output=True, text=True, env=env)
    assert submitted.returncode == 0, submitted.stderr
    executed = subprocess.run([*command, "work"], capture_output=True, text=True, env=env)
    assert executed.returncode == 0, executed.stderr
    result = json.loads(executed.stdout)[0]
    assert result["status"] == "failed"
    assert result["result"]["checks"][-1]["exit_code"] == 7


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
@pytest.mark.parametrize("phase", ["worker", "check"])
def test_cli_signal_stops_child_and_terminalizes_job(signum, phase, tmp_path):
    state = tmp_path / "state"
    pid_file = tmp_path / "child.pid"
    sleeper = tmp_path / "sleeper.py"
    sleeper.write_text("import os, pathlib, sys, time\n"
                       "pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))\n"
                       "time.sleep(60)\n")
    sleeping_command = [sys.executable, str(sleeper), str(pid_file)]
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"roots": [],
        "worker_command": sleeping_command if phase == "worker" else [sys.executable, "-c", "pass"],
        "check_commands": [sleeping_command] if phase == "check" else []}))
    job = Jobs(state).enqueue("document", input_text="Keep this original.", timeout_seconds=60)
    process = subprocess.Popen([sys.executable, "-m", "skill_registry.cli", "--state", str(state),
                                "work"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               env={**os.environ, "SKILL_REGISTRY_CONFIG": str(config)})
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
        assert json.loads(stdout)[0]["status"] == "cancelled"
        record = Jobs(state).get(job["id"])
        assert record["status"] == "cancelled"
        assert record["result"]["cancelled"]
        assert not record["result"]["candidate_ready"]
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        assert Jobs(state).retry(job["id"])["status"] == "queued"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if child_pid:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_watch_sigterm_interrupts_idle_interval(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"roots": []}))
    process = subprocess.Popen([sys.executable, "-u", "-m", "skill_registry.cli", "--state",
        str(tmp_path / "state"), "watch", "--interval", "60"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env={**os.environ, "SKILL_REGISTRY_CONFIG": str(config)})
    try:
        assert process.stdout.readline().strip() == "{"
        process.send_signal(signal.SIGTERM)
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 143, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
