# llmsx/tests/test_concepts_tui.py
"""Offline: every fixture is a fake pack directory under tmp_path.

`llmsx.concepts_tui` had no test coverage at all before this file — the
whole module, including the one write action it has (`$EDITOR` via
`subprocess.call`), ran only by hand. These are the smallest tests that
actually exercise the Textual app rather than just its data layer
(`llmsx.concepts`, covered by `test_concepts.py`).
"""
import json

import pytest

pytest.importorskip("textual")


def _write_pack(root, slug, concept, *, facets=None, related=None):
    pack_dir = root / f"{slug}.llms"
    pack_dir.mkdir(parents=True)
    manifest = {"slug": slug, "concept": concept, "kind": "concept",
                "summary": f"summary for {concept}", "facets": facets or {}, "files": {}}
    (pack_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pack_dir / "llms.txt").write_text(f"# {concept}\n", encoding="utf-8")
    return pack_dir


def _run(coro_factory, data_path):
    import asyncio

    from llmsx.concepts_tui import ConceptPackBrowser

    async def go():
        app = ConceptPackBrowser(str(data_path))
        async with app.run_test(size=(100, 40)) as pilot:
            await coro_factory(app, pilot)
        return app

    return asyncio.run(go())


def test_table_populates_from_the_catalog_and_filters_live(tmp_path):
    _write_pack(tmp_path, "rsl", "Really Simple Licensing", facets={"facts": 3})
    _write_pack(tmp_path, "robots", "robots.txt")

    async def check(app, pilot):
        from textual.widgets import DataTable

        table = app.query_one("#packs-table", DataTable)
        assert table.row_count == 2

        app.query_one("#packs-filter").value = "robots"
        await pilot.pause()
        assert table.row_count == 1

        app.query_one("#packs-filter").value = "zzz-nope"
        await pilot.pause()
        assert table.row_count == 0

    _run(check, tmp_path)


def test_missing_root_is_reported_not_raised(tmp_path):
    async def check(app, pilot):
        from textual.widgets import DataTable

        table = app.query_one("#packs-table", DataTable)
        assert table.row_count == 0

    app = _run(check, tmp_path / "does-not-exist")
    # a genuinely missing root is not an error for iter_packs/library (see
    # test_concepts.py) — so this is not the `_load_failed` path; assert the
    # app simply ran to completion with an empty table.
    assert app._load_failed is False


def test_edit_with_no_selection_prompts_rather_than_crashing(tmp_path):
    # an empty packs directory: the table has no rows, so `_selected_entry()`
    # returns None the same way it would for a populated table with no
    # cursor move — this exercises the guard without needing to fight
    # Textual's default cursor placement once rows exist.
    async def check(app, pilot):
        from textual.widgets import RichLog

        app._edit_selected()
        log = app.query_one("#packs-detail", RichLog)
        assert any("select a concept pack row first" in str(line) for line in log.lines)

    _run(check, tmp_path)


def test_entry_helper_looks_up_by_slug_and_handles_no_match(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")

    async def check(app, pilot):
        assert app._entry(None) is None
        assert app._entry("nope") is None
        entry = app._entry("rsl")
        assert entry is not None
        assert entry["concept"] == "RSL"
        # the entry carries its own directory, so a caller (e.g. the edit
        # action) never needs a second resolve_pack() round trip for it.
        assert entry["dir"].endswith("rsl.llms")

    _run(check, tmp_path)


def test_edit_selected_shlex_splits_an_editor_with_flags(tmp_path, monkeypatch):
    """`$EDITOR="code -w"` used to be passed as a single (nonexistent)
    argv[0]; it must now be split into `["code", "-w", <path>]`."""
    _write_pack(tmp_path, "rsl", "RSL")
    monkeypatch.setenv("EDITOR", "code -w")
    seen = {}

    def fake_call(argv):
        seen["argv"] = argv
        return 0

    async def check(app, pilot):
        import contextlib

        import llmsx.concepts_tui as concepts_tui_mod

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        # App.suspend() has nothing to suspend to under the headless test
        # driver (no real terminal) — stub it so this test exercises the
        # actual argv-building code, not Textual's terminal-suspend plumbing.
        monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext())
        table = app.query_one("#packs-table")
        table.move_cursor(row=0)
        await pilot.pause()
        app._edit_selected()

    _run(check, tmp_path)
    assert seen["argv"][:2] == ["code", "-w"]
    assert seen["argv"][2].endswith("llms.txt")

def test_edit_selected_refuses_a_symlinked_llms_txt(tmp_path, monkeypatch):
    """The same containment rule as concepts.serve(): a pack directory can
    be legitimate while a file inside it — here llms.txt — is a symlink
    escape. The editor must not be launched against the escaped target."""
    pack_dir = _write_pack(tmp_path, "trap", "Trap")
    outside = tmp_path / "outside.txt"
    outside.write_text("SECRET", encoding="utf-8")
    (pack_dir / "llms.txt").unlink()
    (pack_dir / "llms.txt").symlink_to(outside)

    called = {}

    def fake_call(argv):
        called["argv"] = argv
        return 0

    async def check(app, pilot):
        import llmsx.concepts_tui as concepts_tui_mod
        from textual.widgets import RichLog

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        table = app.query_one("#packs-table")
        table.move_cursor(row=0)
        await pilot.pause()
        app._edit_selected()
        log = app.query_one("#packs-detail", RichLog)
        assert any("outside the pack directory" in str(line) for line in log.lines)

    _run(check, tmp_path)
    assert "argv" not in called       # the editor must never have been launched

