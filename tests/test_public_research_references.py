"""Public citation receipts must come from anonymous primary metadata."""
import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_references", ROOT / "scripts/public_research_references.py")
references = importlib.util.module_from_spec(spec)
spec.loader.exec_module(references)


def test_verification_includes_unchanged_packs_and_withholds_inaccessible_keys(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    packs = repo / "site/src/data/concepts"
    packs.mkdir(parents=True)
    (packs / "old.json").write_text(json.dumps({"text": "SERVER-10001 and SERVER-10002"}))
    (hub / "research").mkdir(parents=True)

    def response(command, **kwargs):
        if "SERVER-10001?" in command[-1]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"key": "SERVER-10001", "fields": {"summary": "Public issue"}}))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"errorMessages": ["Unauthorized"]}))

    with patch.object(references.subprocess, "run", side_effect=response) as fetch:
        writes, blocked = references.resolve(repo, hub, {})
    assert fetch.call_count == 2
    assert blocked == ["SERVER-10002"]
    assert "SERVER-10001" in writes[repo / ".privacy-allowlist"]
    assert "SERVER-10002" not in writes[repo / ".privacy-allowlist"]
    assert not (repo / ".privacy-allowlist").exists(), "planning must not mutate the checkout"
    for path, text in writes.items():
        path.write_text(text)
    with patch.object(references.subprocess, "run") as fetch:
        _, blocked = references.resolve(repo, hub, {})
    fetch.assert_not_called()
    assert blocked == ["SERVER-10002"]


def test_repository_export_citations_are_verified_before_publication(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    ticket = "SERVER-" + "99118822"
    changes = {repo / "outputs/llms-concepts/example.llms/units.jsonl": json.dumps({"source_url": "https://jira.mongodb.org/browse/" + ticket})}
    with patch.object(references.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout='{"errorMessages":["Unauthorized"]}')) as fetch:
        writes, blocked = references.resolve(repo, hub, changes)
    assert fetch.call_count == 1
    assert blocked == [ticket]
    assert ticket in writes[hub / "research/.site-public-references.json"]


def test_stale_negative_cache_drains_in_bounded_batches_without_blocking_refresh(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    cache_path = hub / "research/.site-public-references.json"
    cache_path.parent.mkdir(parents=True)
    old = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    cache = {f"SERVER-{number}": {"public": False, "checked": old} for number in range(10000, 10201)}
    cache_path.write_text(json.dumps(cache))
    response = SimpleNamespace(returncode=0, stdout='{"errorMessages":["Unauthorized"]}')
    with patch.object(references.subprocess, "run", return_value=response) as fetch:
        writes, blocked = references.resolve(repo, hub, {})
    assert fetch.call_count == 200
    assert set(blocked) == set(cache)
    refreshed = json.loads(writes[cache_path])
    assert refreshed["SERVER-10200"]["checked"] == old
    cache_path.write_text(writes[cache_path])
    response = SimpleNamespace(returncode=0, stdout=json.dumps({"key": "SERVER-10200", "fields": {"summary": "Now public"}}))
    with patch.object(references.subprocess, "run", return_value=response) as fetch:
        writes, blocked = references.resolve(repo, hub, {})
    assert fetch.call_count == 1
    assert "SERVER-10200" not in blocked
    assert "SERVER-10200" in writes[repo / ".privacy-allowlist"]


def test_current_content_has_priority_over_stale_background_checks(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    cache_path = hub / "research/.site-public-references.json"
    cache_path.parent.mkdir(parents=True)
    old = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    cache_path.write_text(json.dumps({f"SERVER-{number}": {"public": False, "checked": old} for number in range(10000, 10201)}))
    new = "SERVER-99999"
    changes = {repo / "site/src/data/concepts/new.json": json.dumps({"text": new})}
    def response(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps({"key": new, "fields": {"summary": "Public"}}) if new in command[-1] else '{}')
    with patch.object(references.subprocess, "run", side_effect=response) as fetch:
        writes, blocked = references.resolve(repo, hub, changes)
    assert fetch.call_count == 200 and len(blocked) == 201
    assert new in writes[repo / ".privacy-allowlist"]


def test_more_than_200_uncached_current_citations_still_requires_split_refresh(tmp_path):
    repo, hub = tmp_path / "repo", tmp_path / "hub"
    changes = {repo / "site/src/data/concepts/new.json": " ".join(f"SERVER-{n}" for n in range(20000, 20201))}
    with patch.object(references.subprocess, "run") as fetch, pytest.raises(ValueError, match="More than 200 new"):
        references.resolve(repo, hub, changes)
    fetch.assert_not_called()
