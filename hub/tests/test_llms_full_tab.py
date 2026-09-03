"""LLMs-full tab: model module (rows/detail/search/argv builders) + the
catalog's manage ops (delete, export-mirror) + a TUI drive-through."""

import json
from pathlib import Path

import pytest

import llms_full_catalog as catalog
from hub_manager import core, llms_full

BODY = ("# Hooks reference\nSource: https://d.example/hooks\n\nHooks run shell commands.\n\n"
        "# Overview\nSource: https://d.example/overview\n\nConnection pooling is reused.\n"
        + "x" * 1200)


@pytest.fixture
def mirror(tmp_path, monkeypatch):
    base = tmp_path / "llms-full"
    monkeypatch.setattr(catalog, "BASE_DIR", base)
    files = base / "files"
    files.mkdir(parents=True)
    (files / "d.example.txt").write_text(BODY)
    catalog._save(catalog.catalog_path(base), [
        {"key": "d.example", "url": "https://d.example/llms-full.txt", "name": "D Docs",
         "site": "https://d.example", "category": "developer tools",
         "description": "Docs for D.", "sources": ["llms-txt-hub", "llmstxt.site"]},
        {"key": "gone.dev", "url": "https://gone.dev/llms-full.txt", "name": "Gone",
         "site": "", "category": "", "description": "", "sources": ["llmstxt.site"]},
    ])
    catalog._save(catalog.manifest_path(base), {
        "d.example": {"key": "d.example", "url": "https://d.example/llms-full.txt",
                      "name": "D Docs", "site": "https://d.example", "category": "",
                      "status": "ok", "bytes": len(BODY), "pages": 2,
                      "file": str(files / "d.example.txt"), "fetched_at": "2026-08-30T01:00:00"},
        "gone.dev": {"key": "gone.dev", "url": "https://gone.dev/llms-full.txt", "name": "Gone",
                     "site": "", "category": "", "status": "failed", "reason": "HTTP 404",
                     "bytes": 0, "pages": 0, "fetched_at": "2026-08-30T01:00:00"},
    })
    return base


def test_rows_join_catalog_metadata_and_filter_by_status(mirror):
    ok = llms_full.rows()
    assert [r["key"] for r in ok] == ["d.example"]
    assert ok[0]["category"] == "developer tools"      # from the catalog, not the manifest
    assert ok[0]["description"] == "Docs for D."
    assert ok[0]["sources"] == ["llms-txt-hub", "llmstxt.site"]
    assert [r["key"] for r in llms_full.rows(status="all")] == ["d.example", "gone.dev"]
    assert [r["key"] for r in llms_full.rows(status="failed")] == ["gone.dev"]


def test_sort_rows_and_size_str():
    rows = [{"key": "b", "pages": 1, "bytes": 5_000_000, "fetched_at": "2", "name": "Zed"},
            {"key": "a", "pages": 9, "bytes": 900, "fetched_at": "1", "name": "alpha"}]
    assert [r["key"] for r in llms_full.sort_rows(rows, "key")] == ["a", "b"]
    assert [r["key"] for r in llms_full.sort_rows(rows, "pages", reverse=True)] == ["a", "b"]
    assert [r["key"] for r in llms_full.sort_rows(rows, "bytes")] == ["a", "b"]
    assert [r["key"] for r in llms_full.sort_rows(rows, "fetched")] == ["a", "b"]
    assert [r["key"] for r in llms_full.sort_rows(rows, "name")] == ["a", "b"]
    assert llms_full.size_str(900) == "900"
    assert llms_full.size_str(45_000) == "45K"
    assert llms_full.size_str(5_000_000) == "5.0M"


def test_detail_shows_link_titles_and_failure_reason(mirror, monkeypatch):
    monkeypatch.setattr(core, "MIRROR_OUT_DIR", mirror / "text-mirror")
    rows = {r["key"]: r for r in llms_full.rows(status="all")}
    d = llms_full.detail(rows["d.example"])
    assert "[link=file://" in d and "d.example.txt" in d
    assert "Hooks reference · Overview" in d
    assert "listed by:   llms-txt-hub, llmstxt.site" in d
    assert "mirror:" not in d  # nothing exported yet
    g = llms_full.detail(rows["gone.dev"])
    assert "failed — HTTP 404" in g and "file:" not in g


def test_search_file_carries_source_url(mirror):
    path = str(mirror / "files" / "d.example.txt")
    ok, text = llms_full.search_file(path, "connection pool", "fuzzy")
    assert ok and "https://d.example/overview" in text and "Connection pooling" in text
    ok, text = llms_full.search_file(path, r"shell\s+commands", "regex")
    assert ok and "https://d.example/hooks" in text
    assert llms_full.search_file(path, "(", "regex")[0] is False
    assert llms_full.search_file("", "x", "fuzzy") == (False, "file missing: .")


def test_argv_builders_and_editor(monkeypatch):
    monkeypatch.setattr(core, "python_for_hub", lambda: "/py")
    monkeypatch.setattr(core, "MIRROR_OUT_DIR", Path("/tm"))
    entry = {"key": "d.example", "url": "https://d.example/llms-full.txt"}
    assert llms_full.redownload_argv(entry)[2:] == [
        "download", "--refresh", "--only", "https://d.example/llms-full.txt", "--jobs", "1"]
    chain = llms_full.refresh_all_argvs()
    assert [c[2] for c in chain] == ["compile", "download"] and "--retry-failed" in chain[1]
    add = llms_full.add_argvs(["https://a/llms-full.txt", "https://b/llms-full.txt"])
    assert add[0][2:] == ["compile", "--seed", "https://a/llms-full.txt",
                          "--seed", "https://b/llms-full.txt"]
    assert len(add) == 3 and add[2][4] == "https://b/llms-full.txt"
    idx = llms_full.index_argvs(entry)
    assert idx[0][2:] == ["export-mirror", "d.example", "/tm/d.example.llms-full.md"]
    assert idx[1][2:] == ["index", "/tm/d.example.llms-full.md", "--name", "d.example"]
    monkeypatch.setenv("VISUAL", "code -w")
    assert llms_full.editor_argv("/f") == ["code", "-w", "/f"]
    monkeypatch.delenv("VISUAL")
    monkeypatch.delenv("EDITOR", raising=False)
    assert llms_full.editor_argv("/f") == ["vi", "/f"]


def test_catalog_delete_and_export_mirror(mirror, tmp_path):
    out = tmp_path / "text-mirror" / "d.example.llms-full.md"
    res = catalog.export_mirror("d.example", out)
    assert res["pages"] == 2 and out.exists()
    text = out.read_text()
    assert "URL: https://d.example/hooks" in text and "# Hooks reference" in text
    assert "error" in catalog.export_mirror("gone.dev", tmp_path / "x.md")

    res = llms_full.delete("d.example")
    assert res == {"key": "d.example", "deleted": True, "file_removed": True}
    assert not (mirror / "files" / "d.example.txt").exists()
    assert "d.example" not in json.loads(catalog.manifest_path(mirror).read_text())
    assert llms_full.delete("d.example")["deleted"] is False


def test_export_mirror_wraps_a_pageless_blob(mirror):
    files = mirror / "files"
    (files / "blob.txt").write_text("# Just markdown\n\nno Source lines\n" + "y" * 1200)
    man = json.loads(catalog.manifest_path(mirror).read_text())
    man["blob"] = {"key": "blob", "url": "https://blob/llms-full.txt", "name": "Blob",
                   "status": "ok", "bytes": 1300, "pages": 0, "file": str(files / "blob.txt")}
    catalog._save(catalog.manifest_path(mirror), man)
    res = catalog.export_mirror("blob", mirror / "blob.md")
    assert res["pages"] == 1
    assert "URL: https://blob/llms-full.txt" in (mirror / "blob.md").read_text()


def test_catalog_cli_delete_and_export(mirror, tmp_path, capsys):
    assert catalog.main(["export-mirror", "d.example", str(tmp_path / "m.md")]) == 0
    assert catalog.main(["delete", "d.example"]) == 0
    assert catalog.main(["delete", "d.example"]) == 1
    assert catalog.main(["export-mirror", "nope", str(tmp_path / "n.md")]) == 1


def _stub_tabs(monkeypatch):
    from hub_manager import (docsets as docsets_mod, health, queue_model,
                             remotes as remotes_mod, usage as usage_mod)
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(queue_model, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, "[]"))


def test_tab_lists_filters_details_and_searches(hub_tmp, mirror, monkeypatch):
    import asyncio

    from textual.widgets import DataTable, Input, RichLog, Select

    from hub_manager.app import HubManagerApp

    _stub_tabs(monkeypatch)
    monkeypatch.setattr(core, "MIRROR_OUT_DIR", mirror / "text-mirror")

    async def drive() -> dict:
        app = HubManagerApp()
        async with app.run_test(size=(140, 45)) as pilot:
            await pilot.pause()
            app._activate_pane("tab-llmsfull")
            await pilot.pause()
            table = app.query_one("#llmsfull-table", DataTable)
            ok_rows = table.row_count
            # status filter → failed rows appear
            app.query_one("#llmsfull-status", Select).value = "all"
            await pilot.pause()
            all_rows = table.row_count
            app.query_one("#llmsfull-filter", Input).value = "gone"
            await pilot.pause()
            filtered = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
            app.query_one("#llmsfull-filter", Input).value = ""
            await pilot.pause()
            # click the ok row → detail
            table.move_cursor(row=0)
            await pilot.pause()
            table.action_select_cursor()
            await pilot.pause()
            detail = "\n".join(str(line.text) for line in
                               app.query_one("#llmsfull-results", RichLog).lines)
            # search inside it
            app.query_one("#llmsfull-mode", Select).value = "regex"
            app.query_one("#llmsfull-query", Input).value = "pooling"
            app.query_one("#llmsfull-search").press()
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.pause()
            pane = "\n".join(str(line.text) for line in
                             app.query_one("#llmsfull-results", RichLog).lines)
            return {"ok": ok_rows, "all": all_rows, "filtered": filtered,
                    "detail": detail, "pane": pane}

    r = asyncio.run(drive())
    assert r["ok"] == 1 and r["all"] == 2 and r["filtered"] == ["gone.dev"]
    assert "d.example" in r["detail"] and "D Docs" in r["detail"]
    assert "Hooks reference" in r["detail"]
    assert ">>> [regex] [d.example] pooling" in r["pane"]
    assert "https://d.example/overview" in r["pane"]


def test_tab_index_and_delete_actions(hub_tmp, mirror, monkeypatch):
    import asyncio

    from textual.widgets import DataTable

    from hub_manager import app as app_mod
    from hub_manager.app import HubManagerApp

    _stub_tabs(monkeypatch)
    monkeypatch.setattr(core, "MIRROR_OUT_DIR", mirror / "text-mirror")
    monkeypatch.setattr(core, "python_for_hub", lambda: "/py")
    started: list[tuple[str, list[list[str]]]] = []

    async def drive() -> dict:
        app = HubManagerApp()
        monkeypatch.setattr(app, "_start_job_chain",
                            lambda slot, argvs, log: started.append((slot, argvs)))
        async with app.run_test(size=(140, 45)) as pilot:
            await pilot.pause()
            app._activate_pane("tab-llmsfull")
            await pilot.pause()
            app.query_one("#llmsfull-table", DataTable).move_cursor(row=0)
            await pilot.pause()
            app.action_index_llms_full()
            await pilot.pause()
            # delete: the confirm screen comes up; answer yes
            app.action_delete_item()
            await pilot.pause()
            assert isinstance(app.screen, app_mod.ConfirmScreen)
            app.screen.dismiss(True)
            await pilot.pause()
            await pilot.pause()
            return {"rows": app.query_one("#llmsfull-table", DataTable).row_count}

    r = asyncio.run(drive())
    assert started and started[0][0] == "index"
    assert started[0][1][0][2] == "export-mirror" and started[0][1][1][2] == "index"
    assert r["rows"] == 0                                   # the only ok row is gone
    assert not (mirror / "files" / "d.example.txt").exists()
