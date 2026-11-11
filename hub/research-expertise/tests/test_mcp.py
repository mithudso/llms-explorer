"""Verify the retrieval tool contract without opening a database connection."""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import pytest


pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise import mcp_server


class FakeStore:
    def status(self):
        return {"documents": 7}

    def search(self, **kwargs):
        return kwargs

    def passage(self, passage_id):
        return {"id": passage_id}

    def neighbors(self, **kwargs):
        return kwargs


@pytest.fixture(autouse=True)
def fake_store(monkeypatch):
    monkeypatch.setattr(mcp_server, "_store", FakeStore)


def test_tools_keep_read_contract_and_expose_only_constrained_capture():
    tools = [tool.model_dump(by_alias=True)
             for tool in asyncio.run(mcp_server.mcp.list_tools())]
    assert {tool["name"] for tool in tools} == {
        "expertise_status",
        "expertise_search",
        "expertise_passage",
        "expertise_neighbors",
        "expertise_save_research",
    }
    assert all(
        tool["annotations"]["readOnlyHint"]
        for tool in tools
        if tool["name"] != "expertise_save_research"
    )
    capture_tool = next(tool for tool in tools if tool["name"] == "expertise_save_research")
    assert not capture_tool["annotations"]["readOnlyHint"]
    assert capture_tool["annotations"]["idempotentHint"]
    assert "root" not in capture_tool["inputSchema"].get("properties", {})
    assert capture_tool["annotations"]["destructiveHint"]
    assert all(
        not tool["annotations"]["destructiveHint"]
        for tool in tools
        if tool["name"] != "expertise_save_research"
    )
    assert all("cypher" not in tool["inputSchema"].get("properties", {}) for tool in tools)


def test_tools_dispatch_normalized_inputs():
    assert mcp_server.expertise_status() == {"documents": 7}
    assert mcp_server.expertise_search("  actual question  ", 3, " topic ") == {
        "query": "actual question",
        "top": 3,
        "concept": "topic",
    }
    assert mcp_server.expertise_passage(" id ") == {"id": "id"}
    assert mcp_server.expertise_neighbors(" topic ", 2) == {"concept": "topic", "top": 2}


@pytest.mark.parametrize("top", [0, -1, 21, 1.5, True, "5"])
def test_search_and_neighbors_reject_invalid_limits(top):
    with pytest.raises(ValueError, match="top"):
        mcp_server.expertise_search("question", top)
    with pytest.raises(ValueError, match="top"):
        mcp_server.expertise_neighbors("topic", top)


@pytest.mark.parametrize("query", ["", "  ", "x" * 2001, 42])
def test_search_rejects_blank_or_oversized_query(query):
    with pytest.raises(ValueError, match="query"):
        mcp_server.expertise_search(query)


@pytest.mark.parametrize("value", ["", "  ", "x" * 301, 42])
def test_passage_and_neighbors_reject_invalid_identifiers(value):
    with pytest.raises(ValueError):
        mcp_server.expertise_passage(value)
    with pytest.raises(ValueError):
        mcp_server.expertise_neighbors(value)


def test_search_allows_empty_filter_but_rejects_long_concept():
    assert mcp_server.expertise_search("question")["concept"] == ""
    with pytest.raises(ValueError, match="concept"):
        mcp_server.expertise_search("question", concept="x" * 301)


def test_capture_dispatches_explicit_evidence_and_checksum(monkeypatch):
    def save(store, *args):
        assert isinstance(store, FakeStore)
        return {"received": args}

    monkeypatch.setattr(mcp_server, "save_research", save)
    findings = [{"text": "Finding", "source_ids": ["S1"], "quotes": []}]
    sources = [{"id": "S1", "url": "https://example.org", "title": "Source", "content": "Text"}]
    result = mcp_server.expertise_save_research(
        "topic", "Title", "Question", "Summary", findings, sources, "a" * 64
    )
    assert result["received"] == (
        "topic",
        "Title",
        "Question",
        "Summary",
        findings,
        sources,
        "a" * 64,
    )


def test_mcp_tool_work_does_not_block_the_protocol_event_loop(monkeypatch):
    import threading

    started, release = threading.Event(), threading.Event()

    class BlockingStore:
        def status(self):
            started.set()
            assert release.wait(timeout=2)
            return {"state": "ready"}

    monkeypatch.setattr(mcp_server, "_store", BlockingStore)

    async def exercise():
        task = asyncio.create_task(mcp_server.mcp.call_tool("expertise_status", {}))
        try:
            assert await asyncio.to_thread(started.wait, 3)
            # The loop must run while the database worker is still blocked.
            assert not task.done()
        finally:
            release.set()
            await task

    asyncio.run(exercise())


def test_mcp_store_work_and_close_share_one_owner_thread(monkeypatch):
    from functools import lru_cache
    import threading

    calls = []

    class ThreadStore:
        def __init__(self): calls.append(("init", threading.get_ident()))
        def status(self):
            calls.append(("status", threading.get_ident()))
            return {"state": "ready"}
        def close(self): calls.append(("close", threading.get_ident()))

    factory = lru_cache(maxsize=1)(ThreadStore)
    monkeypatch.setattr(mcp_server, "_store", factory)
    asyncio.run(mcp_server.mcp.call_tool("expertise_status", {}))
    asyncio.run(mcp_server.mcp.call_tool("expertise_status", {}))
    mcp_server._worker.submit(mcp_server._close_store).result(timeout=3)
    assert [name for name, _ in calls] == ["init", "status", "status", "close"]
    assert len({thread for _, thread in calls}) == 1
    assert calls[0][1] != threading.get_ident()


@pytest.mark.parametrize("failure", [False, True])
def test_main_always_shuts_down_the_owner_worker(monkeypatch, failure):
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        if failure:
            raise RuntimeError("transport closed")

    monkeypatch.setattr(mcp_server.mcp, "run", run)
    monkeypatch.setattr(mcp_server, "_shutdown", lambda: calls.append("shutdown"))
    if failure:
        with pytest.raises(RuntimeError, match="transport closed"):
            mcp_server.main()
    else:
        mcp_server.main()
    assert calls == [{"transport": "stdio"}, "shutdown"]


def test_cancelled_tool_leaves_running_work_owned_until_completion(monkeypatch):
    import threading

    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    class BlockingStore:
        def status(self):
            started.set()
            assert release.wait(timeout=3)
            finished.set()
            return {"state": "ready"}

    monkeypatch.setattr(mcp_server, "_store", BlockingStore)

    async def exercise():
        task = asyncio.create_task(mcp_server.mcp.call_tool("expertise_status", {}))
        try:
            assert await asyncio.to_thread(started.wait, 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not finished.is_set()
        finally:
            release.set()
            assert await asyncio.to_thread(finished.wait, 3)

    asyncio.run(exercise())


def test_real_stdio_retrieval_protocol_uses_fixture_store_only():
    """Exercise SDK framing, tool aliases and dispatch without Neo4j or embeddings."""
    fixture_server = """
from functools import lru_cache
from research_expertise import mcp_server

class FixtureStore:
    def status(self):
        return {"documents": 7, "backend": "fixture"}
    def search(self, **kwargs):
        return kwargs
    def passage(self, passage_id):
        return {"id": passage_id}
    def neighbors(self, **kwargs):
        return kwargs

@lru_cache(maxsize=1)
def fixture_store():
    return FixtureStore()

mcp_server._store = fixture_store
mcp_server.main()
"""

    def payload(result):
        # An unstructured dict annotation may serialize as JSON text on either SDK.
        if result["structuredContent"] is not None:
            return result["structuredContent"]
        return json.loads("".join(block["text"] for block in result["content"]))

    async def scenario():
        params = StdioServerParameters(
            command=sys.executable, args=["-c", fixture_server], env=dict(os.environ)
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = {tool.name: tool.model_dump(by_alias=True)
                         for tool in (await session.list_tools()).tools}
                assert set(tools) == {
                    "expertise_status", "expertise_search", "expertise_passage",
                    "expertise_neighbors", "expertise_save_research",
                }
                assert tools["expertise_status"]["annotations"]["readOnlyHint"]
                assert tools["expertise_save_research"]["annotations"]["destructiveHint"]
                status = (await session.call_tool("expertise_status", {})).model_dump(by_alias=True)
                assert not status["isError"]
                assert payload(status) == {"documents": 7, "backend": "fixture"}
                search = (await session.call_tool("expertise_search", {
                    "query": "  evidence  ", "top": 3, "concept": " topic ",
                })).model_dump(by_alias=True)
                assert not search["isError"]
                assert payload(search) == {
                    "query": "evidence", "top": 3, "concept": "topic",
                }
                invalid = (await session.call_tool("expertise_search", {
                    "query": "evidence", "top": 21,
                })).model_dump(by_alias=True)
                assert invalid["isError"]

    asyncio.run(scenario())
