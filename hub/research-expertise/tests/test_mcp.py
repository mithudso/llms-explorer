"""Verify the retrieval tool contract without opening a database connection."""

import asyncio

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
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "expertise_status",
        "expertise_search",
        "expertise_passage",
        "expertise_neighbors",
        "expertise_save_research",
    }
    assert all(
        tool.annotations.readOnlyHint for tool in tools if tool.name != "expertise_save_research"
    )
    capture_tool = next(tool for tool in tools if tool.name == "expertise_save_research")
    assert not capture_tool.annotations.readOnlyHint
    assert capture_tool.annotations.idempotentHint
    assert "root" not in capture_tool.inputSchema.get("properties", {})
    assert capture_tool.annotations.destructiveHint
    assert all(
        not tool.annotations.destructiveHint
        for tool in tools
        if tool.name != "expertise_save_research"
    )
    assert all("cypher" not in tool.inputSchema.get("properties", {}) for tool in tools)


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
