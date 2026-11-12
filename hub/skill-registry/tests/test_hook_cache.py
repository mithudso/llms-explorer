import json
import os
import subprocess
import sys
import time

import pytest

from skill_registry.hook_cache import load_cache, refresh_cache


def row(identity, name, description, **extras):
    return {"id": identity, "name": name, "description": description,
            "sha256": identity * 64, "release_sha256": "f" * 64, **extras}


class Catalog:
    def catalog(self, after="", limit=200):
        if not after:
            return {"skills": [row("a", "mongodb-query-tuning", "Diagnose slow MongoDB queries",
                text="PRIVATE WORKFLOW BODY", source={"path": "/private/source"},
                metadata={"keywords": ["explain", "indexes"], "triggers": ["slow queries"]})],
                "has_more": True, "next_after": "a"}
        return {"skills": [row("b", "gardening", "Grow flowers and water plants")],
                "has_more": False, "next_after": None}


def test_cache_fetches_only_metadata_and_routes_without_skill_files(tmp_path):
    path = tmp_path / "routing.json"
    receipt = refresh_cache(Catalog(), path)
    assert receipt["skills"] == 2 and receipt["metadata_only"]
    assert path.stat().st_mode & 0o777 == 0o600
    text = path.read_text()
    assert "PRIVATE WORKFLOW BODY" not in text and "/private/source" not in text
    store = load_cache(path)
    result = store.search("Diagnose slow MongoDB queries with explain and indexes")
    assert result["hits"][0]["name"] == "mongodb-query-tuning"
    assert result["hits"][0]["release_sha256"] == "f" * 64
    assert not result["semantic"]
    assert store.search("What is the current time in New York?")["hits"] == []
    assert store.search("Please help me set up a system for my tasks")["hits"] == []


def test_cache_requires_fresh_unmodified_schema_and_preserves_on_failed_refresh(tmp_path):
    path = tmp_path / "routing.json"
    refresh_cache(Catalog(), path)
    original = path.read_bytes()
    value = json.loads(original)
    assert load_cache(path, now=value["generated_at"] + 86401) is None
    assert load_cache(path, now=value["generated_at"] - 1) is None

    class Broken:
        def catalog(self, **kwargs):
            raise ValueError("Network failed")
    with pytest.raises(ValueError):
        refresh_cache(Broken(), path)
    assert path.read_bytes() == original
    path.write_text("invalid json")
    assert load_cache(path) is None


def test_cache_detects_pagination_cycle(tmp_path):
    class Repeated:
        def catalog(self, **kwargs):
            return {"skills": [], "has_more": True, "next_after": "same"}
    with pytest.raises(ValueError, match="did not advance"):
        refresh_cache(Repeated(), tmp_path / "routing.json")


def test_real_hook_uses_local_metadata_cache_with_no_credentials(tmp_path):
    path = tmp_path / "routing.json"
    refresh_cache(Catalog(), path)
    env = {key: value for key, value in os.environ.items()
           if key not in {"MONGODB_URI2", "SKILL_REGISTRY_ENV_FILE", "SKILL_MCP_URL"}}
    started = time.monotonic()
    result = subprocess.run([sys.executable, "-m", "skill_registry.prompt_hook"],
        input=b'{"prompt":"Diagnose slow MongoDB queries and explain indexes"}',
        capture_output=True, timeout=3, env={**env, "SKILL_HOOK_CACHE": str(path)})
    assert result.returncode == 0 and result.stderr == b""
    assert "mongodb-query-tuning" in json.loads(result.stdout)[
        "hookSpecificOutput"]["additionalContext"]
    assert time.monotonic() - started < 2
