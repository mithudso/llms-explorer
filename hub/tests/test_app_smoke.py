"""Textual pilot smoke test: the app mounts, all tabs exist, queue renders.

Network/subprocess-touching refreshes are stubbed so the test is hermetic
and fast.
"""

import asyncio
import json

from hub_manager import core, health
from hub_manager import docsets as docsets_mod
from hub_manager.app import HubManagerApp

TAB_IDS = {"tab-queue", "tab-health", "tab-concepts", "tab-docsets", "tab-llmsfull", "tab-ask",
           "tab-index",
           "tab-mcp", "tab-usage", "tab-remotes", "tab-repos", "tab-scripts",
           "tab-logs", "tab-settings"}


def test_app_smoke(hub_tmp, monkeypatch):
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "https://docs.example.com/": {
            "status": "failed", "stage_done": ["mirror"], "attempts": 3,
            "error": "distill: boom", "updated": "2026-08-21T00:00:00"},
        "https://ok.example.com/": {
            "status": "done", "stage_done": ["distill", "index", "mirror"],
            "attempts": 0, "updated": "2026-08-21T00:00:00"},
    }}))
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [
        health.HealthCheck("stub", True, "all good", check_id="idle-indexer")])
    monkeypatch.setattr(health, "check_mcp", lambda: health.HealthCheck(
        "MCP server (HTTP)", None, "stubbed — stdio"))
    from hub_manager import queue_model as qm
    from hub_manager import usage as usage_mod
    monkeypatch.setattr(qm, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    from hub_manager import remotes as remotes_mod
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, json.dumps([
        {"docset": "example__docs", "pages": 10, "chunks": 42,
         "model": "mxbai-embed-large", "backend": "chroma",
         "updated_at": "2026-08-21 00:00:00"}])))

    async def drive() -> dict:
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from textual.widgets import TabbedContent, TabPane, DataTable
            tabs = {pane.id for pane in app.query(TabPane)}
            queue_rows = app.query_one("#queue-table", DataTable).row_count
            summary = str(app.query_one("#queue-summary").render())
            docsets_table = app.query_one("#docsets-table", DataTable)
            # switch through every tab without crashing
            tc = app.query_one(TabbedContent)
            for tab_id in sorted(TAB_IDS):
                tc.active = tab_id
                await pilot.pause()
            return {"tabs": tabs, "queue_rows": queue_rows,
                    "summary": summary,
                    "docsets_rows": docsets_table.row_count}

    result = asyncio.run(drive())
    assert result["tabs"] == TAB_IDS
    assert result["queue_rows"] == 2
    assert "done=1" in result["summary"] and "failed=1" in result["summary"]
    assert result["docsets_rows"] == 1  # JSON list output parsed into one row


def test_app_retry_and_delete_actions(hub_tmp, monkeypatch):
    """Action glue: modal-callback → queue_model → refresh path."""
    from hub_manager import queue_model
    queue_model.add_urls(["https://gone.example/", "https://fail.example/"])
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "https://gone.example/": {"status": "done", "stage_done": []},
        "https://fail.example/": {"status": "failed", "stage_done": [],
                                  "attempts": 3, "error": "boom"},
    }}))
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, "[]"))
    from hub_manager import queue_model as qm
    from hub_manager import usage as usage_mod
    monkeypatch.setattr(qm, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    from hub_manager import remotes as remotes_mod
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])

    async def drive() -> dict:
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.action_retry_failed()
            await pilot.pause()
            statuses = {i.url: i.status for i in queue_model.load_items()}
            # delete: bypass the confirm modal, invoke its callback directly
            app.push_screen = lambda screen, cb=None: cb(True) if cb else None
            from textual.widgets import DataTable
            table = app.query_one("#queue-table", DataTable)
            table.move_cursor(row=0)
            url = app._selected_url()
            app.action_delete_item()
            await pilot.pause()
            return {"statuses": statuses, "deleted": url,
                    "after": [i.url for i in queue_model.load_items()]}

    result = asyncio.run(drive())
    assert result["statuses"]["https://fail.example/"] == "pending"
    assert result["deleted"] not in result["after"]
    assert len(result["after"]) == 1


def test_down_arrow_descends_from_tab_bar(hub_tmp, monkeypatch):
    """Focus on the tab bar + down arrow moves into the pane content."""
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, "[]"))
    from hub_manager import queue_model as qm
    from hub_manager import usage as usage_mod
    monkeypatch.setattr(qm, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    from hub_manager import remotes as remotes_mod
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])

    async def drive() -> dict:
        from textual.widgets import DataTable, Tabs
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.query_one(Tabs).focus()
            await pilot.pause()
            was_tabs = isinstance(app.focused, Tabs)
            await pilot.press("down")
            await pilot.pause()
            return {"was_tabs": was_tabs,
                    "now_table": isinstance(app.focused, DataTable),
                    "still_tabs": isinstance(app.focused, Tabs)}

    result = asyncio.run(drive())
    assert result["was_tabs"] is True
    assert result["still_tabs"] is False
    assert result["now_table"] is True  # queue tab: first focusable is the table


def test_queue_row_expand_shows_report(hub_tmp, monkeypatch):
    """Enter on a queue row opens the detail modal and fills in a real
    report (stage checklist etc.) once the background worker finishes --
    Ollama/box-health probes are stubbed so the test stays hermetic."""
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "https://docs.example.com/": {
            "status": "running", "stage_done": ["mirror"], "attempts": 1,
            "error": "", "updated": "2026-08-21T00:00:00"},
    }}))
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(health, "check_ollama_hosts", lambda: [
        health.HealthCheck("ollama http://stub:1", True, "stubbed")])
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, "[]"))
    from hub_manager import queue_model as qm
    from hub_manager import usage as usage_mod
    monkeypatch.setattr(qm, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    from hub_manager import remotes as remotes_mod
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])

    async def drive() -> dict:
        from textual.widgets import DataTable
        from hub_manager.app import ItemDetailScreen
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            table = app.query_one("#queue-table", DataTable)
            table.focus()
            table.move_cursor(row=0)
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            for _ in range(20):  # worker thread + call_from_thread round-trip
                if any(isinstance(s, ItemDetailScreen) for s in app.screen_stack):
                    break
                await pilot.pause()
            screen = next(s for s in app.screen_stack if isinstance(s, ItemDetailScreen))
            for _ in range(20):
                text = str(screen.query_one("#detail-text").render())
                if "Loading" not in text:
                    break
                await pilot.pause()
            return {"screen_pushed": True, "text": text}

    result = asyncio.run(drive())
    assert result["screen_pushed"]
    assert "docs.example.com" in result["text"]
    assert "Stages" in result["text"]
    assert "mirror" in result["text"] and "refine" in result["text"]
    assert "Box health" in result["text"]


def _stub_refreshes(monkeypatch, docset_rows):
    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp",
                        lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(docsets_mod, "list_docsets",
                        lambda: (True, json.dumps(docset_rows)))
    from hub_manager import queue_model as qm
    from hub_manager import usage as usage_mod
    monkeypatch.setattr(qm, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(usage_mod, "scan", lambda days=7: usage_mod.UsageReport(
        days=days, files_scanned=0))
    from hub_manager import remotes as remotes_mod
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])


def test_docsets_tab_delete_refresh_expand(hub_tmp, monkeypatch, tmp_path):
    """The Docsets-tab row actions: d → confirm → docsets.delete; e → an
    `index --name` job from the source mirror; c → recrawl of the queue item
    the docset came from (raising the page cap when asked)."""
    from hub_manager import queue_model
    mirror = tmp_path / "docs.example.com.md"
    mirror.write_text("hello")
    queue_model.add_urls(["https://docs.example.com/"])
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "https://docs.example.com/": {"status": "done", "attempts": 2,
                                      "stage_done": ["mirror", "distill", "index"],
                                      "mirror": str(mirror)}}}))
    _stub_refreshes(monkeypatch, [
        {"docset": "docsexamplecom__docs-example-com", "pages": 3, "chunks": 9,
         "model": "m", "backend": "sqlite", "updated_at": "2026-08-30 00:00:00",
         "source_path": str(mirror)},
        {"docset": "orphan__site", "pages": 1, "chunks": 1, "model": "m",
         "backend": "sqlite", "updated_at": "", "source_path": ""}])
    deleted: list[str] = []
    monkeypatch.setattr(docsets_mod, "delete",
                        lambda key: (deleted.append(key) or True, "gone"))
    monkeypatch.setattr(queue_model, "manager_pid", lambda: None)

    async def drive() -> dict:
        app = HubManagerApp()
        jobs: list[list[str]] = []
        app._start_job = lambda slot, argv, log: jobs.append([slot, *argv])
        app._start_job_chain = lambda slot, argvs, log: jobs.append([slot, *argvs[0]])
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from textual.widgets import DataTable, TabbedContent
            app.query_one(TabbedContent).active = "tab-docsets"
            await pilot.pause()
            table = app.query_one("#docsets-table", DataTable)
            table.move_cursor(row=0)
            # modal bypass: ConfirmScreen → yes, PromptScreen → answer
            answers = iter([True, "5000", "https://orphan.site/"])
            app.push_screen = lambda screen, cb=None: cb(next(answers)) if cb else None

            app.action_delete_item()
            await pilot.pause()
            app.action_retry_item()
            await pilot.pause()
            app.action_recrawl_item()
            await pilot.pause()
            item = {i.url: i for i in queue_model.load_items()}["https://docs.example.com/"]
            cap = app.settings["max_pages"]

            table.move_cursor(row=1)  # orphan: no queue item → seed prompt
            app.action_recrawl_item()
            await pilot.pause()
            urls = [i.url for i in queue_model.load_items()]
            return {"deleted": deleted, "jobs": jobs, "status": item.status,
                    "attempts": item.attempts, "cap": cap, "urls": urls}

    result = asyncio.run(drive())
    assert result["deleted"] == ["docsexamplecom__docs-example-com"]
    assert result["jobs"] == [["index", core.python_for_hub(), "-m", "docset_refine", "all",
                               str(mirror)]]
    assert (result["status"], result["attempts"]) == ("pending", 0)
    assert result["cap"] == 5000  # raised on request and persisted
    assert json.loads((hub_tmp / "hub-manager.json").read_text())["max_pages"] == 5000
    assert "https://orphan.site/" in result["urls"]


def test_docsets_tab_refresh_needs_the_mirror_on_this_box(hub_tmp, monkeypatch):
    _stub_refreshes(monkeypatch, [
        {"docset": "far__away", "pages": 1, "chunks": 1, "model": "m",
         "backend": "chroma", "updated_at": "", "source_path": "/nope/far.md"}])

    async def drive() -> list:
        app = HubManagerApp()
        jobs: list = []
        app._start_job = lambda slot, argv, log: jobs.append(argv)
        app._start_job_chain = lambda slot, argvs, log: jobs.append(argvs)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            from textual.widgets import DataTable, TabbedContent
            app.query_one(TabbedContent).active = "tab-docsets"
            await pilot.pause()
            app.query_one("#docsets-table", DataTable).move_cursor(row=0)
            app.action_retry_item()
            await pilot.pause()
            return jobs

    assert asyncio.run(drive()) == []  # refused, not spawned against a missing file
