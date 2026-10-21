"""Public citation receipts must come from anonymous primary metadata."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
