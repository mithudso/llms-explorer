"""Exercise the maintained adapter's lease boundary without processes or research."""

from __future__ import annotations

import importlib.util
import json
import re
import stat
import subprocess
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = {"enabled": True, "python": "/private/library/.venv/bin/python",
            "env_file": "/private/library/research-library.env"}


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def coordination():
    return load_module("tested_research_library_coordination", "research_library_coordination.py")


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "config" / "coordination.json"
    path.parent.mkdir()
    monkeypatch.setenv("RESEARCH_LIBRARY_COORDINATION_CONFIG", str(path))
    return path


def args(**overrides):
    return SimpleNamespace(**{"slug": "research-run", "topic": "Distributed leases",
                              "concepts": "Fencing, Recovery", "dry_run": False,
                              "status": "COMPLETED", **overrides})


class SharedRuntime:
    def __init__(self, root):
        self.RESEARCH_DIR = root
        self.calls = []
        self.results = {}
        self.behaviors = {}
        for name in ("cmd_init", "cmd_research", "cmd_gate", "cmd_finish"):
            setattr(self, name, self._command(name))

    def _command(self, name):
        def command(arguments):
            self.calls.append((name, arguments))
            if name in self.behaviors:
                return self.behaviors[name](arguments)
            return self.results.get(name, 0)
        return command

    @staticmethod
    def check_slug(slug):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("invalid slug")
        return slug

    @staticmethod
    def slugify(topic):
        return topic.lower().replace(" ", "-")

    def run_dir(self, slug):
        return self.RESEARCH_DIR / slug

    def load_manifest(self, slug):
        return json.loads((self.run_dir(slug) / "manifest.json").read_text())

    def manifest(self, **overrides):
        value = {"slug": "research-run", "topic": "Distributed leases", "concepts": [
            {"name": "Already researched", "status": "done"},
            {"name": "Also researched", "status": "complete"},
            {"name": "Fencing", "status": "pending"},
            {"name": "Recovery", "status": "incomplete"},
        ], **overrides}
        path = self.run_dir(value["slug"]) / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return value


@pytest.fixture
def guarded(coordination, tmp_path, monkeypatch):
    shared = SharedRuntime(tmp_path / "research")
    calls = []
    bundle = {"ok": True, "run_id": "research-run", "owner": "legacy:research-run",
              "concept_ids": ["c-fencing"], "tokens": {"c-fencing": "private-token"},
              "fences": {"c-fencing": 7}}

    def request(settings, operation, arguments):
        assert settings == SETTINGS
        assert operation == "coordinate"
        calls.append(deepcopy(arguments))
        return deepcopy(bundle)

    @contextmanager
    def heartbeat(settings, slug, acquired):
        def checkpoint():
            coordination.request(settings, "coordinate", {
                "action": "renew", "run_id": slug, "bundle": acquired, "ttl_seconds": 900})
        yield checkpoint
        checkpoint()

    monkeypatch.setattr(coordination, "config", lambda: SETTINGS)
    monkeypatch.setattr(coordination, "request", request)
    monkeypatch.setattr(coordination, "_heartbeat", heartbeat)
    coordination.install(shared)
    return SimpleNamespace(shared=shared, calls=calls, bundle=bundle)


def test_missing_configuration_is_a_noop(coordination, settings_file):
    assert coordination.config() is None


@pytest.mark.parametrize("enabled", [False, None, "true", 1])
def test_only_explicit_boolean_enables_coordination(coordination, settings_file, enabled):
    settings_file.write_text(json.dumps({"enabled": enabled}))
    assert coordination.config() is None


def test_enabled_configuration_preserves_exact_absolute_paths(coordination, settings_file):
    configured = {**SETTINGS, "python": "/private/Library Runtime/bin/python",
                  "env_file": "/private/Library Runtime/env/research.env"}
    settings_file.write_text(json.dumps(configured))
    assert coordination.config() == configured


@pytest.mark.parametrize("key,value", [("python", "python3"), ("env_file", "env/file"),
                                        ("python", None), ("env_file", 42)])
def test_enabled_configuration_rejects_ambiguous_paths(
        coordination, settings_file, key, value):
    settings_file.write_text(json.dumps({**SETTINGS, key: value}))
    with pytest.raises(ValueError, match="absolute Python and environment paths"):
        coordination.config()


@pytest.mark.parametrize("content,message", [("[]", "invalid"), ("x" * 65537, "oversized")])
def test_configuration_shape_and_size_are_bounded(coordination, settings_file, content, message):
    settings_file.write_text(content)
    with pytest.raises(ValueError, match=message):
        coordination.config()


def test_request_uses_exact_executable_private_env_and_json_stdin(coordination, monkeypatch):
    calls = []
    monkeypatch.setenv("MONGODB_URI2", "mongodb://user:secret@private.invalid")
    payload = {"action": "acquire", "names": ["a; $(never-execute)"], "run_id": "research-run"}

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=0, stdout='{"ok":true,"fences":{"a":2}}',
                               stderr="private diagnostic")

    monkeypatch.setattr(coordination.subprocess, "run", run)
    assert coordination.request(SETTINGS, "coordinate", payload) == {"ok": True, "fences": {"a": 2}}
    command, options = calls[0]
    assert command == [SETTINGS["python"], "-m", "research_library_service.cli",
                       "--env-file", SETTINGS["env_file"], "request"]
    assert options == {"input": json.dumps({"operation": "coordinate", "arguments": payload}),
                       "text": True, "capture_output": True, "timeout": 45}
    assert "secret" not in repr(calls)


@pytest.mark.parametrize("returncode,stdout", [
    (1, '{"error":"private-token"}'), (0, 'private-token invalid JSON'),
    (0, '{"ok":false,"details":"private-token"}'),
    (0, '{"error":"private-token"}'), (0, '["private-token"]'),
    (0, 'private-token' + 'x' * (4 * 1024 * 1024)),
])
def test_child_failures_and_invalid_receipts_do_not_echo_diagnostics(
        coordination, monkeypatch, returncode, stdout):
    monkeypatch.setattr(coordination.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr="mongodb://credentials/private-token"))
    with pytest.raises(ValueError) as failure:
        coordination.request(SETTINGS, "coordinate", {"action": "renew"})
    assert "private-token" not in str(failure.value)
    assert "credentials" not in str(failure.value)


@pytest.mark.parametrize("error", [OSError("private-token inaccessible"),
    subprocess.TimeoutExpired("private-token command", 45, output="private-token"),
    subprocess.CalledProcessError(1, "private-token", stderr="private-token")])
def test_subprocess_transport_failures_have_sanitized_errors(coordination, monkeypatch, error):
    def fail(*arguments, **keywords):
        raise error

    monkeypatch.setattr(coordination.subprocess, "run", fail)
    with pytest.raises(ValueError, match="transport is unavailable") as failure:
        coordination.request(SETTINGS, "coordinate", {"action": "renew"})
    assert "private-token" not in str(failure.value)


def test_request_utf8_size_limit_is_checked_before_starting_child(coordination, monkeypatch):
    invocations = []
    monkeypatch.setattr(coordination.subprocess, "run", lambda *a, **k: invocations.append(a))
    with pytest.raises(ValueError, match="request is oversized"):
        coordination.request(SETTINGS, "coordinate", {"names": ["🐘" * 200000]})
    assert not invocations


def test_private_bundle_is_replaced_atomically_with_private_permissions(coordination, tmp_path):
    shared = SharedRuntime(tmp_path / "research")
    value = {"tokens": {"c-one": "first-secret"}}
    coordination._save(shared, "research-run", value)
    path = coordination._state(shared, "research-run")
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert coordination._load(shared, "research-run") == value
    coordination._save(shared, "research-run", {"tokens": {"c-one": "replacement"}})
    assert coordination._load(shared, "research-run")["tokens"]["c-one"] == "replacement"
    assert list(path.parent.iterdir()) == [path]
    with pytest.raises(ValueError, match="invalid slug"):
        coordination._state(shared, "../escape")


def test_disabled_adapter_forwards_every_operation_without_requests(guarded, coordination, monkeypatch):
    monkeypatch.setattr(coordination, "config", lambda: None)
    for operation in ("cmd_init", "cmd_research", "cmd_gate", "cmd_finish"):
        assert getattr(guarded.shared, operation)(args()) == 0
    assert [name for name, _ in guarded.shared.calls] == [
        "cmd_init", "cmd_research", "cmd_gate", "cmd_finish"]
    assert not guarded.calls
    assert not guarded.shared.RESEARCH_DIR.exists()


@pytest.mark.parametrize("operation", ["cmd_init", "cmd_research", "cmd_gate", "cmd_finish"])
def test_dry_run_bypasses_coordination_without_writing_bundle(guarded, operation):
    assert getattr(guarded.shared, operation)(args(dry_run=True)) == 0
    assert not guarded.calls
    assert not guarded.shared.RESEARCH_DIR.exists()


def test_installation_is_idempotent(guarded, coordination):
    before = guarded.shared.cmd_init
    coordination.install(guarded.shared)
    assert guarded.shared.cmd_init is before
    guarded.shared.cmd_init(args())
    assert [call["action"] for call in guarded.calls] == ["acquire"]


def test_init_acquires_before_starting_with_deduplicated_names(guarded, coordination):
    def initialize(arguments):
        assert guarded.calls[0]["action"] == "acquire"
        assert coordination._load(guarded.shared, "research-run") == guarded.bundle
        return 17

    guarded.shared.behaviors["cmd_init"] = initialize
    assert guarded.shared.cmd_init(args(concepts=" Fencing, Recovery, Fencing, ")) == 17
    assert guarded.calls == [{"action": "acquire", "run_id": "research-run",
                              "names": ["Distributed leases", "Fencing", "Recovery"],
                              "bundle": None, "ttl_seconds": 900}]


def test_init_derives_slug_when_none_is_supplied(guarded, coordination):
    assert guarded.shared.cmd_init(args(slug=None)) == 0
    assert guarded.calls[0]["run_id"] == "distributed-leases"
    assert coordination._load(guarded.shared, "distributed-leases") == guarded.bundle


def test_new_init_failure_releases_only_when_no_manifest_exists(guarded, coordination):
    def fail(arguments):
        raise RuntimeError("init failed")

    guarded.shared.behaviors["cmd_init"] = fail
    with pytest.raises(RuntimeError, match="init failed"):
        guarded.shared.cmd_init(args())
    assert [call["action"] for call in guarded.calls] == ["acquire", "release"]
    assert not coordination._state(guarded.shared, "research-run").exists()


def test_init_failure_after_manifest_creation_preserves_research_hold(guarded, coordination):
    def fail(arguments):
        guarded.shared.manifest()
        raise RuntimeError("init partly persisted")

    guarded.shared.behaviors["cmd_init"] = fail
    with pytest.raises(RuntimeError, match="partly persisted"):
        guarded.shared.cmd_init(args())
    assert [call["action"] for call in guarded.calls] == ["acquire"]
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle


@pytest.mark.parametrize("operation", ["cmd_init", "cmd_research"])
def test_resume_and_refresh_reuse_bundle_and_only_request_unfinished_concepts(
        guarded, coordination, operation):
    previous = {"owner": "legacy:research-run", "tokens": {"old": "old-token"}}
    coordination._save(guarded.shared, "research-run", previous)
    guarded.shared.manifest()
    assert getattr(guarded.shared, operation)(args(refresh=True)) == 0
    assert guarded.calls[0]["bundle"] == previous
    assert guarded.calls[0]["names"] == ["Distributed leases", "Fencing", "Recovery"]
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle


def test_failed_resumed_init_does_not_release_an_existing_hold(guarded, coordination):
    coordination._save(guarded.shared, "research-run", guarded.bundle)

    def fail(arguments):
        raise RuntimeError("resume refused")

    guarded.shared.behaviors["cmd_init"] = fail
    with pytest.raises(RuntimeError, match="resume refused"):
        guarded.shared.cmd_init(args())
    assert [call["action"] for call in guarded.calls] == ["acquire"]
    assert coordination._state(guarded.shared, "research-run").is_file()


def test_denied_acquire_never_starts_work_or_removes_stop(guarded, coordination, monkeypatch):
    guarded.shared.manifest()
    stop = guarded.shared.run_dir("research-run") / "STOP"
    stop.write_text("paused by owner")
    coordination._save(guarded.shared, "research-run", guarded.bundle)

    def deny(*arguments):
        raise ValueError("existing STOP hold")

    monkeypatch.setattr(coordination, "request", deny)
    with pytest.raises(ValueError, match="STOP hold"):
        guarded.shared.cmd_research(args())
    assert not guarded.shared.calls
    assert stop.read_text() == "paused by owner"
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle


@pytest.mark.parametrize("operation", ["cmd_research", "cmd_gate", "cmd_finish"])
def test_failed_work_retains_bundle_and_restores_previous_checkpoint(guarded, coordination, operation):
    previous_checkpoint = lambda: None
    guarded.shared._research_library_lease_checkpoint = previous_checkpoint

    def fail(arguments):
        assert callable(guarded.shared._research_library_lease_checkpoint)
        assert guarded.shared._research_library_lease_checkpoint is not previous_checkpoint
        raise ValueError("gate or work failed")

    guarded.shared.behaviors[operation] = fail
    with pytest.raises(ValueError, match="gate or work failed"):
        getattr(guarded.shared, operation)(args())
    assert [call["action"] for call in guarded.calls] == ["acquire", "renew"]
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle
    assert guarded.shared._research_library_lease_checkpoint is previous_checkpoint


@pytest.mark.parametrize("status,result,released", [("COMPLETED", 0, True),
    ("COMPLETED", 2, False), ("BUDGET_EXHAUSTED", 0, False)])
def test_only_successful_completed_finish_releases_bundle(
        guarded, coordination, status, result, released):
    guarded.shared.results["cmd_finish"] = result
    assert guarded.shared.cmd_finish(args(status=status)) == result
    actions = [call["action"] for call in guarded.calls]
    assert actions == ["acquire", "renew", "renew"] + (["release"] if released else [])
    assert coordination._state(guarded.shared, "research-run").exists() is not released
    assert guarded.shared._research_library_lease_checkpoint is None


@pytest.mark.parametrize("status", ["FAILED", "BLOCKED", "CANCELLED"])
def test_nonpublishing_finish_bookkeeping_preserves_existing_hold(guarded, coordination, status):
    coordination._save(guarded.shared, "research-run", guarded.bundle)
    assert guarded.shared.cmd_finish(args(status=status)) == 0
    assert not guarded.calls
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle


def test_preoperation_renewal_failure_withholds_work_and_keeps_bundle(
        guarded, coordination, monkeypatch):
    original = coordination.request

    def request(settings, operation, arguments):
        if arguments["action"] == "renew":
            raise ValueError("fence no longer owned")
        return original(settings, operation, arguments)

    monkeypatch.setattr(coordination, "request", request)
    with pytest.raises(ValueError, match="fence no longer owned"):
        guarded.shared.cmd_finish(args())
    assert not guarded.shared.calls
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle
    assert guarded.shared._research_library_lease_checkpoint is None


def test_exit_renewal_failure_never_releases_completed_bundle(guarded, coordination, monkeypatch):
    original, renewals = coordination.request, []

    def request(settings, operation, arguments):
        if arguments["action"] == "renew":
            renewals.append(True)
            if len(renewals) == 2:
                raise ValueError("renewal failed")
        return original(settings, operation, arguments)

    monkeypatch.setattr(coordination, "request", request)
    with pytest.raises(ValueError, match="renewal failed"):
        guarded.shared.cmd_finish(args())
    assert len(guarded.shared.calls) == 1
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle
    assert "release" not in [call["action"] for call in guarded.calls]


def test_release_failure_preserves_bundle_for_recovery(guarded, coordination, monkeypatch):
    original = coordination.request

    def request(settings, operation, arguments):
        if arguments["action"] == "release":
            raise ValueError("release unavailable")
        return original(settings, operation, arguments)

    monkeypatch.setattr(coordination, "request", request)
    with pytest.raises(ValueError, match="release unavailable"):
        guarded.shared.cmd_finish(args())
    assert coordination._load(guarded.shared, "research-run") == guarded.bundle


@pytest.mark.parametrize("failed", [False, True])
def test_heartbeat_uses_current_bundle_and_stops_its_thread(coordination, monkeypatch, failed):
    calls, events, threads = [], [], []

    class Event:
        def __init__(self):
            self.set_called = False
            events.append(self)

        def wait(self, seconds):
            assert seconds == 60
            return not failed

        def set(self):
            self.set_called = True

    class Thread:
        def __init__(self, *, target, daemon, name):
            self.target = target
            self.daemon = daemon
            self.name = name
            self.joined = None
            threads.append(self)

        def start(self):
            self.target()

        def join(self, timeout):
            self.joined = timeout

    def request(settings, operation, arguments):
        calls.append((settings, operation, arguments))
        if failed:
            raise subprocess.TimeoutExpired("private-command", 45)
        return {"ok": True}

    monkeypatch.setattr(coordination.threading, "Event", Event)
    monkeypatch.setattr(coordination.threading, "Thread", Thread)
    monkeypatch.setattr(coordination, "request", request)
    bundle = {"tokens": {"c-one": "exact-owned-token"}, "fences": {"c-one": 9}}
    if failed:
        with (pytest.raises(ValueError, match="heartbeat failed; completion is withheld"),
              coordination._heartbeat(SETTINGS, "research-run", bundle) as checkpoint):
            checkpoint()
    else:
        with coordination._heartbeat(SETTINGS, "research-run", bundle) as checkpoint:
            checkpoint()
    assert all(call == (SETTINGS, "coordinate", {"action": "renew", "run_id": "research-run",
        "bundle": bundle, "ttl_seconds": 900}) for call in calls)
    assert events[0].set_called
    assert threads[0].daemon and threads[0].name == "research-library-heartbeat"
    assert threads[0].joined == 46


@pytest.mark.parametrize("enabled", [False, True])
def test_codex_adapter_installs_coordination_unless_explicitly_disabled(
        tmp_path, monkeypatch, settings_file, enabled):
    settings_file.write_text(json.dumps(SETTINGS))
    runtime = tmp_path / "dr_runtime.py"
    research = tmp_path / "private-research"
    runtime.write_text('''from pathlib import Path
RESEARCH_DIR = Path(''' + repr(str(research)) + ''')
AGENT_MODEL_BY_DEPTH = {"standard": "old"}
AGENT_EFFORT_BY_DEPTH = {"standard": "old"}
AGENT_PASSES_BY_DEPTH = {"standard": 2}
def check_slug(value): return value
def slugify(value): return value.lower().replace(" ", "-")
def run_dir(slug): return RESEARCH_DIR / slug
def load_manifest(slug): return {"topic": "Distributed leases", "concepts": []}
def cmd_init(args): return 77
def validate_claims(doc): return []
def noop(*args, **kwargs): return None
for symbol in ("main", "run_agent", "build_brief", "build_gate_brief", "atomic_write", "_now",
               "cmd_research", "cmd_gate", "cmd_finish", "escalation_reasons", "_tree_upsert",
               "build_parser", "lib_snapshot", "_create_run"):
    globals()[symbol] = noop
''')
    invocations = []

    def run(command, **options):
        invocations.append((command, json.loads(options["input"])))
        return SimpleNamespace(returncode=0, stdout='{"ok":true,"tokens":{"c-one":"secret"}}')

    monkeypatch.setattr(subprocess, "run", run)
    adapter = load_module("tested_coordination_adapter", "codex_dr_run.py")
    shared = adapter.load_shared(runtime, library_coordination=enabled)
    assert shared.cmd_init(args()) == 77
    state = research / ".library-coordination/research-run.json"
    if enabled:
        assert invocations[0][0][0] == SETTINGS["python"]
        assert invocations[0][1]["arguments"]["action"] == "acquire"
        assert json.loads(state.read_text())["tokens"] == {"c-one": "secret"}
    else:
        assert not invocations
        assert not state.exists()


@pytest.mark.parametrize("failure_at", [1, 2, None])
def test_artifact_publication_checks_ownership_before_build_and_commit_and_rolls_back(
        tmp_path, monkeypatch, failure_at):
    artifacts = load_module("tested_coordination_artifacts", "codex_dr_artifacts.py")
    transactions = load_module("tested_coordination_transactions", "research_transaction.py")
    shared = SharedRuntime(tmp_path / "research")
    shared.RESEARCH_DIR.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    destination = repo / "canonical-projection.txt"
    destination.write_text("previous projection")
    canonical_path = tmp_path / "canonical.json"
    artifact = {"documents": {"concept": {}}, "artifact_sha256": "a" * 64, "validation": {"ok": True}}
    checkpoints, builds = [], []

    def checkpoint():
        checkpoints.append(True)
        if len(checkpoints) == failure_at:
            raise ValueError("distributed fence lost")

    def atomic_write(path, content):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    def build(*arguments):
        builds.append(True)
        canonical_path.write_text(json.dumps(artifact))
        return artifact, canonical_path

    def finalize(*arguments):
        shared.atomic_write(destination, "new projection")
        return {"ok": True, "packs": [], "trees": []}

    canonical = SimpleNamespace(build=build, verify=lambda value: value)
    monkeypatch.setattr(artifacts, "load_module", lambda name, path:
        canonical if name == "canonical_research_artifact" else transactions)
    monkeypatch.setattr(artifacts, "_finalize_artifacts", finalize)
    shared.atomic_write = atomic_write
    shared._research_library_lease_checkpoint = checkpoint
    manifest = {"slug": "research-run"}
    if failure_at:
        with pytest.raises(ValueError, match="distributed fence lost"):
            artifacts._transactional_finalize(shared, manifest, {"concept": {}}, "COMPLETED", repo)
        assert destination.read_text() == "previous projection"
        assert not (shared.run_dir("research-run") / "artifacts/receipt.json").exists()
    else:
        receipt = artifacts._transactional_finalize(shared, manifest, {"concept": {}}, "COMPLETED", repo)
        assert receipt["ok"] is True
        assert destination.read_text() == "new projection"
    assert shared.atomic_write is atomic_write
    journals = list(shared.RESEARCH_DIR.glob("*/artifacts/transactions/*/journal.json"))
    if failure_at == 1:
        assert not builds
        assert not journals
    else:
        assert len(builds) == 1
        assert len(journals) == 1
        assert json.loads(journals[0].read_text())["status"] == (
            "rolled-back" if failure_at else "complete")
