"""Network budget and source retention must hold independently of model instructions."""
import json
from io import BytesIO
from pathlib import Path

from llmsx.retrieval_proxy import RetrievalProxy
from llmsx import ollama_agent as agent


def setup_proxy(tmp_path, limit=2):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"mcpServers": {"firecrawl": {
        "type": "http", "url": "https://example.com/private-key"}}}))
    return RetrievalProxy(config, tmp_path / "cache", limit), config


def scrape(n, url):
    return {"jsonrpc": "2.0", "id": n, "method": "tools/call",
            "params": {"name": "firecrawl_scrape", "arguments": {"url": url}}}


def test_bound_caches_repeats_and_counts_failed_fetches(tmp_path, monkeypatch):
    proxy, _ = setup_proxy(tmp_path)
    calls = []

    def remote(request):
        calls.append(request)
        return {"jsonrpc": "2.0", "id": request["id"], "result": {
            "isError": True, "content": [{"type": "text", "text": "fetch failed"}]}}

    monkeypatch.setattr(proxy, "remote", remote)
    proxy.handle(scrape(1, "https://one.example"))
    proxy.handle(scrape(2, "https://one.example"))
    proxy.handle(scrape(3, "https://two.example"))
    blocked = proxy.handle(scrape(4, "https://three.example"))
    assert len(calls) == 2 and proxy.fetches == 2
    assert blocked["result"]["isError"]
    assert "No network fetch occurred" in blocked["result"]["content"][0]["text"]
    audit = json.loads((proxy.cache / "fetch-budget.json").read_text())
    assert audit == {"fetches": 2, "limit": 2, "cached_reads": 1, "blocked": 1}


def test_large_source_is_retained_exactly_outside_context(tmp_path, monkeypatch):
    proxy, _ = setup_proxy(tmp_path)
    original = {"content": [{"type": "text", "text": json.dumps({"markdown": "body " * 4000})}]}
    monkeypatch.setattr(proxy, "remote", lambda req: {"id": req["id"], "result": original})
    result = proxy.handle(scrape(1, "https://one.example"))["result"]
    metadata = json.loads(result["content"][0]["text"])
    path = proxy.cache / (metadata["source_file"].split("/")[-1])
    assert json.loads(path.read_text()) == original
    assert path.stat().st_mode & 0o777 == 0o600
    assert len(result["content"][0]["text"]) < 1000
    assert metadata["fetches_used"] == 1


def test_proxy_config_keeps_secret_out_of_arguments(tmp_path, monkeypatch):
    _, config = setup_proxy(tmp_path)
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path))
    path = agent.retrieval_config(config, gate=True)
    data = json.loads(Path(path).read_text())
    args = data["mcpServers"]["firecrawl"]["args"]
    assert args[-2:] == ["--limit", "15"]
    assert "private-key" not in json.dumps(data)


def test_remote_tool_list_is_limited_to_research_tools(tmp_path, monkeypatch):
    proxy, _ = setup_proxy(tmp_path)
    monkeypatch.setattr(proxy, "remote", lambda req: {"id": req["id"], "result": {
        "tools": [{"name": "firecrawl_scrape"}, {"name": "firecrawl_search"},
                  {"name": "firecrawl_crawl"}]}})
    result = proxy.handle({"id": 1, "method": "tools/list"})
    assert [t["name"] for t in result["result"]["tools"]] == [
        "firecrawl_scrape", "firecrawl_search", "read_source"]


def test_sse_keepalive_does_not_break_mcp_initialization(tmp_path, monkeypatch):
    proxy, _ = setup_proxy(tmp_path)

    class Response(BytesIO):
        status = 200
        headers = {"Content-Type": "text/event-stream", "Mcp-Session-Id": "session"}

    wire = (b"data:\n\n: keepalive\n\nevent: message\n"
            b'data: {"jsonrpc":"2.0",\n'
            b'data: "id":0,"result":{"protocolVersion":"2025-11-25"}}\n\n')
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(wire))
    result = proxy.remote({"jsonrpc": "2.0", "id": 0, "method": "initialize"})
    assert result["result"]["protocolVersion"] == "2025-11-25"
    assert proxy.session == "session"


def test_source_extraction_retains_object_headings_and_blocks_outside_files(tmp_path):
    import pytest

    proxy, _ = setup_proxy(tmp_path)
    path = proxy.cache / "page.json"
    markdown = ("# Archive API\n## criteria\n" + "other field\n" * 20
                + "expireAfterDays: days before archiving\n## dataExpirationRule\n"
                + "expireAfterDays: minimum 7 before deletion\n")
    path.write_text(json.dumps({"content": [{"type": "text", "text": json.dumps({
        "markdown": markdown})}]}))
    response = proxy.read_source({"source_file": str(path), "queries": ["expireAfterDays"]})
    result = json.loads(response["content"][0]["text"])
    assert result["total_matches"] == 2 and not result["truncated"]
    text = "\n".join(result["excerpts"])
    assert "## criteria" in text and "## dataExpirationRule" in text
    assert "before archiving" in text and "before deletion" in text
    with pytest.raises(ValueError, match="saved relay source"):
        proxy.read_source({"source_file": str(tmp_path / "secret.json"), "queries": ["key"]})


def test_verdict_writer_rejects_uncited_evidence_and_serializes_quotes(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    proxy.gate_path = tmp_path / "gate.json"
    url = "https://example.com/page"
    quote = 'The "DATE" field determines document archival age.'
    verdict = {"concept": "Archive age", "claim": "DATE determines age",
               "footnotes": ["[^c1-1]"], "urls": [url], "verdict": "SUPPORTED",
               "evidence": quote}
    assert proxy.record_verdict(verdict)["isError"]
    assert not proxy.gate_path.exists()
    proxy.source_bodies[url] = "# criteria\n" + quote
    assert not proxy.record_verdict(verdict).get("isError")
    saved = json.loads(proxy.gate_path.read_text())
    assert saved["sampled"] == 1 and saved["verdicts"][0]["evidence"] == quote
    assert proxy.gate_path.stat().st_mode & 0o777 == 0o600
    proxy.record_verdict(dict(verdict, verdict="UNVERIFIED", evidence="Cannot decide the scope."))
    assert json.loads(proxy.gate_path.read_text())["sampled"] == 1


def test_verdict_writer_rejects_empty_evidence_and_malformed_footnotes(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    proxy.gate_path = tmp_path / "gate.json"
    verdict = {"concept": "Archive age", "claim": "DATE determines age",
               "footnotes": ["[^c1-1]"], "urls": ["https://example.com/page"],
               "verdict": "UNVERIFIED", "evidence": ""}
    assert proxy.record_verdict(verdict)["isError"]
    verdict.update(evidence="The source is unavailable.", footnotes=["^c1-1"])
    assert proxy.record_verdict(verdict)["isError"]
    assert not proxy.gate_path.exists()


def test_verdict_cannot_use_an_unrelated_url_for_a_footnote(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    proxy.gate_path = tmp_path / "gate.json"
    proxy.references = {"[^c1-1]": "https://example.com/criteria"}
    quote = "The date field determines document archival age."
    proxy.source_bodies["https://example.com/other"] = quote
    verdict = {"concept": "Archive age", "claim": "DATE determines age",
               "footnotes": ["[^c1-1]"], "urls": ["https://example.com/other"],
               "verdict": "SUPPORTED", "evidence": quote}
    assert proxy.record_verdict(verdict)["isError"]
    verdict["urls"].append("https://example.com/criteria")
    assert proxy.record_verdict(verdict)["isError"]
    assert not proxy.gate_path.exists()


def test_verdict_errors_report_unsaved_progress_and_missing_headings(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    proxy.gate_path = tmp_path / "gate.json"
    proxy.core_headings = [f"Concept {i}" for i in range(5)]
    verdict = {"concept": "Concept 0", "claim": "The archival age uses DATE.",
               "footnotes": ["[^c1-1]"], "urls": ["https://example.com/page"],
               "verdict": "UNVERIFIED", "evidence": "The cited page is unavailable."}
    result = proxy.record_verdict(verdict)
    progress = json.loads(result["content"][0]["text"])
    assert progress["sampled"] == 1 and progress["remaining"] == 9
    assert progress["missing"]["Concept 0"] == 1
    assert progress["verdict_counts"]["UNVERIFIED"] == 1
    result = proxy.record_verdict(dict(verdict, claim="Another claim", evidence=""))
    failed = json.loads(result["content"][0]["text"])
    assert result["isError"] and failed["progress"]["sampled"] == 1
    assert "NOT saved" in failed["instruction"]
    assert json.loads(proxy.gate_path.read_text())["sampled"] == 1


def test_visible_quote_matching_ignores_markup_but_keeps_numbers_and_words(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    proxy.gate_path = tmp_path / "gate.json"
    url = "https://example.com/page"
    proxy.source_bodies[url] = (
        "The `dateField` must use [ISODate](https://example.com/glossary). "
        "**Retention** has a minimum of `7` days.")
    verdict = {"concept": "Archive age", "claim": "DATE must use ISODate",
               "footnotes": ["[^c1-1]"], "urls": [url], "verdict": "SUPPORTED",
               "evidence": "The dateField must use ISODate."}
    assert not proxy.record_verdict(verdict).get("isError")
    for changed in ("Retention has a minimum of 17 days.", "ISODate must use the dateField."):
        assert proxy.record_verdict(dict(verdict, evidence=changed))["isError"]


def test_gate_search_cannot_bypass_scrape_budget(tmp_path, monkeypatch):
    proxy, _ = setup_proxy(tmp_path)
    calls = []
    monkeypatch.setattr(proxy, "remote", lambda req: calls.append(req))
    result = proxy.handle({"id": 1, "method": "tools/call", "params": {
        "name": "firecrawl_search", "arguments": {
            "query": "archive age", "scrapeOptions": {"formats": ["markdown"]}}}})
    assert result["result"]["isError"] and not calls
    assert proxy.fetches == 0


def test_api_property_excerpt_keeps_enclosing_object_and_deletion_purpose(tmp_path):
    proxy, _ = setup_proxy(tmp_path)
    path = proxy.cache / "api.json"
    markdown = (
        "# Request body\n-\ncriteria\n\nobject\n\nCriteria for archival.\n"
        "    -\n       expireAfterDays\n\n      integer(int32)\n"
        "\n      Number of days before archiving.\n"
        "-\ndataExpirationRule\n\nobject\n\nRule for deletion from the archive.\n"
        "    -\n       expireAfterDays\n\n      integer(int32)\n"
        + "\n" * 15 + "      Minimum value is 7, maximum value is 9215.\n")
    path.write_text(json.dumps({"markdown": markdown}))
    result = proxy.read_source({"source_file": str(path), "queries": ["9215"],
                                "context_lines": 1})
    text = "\n".join(json.loads(result["content"][0]["text"])["excerpts"])
    assert "[dataExpirationRule.expireAfterDays]" in text
    assert "Rule for deletion from the archive" in text
    assert "[criteria.expireAfterDays]" not in text
