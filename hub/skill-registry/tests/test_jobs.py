import json
import shutil
import subprocess
import sys
import threading
import time
import tomllib

import pytest

from skill_registry.catalog import Catalog
from skill_registry.jobs import Jobs, artifact_snapshot
from skill_registry.worker import _argv, _disabled_mcp_override, codex_command, run_one


def command_script(tmp_path, code):
    script = tmp_path / "worker.py"
    script.write_text(code)
    return [sys.executable, str(script), "{target}", "{receipt}"]


def test_skill_input_binds_all_resources_and_permissions(skill, tmp_path):
    jobs = Jobs(tmp_path / "state")
    job = jobs.enqueue("skill", target=skill / "SKILL.md")
    expected = artifact_snapshot("skill", skill / "SKILL.md", None)[2]
    assert expected == job["input_sha256"]
    assert set(job["params"]["snapshot_files"]) == {"SKILL.md", "references/guide.md", "scripts/check.py"}
    original = jobs.state / "runs" / job["id"] / "original"
    assert (original / "scripts/check.py").stat().st_mode & 0o100
    (skill / "references/guide.md").write_text("A changed condition")
    assert artifact_snapshot("skill", skill / "SKILL.md", None)[2] != expected
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        jobs.enqueue("skill", target=skill / "SKILL.md", expected_sha256=expected)


def test_worker_actual_candidate_checks_and_exit_zero_not_convergence(tmp_path):
    jobs = Jobs(tmp_path / "state")
    original = tmp_path / "report.md"
    original.write_text("vague prose\n")
    request = jobs.enqueue("document", target=original)
    command = command_script(tmp_path, "from pathlib import Path\nimport sys\np=Path(sys.argv[1]);p.write_text('Concrete revised prose.\\n')\n")
    result = run_one(jobs, command)
    assert result["status"] == "executed"
    assert result["result"]["changed"]
    assert result["result"]["checks_passed"]
    assert result["result"]["exit_code"] == 0
    assert not result["result"]["converged"]
    assert not result["result"]["published"]
    assert original.read_text() == "vague prose\n"
    assert result["input_sha256"] == request["input_sha256"]


def test_failed_configured_check_prevents_success(tmp_path):
    jobs = Jobs(tmp_path / "state")
    jobs.enqueue("query", input_text="SELECT 1")
    result = run_one(jobs, command_script(tmp_path, "pass\n"),
                     check_commands=[[sys.executable, "-c", "raise SystemExit(7)"]])
    assert result["status"] == "failed"
    assert not result["result"]["checks_passed"]
    assert result["result"]["checks"][-1]["exit_code"] == 7


def test_timeout_and_explicit_retry_preserve_attempts(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("code", input_text="print(1)", timeout_seconds=1)
    result = run_one(jobs, command_script(tmp_path, "import time\ntime.sleep(30)\n"))
    assert result["status"] == "failed"
    assert result["result"]["timed_out"]
    retry = jobs.retry(request["id"])
    assert retry["id"] != request["id"]
    assert retry["input_sha256"] == request["input_sha256"]
    assert retry["params"]["retry_of"] == request["id"]
    assert (jobs.state / "runs" / request["id"]).is_dir()


def test_cancellation_stops_running_worker(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="text", timeout_seconds=10)
    values = []
    thread = threading.Thread(target=lambda: values.append(run_one(
        jobs, command_script(tmp_path, "import time\ntime.sleep(30)\n"))))
    thread.start()
    deadline = time.monotonic() + 3
    while jobs.get(request["id"])["status"] != "running" and time.monotonic() < deadline:
        time.sleep(0.01)
    jobs.cancel(request["id"])
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert values[0]["status"] == "cancelled"


def test_lease_ownership_and_report_binding(tmp_path):
    jobs = Jobs(tmp_path / "state")
    queued = jobs.enqueue("agent", input_text="agent definition")
    claimed = jobs.claim("worker")
    with pytest.raises(ValueError, match="lease"):
        jobs.complete(queued["id"], "other", claimed["lease_token"], {"input_sha256": queued["input_sha256"]})
    with pytest.raises(ValueError, match="bind"):
        jobs.complete(queued["id"], "worker", claimed["lease_token"], {"input_sha256": "incorrect"})
    assert "lease_token" not in jobs.get(queued["id"])


def test_scheduler_opt_in_deduplication_and_resource_change(skill, roots, tmp_path):
    optimizer = skill.parent / "optimizer"
    optimizer.mkdir()
    (optimizer / "SKILL.md").write_text("---\nname: skill-optimizer\ndescription: Optimize skills\n---\nRead the native procedure.\n")
    catalog = Catalog(tmp_path / "state", roots)
    catalog.refresh()
    sid = next(r["id"] for r in catalog.lookup("example", refresh=False)["hits"] if r["name"] == "example")
    jobs = Jobs(tmp_path / "state")
    assert not jobs.schedule(catalog)["queued"]
    jobs.policy(sid, enabled=True)
    first = jobs.schedule(catalog)
    assert len(first["queued"]) == 1
    assert not jobs.schedule(catalog)["queued"]
    claimed = jobs.claim("test")
    jobs.complete(claimed["id"], "test", claimed["lease_token"], {"input_sha256": claimed["input_sha256"]})
    assert not jobs.schedule(catalog)["queued"]
    (skill / "references/guide.md").write_text("New evidence")
    assert len(jobs.schedule(catalog)["queued"]) == 1


def test_original_snapshot_tampering_cannot_pass_worker(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="original")
    original = jobs.state / "runs" / request["id"] / "original/artifact.txt"
    original.write_text("tampered")
    result = run_one(jobs, command_script(tmp_path, "pass\n"))
    assert result["status"] == "failed"
    assert result["result"]["error"] == "Original snapshot changed during worker execution"


def test_native_report_is_bound_but_not_independent_convergence(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("prompt", input_text="original prompt")
    report = {"schema": "optimizer-worker/v1", "input_sha256": request["input_sha256"],
              "optimizer_id": "prompt-deep-optimizer", "status": "CLEAN"}
    command = command_script(tmp_path, "from pathlib import Path\nimport sys\nPath(sys.argv[2]).write_text(" + repr(json.dumps(report)) + ")\n")
    result = run_one(jobs, command)
    assert result["status"] == "executed"
    assert result["result"]["convergence"]["status"] == "CLEAN"
    assert not result["result"]["convergence"]["independently_verified"]
    assert not result["result"]["converged"]


def test_cancellation_also_stops_configured_check_process(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="text", timeout_seconds=10)
    values = []
    thread = threading.Thread(target=lambda: values.append(run_one(jobs,
        command_script(tmp_path, "pass\n"),
        check_commands=[[sys.executable, "-c", "import time;time.sleep(30)"]])))
    thread.start()
    deadline = time.monotonic() + 3
    while not (jobs.state / "runs" / request["id"] / "check-0.log").exists():
        assert time.monotonic() < deadline
        time.sleep(0.01)
    jobs.cancel(request["id"])
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert values[0]["status"] == "cancelled"


def test_worker_and_checks_do_not_inherit_registry_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_REGISTRY_TOKEN", "synthetic-registry-token")
    monkeypatch.setenv("SKILL_REGISTRY_TOKEN_FILE", "/synthetic/private/token")
    jobs = Jobs(tmp_path / "state")
    jobs.enqueue("document", input_text="Original")
    check = "import os;assert 'SKILL_REGISTRY_TOKEN' not in os.environ;assert 'SKILL_REGISTRY_TOKEN_FILE' not in os.environ"
    command = command_script(tmp_path, check + "\n")
    result = run_one(jobs, command, check_commands=[[sys.executable, "-c", check]])
    assert result["status"] == "executed" and result["result"]["checks_passed"]


def test_codex_backend_disables_mcp_and_tool_network(tmp_path, monkeypatch):
    config = tmp_path / "codex"
    config.mkdir()
    (config / "config.toml").write_text('[mcp_servers.registry]\ncommand="unused"\n[mcp_servers."other.server"]\ncommand="unused"\n')
    monkeypatch.setenv("CODEX_HOME", str(config))
    command = _argv(codex_command(), {"target": "/candidate/SKILL.md", "workspace": "/candidate",
                                    "prompt": "/request.md", "receipt": "/receipt.json"})
    assert "workspace-write" in command
    override = next(value for value in command if value.startswith("mcp_servers="))
    assert tomllib.loads(override)["mcp_servers"] == {
        "registry": {"enabled": False}, "other.server": {"enabled": False}}
    assert not any(value.startswith('mcp_servers."') for value in command)
    assert "sandbox_workspace_write.network_access=false" in command
    assert "features.plugins=false" in command
    assert "features.apps=false" in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command


@pytest.mark.skipif(shutil.which("codex") is None, reason="Optional installed Codex CLI preflight")
def test_real_codex_parses_named_server_overrides_without_starting_models(tmp_path):
    command = _argv(codex_command(), {"target": str(tmp_path / "candidate/artifact.txt"),
        "workspace": str(tmp_path), "prompt": str(tmp_path / "request.md"),
        "receipt": str(tmp_path / "receipt.json")})
    overrides = [command[index + 1] for index, part in enumerate(command) if part == "-c"]
    servers = next((tomllib.loads(value)["mcp_servers"] for value in overrides
                    if value.startswith("mcp_servers=")), {})
    fixtures = ["registry-fixture.server", 'registry-fixture."quoted"']
    override = _disabled_mcp_override([*servers, *fixtures])
    # Add inert transports within the same CLI value. The list command reads
    # configuration only; it neither launches these servers nor calls a model.
    for name in fixtures:
        key = json.dumps(name, ensure_ascii=False)
        override = override.replace(key + "={enabled=false}",
                                    key + '={enabled=false,command="/usr/bin/false"}')
    argv = ["codex"]
    for value in overrides:
        if not value.startswith("mcp_servers="):
            argv.extend(["-c", value])
    argv.extend(["-c", override, "mcp", "list", "--json"])
    result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, "Codex configuration-only preflight failed"
    rows = json.loads(result.stdout)
    assert set(fixtures).issubset({row["name"] for row in rows})
    assert all(row.get("enabled") is False for row in rows)


def test_builtin_codex_literal_braces_do_not_become_worker_placeholders(tmp_path, monkeypatch):
    config = tmp_path / "codex"
    config.mkdir()
    (config / "config.toml").write_text('[mcp_servers."literal{target}.server"]\ncommand="unused"\n')
    monkeypatch.setenv("CODEX_HOME", str(config))
    command = _argv(codex_command(), {"target": "/actual-candidate", "receipt": "/receipt.json"})
    override = next(value for value in command if value.startswith("mcp_servers="))
    assert tomllib.loads(override)["mcp_servers"] == {"literal{target}.server": {"enabled": False}}
    assert command[-2] == "/receipt.json"
    with pytest.raises(ValueError, match="Unsupported command placeholder"):
        _argv(["worker", "{unapproved}"], {"target": "/actual-candidate"})


def test_configured_check_cannot_change_original_snapshot_and_claim_success(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="Original")
    original = jobs.state / "runs" / request["id"] / "original/artifact.txt"
    result = run_one(jobs, command_script(tmp_path, "pass\n"), check_commands=[[
        sys.executable, "-c", "from pathlib import Path;Path(" + repr(str(original)) + ").write_text('corrupted')"]])
    assert result["status"] == "failed" and not result["result"]["checks_passed"]
    assert result["result"]["error"] == "Original snapshot changed during verification"


def test_accepted_cancel_cannot_be_overridden_by_completion(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="Original")
    claimed = jobs.claim("worker")
    assert jobs.cancel(request["id"])["cancel_outcome"] == "accepted"
    completed = jobs.complete(request["id"], "worker", claimed["lease_token"], {
        "input_sha256": request["input_sha256"], "candidate_ready": True, "checks_passed": True})
    assert completed["status"] == "cancelled"
    assert not completed["result"]["candidate_ready"]


def test_cancel_after_completion_is_explicitly_too_late(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="Original")
    claimed = jobs.claim("worker")
    jobs.complete(request["id"], "worker", claimed["lease_token"], {"input_sha256": request["input_sha256"]})
    result = jobs.cancel(request["id"])
    assert result["cancel_outcome"] == "too_late" and result["status"] == "executed"


@pytest.mark.parametrize("root", ["candidate", "original"])
def test_worker_rejects_whole_workspace_root_symlink_swap(tmp_path, root):
    jobs = Jobs(tmp_path / "state")
    jobs.enqueue("document", input_text="Original")
    external = tmp_path / "external"
    external.mkdir()
    (external / "artifact.txt").write_text("Original")
    command = command_script(tmp_path,
        "from pathlib import Path\nimport shutil,sys\np=Path(sys.argv[1]).parent.parent/" + repr(root)
        + "\nshutil.rmtree(p)\np.symlink_to(" + repr(str(external)) + ",target_is_directory=True)\n")
    result = run_one(jobs, command)
    assert result["status"] == "failed"
    assert "root escaped" in result["result"]["error"]
    assert not result["result"]["checks_passed"]
    assert (external / "artifact.txt").read_text() == "Original"


def test_large_valid_receipt_is_retained_without_oversized_result_or_false_convergence(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="Original")
    report = {"schema": "optimizer-worker/v1", "input_sha256": request["input_sha256"],
              "optimizer_id": "ddo", "status": "CLEAN", "summary": "x" * 130500}
    command = command_script(tmp_path, "from pathlib import Path\nimport sys\nPath(sys.argv[2]).write_text(" + repr(json.dumps(report)) + ")\n")
    result = run_one(jobs, command)
    assert result["status"] == "executed"
    assert result["result"]["worker_report_artifact"]["bytes"] > 130000
    assert result["result"]["worker_report"]["details"]
    assert not result["result"]["converged"]


def test_oversized_receipt_terminalizes_failed_instead_of_leaving_running(tmp_path):
    jobs = Jobs(tmp_path / "state")
    request = jobs.enqueue("document", input_text="Original")
    command = command_script(tmp_path, "from pathlib import Path\nimport sys\nPath(sys.argv[2]).write_text('x'*150000)\n")
    result = run_one(jobs, command)
    assert result["status"] == "failed" and not result["result"]["checks_passed"]
    assert jobs.get(request["id"])["status"] == "failed"
