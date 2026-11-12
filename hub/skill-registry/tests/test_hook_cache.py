import json
import os
import subprocess
import sys
import time

import pytest

from skill_registry.hook_cache import SCHEMA, MetadataStore, load_cache, refresh_cache


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
    from skill_registry.prompt_hook import suggestions
    named = suggestions("Find gardening", store)
    assert "gardening" in named["hookSpecificOutput"]["additionalContext"]


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


def test_positive_routing_beats_generic_metadata_and_deduplicates_names():
    rows = [
        row("a", "prompt-helper", "Optimize Prism caches and write useful prompts. "
            "Prism caches optimize Prism caches. Generic prompt editing guidance."),
        row("b", "prism-cache-optimizer", "Audit and improve Prism cache efficiency."),
        row("c", "prism-cache-optimizer", "A second installation of the cache optimizer."),
        row("d", "prism-cache-audit", "Inspect Prism cache hit rates and memory costs."),
    ]
    store = MetadataStore(rows)
    result = store.search("Optimize all of my Prism caches")
    assert result["hits"][0]["name"] == "prism-cache-optimizer"
    assert len({hit["name"] for hit in result["hits"]}) == len(result["hits"])
    assert result["reranked_candidates"] <= 200


def test_documents_inflection_and_specific_positive_names_beat_generic_search():
    store = MetadataStore([
        row("a", "Search", "Find official Prism vector API documentation. "
            "Search official Prism vector API documentation and official documentation."),
        row("b", "prism-api-migration", "Migrate Prism API vector clients to newer versions."),
        row("c", "prism-docs", "Use official Prism sources for API and vector documentation."),
    ])
    assert store.search("Find official Prism vector API documentation")["hits"][0][
        "name"] == "prism-docs"


def test_shared_stopwords_silence_greetings_and_skip_when_is_negative_evidence():
    store = MetadataStore([
        row("a", "status-helper", "Explain how you are doing today and summarize the status."),
        row("b", "prompt-helper", "Improve prompts. SKIP when: Prism cache optimization."),
        row("c", "prism-cache-optimizer", "Audit Prism cache optimization."),
    ])
    assert store.search("How are you today?")["hits"] == []
    assert store.search("Please show me how you are doing")["hits"] == []
    hits = store.search("Optimize Prism caches")["hits"]
    assert hits[0]["name"] == "prism-cache-optimizer"
    assert "prompt-helper" not in {hit["name"] for hit in hits}


def test_fresh_subprocess_routes_large_metadata_catalog_within_hook_deadline(tmp_path):
    path = tmp_path / "large-routing.json"
    rows = [{"id": f"noise-{i}", "name": f"unrelated-workflow-{i}",
             "description": "Maintain fictional shipping schedules and warehouse inventory. " * 12,
             "sha256": f"{i:064x}", "release_sha256": "f" * 64}
            for i in range(2662)]
    rows.append(row("a", "prism-runtime-quality", "Review Prism runtime performance and test quality."))
    path.write_text(json.dumps({"schema": SCHEMA, "generated_at": time.time(), "skills": rows}))
    env = {key: value for key, value in os.environ.items()
           if key not in {"MONGODB_URI2", "SKILL_REGISTRY_ENV_FILE", "SKILL_MCP_URL"}}
    result = subprocess.run([sys.executable, "-m", "skill_registry.prompt_hook"],
        input=b'{"prompt":"Review Prism runtime performance and test quality"}',
        capture_output=True, timeout=4.5, env={**env, "SKILL_HOOK_CACHE": str(path),
                                            "SKILL_HOOK_TIMEOUT": "3"})
    assert result.returncode == 0 and result.stderr == b""
    assert "prism-runtime-quality" in json.loads(result.stdout)[
        "hookSpecificOutput"]["additionalContext"]
