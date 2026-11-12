import json
import os
import subprocess
import sys

import pytest

from skill_registry.prompt_hook import HTTPStore, suggestions


class Store:
    def __init__(self, hits):
        self.hits = hits

    def search(self, query, top, mode):
        return {"hits": self.hits}


def test_hook_suggests_relevant_metadata_without_loading_or_executing():
    hits = [{"id": "s1", "name": "mongodb-query-tuning", "description": "Optimize MongoDB queries",
             "sha256": "a" * 64, "release_sha256": "b" * 64,
             "text": "NEVER INCLUDE THE SKILL BODY"},
            {"id": "irrelevant", "name": "gardening", "description": "Water plants"}]
    result = suggestions("Optimize the slow MongoDB queries in my application", Store(hits))
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "mongodb-query-tuning" in context and "skill_get" in context
    assert "NEVER INCLUDE" not in context and "gardening" not in context
    assert json.loads(context.split("\n", 1)[1])[0]["pin_sha256"] == "b" * 64
    assert result["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_hook_supports_semantic_paraphrases_and_caps_candidates():
    hits = [{"id": str(i), "name": "workflow", "semantic_score": 0.82} for i in range(8)]
    context = suggestions("A task with different words entirely", Store(hits))[
        "hookSpecificOutput"]["additionalContext"]
    assert len(json.loads(context.split("\n", 1)[1])) == 3
    assert suggestions("short", Store(hits)) == {}
    assert suggestions("Please help me with a random unrelated task", Store([
        {"name": "foo", "description": "bar", "semantic_score": 0.2}])) == {}
    assert suggestions("A task with different words entirely", Store([
        {"id": "semantic", "name": "workflow", "channels": {"semantic": {"score": 0.85}}}]))


@pytest.mark.parametrize("payload", [b"not json", b"{}", b'{"prompt":7}', b"x" * 140000])
def test_hook_malformed_input_is_silent_and_successful(payload):
    result = subprocess.run([sys.executable, "-m", "skill_registry.prompt_hook"], input=payload,
                            capture_output=True, timeout=5)
    assert result.returncode == 0 and result.stdout == b"" and result.stderr == b""


def test_hook_missing_credentials_fails_open_without_logs():
    env = {key: value for key, value in os.environ.items()
           if key not in {"MONGODB_URI2", "SKILL_REGISTRY_ENV_FILE", "SKILL_MCP_URL"}}
    result = subprocess.run([sys.executable, "-m", "skill_registry.prompt_hook"],
        input=b'{"prompt":"Please optimize these MongoDB queries"}', capture_output=True,
        timeout=6, env={**env, "SKILL_HOOK_TIMEOUT": "0.2"})
    assert result.returncode == 0 and result.stdout == b"" and result.stderr == b""


def test_hook_remote_client_rejects_plaintext_and_inline_credentials():
    with pytest.raises(ValueError, match="HTTPS"):
        HTTPStore("http://skills.example.test/mcp", "secret")
    with pytest.raises(ValueError, match="separate bearer"):
        HTTPStore("https://user:pass@skills.example.test/mcp", "secret")
    assert HTTPStore("http://127.0.0.1:8741/mcp", "secret")
