# ruff: noqa: E501
"""llms-full.txt catalog: source parsers, merge, validation, download, list/read."""

import json

import llms_full_catalog as lfc

README = """
### 💻 developer tools

- ![Medusa favicon](https://x/favicon) **[Medusa](https://medusajs.com/)** - A commerce platform. <sub>[llms.txt](https://docs.medusajs.com/llms.txt) • [llms-full.txt](https://docs.medusajs.com/llms-full.txt)</sub>
- ![Only index](https://x) **[IndexOnly](https://indexonly.dev)** - no full file. <sub>[llms.txt](https://indexonly.dev/llms.txt)</sub>

### 🤖 ai ml

- ![Pydantic favicon](https://x) **[Pydantic AI](https://ai.pydantic.dev)** - Agent framework. <sub>[llms.txt](https://ai.pydantic.dev/llms.txt) • [llms-full.txt](https://ai.pydantic.dev/llms-full.txt)</sub>
"""

SITE = """<table><tbody>
<tr><td>Medusa</td><td><a href="https://medusajs.com/">medusajs.com/</a></td><td><a href="https://docs.medusajs.com/llms.txt">i</a></td><td>10</td><td><a href="https://docs.medusajs.com/llms-full.txt">f</a></td><td>99</td></tr>
<tr><td>Angular</td><td><a href="https://angular.dev/">angular.dev</a></td><td><a href="https://angular.dev/llms.txt">i</a></td><td>1</td><td><a href="https://angular.dev/context/llm-files/llms-full.txt">f</a></td><td>2</td></tr>
<tr><td>Hotel</td><td><a href="https://hotel.example/">h</a></td><td><a href="https://hotel.example/llms.txt">i</a></td><td>0</td><td></td><td></td></tr>
</tbody></table>"""

GOOD = ("# Hooks\nSource: https://d.example/hooks\n\nbody\n\n# Overview\n"
        "Source: https://d.example/overview\n\nmore\n" + "x" * 1200).encode()


def test_key_for_drops_www_and_slugs_paths():
    assert lfc.key_for("https://www.medusajs.com/llms-full.txt") == "medusajs.com"
    assert lfc.key_for("https://angular.dev/context/llm-files/llms-full.txt") == \
        "angular.dev__context-llm-files"


def test_parse_hub_readme_keeps_category_and_skips_index_only():
    rows = lfc.parse_hub_readme(README)
    assert [r["key"] for r in rows] == ["docs.medusajs.com", "ai.pydantic.dev"]
    assert rows[0]["category"] == "developer tools" and rows[0]["name"] == "Medusa"
    assert rows[1]["category"] == "ai ml"
    assert rows[0]["description"] == "A commerce platform."
    assert rows[0]["sources"] == ["llms-txt-hub"]


def test_parse_llmstxt_site_needs_full_column():
    rows = lfc.parse_llmstxt_site(SITE)
    assert [r["name"] for r in rows] == ["Medusa", "Angular"]
    assert rows[1]["url"] == "https://angular.dev/context/llm-files/llms-full.txt"
    assert rows[0]["site"] == "https://medusajs.com/"


def test_parse_url_sweep_dedupes():
    text = "see https://a.dev/llms-full.txt and https://a.dev/llms-full.txt, https://b.dev/llms-full.txt."
    rows = lfc.parse_url_sweep(text, "x")
    assert [r["url"] for r in rows] == ["https://a.dev/llms-full.txt", "https://b.dev/llms-full.txt"]


def test_parse_rollout_only_llms_full_hits():
    rollout = [{"url": "https://docs.x.com/", "method": "llms-full",
                "source": "https://docs.x.com/llms-full.txt"},
               {"url": "https://y.com/", "method": "llms", "source": "https://y.com/llms.txt"}]
    rows = lfc.parse_rollout(rollout)
    assert len(rows) == 1 and rows[0]["sources"] == ["docslist.textmirror"]


def test_merge_rows_richest_metadata_wins_and_sources_accumulate():
    a = lfc.parse_hub_readme(README)
    b = lfc.parse_llmstxt_site(SITE)
    c = lfc.parse_url_sweep("https://docs.medusajs.com/llms-full.txt", "cloud")
    rows = lfc.merge_rows(a, b, c)
    med = next(r for r in rows if r["key"] == "docs.medusajs.com")
    assert med["category"] == "developer tools"
    assert med["sources"] == ["llms-txt-hub", "llmstxt.site", "cloud"]
    assert {r["key"] for r in rows} == {"docs.medusajs.com", "ai.pydantic.dev",
                                        "angular.dev__context-llm-files"}


def test_merge_rows_keeps_existing_and_uniquifies_keys():
    existing = [{"key": "a.dev", "url": "https://a.dev/llms-full.txt", "name": "A",
                 "site": "", "category": "", "description": "", "sources": ["old"]}]
    new = [lfc._row("http://a.dev/llms-full.txt", source="new")]  # same key, other scheme
    rows = lfc.merge_rows(new, existing=existing)
    assert sorted(r["key"] for r in rows) == ["a.dev", "a.dev-2"]
    assert next(r for r in rows if r["url"].startswith("https"))["sources"] == ["old"]


def test_validate():
    assert lfc.validate(GOOD, "text/plain") == ("ok", 2, "")
    assert lfc.validate(GOOD, "text/html; charset=utf-8")[0] == "rejected"
    assert lfc.validate(b"<!DOCTYPE html><html>" + b"x" * 2000, "text/plain")[0] == "rejected"
    assert lfc.validate(b"# tiny\n", "text/plain")[0] == "rejected"
    # markdown without Source: blocks is still docs — kept, pages=0
    assert lfc.validate(b"# Docs\n\nplain markdown\n" + b"y" * 1200, "text/plain") == ("ok", 0, "")


def _fake_get(responses):
    def get(url, timeout=0, max_bytes=0, attempts=0):
        r = responses.get(url)
        if r is None:
            return None, "", "HTTP 404"
        body, ctype = r
        return body, ctype, ""
    return get


def test_download_all_writes_files_and_manifest(tmp_path):
    base = tmp_path / "llms-full"
    rows = lfc.merge_rows(lfc.parse_hub_readme(README), lfc.parse_llmstxt_site(SITE))
    lfc._save(lfc.catalog_path(base), rows)
    get = _fake_get({
        "https://docs.medusajs.com/llms-full.txt": (GOOD, "text/plain"),
        "https://ai.pydantic.dev/llms-full.txt": (b"<html>nope" + b"x" * 2000, "text/html"),
    })
    counts = lfc.download_all(base, jobs=2, get=get, log=lambda *_: None)
    assert counts == {"ok": 1, "rejected": 1, "failed": 1}
    man = json.loads(lfc.manifest_path(base).read_text())
    assert man["docs.medusajs.com"]["status"] == "ok"
    assert man["docs.medusajs.com"]["pages"] == 2
    assert (base / "files" / "docs.medusajs.com.txt").read_bytes() == GOOD
    assert man["ai.pydantic.dev"]["status"] == "rejected"
    assert man["angular.dev__context-llm-files"]["status"] == "failed"
    assert man["angular.dev__context-llm-files"]["reason"] == "HTTP 404"

    # resume: nothing re-fetched unless retry-failed/refresh
    calls = []

    def counting(url, **kw):
        calls.append(url)
        return GOOD, "text/plain", ""
    assert lfc.download_all(base, get=counting, log=lambda *_: None) == \
        {"ok": 0, "rejected": 0, "failed": 0}
    assert calls == []
    lfc.download_all(base, retry_failed=True, get=counting, log=lambda *_: None)
    assert sorted(calls) == ["https://ai.pydantic.dev/llms-full.txt",
                             "https://angular.dev/context/llm-files/llms-full.txt"]


def test_list_and_read(tmp_path):
    base = tmp_path / "llms-full"
    rows = lfc.parse_hub_readme(README)
    lfc._save(lfc.catalog_path(base), rows)
    get = _fake_get({"https://docs.medusajs.com/llms-full.txt": (GOOD, "text/plain")})
    lfc.download_all(base, get=get, log=lambda *_: None)

    ok = lfc.list_entries(base)
    assert [e["key"] for e in ok] == ["docs.medusajs.com"]
    assert [e["key"] for e in lfc.list_entries(base, status="all", query="pydantic")] == \
        ["ai.pydantic.dev"]
    assert lfc.list_entries(base, query="nomatch") == []
    assert [e["key"] for e in lfc.list_entries(base, min_pages=2)] == ["docs.medusajs.com"]
    assert lfc.list_entries(base, min_pages=3) == []

    r = lfc.read_entry("docs.medusajs.com", base, limit=10)
    assert r["text"] == GOOD.decode()[:10] and r["next_offset"] == 10
    assert r["total_chars"] == len(GOOD)
    r2 = lfc.read_entry("docs.medusajs.com", base, page="overview")
    assert r2["page_url"] == "https://d.example/overview" and r2["text"].startswith("more")
    assert "error" in lfc.read_entry("docs.medusajs.com", base, page="nothing")
    assert "error" in lfc.read_entry("ai.pydantic.dev", base)
    assert "error" in lfc.read_entry("nope", base)

    # a vanished file is reported as missing, never as a dead ok path
    (base / "files" / "docs.medusajs.com.txt").unlink()
    assert lfc.list_entries(base) == []
    assert lfc.list_entries(base, status="missing")[0]["key"] == "docs.medusajs.com"
    assert "missing" in lfc.read_entry("docs.medusajs.com", base)["error"]


def test_compile_offline_uses_saved_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(lfc, "HUB_DIR", tmp_path)  # no live rollout probe
    base = tmp_path / "llms-full"
    readme = tmp_path / "hub_readme.md"
    readme.write_text(README)
    site = tmp_path / "site.html"
    site.write_text(SITE)
    rows = lfc.compile_catalog(base, seeds=["https://seed.dev/llms-full.txt"],
                               offline=[readme, site], log=lambda *_: None)
    keys = {r["key"] for r in rows}
    assert keys == {"docs.medusajs.com", "ai.pydantic.dev", "angular.dev__context-llm-files",
                    "seed.dev"}
    assert lfc.catalog_path(base).exists()
    med = next(r for r in rows if r["key"] == "docs.medusajs.com")
    assert med["category"] == "developer tools"
