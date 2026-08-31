# ruff: noqa: E501  -- fixture strings are real llms lines
"""Follow-ups from the /ldo estate run: split-aware MCP index tool, keyword /
hybrid query modes, outline descriptions, keyword-index in the pipeline's
index stage, and the lint gate in docset_rollout cleanup."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "mcp-server"))
import hub_mcp_server  # noqa: E402
from docset_refine import export_llms  # noqa: E402


# ------------------------------------------------------------- export --


def test_outline_description_for_pages_without_prose():
    page = {"url": "https://h/errors", "text": "# All\n\n## All Validation Errors\n\n### Account\n\n"
            "| Code | Text |\n|---|---|\n| 1 | a |\n| 2 | b |\n"}
    d = export_llms._description(page, {})
    assert d == "Covers All Validation Errors, Account; 2 table rows."
    assert export_llms._description({"url": "u", "text": "# Only a title\n"}, {}) == ""
    code = {"url": "u", "text": "```\n1\n2\ncurl https://api.example.com/v1 -H x\n```\n"}
    assert export_llms._description(code, {}) == "Code sample: curl https://api.example.com/v1 -H x"


def test_empty_pages_are_dropped_from_exports():
    pages = [{"url": "https://h/a", "text": "x" * 50}, {"url": "https://h/empty", "text": ""},
             {"url": "https://h/short", "text": "hi"}]
    kept, n = export_llms.drop_empty_pages(pages)
    assert [p["url"] for p in kept] == ["https://h/a"] and n == 2


def test_dedupe_pages_drops_trailing_slash_twins():
    pages = [{"url": "https://h/a/"}, {"url": "https://h/a"}, {"url": "https://h/b"}]
    assert [p["url"] for p in export_llms.dedupe_pages(pages)] == ["https://h/a/", "https://h/b"]


# ---------------------------------------------------------------- mcp --


class FakeStore:
    def __init__(self, tmp):
        self.tmp = tmp
        self.kw_built = 0

    def list_docsets(self):
        return [{"docset": "ex__ex", "source_path": str(self.tmp / "ex.clean.md")}]

    def docset_model(self, key):
        return "m"

    def query(self, key, qvec, top):
        return [{"score": 0.9, "url": "https://h/a", "seq": 1, "text": "vector hit"},
                {"score": 0.8, "url": "https://h/b", "seq": 2, "text": "both"}]

    def keyword_count(self, key):
        return self.kw_built

    def keyword_replace(self, key, rows):
        self.kw_built = 3

    def dump_chunks(self, key):
        return iter([])

    def keyword_query(self, key, q, top, mode="any"):
        return [{"score": 5.0, "url": "https://h/b", "seq": 2, "snippet": "both"},
                {"score": 1.0, "url": "https://h/c", "seq": 3, "snippet": "kw only"}]


@pytest.fixture
def fake(tmp_path, monkeypatch):
    store = FakeStore(tmp_path)
    monkeypatch.setattr(hub_mcp_server, "_get_store", lambda: store)
    monkeypatch.setattr(hub_mcp_server.docset_indexer, "resolve_layer",
                        lambda s, d, layer: (d + "__facts", "facts"))
    monkeypatch.setattr(hub_mcp_server.embed_core, "embed_texts", lambda qs, model=None: [[0.1]])
    return store


def test_query_modes_keyword_builds_lazily_and_hybrid_fuses(fake):
    kw = json.loads(hub_mcp_server.hub_query_docset("ex__ex", "PreToolUse", mode="keyword"))
    assert kw["mode"] == "keyword" and fake.kw_built == 3 and kw["results"][0]["url"] == "https://h/b"
    hy = json.loads(hub_mcp_server.hub_query_docset("ex__ex", "PreToolUse", mode="hybrid"))
    assert hy["results"][0]["url"] == "https://h/b" and hy["results"][0]["legs"] == 2
    assert {r["url"] for r in hy["results"]} == {"https://h/a", "https://h/b", "https://h/c"}
    assert hub_mcp_server.hub_query_docset("ex__ex", "q", mode="nope").startswith("ERROR")
    sem = json.loads(hub_mcp_server.hub_query_docset("ex__ex", "q"))
    assert sem["mode"] == "semantic" and sem["results"][0]["url"] == "https://h/a"


def test_docset_index_serves_sections_of_a_split(fake, tmp_path):
    d = tmp_path / "ex.llms"
    (d / "guide").mkdir(parents=True)
    (d / "llms.txt").write_text("# Ex\n\n> S.\n\n## Sections\n\n- [Guide](guide/llms.txt): 1 pages\n")
    (d / "guide" / "llms.txt").write_text("# Ex — Guide\n\n> 1 page.\n\n## Guide\n\n- [A](https://h/a.md): a\n")
    (d / "manifest.json").write_text(json.dumps({"sections": ["guide/llms.txt"]}))
    root = json.loads(hub_mcp_server.hub_docset_index("ex__ex"))
    assert root["sections"] == ["guide/llms.txt"] and root["served_at"].endswith("/d/ex/llms.txt")
    sec = json.loads(hub_mcp_server.hub_docset_index("ex__ex", "guide/llms.txt"))
    assert sec["text"].startswith("# Ex — Guide") and sec["served_at"].endswith("/d/ex/guide/llms.txt")
    assert hub_mcp_server.hub_docset_index("ex__ex", "../llms.txt").startswith("ERROR")
    assert hub_mcp_server.hub_docset_index("ex__ex", "guide/manifest.json").startswith("ERROR")


# ----------------------------------------------------------- pipeline --


def test_index_stage_builds_keyword_indexes(tmp_path):
    spec = importlib.util.spec_from_file_location("pm_followups", ROOT / "scripts" / "pipeline_manager.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    mirror = tmp_path / "ex.dev.md"
    mirror.write_text("m")
    ref = tmp_path / "ex.dev.reference"
    ref.mkdir()
    (ref / "all_units.jsonl").write_text('{"id":"u1"}\n')
    argvs = pm.index_argvs(mirror)
    cmds = [(a[2], a[-2:]) for a in argvs]
    key = pm.docset_key_for(mirror)
    assert cmds == [("index", ["--name", key]), ("keyword-index", ["--layer", "raw"]),
                    ("index", ["--name", key]), ("keyword-index", ["--layer", "facts"])]
    assert argvs[1][3] == key and argvs[3][3] == key


# ------------------------------------------------------------ rollout --


def test_cleanup_lint_gate_counts_high_findings(tmp_path):
    import docset_rollout as dr

    d = tmp_path / "ex.llms"
    d.mkdir()
    (d / "llms.txt").write_text("# One\n# Two\n\n## A\n\n- [x](https://e.com/x.md): notes that are long enough here\n")
    r = dr.cleanup(tmp_path, log=lambda s: None)
    assert r["lint"] == {"docsets": 1, "files": 1, "high": 1, "medium": pytest.approx(r["lint"]["medium"])}
    assert r["lint"]["high"] == 1
    assert "lint" not in dr.cleanup(tmp_path, log=lambda s: None, lint=False)


# ------------------------------------------------------- snapshot hook --


def test_snapshot_refresh_is_best_effort(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("pm_snapshot", ROOT / "scripts" / "pipeline_manager.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    monkeypatch.setenv("LLMS_EXPLORER_REFRESH", "1")  # conftest opts every test out
    monkeypatch.setattr(pm, "SNAPSHOT_REFRESH", tmp_path / "missing.sh")
    pm._refresh_snapshot()  # no script: silently nothing
    script = tmp_path / "refresh.sh"
    script.write_text("#!/bin/sh\necho ran > \"$(dirname \"$0\")/ran\"\n")
    monkeypatch.setattr(pm, "SNAPSHOT_REFRESH", script)
    pm._refresh_snapshot()
    assert (tmp_path / "ran").read_text().strip() == "ran"
    script.write_text("#!/bin/sh\nexit 3\n")
    pm._refresh_snapshot()  # a failing script never raises
    (tmp_path / "ran").unlink()
    monkeypatch.setenv("LLMS_EXPLORER_REFRESH", "0")
    script.write_text("#!/bin/sh\necho ran > \"$(dirname \"$0\")/ran\"\n")
    pm._refresh_snapshot()
    assert not (tmp_path / "ran").exists()  # opted out
