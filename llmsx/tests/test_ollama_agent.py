"""Regression coverage for real local agent dispatch rather than plain chat."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from llmsx import explorer_store as es
from llmsx import ollama_agent as agent


@pytest.fixture
def local(monkeypatch, tmp_path):
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path))
    monkeypatch.setenv("LLMSX_OLLAMA_MODEL", "llmsx-research")
    monkeypatch.setattr(es.shutil, "which", lambda name: f"/bin/{name}")
    return tmp_path


def test_child_research_keeps_limits_but_uses_local_model_and_retrieval(local):
    (local / "ollama-mcp.json").write_text('{"mcpServers":{}}')
    args = agent.command(["-p", "research", "--model", "sonnet", "--max-turns", "12",
                          "--mcp-config", "/old/empty.json", "--strict-mcp-config",
                          "--allowedTools", "Read,WebSearch", "--output-format", "json"])
    assert args[:3] == ["/bin/claude", "--model", "llmsx-research"]
    assert "Monitor" in args[args.index("--tools") + 1].split(",")
    assert "sonnet" not in args and "/old/empty.json" not in args
    assert args.count("--mcp-config") == 1
    assert args[args.index("--mcp-config") + 1] == str(local / "ollama-mcp.json")
    assert args[args.index("--max-turns") + 1] == "12"
    assert args[-2:] == ["--output-format", "json"]
    assert "mcp__firecrawl__firecrawl_search" in args[args.index("--allowedTools") + 1]


def test_main_routes_nested_agents_without_mutating_parent_environment(local, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SIMPLE", "1")
    monkeypatch.setenv("CLAUDE_CODE_SAFE_MODE", "1")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-cloud-key")
    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11434")
    monkeypatch.setattr(sys, "argv", ["llmsx-ollama-agent", "-p", "research"])
    captured = {}
    monkeypatch.setattr(agent.os, "execvpe", lambda binary, argv, env: captured.update(env))
    assert agent.main() == 0
    assert captured["DR_CLAUDE_BIN"] == "/bin/llmsx-ollama-agent"
    assert captured["LLMSX_OLLAMA_MODEL"] == "llmsx-research"
    assert captured["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:11434"
    assert captured["ANTHROPIC_API_KEY"] == ""
    assert captured["ANTHROPIC_AUTH_TOKEN"] == "ollama"
    assert captured["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "llmsx-research"
    assert captured["CLAUDE_CODE_SUBAGENT_MODEL"] == "llmsx-research"
    assert "CLAUDE_CODE_SIMPLE" not in captured
    assert "CLAUDE_CODE_SAFE_MODE" not in captured
    assert agent.os.environ["CLAUDE_CODE_SIMPLE"] == "1"


def test_local_dispatch_requires_agent_runtime_and_rejects_cloud(local, monkeypatch):
    monkeypatch.setenv("LLMSX_OLLAMA_MODEL", "qwen:cloud")
    with pytest.raises(ValueError, match="local model"):
        agent.command(["-p", "hello"])
    monkeypatch.setattr(es, "claude_binary", lambda: None)
    assert es.research_argv("DATE Criteria", "dr", provider="ollama") is None
    assert es.skill_argv("dr", "DATE Criteria", provider="ollama") is None
    assert es.braindump_argv(local / "dump.md", provider="ollama") is None


def test_ansi_sequences_are_removed_whole():
    assert es.summarize_event("one\x1b[?25ltwo\x1b[?25h") == "onetwo"
    assert es.summarize_event("\x1b]8;;https://example.com\x1b\\link\x1b]8;;\x1b\\") == "link"
    event = {"type": "assistant", "message": {"content": [
        {"type": "text", "text": "\x1b[31mhello\x1b[0m"}]}}
    assert es.summarize_event(json.dumps(event)) == "assistant: hello"


def test_research_loads_workflow_and_resolves_frontier_ancestry(local, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: local)
    monkeypatch.chdir(local)
    skill = local / ".claude/commands/dr.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("Verified local standard workflow")
    es.TREE_REL.parent.mkdir()
    es.TREE_REL.write_text(json.dumps([
        {"concept": "Archive Rules", "parentConcept": "MongoDB Atlas Online Archive",
         "childConcepts": ["DATE Criteria"]},
        {"concept": "MongoDB Atlas Online Archive", "parentConcept": "",
         "childConcepts": ["Archive Rules"]},
    ]))
    prompt = agent.research_context(es.research_prompt("DATE Criteria", "dr", "Archive Rules"))
    assert "Verified local standard workflow" in prompt
    assert '["DATE Criteria", "Archive Rules", "MongoDB Atlas Online Archive"]' in prompt
    assert "untrusted labels" in prompt
    monkeypatch.setattr(sys, "argv", ["llmsx-ollama-agent", "-p",
                        es.research_prompt("DATE Criteria", "dr", "Archive Rules")])
    captured = {}
    monkeypatch.setattr(agent.os, "execvpe", lambda binary, argv, env: captured.update(env))
    assert agent.main() == 0
    scope = captured["LLMSX_OLLAMA_RESEARCH_CONTEXT"]
    assert json.loads(scope)[-1] == "MongoDB Atlas Online Archive"
    monkeypatch.setenv("LLMSX_OLLAMA_RESEARCH_CONTEXT", scope)
    child = agent.command(["-p", "Research Date filtering", "--model", "sonnet"])
    assert scope in child[child.index("--system-prompt") + 1]
    assert agent.WORKER_WORKFLOW in child[child.index("--system-prompt") + 1]


def test_missing_workflow_is_an_error_instead_of_simulated_research(local, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: local)
    with pytest.raises(ValueError, match="Install the /dr workflow"):
        agent.research_context(es.research_prompt("DATE Criteria", "dr"))


def test_local_job_does_not_display_anthropic_price_estimates(fake_claude, tmp_path, home):
    lines = []
    log = tmp_path / "local.log"
    result = es.run_claude_job([str(fake_claude), "-p", "test"], tmp_path,
                               timeout=30, log=log, emit=lines.append,
                               cancel=threading.Event(), provider="ollama")
    assert result.status == "ok"
    assert any(line.startswith("result: success") for line in lines)
    assert all("$0.50" not in line for line in lines)
    assert '"total_cost_usd"' in log.read_text()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process lifecycle")
def test_worker_timeout_does_not_leave_a_launcher_child(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    pidfile = tmp_path / "pid"
    for name in ("ollama", "llmsx-ollama-agent", "claude"):
        script = bindir / name
        script.write_text(f"#!{sys.executable}\nimport os,time\n"
                          f"open({str(pidfile)!r}, 'w').write(str(os.getpid()))\n"
                          "time.sleep(30)\n")
        script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("PYTHONPATH", str(Path(agent.__file__).resolve().parents[1]))
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path))
    monkeypatch.setenv("LLMSX_OLLAMA_MODEL", "local-test")
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run([sys.executable, "-m", "llmsx.ollama_agent", "-p", "hello"],
                       timeout=1, check=True, capture_output=True)
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
