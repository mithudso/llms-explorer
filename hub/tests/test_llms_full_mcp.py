"""hub_llms_full_list / hub_llms_full_read MCP tools over a fixture mirror."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server"))
import hub_mcp_server  # noqa: E402
import llms_full_catalog as lfc  # noqa: E402

BODY = "# Hooks\nSource: https://d.example/hooks\n\nhook body\n" + "x" * 1200


@pytest.fixture
def mirror(tmp_path, monkeypatch):
    base = tmp_path / "llms-full"
    monkeypatch.setattr(lfc, "BASE_DIR", base)
    files = base / "files"
    files.mkdir(parents=True)
    (files / "docs.example.txt").write_text(BODY)
    manifest = {
        "docs.example": {"key": "docs.example", "url": "https://docs.example/llms-full.txt",
                         "name": "Example", "site": "https://example",
                         "category": "developer tools",
                         "status": "ok", "bytes": len(BODY), "pages": 1,
                         "file": str(files / "docs.example.txt"), "fetched_at": "t"},
        "blob.dev": {"key": "blob.dev", "url": "https://blob.dev/llms-full.txt", "name": "Blob",
                     "site": "", "category": "", "status": "ok", "bytes": len(BODY), "pages": 0,
                     "file": str(files / "docs.example.txt"), "fetched_at": "t"},
        "spam.biz": {"key": "spam.biz", "url": "https://spam.biz/llms-full.txt", "name": "Spam",
                     "site": "", "category": "agency services", "status": "rejected",
                     "reason": "HTML body (soft 404)", "bytes": 3000, "pages": 0,
                     "fetched_at": "t"},
    }
    (base / "manifest.json").write_text(json.dumps(manifest))
    return base


def test_list_defaults_to_downloaded_with_pages(mirror):
    out = json.loads(hub_mcp_server.hub_llms_full_list())
    assert out["total"] == 1 and [e["key"] for e in out["entries"]] == ["docs.example"]
    # min_pages=0 shows the 0-page blob too; the rejected row still needs status
    out = json.loads(hub_mcp_server.hub_llms_full_list(min_pages=0))
    assert [e["key"] for e in out["entries"]] == ["blob.dev", "docs.example"]
    ex = next(e for e in out["entries"] if e["key"] == "docs.example")
    assert ex["category"] == "developer tools"
    assert out["dir"] == str(mirror / "files")


def test_list_filters(mirror):
    assert json.loads(hub_mcp_server.hub_llms_full_list(status="all"))["total"] == 2
    assert json.loads(hub_mcp_server.hub_llms_full_list(status="all", min_pages=0))["total"] == 3
    out = json.loads(hub_mcp_server.hub_llms_full_list(status="all", query="spam"))
    assert [e["key"] for e in out["entries"]] == ["spam.biz"]
    assert out["entries"][0]["reason"].startswith("HTML")
    out = json.loads(hub_mcp_server.hub_llms_full_list(status="all", category="Agency Services"))
    assert [e["key"] for e in out["entries"]] == ["spam.biz"]
    out = json.loads(hub_mcp_server.hub_llms_full_list(status="all", min_pages=0, limit=1))
    assert out["total"] == 3 and out["returned"] == 1


def test_read_slice_and_page(mirror):
    out = json.loads(hub_mcp_server.hub_llms_full_read("docs.example", limit=7))
    assert out["text"] == "# Hooks" and out["next_offset"] == 7
    out = json.loads(hub_mcp_server.hub_llms_full_read("docs.example", page="hooks"))
    assert out["page_url"] == "https://d.example/hooks" and out["text"].startswith("hook body")
    assert "error" in json.loads(hub_mcp_server.hub_llms_full_read("spam.biz"))
    assert hub_mcp_server.hub_llms_full_read("  ").startswith("ERROR")


def test_list_is_empty_without_a_mirror(tmp_path, monkeypatch):
    monkeypatch.setattr(lfc, "BASE_DIR", tmp_path / "nothing")
    assert json.loads(hub_mcp_server.hub_llms_full_list())["total"] == 0
