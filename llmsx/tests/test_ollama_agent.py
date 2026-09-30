"""Regression coverage for real local agent dispatch rather than plain chat."""
import json
import sys

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
    assert args[:6] == ["/bin/ollama", "launch", "claude", "--model",
                        "llmsx-research", "--yes"]
    assert "sonnet" not in args and "/old/empty.json" not in args
    assert args.count("--mcp-config") == 1
    assert args[args.index("--mcp-config") + 1] == str(local / "ollama-mcp.json")
    assert args[args.index("--max-turns") + 1] == "12"
    assert args[-2:] == ["--output-format", "json"]
    assert "mcp__firecrawl__firecrawl_search" in args[args.index("--allowedTools") + 1]


def test_main_routes_nested_agents_without_mutating_parent_environment(local, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SIMPLE", "1")
    monkeypatch.setenv("CLAUDE_CODE_SAFE_MODE", "1")
    monkeypatch.setattr(sys, "argv", ["llmsx-ollama-agent", "-p", "research"])
    captured = {}
    monkeypatch.setattr(agent.os, "execvpe", lambda binary, argv, env: captured.update(env))
    assert agent.main() == 0
    assert captured["DR_CLAUDE_BIN"] == "/bin/llmsx-ollama-agent"
    assert captured["LLMSX_OLLAMA_MODEL"] == "llmsx-research"
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
    event = {"type": "assistant", "message": {"content": [
        {"type": "text", "text": "\x1b[31mhello\x1b[0m"}]}}
    assert es.summarize_event(json.dumps(event)) == "assistant: hello"
