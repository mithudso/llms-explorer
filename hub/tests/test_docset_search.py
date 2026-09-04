"""Docsets tab: row detail, source-path link, and fuzzy/regex file search."""

import json

from hub_manager import docsets

MIRROR = """==========
URL: https://docs.example.com/intro
==========

Connection pooling reuses open sockets.
The retry policy is exponential.

==========
URL: https://docs.example.com/tuning
==========

Tune the connection pool size for throughput.
Unrelated paragraph about colors.
"""


def _mirror(tmp_path):
    p = tmp_path / "example.md"
    p.write_text(MIRROR)
    return p


# --------------------------------------------------------------- detail ----


def test_detail_renders_a_file_link_and_size(tmp_path):
    src = _mirror(tmp_path)
    text = docsets.docset_detail(
        {
            "docset": "example__docs",
            "pages": 2,
            "chunks": 9,
            "model": "mxbai-embed-large",
            "backend": "chroma",
            "updated_at": "2026-08-30 00:00:00",
            "source_path": str(src),
        }
    )
    assert "example__docs" in text
    assert f"[link=file://{src}]{src}[/link]" in text
    assert "modified" in text
    # backend must not render as a markup tag -- it is not a Rich style
    assert "(chroma)" in text and "[chroma]" not in text


def test_detail_survives_a_docset_indexed_before_source_path_was_listed():
    text = docsets.docset_detail({"docset": "old__docs"})
    assert "not recorded" in text


def test_detail_flags_a_source_file_that_no_longer_exists(tmp_path):
    text = docsets.docset_detail({"docset": "gone__docs", "source_path": str(tmp_path / "nope.md")})
    assert "unreadable" in text


# --------------------------------------------------------------- search ----


def test_regex_search_reports_line_and_page_url(tmp_path):
    ok, text = docsets.search_file(str(_mirror(tmp_path)), r"pool\w* size", "regex")
    assert ok
    assert "https://docs.example.com/tuning" in text
    assert "Tune the connection pool size" in text
    # the intro page mentions pooling but not "pool size"
    assert "reuses open sockets" not in text


def test_regex_search_rejects_a_bad_pattern(tmp_path):
    ok, text = docsets.search_file(str(_mirror(tmp_path)), "(unclosed", "regex")
    assert not ok and "bad regex" in text


def test_fuzzy_search_ranks_the_closest_line_first(tmp_path):
    ok, text = docsets.search_file(str(_mirror(tmp_path)), "connection pool size", "fuzzy")
    assert ok
    first_hit = text.splitlines()[2]
    assert "Tune the connection pool size" in first_hit
    # a line sharing only one token still matches, just lower
    assert "reuses open sockets" in text


def test_fuzzy_search_ignores_lines_sharing_no_token(tmp_path):
    ok, text = docsets.search_file(str(_mirror(tmp_path)), "colors", "fuzzy")
    assert ok
    assert "Unrelated paragraph about colors" in text
    assert "exponential" not in text


def test_search_reports_no_matches_without_failing(tmp_path):
    ok, text = docsets.search_file(str(_mirror(tmp_path)), "kubernetes", "fuzzy")
    assert ok and "no fuzzy matches" in text


def test_search_caps_the_scan_on_a_huge_mirror(tmp_path, monkeypatch):
    monkeypatch.setattr(docsets, "MAX_SCAN_LINES", 3)
    big = tmp_path / "big.md"
    big.write_text("needle\n" * 50)
    ok, text = docsets.search_file(str(big), "needle", "fuzzy")
    assert ok and "scan stopped at 3 lines" in text
    assert "3 fuzzy match(es)" in text


def test_search_needs_a_source_path_and_an_existing_file(tmp_path):
    ok, text = docsets.search_file("", "q", "fuzzy")
    assert not ok and "no recorded source path" in text
    ok, text = docsets.search_file(str(tmp_path / "gone.md"), "q", "regex")
    assert not ok and "source file missing" in text


def test_semantic_is_not_served_by_the_file_scanner(tmp_path):
    """Semantic must go through the indexer subprocess -- the file scanner
    refuses it rather than silently degrading to a substring match."""
    ok, text = docsets.search_file(str(_mirror(tmp_path)), "q", "semantic")
    assert not ok and "unsupported search mode" in text


# ------------------------------------------------------------------ wiring --


def test_list_docsets_carries_source_path(tmp_path, monkeypatch):
    """The tab can only link to the mirror if `list` emits source_path."""
    import docset_indexer

    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    store = docset_indexer.SqliteStore()
    store.replace_docset(
        "example__docs",
        [
            {
                "id": "c1",
                "url": "https://docs.example.com/intro",
                "seq": 0,
                "text": "hello",
                "vector": [0.1, 0.2],
                "model": "m",
            }
        ],
        {"source_path": "/tmp/example.md", "pages": 1, "model": "m"},
    )
    entry = store.list_docsets()[0]
    store.close()
    assert entry["source_path"] == "/tmp/example.md"
    assert entry["docset"] == "example__docs"
    # docset_detail consumes exactly this shape
    assert "example__docs" in docsets.docset_detail(entry)


def test_list_docsets_reports_keyword_coverage(tmp_path, monkeypatch):
    """The librarian's index-coverage audit needs to spot a semantic-only
    docset in one `list` call rather than probing `keyword` per key."""
    import docset_indexer

    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    store = docset_indexer.SqliteStore()
    for key in ("has-keyword__docs", "semantic-only__docs"):
        store.replace_docset(
            key,
            [{"id": "c1", "url": "https://x/1", "seq": 0, "text": "hello",
              "vector": [0.1, 0.2], "model": "m"}],
            {"source_path": f"/tmp/{key}.md", "pages": 1, "model": "m"},
        )
    store.keyword_replace("has-keyword__docs",
                          [{"url": "https://x/1", "seq": 0, "text": "hello"}])
    by_key = {e["docset"]: e for e in store.list_docsets()}
    store.close()
    assert by_key["has-keyword__docs"]["keyword_chunks"] == 1
    assert by_key["semantic-only__docs"]["keyword_chunks"] == 0


# --------------------------------------------------------------- TUI glue --


def _stub_tabs(monkeypatch, entries):
    """Stub every subprocess/network refresh so the app mounts hermetically."""
    from hub_manager import (
        docsets as docsets_mod,
        health,
        queue_model,
        remotes as remotes_mod,
        usage as usage_mod,
    )

    monkeypatch.setattr(health, "run_all", lambda disabled=None: [])
    monkeypatch.setattr(health, "check_mcp", lambda: health.HealthCheck("MCP", None, "stub"))
    monkeypatch.setattr(queue_model, "serve_alive", lambda timeout=1.0: False)
    monkeypatch.setattr(
        usage_mod, "scan", lambda days=7: usage_mod.UsageReport(days=days, files_scanned=0)
    )
    monkeypatch.setattr(remotes_mod, "all_hosts", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_hosts_readiness", lambda: [])
    monkeypatch.setattr(remotes_mod, "all_repo_status", lambda: [])
    monkeypatch.setattr(docsets_mod, "list_docsets", lambda: (True, json.dumps(entries)))


def test_clicking_a_docset_row_brings_it_up_in_the_pane_below(hub_tmp, monkeypatch, tmp_path):
    import asyncio

    from textual.widgets import DataTable, Input, RichLog, Select, TabbedContent

    from hub_manager import docsets as docsets_mod
    from hub_manager.app import HubManagerApp

    src = _mirror(tmp_path)
    _stub_tabs(
        monkeypatch,
        [
            {
                "docset": "example__docs",
                "pages": 2,
                "chunks": 9,
                "model": "mxbai-embed-large",
                "backend": "chroma",
                "updated_at": "2026-08-30 00:00:00",
                "source_path": str(src),
            }
        ],
    )
    searched: list[tuple] = []
    monkeypatch.setattr(
        docsets_mod,
        "search_docset",
        lambda d, p, q, m, top=20: searched.append((d, p, q, m, top)) or (True, f"{m} ran"),
    )
    monkeypatch.setattr(docsets_mod, "query", lambda d, q, top=5: (True, "semantic ran"))

    async def drive() -> dict:
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.query_one(TabbedContent).active = "tab-docsets"
            await pilot.pause()
            app.query_one("#docsets-table", DataTable).move_cursor(row=0)
            await pilot.pause()
            # click the row: detail lands in the pane below
            app.query_one("#docsets-table", DataTable).action_select_cursor()
            await pilot.pause()
            detail = "\n".join(
                str(line.text) for line in app.query_one("#docset-results", RichLog).lines
            )

            # fuzzy search of the selected docset, via the button
            app.query_one("#docset-mode", Select).value = "fuzzy"
            app.query_one("#docset-query", Input).value = "connection pool"
            app.query_one("#docset-search").press()
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.pause()
            pane = "\n".join(
                str(line.text) for line in app.query_one("#docset-results", RichLog).lines
            )
            return {"detail": detail, "pane": pane}

    result = asyncio.run(drive())
    # the row's own detail, including the full source filepath (the pane
    # soft-wraps it, so compare against the unwrapped text)
    assert "example__docs" in result["detail"]
    assert str(src) in result["detail"].replace("\n", "")
    # search dispatched with BOTH the docset key and its mirror path, so the
    # scanner can fall back to the indexed chunks if the file is not here
    assert searched == [("example__docs", str(src), "connection pool", "fuzzy", 20)]
    assert ">>> [fuzzy] [example__docs] connection pool" in result["pane"]
    assert "fuzzy ran" in result["pane"]


def test_search_without_a_selected_row_says_so(hub_tmp, monkeypatch):
    import asyncio

    from textual.widgets import Input, RichLog, TabbedContent

    from hub_manager.app import HubManagerApp

    _stub_tabs(monkeypatch, [])

    async def drive() -> str:
        app = HubManagerApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.query_one(TabbedContent).active = "tab-docsets"
            await pilot.pause()
            app.query_one("#docset-query", Input).value = "anything"
            app.query_one("#docset-search").press()
            await pilot.pause()
            return "\n".join(
                str(line.text) for line in app.query_one("#docset-results", RichLog).lines
            )

    assert "select a docset row first" in asyncio.run(drive())


# ------------------------------------------------- chunk-scan fallback -----


def _seed_sqlite_docset(tmp_path, monkeypatch, key="example__docs"):
    """A real sqlite-backed docset, so the dump CLI can be exercised for real."""
    import docset_indexer

    db = tmp_path / "docsets.db"
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", db)
    store = docset_indexer.SqliteStore()
    store.replace_docset(
        key,
        [
            {
                "id": "c0",
                "url": "https://docs.example.com/intro",
                "seq": 0,
                "text": "Connection pooling reuses open sockets.\nRetries back off.",
                "vector": [0.1],
                "model": "m",
            },
            {
                "id": "c1",
                "url": "https://docs.example.com/tuning",
                "seq": 1,
                "text": "Tune the connection pool size for throughput.",
                "vector": [0.2],
                "model": "m",
            },
        ],
        {"source_path": "/not/on/this/box/example.md", "pages": 2, "model": "m"},
    )
    store.close()
    return db


def test_dump_falls_back_to_chunks_for_a_pre_pages_docset(tmp_path, monkeypatch, capsys):
    """A docset written before raw pages were stored still dumps."""
    import argparse

    import docset_indexer

    _seed_sqlite_docset(tmp_path, monkeypatch)  # no pages= passed
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    assert docset_indexer.cmd_dump(argparse.Namespace(docset="example__docs", kind="auto")) == 0
    rows = [json.loads(ln) for ln in capsys.readouterr().out.splitlines()]
    assert [r["kind"] for r in rows] == ["chunk", "chunk"]
    assert [r["seq"] for r in rows] == [0, 1]
    assert rows[1]["url"] == "https://docs.example.com/tuning"
    assert "connection pool size" in rows[1]["text"]
    # vectors must never ride along -- the point of dump is text only
    assert all("vector" not in r for r in rows)


def test_chunk_search_finds_and_locates_by_chunk(tmp_path, monkeypatch):
    """End-to-end: the TUI shells out to `dump` and scans its JSONL."""
    from hub_manager import core

    db = _seed_sqlite_docset(tmp_path, monkeypatch)
    monkeypatch.setenv("HUB_DOCSET_DB", str(db))
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(core, "python_for_hub", lambda: __import__("sys").executable)

    ok, text = docsets.search_index("example__docs", "pool size", "regex")
    assert ok, text
    assert "stored text" in text
    assert "chunk 1.0" in text  # pre-pages docset: chunk seq, not file line
    assert "https://docs.example.com/tuning" in text


def test_chunk_search_reports_a_docset_that_does_not_exist(tmp_path, monkeypatch):
    from hub_manager import core

    db = _seed_sqlite_docset(tmp_path, monkeypatch)
    monkeypatch.setenv("HUB_DOCSET_DB", str(db))
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(core, "python_for_hub", lambda: __import__("sys").executable)
    ok, text = docsets.search_index("nope__docs", "anything", "fuzzy")
    # an empty docset is an honest "no matches", not a crash
    assert ok and "no fuzzy matches" in text


def test_search_docset_prefers_the_mirror_when_it_is_here(tmp_path, monkeypatch):
    called: list[str] = []
    monkeypatch.setattr(
        docsets, "search_index", lambda *a, **k: called.append("chunks") or (True, "x")
    )
    src = _mirror(tmp_path)
    ok, text = docsets.search_docset("example__docs", str(src), "connection pool", "fuzzy")
    assert ok and not called
    assert "example.md:" in text


def test_search_docset_falls_back_to_chunks_when_the_mirror_is_elsewhere(tmp_path, monkeypatch):
    """A replicated .chroma-docsets carries the vectors, not the mirror."""
    monkeypatch.setattr(
        docsets, "search_index", lambda d, q, m, top=20: (True, f"chunk hit for {d}")
    )
    ok, text = docsets.search_docset("example__docs", str(tmp_path / "absent.md"), "q", "fuzzy")
    assert ok
    assert "source mirror not on this box" in text
    assert "chunk hit for example__docs" in text


def test_search_docset_falls_back_when_no_path_was_ever_recorded(monkeypatch):
    monkeypatch.setattr(docsets, "search_index", lambda d, q, m, top=20: (True, "chunk hit"))
    ok, text = docsets.search_docset("old__docs", "", "q", "regex")
    assert ok and "no source path recorded" in text


def test_search_docset_surfaces_a_fallback_failure_verbatim(monkeypatch):
    monkeypatch.setattr(
        docsets, "search_index", lambda d, q, m, top=20: (False, "backend unavailable")
    )
    ok, text = docsets.search_docset("old__docs", "", "q", "regex")
    assert not ok and text == "backend unavailable"


def test_both_search_paths_share_one_scorer(tmp_path, monkeypatch):
    """Mirror and chunk scans must rank identically -- same scorer, so a bad
    mode or regex is rejected the same way on either path."""
    for fn, args in (
        (docsets.search_file, (str(_mirror(tmp_path)),)),
        (docsets.search_index, ("example__docs",)),
    ):
        ok, text = fn(*args, "q", "semantic")
        assert not ok and "unsupported search mode" in text
        ok, text = fn(*args, "(unclosed", "regex")
        assert not ok and "bad regex" in text


# ------------------------------------------------- raw page storage --------


def _seed_with_pages(tmp_path, monkeypatch, key="paged__docs"):
    """A docset indexed the current way: chunks AND raw page text."""
    import docset_indexer

    db = tmp_path / "docsets.db"
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", db)
    pages = [
        {
            "url": "https://docs.example.com/intro",
            "text": "Connection pooling reuses open sockets.\nTiny.",
        },
        {
            "url": "https://docs.example.com/tuning",
            "text": "Tune the connection pool size for throughput.",
        },
    ]
    store = docset_indexer.SqliteStore()
    store.replace_docset(
        key,
        [
            {
                "id": "c0",
                "url": pages[0]["url"],
                "seq": 0,
                "text": pages[0]["text"],
                "vector": [0.1],
                "model": "m",
            },
        ],
        {"source_path": "/not/on/this/box/paged.md", "pages": 2, "model": "m"},
        pages=pages,
    )
    store.close()
    return db


def test_index_stores_the_raw_pages_alongside_the_chunks(tmp_path, monkeypatch):
    import docset_indexer

    _seed_with_pages(tmp_path, monkeypatch)
    store = docset_indexer.SqliteStore()
    pages = list(store.dump_pages("paged__docs"))
    chunks = list(store.dump_chunks("paged__docs"))
    store.close()
    assert [p["seq"] for p in pages] == [0, 1]
    assert pages[1]["url"] == "https://docs.example.com/tuning"
    # page 2 was never chunked here -- the raw text is the only copy of it
    assert len(chunks) == 1
    assert "connection pool size" in pages[1]["text"]


def test_reindex_replaces_pages_rather_than_appending(tmp_path, monkeypatch):
    import docset_indexer

    _seed_with_pages(tmp_path, monkeypatch)
    store = docset_indexer.SqliteStore()
    store.replace_docset(
        "paged__docs",
        [],
        {"source_path": "/x.md", "pages": 1, "model": "m"},
        pages=[{"url": "https://docs.example.com/only", "text": "just this"}],
    )
    pages = list(store.dump_pages("paged__docs"))
    store.close()
    assert len(pages) == 1 and pages[0]["text"] == "just this"


def test_omitting_pages_leaves_stored_pages_untouched(tmp_path, monkeypatch):
    """pages=None must not silently wipe text an older caller does not know
    about; only an explicit [] clears it."""
    import docset_indexer

    _seed_with_pages(tmp_path, monkeypatch)
    store = docset_indexer.SqliteStore()
    store.replace_docset("paged__docs", [], {"source_path": "/x.md", "pages": 2, "model": "m"})
    assert len(list(store.dump_pages("paged__docs"))) == 2
    store.replace_docset(
        "paged__docs", [], {"source_path": "/x.md", "pages": 0, "model": "m"}, pages=[]
    )
    assert list(store.dump_pages("paged__docs")) == []
    store.close()


def test_dump_prefers_raw_pages_and_kind_can_force_chunks(tmp_path, monkeypatch, capsys):
    import argparse

    import docset_indexer

    _seed_with_pages(tmp_path, monkeypatch)
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    ns = argparse.Namespace(docset="paged__docs", kind="auto")
    assert docset_indexer.cmd_dump(ns) == 0
    rows = [json.loads(ln) for ln in capsys.readouterr().out.splitlines()]
    assert [r["kind"] for r in rows] == ["page", "page"]

    assert docset_indexer.cmd_dump(argparse.Namespace(docset="paged__docs", kind="chunks")) == 0
    rows = [json.loads(ln) for ln in capsys.readouterr().out.splitlines()]
    assert [r["kind"] for r in rows] == ["chunk"]


def test_search_over_stored_pages_locates_by_page(tmp_path, monkeypatch):
    """Full-fidelity path: the match is in a page that was never chunked."""
    from hub_manager import core

    db = _seed_with_pages(tmp_path, monkeypatch)
    monkeypatch.setenv("HUB_DOCSET_DB", str(db))
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(core, "python_for_hub", lambda: __import__("sys").executable)

    ok, text = docsets.search_index("paged__docs", "pool size", "regex")
    assert ok, text
    assert "stored text" in text
    assert "page 1.0" in text  # located by page index, not chunk
    assert "https://docs.example.com/tuning" in text


# ----------------------------------------------------- delete / refresh --


def _seed_store(tmp_path, monkeypatch, key="example__docs"):
    import docset_indexer

    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    store = docset_indexer.SqliteStore()
    store.replace_docset(
        key,
        [
            {
                "id": "c1",
                "url": "https://docs.example.com/intro",
                "seq": 0,
                "text": "hello",
                "vector": [0.1, 0.2],
                "model": "m",
            }
        ],
        {"source_path": "/tmp/example.md", "pages": 1, "model": "m"},
        pages=[{"url": "https://docs.example.com/intro", "text": "hello"}],
    )
    return docset_indexer, store


def test_sqlite_delete_drops_registry_chunks_and_pages(tmp_path, monkeypatch):
    """A delete must not leave orphans in ANY of the three tables — a stale
    `pages` row would keep the docset text-searchable after it is gone."""
    docset_indexer, store = _seed_store(tmp_path, monkeypatch)
    store.replace_docset(
        "other__docs",
        [
            {
                "id": "c1",
                "url": "https://other.example/",
                "seq": 0,
                "text": "keep me",
                "vector": [0.3],
                "model": "m",
            }
        ],
        {"source_path": "/tmp/other.md", "pages": 1, "model": "m"},
        pages=[{"url": "https://other.example/", "text": "keep me"}],
    )

    assert store.delete_docset("example__docs") is True
    assert [e["docset"] for e in store.list_docsets()] == ["other__docs"]
    assert list(store.dump_pages("example__docs")) == []
    assert list(store.dump_chunks("example__docs")) == []
    # the neighbour is untouched
    assert list(store.dump_pages("other__docs"))
    # deleting again is a no-op, not an error
    assert store.delete_docset("example__docs") is False
    store.close()


def test_delete_command_distinguishes_missing_from_deleted(tmp_path, monkeypatch, capsys):
    docset_indexer, store = _seed_store(tmp_path, monkeypatch)
    store.close()

    assert docset_indexer.main(["delete", "example__docs"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out == {
        "docset": "example__docs",
        "backend": "sqlite",
        "deleted": True,
        "facts_deleted": False,
    }

    assert docset_indexer.main(["delete", "example__docs"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out.strip())["deleted"] is False
    assert "no docset named" in captured.err
    assert docset_indexer.SqliteStore().list_docsets() == []


def test_tui_delete_wrapper_reports_missing_as_failure(tmp_path, monkeypatch):
    """The tab only offers rows it just listed, so 'not found' is a failure."""
    from hub_manager import core

    docset_indexer, store = _seed_store(tmp_path, monkeypatch)
    store.close()
    monkeypatch.setenv("HUB_DOCSET_DB", str(tmp_path / "docsets.db"))
    monkeypatch.setattr(core, "python_for_hub", lambda: __import__("sys").executable)

    ok, text = docsets.delete("example__docs")
    assert ok, text
    ok, text = docsets.delete("example__docs")
    assert not ok and "no docset named" in text


def test_index_argv_pins_the_docset_key():
    argv = docsets.index_argv("/tmp/example.md", "example__docs")
    assert argv[2:] == ["index", "/tmp/example.md", "--name", "example__docs"]


def test_refresh_argvs_chain_refine_then_both_layers():
    chain = docsets.refresh_argvs("/m/docs.example.com.md", "example__docs")
    ix = str(docsets.core.INDEXER_SCRIPT)
    assert [c[1:3] for c in chain] == [["-m", "docset_refine"], [ix, "index"], [ix, "index"]]
    assert chain[0][3:] == ["all", "/m/docs.example.com.md"]
    assert chain[1][3:] == ["/m/docs.example.com.clean.md", "--name", "example__docs"]
    assert chain[2][3:] == [
        "/m/docs.example.com.reference/all_units.jsonl",
        "--units",
        "--name",
        "example__docs",
    ]
    polish = docsets.refresh_argvs("/m/docs.example.com.md", "example__docs", polish=True)
    assert [c[3] for c in polish[:2]] == ["polish", "render"] and polish[2] == chain[2]


def test_detail_shows_the_fact_layer(tmp_path):
    src = _mirror(tmp_path)
    ref = tmp_path / "example.reference"
    ref.mkdir()
    (ref / "summary.json").write_text(
        json.dumps({"units": 12, "units_by_origin": {"code": 5, "table": 4, "llm": 3}})
    )
    (ref / "reference.md").write_text("# ref")
    text = docsets.docset_detail(
        {"docset": "example__docs", "pages": 2, "chunks": 9, "facts": 12, "source_path": str(src)}
    )
    assert "facts    12 units (indexed as example__docs__facts)" in text
    assert "12 units on disk — code 5, llm 3, table 4" in text
    assert f"[link=file://{ref / 'reference.md'}]" in text
    other = tmp_path / "other.md"
    other.write_text("x")
    bare = docsets.docset_detail({"docset": "x__y", "facts": None, "source_path": str(other)})
    assert "press e to build the fact layer" in bare and "on disk" not in bare


class _Item:
    def __init__(self, url, mirror=""):
        self.url, self.mirror = url, mirror


def test_queue_url_for_prefers_the_recorded_mirror_path():
    items = [
        _Item("https://a.example/", "/m/a.md"),
        _Item("https://docs.example.com/", "/m/docs.example.com.md"),
    ]
    entry = {"docset": "docsexamplecom__docs-example-com", "source_path": "/m/docs.example.com.md"}
    assert docsets.queue_url_for(entry, items) == "https://docs.example.com/"


def test_queue_url_for_falls_back_to_host_slug():
    """Older queue items have no mirror path recorded; the key's host slug
    is minted from the URL host, so that join still works."""
    items = [_Item("https://a.example/"), _Item("https://docs.example.com/x")]
    entry = {"docset": "docsexamplecom__docs-example-com", "source_path": ""}
    assert docsets.queue_url_for(entry, items) == "https://docs.example.com/x"


def test_queue_url_for_none_when_nothing_matches():
    items = [_Item("https://a.example/", "/m/a.md")]
    assert docsets.queue_url_for({"docset": "zzz__zzz", "source_path": "/m/zzz.md"}, items) is None
    assert docsets.queue_url_for({"docset": "", "source_path": ""}, items) is None


def test_mcp_delete_docset_is_a_dry_run_unless_confirmed(tmp_path, monkeypatch):
    """Agent-facing delete: list-then-decide. The dry run must not remove
    anything, and a confirmed delete must invalidate the cached store."""
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "mcp-server"))
    import hub_mcp_server

    docset_indexer, store = _seed_store(tmp_path, monkeypatch)
    store.close()
    monkeypatch.setattr(hub_mcp_server, "_store", None)
    invalidated = []
    monkeypatch.setattr(hub_mcp_server, "_invalidate_store", lambda: invalidated.append(True))

    dry = json.loads(hub_mcp_server.hub_delete_docset("example__docs"))
    assert dry["deleted"] is False and dry["would_delete"]["pages"] == 1
    assert [e["docset"] for e in docset_indexer.SqliteStore().list_docsets()] == ["example__docs"]
    assert invalidated == []

    missing = json.loads(hub_mcp_server.hub_delete_docset("nope__docs", confirm=True))
    assert missing == {"docset": "nope__docs", "deleted": False, "error": "no such docset"}

    done = json.loads(hub_mcp_server.hub_delete_docset("example__docs", confirm=True))
    assert done["deleted"] is True and done["chunks"] == 1
    assert docset_indexer.SqliteStore().list_docsets() == []
    assert invalidated == [True]
    hub_mcp_server._store = None


# ------------------------------------------------------------- facts layer --


def _facts_env(tmp_path, monkeypatch):
    import docset_indexer
    import embed_core

    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(
        embed_core,
        "embed_texts",
        lambda texts, model=None, timeout=120: [[1.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(embed_core, "embed_model", lambda: "m")
    return docset_indexer


def test_index_units_writes_a_facts_docset_with_unit_metadata(tmp_path, monkeypatch, capsys):
    di = _facts_env(tmp_path, monkeypatch)
    uf = tmp_path / "all_units.jsonl"
    uf.write_text(
        json.dumps(
            {
                "id": "u000001",
                "type": "snippet",
                "text": "Exit codes: claude --version",
                "code": {"lang": "bash", "body": "claude --version"},
                "origin": "code",
                "source_url": "https://h/hooks",
                "anchor": "#exit-codes",
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "u000002",
                "type": "fact",
                "text": "too short",
                "origin": "llm",
                "source_url": "https://h/hooks",
                "anchor": "",
            }
        )
        + "\n"
    )
    assert di.main(["index", str(uf), "--units"]) == 2  # --name required
    assert di.main(["index", str(uf), "--units", "--name", "h__hooks"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["docset"] == "h__hooks__facts" and out["units"] == 1
    store = di.SqliteStore()
    rows = list(store.dump_chunks("h__hooks__facts"))
    assert rows[0]["url"] == "https://h/hooks#exit-codes"
    assert rows[0]["text"] == "Exit codes\nclaude --version"  # first code line not doubled
    assert store.list_docsets(include_facts=True)[0]["docset"] == "h__hooks__facts"
    store.close()


def test_query_layer_auto_prefers_facts_and_list_folds_them(tmp_path, monkeypatch, capsys):
    di = _facts_env(tmp_path, monkeypatch)
    store = di.SqliteStore()

    def row(t, **md):
        return {
            "id": t,
            "url": "https://h/p",
            "seq": 0,
            "text": t,
            "vector": [1.0, 0.0],
            "model": "m",
            **md,
        }

    store.replace_docset(
        "h__d", [row("raw chunk text here")], {"source_path": "/m.md", "pages": 1, "model": "m"}
    )
    store.replace_docset(
        "h__d__facts",
        [row("fact text here", unit_type="fact", origin="llm")],
        {"source_path": "/u.jsonl", "pages": 0, "model": "m"},
    )
    store.replace_docset(
        "h__lonely", [row("no facts yet")], {"source_path": "/l.md", "pages": 1, "model": "m"}
    )
    store.close()

    assert di.main(["query", "h__d", "anything"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["layer"] == "facts" and out["queried"] == "h__d__facts"
    assert out["results"][0]["text"] == "fact text here"
    assert out["results"][0]["unit_type"] == "fact" and out["results"][0]["origin"] == "llm"
    assert di.main(["query", "h__d", "anything", "--layer", "raw"]) == 0
    raw = json.loads(capsys.readouterr().out)
    assert raw["layer"] == "raw" and "unit_type" not in raw["results"][0]
    assert di.main(["query", "h__lonely", "anything"]) == 0
    assert json.loads(capsys.readouterr().out)["layer"] == "raw"  # auto falls back

    assert di.main(["list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [e["docset"] for e in listed] == ["h__d", "h__lonely"]
    assert listed[0]["facts"] == 1 and listed[1]["facts"] is None
    assert di.main(["list", "--all"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 3


def test_delete_removes_the_facts_twin(tmp_path, monkeypatch, capsys):
    di = _facts_env(tmp_path, monkeypatch)
    store = di.SqliteStore()
    row = {"id": "c", "url": "u", "seq": 0, "text": "text here ok", "vector": [1.0], "model": "m"}
    store.replace_docset("h__d", [row], {"source_path": "/m.md", "pages": 1, "model": "m"})
    store.replace_docset("h__d__facts", [row], {"source_path": "/u", "pages": 0, "model": "m"})
    store.close()
    assert di.main(["delete", "h__d"]) == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["deleted"] is True and out["facts_deleted"] is True
    assert di.SqliteStore().list_docsets(include_facts=True) == []


def test_mcp_query_docset_layer_and_delete_twin(tmp_path, monkeypatch):
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "mcp-server"))
    import hub_mcp_server

    di = _facts_env(tmp_path, monkeypatch)
    store = di.SqliteStore()

    def row(t, **md):
        return {
            "id": t,
            "url": "https://h/p",
            "seq": 0,
            "text": t,
            "vector": [1.0, 0.0],
            "model": "m",
            **md,
        }

    store.replace_docset(
        "h__d", [row("raw chunk text here")], {"source_path": "/m.md", "pages": 1, "model": "m"}
    )
    store.replace_docset(
        "h__d__facts",
        [row("fact text here", unit_type="fact", origin="llm")],
        {"source_path": "/u.jsonl", "pages": 0, "model": "m"},
    )
    store.close()
    monkeypatch.setattr(hub_mcp_server, "_store", None)
    monkeypatch.setattr(hub_mcp_server, "_invalidate_store", lambda: None)

    out = json.loads(hub_mcp_server.hub_query_docset("h__d", "q"))
    assert out["layer"] == "facts" and out["results"][0]["unit_type"] == "fact"
    assert json.loads(hub_mcp_server.hub_query_docset("h__d", "q", layer="raw"))["layer"] == "raw"
    assert hub_mcp_server.hub_query_docset("h__d", "q", layer="nope").startswith("ERROR")
    listed = json.loads(hub_mcp_server.hub_list_docsets())
    assert [e["docset"] for e in listed] == ["h__d"] and listed[0]["facts"] == 1
    gone = json.loads(hub_mcp_server.hub_delete_docset("h__d", confirm=True))
    assert gone["deleted"] and gone["facts_deleted"] and gone["facts"] == 1
    assert di.SqliteStore().list_docsets(include_facts=True) == []
    hub_mcp_server._store = None


def test_load_units_dedupes_stale_duplicate_ids(tmp_path):
    import docset_indexer

    uf = tmp_path / "all_units.jsonl"
    row = {
        "type": "fact",
        "text": "a fact that is long enough",
        "origin": "llm",
        "source_url": "https://h/p",
        "anchor": "",
    }
    uf.write_text(
        json.dumps({"id": "u000001", **row}) + "\n" + json.dumps({"id": "u000001", **row}) + "\n"
    )
    ids = [r["id"] for r in docset_indexer.load_units(uf)]
    assert ids[0] == "u000001" and ids[1] != "u000001" and len(set(ids)) == 2


def test_mcp_docset_index_returns_the_exported_llms_txt(tmp_path, monkeypatch):
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "mcp-server"))
    import hub_mcp_server

    di = _facts_env(tmp_path, monkeypatch)
    mirror = tmp_path / "ex.dev.md"
    mirror.write_text("x")
    store = di.SqliteStore()
    store.replace_docset(
        "exdev__ex-dev",
        [{"id": "c", "url": "u", "seq": 0, "text": "text here ok", "vector": [1.0], "model": "m"}],
        {"source_path": str(tmp_path / "ex.dev.clean.md"), "pages": 1, "model": "m"},
    )
    store.close()
    monkeypatch.setattr(hub_mcp_server, "_store", None)
    out = json.loads(hub_mcp_server.hub_docset_index("exdev__ex-dev"))
    assert "not exported yet" in out["error"] and out["expected"].endswith("ex.dev.llms/llms.txt")
    d = tmp_path / "ex.dev.llms"
    d.mkdir()
    (d / "llms.txt").write_text("# Ex\n\n> Ex docs.\n")
    out = json.loads(hub_mcp_server.hub_docset_index("exdev__ex-dev"))
    assert out["text"].startswith("# Ex") and out["served_at"].endswith("/d/ex.dev/llms.txt")
    assert out["llms_full_url"].endswith("/d/ex.dev/llms-full.txt")
    assert hub_mcp_server.hub_docset_index("exdev__ex-dev", file="llms-full.txt").startswith(
        "ERROR"
    )
    hub_mcp_server._store = None
