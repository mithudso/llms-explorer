# llmsx/tests/test_explorer_monitor.py — the queue screen's research monitor.
# ruff: noqa: E501
from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("textual")

from llmsx import explorer_store as es  # noqa: E402
from conftest import make_repo  # noqa: E402

SNAPSHOT = {
    "generated_at": "2026-10-18T12:00:00+00:00",
    "runs": [{"source": "suite", "name": "mongodb-2026-10-14", "state": "paused",
              "pending": ["Sharding", "Indexes", "Oplog", "Change Streams", "Atlas Search"],
              "pending_count": 694, "total": 707, "started": None, "updated": None}],
    "website": [{"concept": "Data Analysis", "status": "running"},
                {"concept": "Old One", "status": "done"}],
    "queue": {"available": True, "pending": 4163, "done": 0,
              "next": [{"concept": "Copart Salvage Auctions"}, {"concept": "IAAI Salvage Auctions"}]},
}


def test_monitor_lines_summarise_runs_website_and_queue():
    lines = es.research_monitor_lines(SNAPSHOT)
    assert lines[0].startswith("PAUSED")
    assert "research suite mongodb-2026-10-14: 13/707 done, 694 checked out" in lines[0]
    assert "(Sharding, Indexes, Oplog, Change Streams +690)" in lines[0]
    assert lines[1].startswith("RUNNING") and "website run: Data Analysis" in lines[1]
    assert not any("Old One" in line for line in lines), "finished website runs are not live"
    assert lines[2] == "Queue: 4163 waiting, 0 done · next: Copart Salvage Auctions, IAAI Salvage Auctions"


def test_monitor_lines_when_idle():
    assert es.research_monitor_lines({"runs": [], "website": [], "queue": {}}) == [
        "Nothing is being researched right now."]


def test_api_url_honours_env(monkeypatch):
    monkeypatch.setenv("LLMSX_API_URL", "http://127.0.0.1:9/")
    assert es.api_url() == "http://127.0.0.1:9"


def _queue_screen_text(tmp_path, monkeypatch, fetch):
    from llmsx import explorer_screens as screens
    from llmsx.explorer import Explorer

    monkeypatch.setattr(es, "fetch_research_monitor", fetch)
    repo = make_repo(tmp_path)
    seen = {}

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(160, 44)) as pilot:
            app.action_queue_viewer()
            for _ in range(40):
                await pilot.pause(0.05)
                text = str(app.screen.query_one("#qv-monitor").render())
                if "loading" not in text:
                    break
            assert isinstance(app.screen, screens.QueueViewer)
            seen["text"] = text
    asyncio.run(go())
    return seen["text"]


def test_queue_screen_shows_the_monitor(tmp_path, monkeypatch):
    text = _queue_screen_text(tmp_path, monkeypatch, lambda timeout=8.0: SNAPSHOT)
    assert "Research monitor" in text and "/api/research/queue" in text
    assert "694 checked out" in text and "website run: Data Analysis" in text


def test_queue_screen_survives_an_offline_monitor(tmp_path, monkeypatch):
    def offline(timeout=8.0):
        raise OSError("no route to host")
    text = _queue_screen_text(tmp_path, monkeypatch, offline)
    assert "unavailable: no route to host" in text
