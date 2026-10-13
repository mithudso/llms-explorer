# llmsx/tests/test_explorer_scratchpad.py — facts-first tabs, llms highlighting,
# the scratchpad, spatial down/up focus, and bulk marks for concepts with no facts.
from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("textual")

from llmsx import explorer_store as es  # noqa: E402
from conftest import make_repo  # noqa: E402


async def _settle(app, pilot):
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _run(coro_factory, repo):
    from llmsx.explorer import Explorer

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(160, 44)) as pilot:
            await coro_factory(app, pilot)
        return app

    return asyncio.run(go())


def _llms_dir(tmp_path, monkeypatch, slug="root-domain"):
    base = tmp_path / "llms-concepts"
    d = base / f"{slug}.llms"
    d.mkdir(parents=True)
    (d / "llms-facts.txt").write_text(
        "# Root facts\n\n> summary line\n\n## Section\n\n"
        "- Root is the top [src: notes] — ~/x.md:3 (as of 2026-10-01)\n")
    (d / "llms.txt").write_text("# Root\n\n- [Doc](https://ex.dev/doc): the doc\n")
    monkeypatch.setenv("LLMSX_CONCEPTS_PATH", str(base))
    return d


def test_highlight_line_styles_llms_parts():
    from llmsx.explorer_lines import STYLES, highlight_line
    t = highlight_line("## Section")
    assert any(s.style == STYLES["h2"] for s in t.spans)
    line = "- [Doc](https://ex.dev/doc): never do X [src: a] — ~/f.md:3 (as of 2026-10-01)"
    t = highlight_line(line)
    styles = {str(s.style) for s in t.spans}
    for key in ("bullet", "link_text", "url", "keyword", "tag", "cite", "date"):
        assert STYLES[key] in styles, key
    assert highlight_line("[bold]x[/bold] <script>").plain == "[bold]x[/bold] <script>", \
        "file text is never parsed as markup"


def test_scratchpad_rows_dedupe_and_strip_bullets(home, tmp_path):
    src = tmp_path / "llms-facts.txt"
    assert es.add_to_scratchpad("- Fact one", "Kid Concept", src, 4)
    assert not es.add_to_scratchpad("Fact one", "Other", None), "same text is not saved twice"
    assert not es.add_to_scratchpad("   ")
    assert es.add_to_scratchpad("https://ex.dev/a")
    text = es.read_scratchpad()
    assert text.startswith("# Scratchpad\n\n")
    assert f"- Fact one — Kid Concept · {src}:4 (as of " in text
    assert "- https://ex.dev/a (as of " in text
    assert es.scratchpad_path() == home / "scratchpad.md"


def test_mark_unresearched_marks_and_queues_every_no_facts_concept(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    outline = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    assert es.unresearched_concepts(repo, outline) == ["Root Domain", "Ghost Concept"]
    es.set_mark(repo, "root-domain", "needs-review")
    marked, queued = es.mark_unresearched(repo, outline)
    assert (marked, queued) == (1, 2)
    marks = es.load_marks(repo)
    assert marks["root-domain"]["state"] == "needs-review", "an existing mark is kept"
    assert marks["ghost-concept"]["state"] == "further-research"
    assert "kid-concept" not in marks, "a concept with facts is left alone"
    rows = {e["concept"]: e for e in es.load_queue(repo)}
    assert rows["Ghost Concept"]["parent"] == "Root Domain" and "Root Domain" in rows
    assert "Already Queued" in rows, "the queue is appended, not rewritten"
    assert es.mark_unresearched(repo, outline) == (0, 0), "a second run changes nothing"


def test_facts_first_line_view_scratch_and_picker(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    _llms_dir(tmp_path, monkeypatch)

    async def check(app, pilot):
        from textual.widgets import TabbedContent
        from llmsx.explorer import LinePicker
        from llmsx.explorer_lines import LineView
        tabs = app.query_one("#tabs", TabbedContent)
        app._select("Kid Concept")
        await _settle(app, pilot)
        assert tabs.active == "pane-facts"
        tabs.active = "pane-skill"
        await _settle(app, pilot)
        app._select("Root Domain")         # no pack: lands on the hub's llms-facts.txt
        await _settle(app, pilot)
        assert app._pane_files[tabs.active][0].name == "llms-facts.txt"
        view = app.query_one(f"#{tabs.active}").query_one(LineView)
        assert view.lines[0] == "# Root facts" and view.current() == (1, "# Root facts")
        view.highlighted = 6
        app.action_scratch_line()
        await _settle(app, pilot)
        assert "Root is the top" in es.read_scratchpad()
        assert "llms-facts.txt:7" in es.read_scratchpad()
        app._refresh("Root Domain")         # a re-render of the same concept keeps the tab
        await _settle(app, pilot)
        tabs.active = "pane-skill"
        await _settle(app, pilot)
        app._refresh()
        await _settle(app, pilot)
        assert tabs.active == "pane-skill"
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_scratch_line()            # Markdown tab: the picker opens
        await _settle(app, pilot)
        assert isinstance(app.screen, LinePicker)
        app.screen._picked(type("E", (), {"option_index": 0})())
        await _settle(app, pilot)
        assert es.read_scratchpad().count("\n- ") == 2
        app.screen.dismiss(None)
        await _settle(app, pilot)
        from llmsx.explorer import Scratchpad
        app.query_one("#btn-pad").press()        # the button opens the editor
        await _settle(app, pilot)
        assert isinstance(app.screen, Scratchpad)
        app.screen.dismiss("# Scratchpad\n\n- edited\n")
        await _settle(app, pilot)
        assert es.read_scratchpad() == "# Scratchpad\n\n- edited\n"

    _run(check, repo)


def test_down_moves_focus_to_the_widget_below(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from textual.widgets import Input, Tabs
        from llmsx.explorer import OutlineTree
        app.query_one("#filter", Input).focus()
        await pilot.press("down")
        await _settle(app, pilot)
        assert isinstance(app.focused, OutlineTree)
        app.query_one("#btn-dr").focus()
        await pilot.press("down")
        await _settle(app, pilot)
        assert isinstance(app.focused, Tabs)
        await pilot.press("up")
        await _settle(app, pilot)
        assert app.focused.id and app.focused.id.startswith("btn-"), "up returns to the buttons"
        tree = app.query_one("#outline", OutlineTree)
        tree.root.children[0].expand()
        tree.focus()
        await _settle(app, pilot)
        tree.move_cursor(tree.root.children[0])
        await _settle(app, pilot)
        await pilot.press("down")
        await _settle(app, pilot)
        assert app.focused is tree, "the outline keeps its own down"
        assert tree.cursor_node.data == "Kid Concept"

    _run(check, repo)


def test_mark_unresearched_action_confirms_then_writes(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer import Confirm
        app.action_mark_unresearched()
        await _settle(app, pilot)
        assert isinstance(app.screen, Confirm)
        assert es.load_marks(repo) == {}, "nothing is written before the confirmation"
        app.screen.dismiss(True)
        await _settle(app, pilot)
        assert es.load_marks(repo)["ghost-concept"]["state"] == "further-research"
        labels = []

        def walk(node):
            for c in node.children:
                labels.append(str(c.label))
                walk(c)
        walk(app.query_one("#outline").root)
        assert any("Ghost Concept" in lbl and "[further-research]" in lbl for lbl in labels)

    _run(check, repo)
