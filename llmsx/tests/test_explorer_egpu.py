"""eGPU provider controls: fixture files and mocked transports only.

The installed launcher, model APIs, services, indexing and GPUs never run.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmsx import explorer_store as es


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "user"))
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "config"))
    for name in (
        "LLMSX_PROVIDER",
        "LLMSX_AGENT_ENGINE",
        "LLMSX_MODEL",
        "LLMSX_EGPU_MODEL",
        "LLMSX_EGPU_BIN",
        "LLMSX_EGPU_BINARY",
        "EGPU_HARNESS_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    def deny(*args, **kwargs):
        raise AssertionError("unmocked process, network or signal is forbidden in eGPU preparation")

    monkeypatch.setattr(es.subprocess, "run", deny)
    monkeypatch.setattr(es.subprocess, "Popen", deny)
    monkeypatch.setattr(es.urllib.request, "urlopen", deny)
    monkeypatch.setattr(es.os, "killpg", deny)


@pytest.fixture
def installed(monkeypatch):
    wrapper, package, repo = es.egpu_paths()
    frontdoor = package / "scripts/claude_egpu_frontdoor.py"
    wrapper.parent.mkdir(parents=True)
    frontdoor.parent.mkdir(parents=True)
    wrapper.write_bytes(b"NON-SOURCE FIXTURE WRAPPER; MUST NOT EXECUTE\n")
    wrapper.chmod(0o700)
    frontdoor.write_bytes(b"NON-SOURCE FIXTURE FRONTDOOR; MUST NOT EXECUTE\n")
    monkeypatch.setattr(
        es,
        "EGPU_INSTALLED_HASHES",
        {
            "wrapper": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
            "frontdoor": hashlib.sha256(frontdoor.read_bytes()).hexdigest(),
        },
    )
    (repo / es.TREE_REL).parent.mkdir(parents=True)
    (repo / es.TREE_REL).write_text("[]\n")
    return wrapper, package, repo


def passive(package):
    return {
        "version": "1.0.1",
        "installed": True,
        "ready": True,
        "passive": True,
        "model": es.EGPU_MODEL,
        "context": 32768,
        "package": str(package),
        "compatible_client": str(package / "scripts/egpu_claude_client.py"),
        "research_adapter": str(package / "scripts/egpu_research_agent.py"),
        "full_tools": 23,
        "services_started": False,
        "model_requests": 0,
        "lldb_attaches": 0,
        "physical_qualification_verified": False,
        "research_qualification_verified": False,
    }


def mock_passive(monkeypatch, installed, changes=None, returncode=0):
    wrapper, package, _ = installed
    data = {**passive(package), **(changes or {})}
    calls = []

    def run(argv, **kwargs):
        assert argv == [str(wrapper), "--check-installed"]
        assert kwargs["env"]["EGPU_HARNESS_DIR"] == str(package)
        assert kwargs["capture_output"] and kwargs["text"]
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=returncode, stdout=json.dumps(data), stderr="")

    monkeypatch.setattr(es.subprocess, "run", run)
    return calls


def test_new_provider_preserves_existing_defaults_and_saved_mlx_selection():
    assert es.active_provider() == "claude"
    assert es.PROVIDER_DEFAULT_MODELS["ollama"] == "qwen3.5:27b"
    es.set_provider("ollama")
    es.set_provider_model("ollama", "llmsx-research-gemma31-mlx")
    before = es.load_config()
    assert es.provider_model("egpu") == es.EGPU_MODEL
    assert es.load_config() == before
    assert es.provider_model("ollama") == "llmsx-research-gemma31-mlx"
    assert es.active_provider() == "ollama"
    es.set_provider("egpu")
    assert es.active_provider() == "egpu"
    assert es.provider_model("ollama") == "llmsx-research-gemma31-mlx"


@pytest.mark.parametrize("source", ["specific_env", "generic_env", "stored", "setter"])
def test_wrong_model_refused_without_fallback(monkeypatch, source):
    if source == "specific_env":
        monkeypatch.setenv("LLMSX_EGPU_MODEL", "gemma4:12b-mlx")
    elif source == "generic_env":
        monkeypatch.setenv("LLMSX_MODEL", "cloud-model")
    elif source == "stored":
        es.save_config({"models": {"egpu": "qwen3:4b", "ollama": "llmsx-research-gemma31-mlx"}})
    with pytest.raises(ValueError, match="only the reviewed model"):
        if source == "setter":
            es.set_provider_model("egpu", "qwen3:4b")
        else:
            es.provider_model("egpu")


def test_egpu_has_no_api_key_and_refuses_storage():
    es.save_config({"api_keys": {"egpu": "fixture-secret", "claude": "existing-secret"}})
    assert es.provider_api_key("egpu") == ""
    before = es.config_path().read_bytes()
    with pytest.raises(ValueError, match="does not accept an API key"):
        es.set_provider_api_key("egpu", "fixture-new-secret")
    assert es.config_path().read_bytes() == before
    es.set_provider_api_key("egpu", "-")
    assert es.load_config()["api_keys"] == {"claude": "existing-secret"}


@pytest.mark.parametrize("name", ["LLMSX_EGPU_BIN", "LLMSX_EGPU_BINARY", "EGPU_HARNESS_DIR"])
def test_foreign_route_refused_before_any_process(installed, monkeypatch, name):
    monkeypatch.setenv(name, "/tmp/foreign-route")
    with pytest.raises(ValueError, match="must identify"):
        es.research_argv("Fixture Topic", "dr", provider="egpu")
    assert not es.has_provider_binary("egpu")
    assert es.probe_egpu_installation()[0] is False


@pytest.mark.parametrize("changed", ["wrapper", "frontdoor", "mode", "fifo"])
def test_unreviewed_installed_bytes_are_never_executed(installed, changed):
    wrapper, package, _ = installed
    frontdoor = package / "scripts/claude_egpu_frontdoor.py"
    if changed == "mode":
        wrapper.chmod(0o600)
    elif changed == "fifo":
        frontdoor.unlink()
        os.mkfifo(frontdoor)
    else:
        (wrapper if changed == "wrapper" else frontdoor).write_bytes(b"legacy Tinygrad fixture")
    assert not es.has_provider_binary("egpu")
    assert es.test_provider_key("egpu").startswith("refusing:")


def test_passive_contract_uses_exact_checked_route_and_no_qualification_claim(
    installed, monkeypatch
):
    calls = mock_passive(monkeypatch, installed)
    ok, msg = es.probe_provider_auth("egpu", "ignored-fixture-key", timeout=2)
    assert ok and "GPU and research qualification were not checked" in msg
    assert calls[0][1]["timeout"] == 2
    assert es.test_provider_key("egpu").startswith("ready: reviewed installation ready")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"installed": False},
        {"ready": False},
        {"passive": False},
        {"services_started": True},
        {"model_requests": 1},
        {"model_requests": False},
        {"lldb_attaches": 1},
        {"full_tools": 4},
        {"context": 8192},
        {"model": "qwen3:4b"},
        {"package": "/tmp/disposable"},
        {"compatible_client": "/tmp/private-client"},
        {"research_adapter": "/tmp/other-adapter"},
        {"physical_qualification_verified": True},
        {"research_qualification_verified": True},
    ],
)
def test_passive_contract_rejects_invalid_fields(installed, monkeypatch, changes):
    mock_passive(monkeypatch, installed, changes)
    assert es.probe_egpu_installation()[0] is False


@pytest.mark.parametrize("stdout", ["not JSON", "[]", "null", "x" * 131073])
def test_passive_malformed_response_refused(installed, monkeypatch, stdout):
    monkeypatch.setattr(
        es.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=stdout, stderr=""),
    )
    assert not es.probe_egpu_installation()[0]


def test_passive_timeout_and_nonzero_refused(installed, monkeypatch):
    mock_passive(monkeypatch, installed, returncode=1)
    assert not es.probe_egpu_installation()[0]

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("fixture-passive-check", 4)

    monkeypatch.setattr(es.subprocess, "run", timeout)
    assert not es.probe_egpu_installation()[0]


def test_canonical_standard_argv_binds_parent_and_streaming(installed):
    wrapper, _, repo = installed
    expected = [
        str(wrapper),
        "--research",
        "Fixture Topic",
        "--depth",
        "standard",
        "--budget-minutes",
        "150",
        "--parent",
        "Fixture Parent",
        "--output-format",
        "stream-json",
        "--verbose",
    ]
    assert es.research_argv("Fixture Topic", "dr", "Fixture Parent", "egpu") == expected
    assert es.egpu_research_request(expected, repo) == ("Fixture Topic", "Fixture Parent")
    no_parent = es.research_argv("Fixture Topic", "dr", provider="egpu")
    assert es.egpu_research_request(no_parent, repo) == ("Fixture Topic", None)


@pytest.mark.parametrize("mode", ["family", "deep", "crawl", "full", "queue", "unknown"])
def test_unsupported_research_refuses_even_without_installed_launcher(mode):
    with pytest.raises(ValueError, match="standard /dr only"):
        es.research_argv("Fixture Topic", mode, provider="egpu")


@pytest.mark.parametrize(
    "topic,parent",
    [
        ("-bad", None),
        ("`bad`", None),
        ("Fixture", "bad\nparent"),
        ("Fixture", "-parent"),
        ("Fixture ", None),
        ("Fixture", "Parent "),
    ],
)
def test_unsafe_topic_and_parent_refused(installed, topic, parent):
    with pytest.raises(ValueError):
        es.research_argv(topic, "dr", parent, "egpu")


def test_other_workflows_and_arbitrary_flags_cannot_use_egpu(installed):
    with pytest.raises(ValueError, match="standalone skills"):
        es.skill_argv("skill-optimizer", "fixture", "egpu")
    with pytest.raises(ValueError, match="braindump"):
        es.braindump_argv(Path("fixture.md"), "egpu")
    argv = es.research_argv("Fixture Topic", "dr", provider="egpu")
    with pytest.raises(ValueError, match="standard /dr"):
        es.egpu_research_request([*argv, "--model", "other"])
    with pytest.raises(ValueError, match="canonical standard /dr"):
        es.egpu_research_request(["foreign"] + argv[1:])


class FixtureProcess:
    pid = 987654321
    returncode = 0

    def __init__(self, events):
        self.stdout = io.StringIO("".join(json.dumps(ev) + "\n" for ev in events))

    def wait(self, timeout=None):
        return self.returncode


def run_fixture_job(monkeypatch, installed, tmp_path, events, completion=None, cancel=None):
    from llmsx import ollama_agent

    mock_passive(monkeypatch, installed)
    launches = []

    def popen(argv, **kwargs):
        launches.append((argv, kwargs))
        return FixtureProcess(events)

    monkeypatch.setattr(es.subprocess, "Popen", popen)
    if completion is not None:
        monkeypatch.setattr(ollama_agent, "completion_check", completion)
    argv = es.research_argv("Fixture Topic", "dr", "Fixture Parent", "egpu")
    lines = []
    log = tmp_path / "fixture.log"
    result = es.run_claude_job(
        argv,
        installed[2],
        timeout=1,
        log=log,
        emit=lines.append,
        cancel=cancel or threading.Event(),
        provider="egpu",
    )
    return result, launches, lines, log


def test_exit_zero_and_chat_json_do_not_complete_research(installed, monkeypatch, tmp_path):
    result, launches, _, _ = run_fixture_job(
        monkeypatch,
        installed,
        tmp_path,
        [{"type": "result", "is_error": False, "result": "all done"}],
    )
    assert result.status == "error" and "could not verify" in result.message
    assert len(launches) == 1


def test_egpu_job_streams_raw_suppresses_cloud_cost_and_verifies_topic(
    installed, monkeypatch, tmp_path
):
    checked = []

    def completion(args):
        checked.append(args)
        assert args[0] == "-p" and "research the concept `Fixture Topic`" in args[1]
        assert "Fixture Parent" in args[1]
        return None, None

    result, launches, lines, log = run_fixture_job(
        monkeypatch,
        installed,
        tmp_path,
        [
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "fixture"}]}},
            {"type": "result", "is_error": False, "total_cost_usd": 999, "result": "fixture done"},
        ],
        completion,
    )
    assert result.status == "ok" and len(checked) == 1 and len(launches) == 1
    assert not any("$999" in line for line in lines)
    assert '"total_cost_usd": 999' in log.read_text()
    kwargs = launches[0][1]
    assert kwargs["cwd"] == str(installed[2]) and kwargs["start_new_session"] is True
    assert kwargs["env"]["EGPU_HARNESS_DIR"] == str(installed[1])


def test_result_error_never_falls_back_or_rechecks_completion(installed, monkeypatch, tmp_path):
    def forbidden(args):
        raise AssertionError("failed runner must not verify or retry")

    result, launches, _, _ = run_fixture_job(
        monkeypatch,
        installed,
        tmp_path,
        [{"type": "result", "is_error": True, "result": "fixture failure"}],
        forbidden,
    )
    assert result.status == "error" and result.message == "fixture failure"
    assert len(launches) == 1


@pytest.mark.parametrize("outcome", ["cancelled", "timeout"])
def test_egpu_cancellation_or_deadline_only_signals_owned_job_group(
    installed, monkeypatch, tmp_path, outcome
):
    signals = []
    monkeypatch.setattr(es.os, "killpg", lambda pid, sig: signals.append((pid, sig)))

    class ImmediateGuard:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(es.threading, "Thread", ImmediateGuard)
    cancel = threading.Event()
    if outcome == "cancelled":
        cancel.set()
    else:
        ticks = iter([1000, 11801])
        monkeypatch.setattr(es.time, "monotonic", lambda: next(ticks))
    result, launches, _, _ = run_fixture_job(monkeypatch, installed, tmp_path, [], cancel=cancel)
    assert result.status == outcome and len(launches) == 1
    assert signals == [(FixtureProcess.pid, es.signal.SIGTERM)]
    if outcome == "timeout":
        assert "10800s" in result.message


@pytest.mark.parametrize("outcome", ["cancelled", "timeout"])
def test_ui_cancellation_restores_only_the_job_tree_snapshot(installed, outcome):
    pytest.importorskip("textual")
    from llmsx.explorer import Explorer

    repo = installed[2]
    snapshot = es.snapshot_tree(repo)
    (repo / es.TREE_REL).write_text('["damaged NON-SOURCE fixture"]')
    messages = []
    app = SimpleNamespace(
        repo=repo,
        _refresh=lambda: None,
        _job_line=lambda *_: None,
        _job_screen=lambda _: None,
        _status=messages.append,
    )
    job = SimpleNamespace(done=False, state="running", what="fixture", log=repo / "fixture.log")
    Explorer._job_done(app, job, es.JobResult(outcome, -15, outcome), snapshot)
    assert es.snapshot_tree(repo) == snapshot
    assert job.done and job.state == outcome and "snapshot restored" in messages[-1]


@pytest.mark.parametrize(
    "mutation", [None, "missing_concept", "gate_missing", "contradicted", "unverified"]
)
def test_egpu_uses_actual_canonical_completion_artifacts(
    installed, monkeypatch, tmp_path, mutation
):
    """Mechanical artifact controls use explicit NON-SOURCE fixture claims."""
    folder = Path.home() / ".global-ai-hub/research/fixture-topic"
    folder.mkdir(parents=True)
    artifact = folder / "SKILL.md"
    artifact.write_text("NON-SOURCE FIXTURE artifact")
    concepts = [{"name": f"fixture{i}", "status": "done"} for i in range(5)]
    verdicts = [
        {
            "concept": f"fixture{i % 5}",
            "claim": f"NON-SOURCE FIXTURE {i}",
            "verdict": "SUPPORTED",
            "evidence": "NON-SOURCE FIXTURE support",
            "footnotes": [f"[^fixture-{i}]"],
            "urls": [f"https://example.invalid/{i}"],
        }
        for i in range(10)
    ]
    counts = {"SUPPORTED": 10}
    if mutation == "missing_concept":
        concepts[0]["status"] = "pending"
    elif mutation in ("contradicted", "unverified"):
        label = mutation.upper()
        verdicts[-1]["verdict"] = label
        counts = {"SUPPORTED": 9, label: 1}
    gate = folder / "gate.json"
    gate.write_text(json.dumps({"sampled": 10, "verdicts": verdicts}))
    manifest = {
        "concepts": concepts,
        "exit_status": "COMPLETED",
        "install_path": str(artifact),
        "gate": {"path": str(gate), "is_error": False, "counts": counts},
    }
    (folder / "manifest.json").write_text(json.dumps(manifest))
    if mutation == "gate_missing":
        gate.unlink()
    result, launches, lines, _ = run_fixture_job(
        monkeypatch,
        installed,
        tmp_path,
        [{"type": "result", "is_error": False, "result": "fixture done"}],
    )
    assert len(launches) == 1
    if mutation in (None, "unverified"):
        assert result.status == "ok"
        if mutation == "unverified":
            assert "UNVERIFIED" in result.message and result.message in lines
    else:
        assert result.status == "error"


def test_noncanonical_repo_and_failed_readiness_refuse_before_job_process(
    installed, monkeypatch, tmp_path
):
    argv = es.research_argv("Fixture Topic", "dr", provider="egpu")
    log = tmp_path / "not-created" / "fixture.log"
    result = es.run_claude_job(
        argv,
        tmp_path,
        timeout=1,
        log=log,
        emit=lambda _: None,
        cancel=threading.Event(),
        provider="egpu",
    )
    assert result.status == "oserror" and "canonical Explorer repository" in result.message
    assert not log.parent.exists()
    mock_passive(monkeypatch, installed, {"ready": False})
    result = es.run_claude_job(
        argv,
        installed[2],
        timeout=1,
        log=log,
        emit=lambda _: None,
        cancel=threading.Event(),
        provider="egpu",
    )
    assert result.status == "oserror" and not log.parent.exists()


def test_mode_options_preserve_others_and_restrict_egpu():
    assert es.available_research_modes("egpu", True) == ["dr", "queue"]
    assert es.available_research_modes("egpu", False) == ["queue"]
    assert es.available_research_modes("ollama", True) == list(es.RESEARCH_MODES)


def test_unavailable_ui_reports_reviewed_installation_instead_of_missing_path():
    pytest.importorskip("textual")
    import asyncio

    from textual.app import App
    from textual.widgets import Static

    from llmsx.explorer import Research

    async def check():
        app = App()
        async with app.run_test() as pilot:
            app.push_screen(Research("Fixture", None, provider="egpu", have_agent=False))
            await pilot.pause()
            hint = str(app.screen.query_one("#provider-hint", Static).render())
            assert "reviewed eGPU installation unavailable" in hint
            assert "not found on PATH" not in hint

    asyncio.run(check())


def test_concepts_screen_refuses_before_any_cloud_process(monkeypatch):
    pytest.importorskip("textual")
    from llmsx.concepts_tui import ConceptPackBrowser

    monkeypatch.setenv("LLMSX_PROVIDER", "egpu")
    messages = []
    ConceptPackBrowser._run_claude_skill(
        None, "/dr fixture", SimpleNamespace(update=messages.append)
    )
    assert len(messages) == 1 and "unsupported" in messages[0]


def test_ui_refuses_unsupported_research_and_never_retries_job_exception(installed, monkeypatch):
    pytest.importorskip("textual")
    from llmsx.explorer import Explorer

    messages, launches = [], []

    def run_job(argv, what, provider=None):
        launches.append((argv, what, provider))
        raise RuntimeError("fixture runner failure")

    app = SimpleNamespace(_status=messages.append, _run_job=run_job)
    Explorer._run_research(app, "Fixture", "deep", None, "egpu")
    assert not launches and "unsupported" in messages[-1]
    with pytest.raises(RuntimeError, match="fixture runner failure"):
        Explorer._run_research(app, "Fixture", "dr", None, "egpu")
    assert len(launches) == 1


@pytest.mark.parametrize("entry", ["quick", "modal"])
def test_ui_does_not_silently_drop_unsafe_egpu_parent(installed, monkeypatch, entry):
    pytest.importorskip("textual")
    from llmsx.explorer import Explorer

    monkeypatch.setenv("LLMSX_PROVIDER", "egpu")
    messages, launches = [], []
    app = SimpleNamespace(
        _selected="Fixture",
        _outline=None,
        _node=lambda _: {"parentConcept": "unsafe\nparent"},
        _status=messages.append,
        _run_research=lambda *a, **kw: launches.append((a, kw)),
        push_screen=lambda screen, done: done(("dr", "egpu")),
    )
    if entry == "quick":
        Explorer.action_quick_dr(app)
    else:
        Explorer.action_research(app)
    assert not launches and "parent is unsafe" in messages[-1]


def test_ui_job_uses_fixed_10800_deadline_and_refuses_wrong_repo(installed, monkeypatch):
    pytest.importorskip("textual")
    from llmsx.explorer import Explorer

    monkeypatch.setenv("LLMSX_RESEARCH_TIMEOUT", "1")
    argv = es.research_argv("Fixture", "dr", provider="egpu")
    calls, messages = [], []

    def job(*args, **kwargs):
        calls.append((args, kwargs))
        return es.JobResult("ok", 0, "fixture")

    monkeypatch.setattr(es, "run_claude_job", job)
    app = SimpleNamespace(
        _job=None,
        repo=installed[2],
        _status=messages.append,
        _post=lambda f, *a: None,
        _job_line=None,
        _job_done=None,
        run_worker=lambda f, **kw: f(),
        push_screen=lambda _: None,
    )
    Explorer._run_job(app, argv, "fixture", "egpu")
    assert len(calls) == 1 and calls[0][1]["timeout"] == 10800
    app._job = None
    app.repo = installed[2].parent
    Explorer._run_job(app, argv, "fixture", "egpu")
    assert len(calls) == 1 and app._job is None and "canonical Explorer" in messages[-1]


def test_settings_and_research_widgets_show_only_supported_controls(installed, monkeypatch):
    pytest.importorskip("textual")
    import asyncio

    from textual.app import App
    from textual.widgets import Button, Input

    from llmsx.explorer import Research, ResearchSelect, Settings

    async def check():
        app = App()
        async with app.run_test() as pilot:
            app.push_screen(Research("Fixture", None, provider="egpu", have_agent=True))
            await pilot.pause()
            assert app.screen.query_one("#mode", ResearchSelect)._options == [
                ("dr", "dr"),
                ("queue", "queue"),
            ]
            assert app.screen.query_one("#quick-deep", Button).disabled
            assert app.screen.query_one("#quick-family", Button).disabled
            app.pop_screen()
            app.push_screen(Settings({"provider": "egpu"}, False, lambda *_: "fixture"))
            await pilot.pause()
            model = app.screen.query_one("#model", Input)
            key = app.screen.query_one("#provider_key", Input)
            assert model.disabled and model.value == es.EGPU_MODEL
            assert key.disabled and key.value == ""

    asyncio.run(check())
