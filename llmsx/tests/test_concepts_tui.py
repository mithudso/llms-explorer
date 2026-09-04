# llmsx/tests/test_concepts_tui.py
"""Offline: every fixture is a fake pack directory under tmp_path.

`llmsx.concepts_tui` had no test coverage at all before this file — the
whole module, including the one write action it has (`$EDITOR` via
`subprocess.call`), ran only by hand. These are the smallest tests that
actually exercise the Textual app rather than just its data layer
(`llmsx.concepts`, covered by `test_concepts.py`).
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("textual")


def _write_pack(root, slug, concept, *, facets=None, related=None, files=None):
    """`related` seeds `concept-graph.json` nodes (plain term strings, most-
    referenced first — see `concepts.related_terms()`); `files` seeds the
    manifest's `files` map (name -> token count) and writes each file's
    content to disk so a preview can actually read it."""
    pack_dir = root / f"{slug}.llms"
    pack_dir.mkdir(parents=True)
    files = files or {}
    manifest = {"slug": slug, "concept": concept, "kind": "concept",
                "summary": f"summary for {concept}", "facets": facets or {},
                "files": {name: {"tokens": tokens} for name, tokens in files.items()}}
    (pack_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pack_dir / "llms.txt").write_text(f"# {concept}\n", encoding="utf-8")
    for name in files:
        if name != "llms.txt":
            (pack_dir / name).write_text(f"content of {name} for {concept}\n", encoding="utf-8")
    if related:
        graph = {"nodes": [{"term": term, "relation": "related", "hits": weight}
                            for weight, term in enumerate(reversed(related), start=1)]}
        (pack_dir / "concept-graph.json").write_text(json.dumps(graph), encoding="utf-8")
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
        from textual.widgets import Static

        app._edit_selected()
        status = app.query_one("#packs-status", Static)
        assert "select a concept pack row first" in str(status.content)

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
        from textual.widgets import Static

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        table = app.query_one("#packs-table")
        table.move_cursor(row=0)
        await pilot.pause()
        app._edit_selected()
        status = app.query_one("#packs-status", Static)
        assert "outside the pack directory" in str(status.content)

    _run(check, tmp_path)
    assert "argv" not in called       # the editor must never have been launched


def test_populate_tree_builds_clickable_concept_and_file_branches(tmp_path):
    """Selecting a pack must expand into a `Tree` with a "Related concepts"
    branch (one node per term from `concept-graph.json`) and a "Files"
    branch (one leaf per manifest file) — the whole point of the tree view
    over the old flat RichLog dump. A related term that matches another
    pack (robots.txt) becomes an expandable pack-ref node; one that matches
    nothing (TDMRep) stays a plain leaf."""
    _write_pack(tmp_path, "robots", "robots.txt")
    _write_pack(tmp_path, "rsl", "RSL", related=["robots.txt", "TDMRep"],
                files={"llms.txt": 42, "llms-facts.txt": 7})

    async def check(app, pilot):
        from textual.widgets import Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        concepts_branch, files_branch = tree.root.children[-2], tree.root.children[-1]

        concept_labels = [str(c.label) for c in concepts_branch.children]
        assert concept_labels == ["robots.txt", "TDMRep"]
        robots_node, tdmrep_node = concepts_branch.children
        assert robots_node.data["kind"] == "pack-ref"
        assert robots_node.data["entry"]["slug"] == "robots"
        assert tdmrep_node.data == {"kind": "concept-term", "term": "TDMRep"}

        file_labels = [str(f.label) for f in files_branch.children]
        assert any("llms.txt" in label and "42" in label for label in file_labels)
        assert any("llms-facts.txt" in label and "7" in label for label in file_labels)

    _run(check, tmp_path)


def test_expanding_a_pack_ref_node_lazily_populates_its_own_subtree(tmp_path):
    """A related concept that resolves to another pack must drill IN
    PLACE — its own summary/useful-for/Related-concepts/Files nested
    beneath it — rather than replacing the whole tree, so the parent
    pack's context is never lost."""
    _write_pack(tmp_path, "robots", "robots.txt", files={"llms.txt": 5})
    _write_pack(tmp_path, "rsl", "RSL", related=["robots.txt"])

    async def check(app, pilot):
        from textual.widgets import Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        concepts_branch = tree.root.children[-2]
        robots_node = concepts_branch.children[0]
        assert robots_node.data.get("_populated") is None
        assert len(robots_node.children) == 0     # not yet populated

        robots_node.expand()
        await pilot.pause()

        assert robots_node.data["_populated"] is True
        assert len(robots_node.children) > 0
        nested_files_branch = robots_node.children[-1]
        assert any("llms.txt" in str(f.label) for f in nested_files_branch.children)
        # the root pack is untouched — drilling in is additive, not a jump
        assert app._current_entry["slug"] == "rsl"

    _run(check, tmp_path)


def test_a_cycle_back_to_an_ancestor_pack_renders_as_a_leaf_not_infinite_recursion(tmp_path):
    _write_pack(tmp_path, "a", "A", related=["B"])
    _write_pack(tmp_path, "b", "B", related=["A"])

    async def check(app, pilot):
        from textual.widgets import Tree

        app._populate_tree(app._entry("a"))
        tree = app.query_one("#packs-tree", Tree)
        b_node = tree.root.children[-2].children[0]
        assert b_node.data["ancestors"] == ["a", "b"]

        b_node.expand()
        await pilot.pause()

        b_concepts_branch = b_node.children[-2]
        a_leaf = b_concepts_branch.children[0]
        assert "cycle" in str(a_leaf.label)
        assert a_leaf.data == {"kind": "concept-term", "term": "A"}
        assert a_leaf.allow_expand is False or len(a_leaf.children) == 0

    _run(check, tmp_path)


def test_selecting_a_file_leaf_opens_a_preview_with_metadata_above_content(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={"llms-facts.txt": 7})

    async def check(app, pilot):
        from textual.widgets import Static

        entry = app._entry("rsl")
        app._populate_tree(entry)
        status = app.query_one("#packs-status", Static)
        app._preview_file(entry, "llms-facts.txt", status)
        await pilot.pause()

        from llmsx.concepts_tui import FilePreviewScreen

        assert isinstance(app.screen, FilePreviewScreen)
        assert "RSL" in app.screen._meta and "summary for RSL" in app.screen._meta
        assert "content of llms-facts.txt for RSL" in app.screen._body
        assert "previewing llms-facts.txt" in str(status.content)
        assert app._current_file == (entry, "llms-facts.txt")

    _run(check, tmp_path)


def test_preview_file_refuses_a_symlink_escape(tmp_path):
    """Same containment rule as `_edit_file()`: a file inside an
    otherwise-legitimate pack directory can still be a symlink escape."""
    pack_dir = _write_pack(tmp_path, "trap", "Trap", files={"llms-facts.txt": 1})
    outside = tmp_path / "outside.txt"
    outside.write_text("SECRET", encoding="utf-8")
    (pack_dir / "llms-facts.txt").unlink()
    (pack_dir / "llms-facts.txt").symlink_to(outside)

    async def check(app, pilot):
        from textual.widgets import Static

        entry = app._entry("trap")
        app._populate_tree(entry)
        status = app.query_one("#packs-status", Static)
        app._preview_file(entry, "llms-facts.txt", status)
        assert "outside the pack directory" in str(status.content)
        assert app.screen.id == "_default"       # still on the main screen

    _run(check, tmp_path)


def test_edit_current_file_edits_whatever_was_last_previewed(tmp_path, monkeypatch):
    """The tree-level edit action must target the last-previewed file, not
    always the top-level row's llms.txt — a nested pack's file included."""
    _write_pack(tmp_path, "rsl", "RSL", files={"llms-facts.txt": 7})
    monkeypatch.setenv("EDITOR", "true")
    seen = {}

    def fake_call(argv):
        seen["argv"] = argv
        return 0

    async def check(app, pilot):
        import contextlib

        from textual.widgets import Static

        import llmsx.concepts_tui as concepts_tui_mod

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext())
        entry = app._entry("rsl")
        app._populate_tree(entry)
        status = app.query_one("#packs-status", Static)
        app._preview_file(entry, "llms-facts.txt", status)
        app._edit_current_file()

    _run(check, tmp_path)
    assert seen["argv"][-1].endswith("llms-facts.txt")


def test_edit_current_file_with_nothing_previewed_prompts_rather_than_crashing(tmp_path):
    async def check(app, pilot):
        from textual.widgets import Static

        app._edit_current_file()
        status = app.query_one("#packs-status", Static)
        assert "select a file in the tree first" in str(status.content)

    _run(check, tmp_path)


def test_current_node_term_falls_back_from_node_to_selected_pack(tmp_path):
    """The skill buttons need a target term: prefer whatever tree node is
    highlighted, else fall back to the pack row that built the tree."""
    _write_pack(tmp_path, "rsl", "RSL")

    async def check(app, pilot):
        entry = app._entry("rsl")
        app._populate_tree(entry)
        assert app._current_node_term() == "RSL"      # no node highlighted yet

        app._current_node_data = {"kind": "concept-term", "term": "some-term"}
        assert app._current_node_term() == "some-term"

        app._current_node_data = {"kind": "pack-ref", "entry": entry}
        assert app._current_node_term() == "RSL"

    _run(check, tmp_path)


def test_optimizer_target_dispatches_llms_files_to_ldo_and_others_to_ddo(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={"llms.txt": 1})

    async def check(app, pilot):
        entry = app._entry("rsl")
        app._populate_tree(entry)

        # nothing highlighted: falls back to the pack's own llms.txt
        target = app._optimizer_target()
        assert target is not None and target.name == "llms.txt"
        assert app._optimizer_command_for(target) == "/ldo"

        assert app._optimizer_command_for(Path("SKILL.md")) == "/sko"
        assert app._optimizer_command_for(Path("README.md")) == "/ddo"

    _run(check, tmp_path)


def test_run_claude_skill_shells_out_and_refreshes(tmp_path, monkeypatch):
    _write_pack(tmp_path, "rsl", "RSL")
    seen = {}

    def fake_call(argv):
        seen["argv"] = argv
        return 0

    async def check(app, pilot):
        import contextlib

        from textual.widgets import Static

        import llmsx.concepts_tui as concepts_tui_mod

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext())
        status = app.query_one("#packs-status", Static)
        app._run_claude_skill("/dr some-topic", status)
        assert seen["argv"] == ["claude", "-p", "/dr some-topic"]
        assert "back from claude" in str(status.content)

    _run(check, tmp_path)


def test_run_claude_skill_missing_binary_reports_status_not_crash(tmp_path, monkeypatch):
    async def check(app, pilot):
        import contextlib

        from textual.widgets import Static

        monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext())

        def fake_call(argv):
            raise FileNotFoundError("no such file: claude")

        import llmsx.concepts_tui as concepts_tui_mod

        monkeypatch.setattr(concepts_tui_mod.subprocess, "call", fake_call)
        status = app.query_one("#packs-status", Static)
        app._run_claude_skill("/dr x", status)
        assert "claude CLI not found on PATH" in str(status.content)

    _run(check, tmp_path)


def test_selecting_a_pack_ref_node_also_previews_its_primary_file(tmp_path):
    """Confirmed behavior: picking a concept must show its file AND its
    metadata together, not just drill into a sub-tree."""
    _write_pack(tmp_path, "robots", "robots.txt", files={"llms.txt": 5})
    _write_pack(tmp_path, "rsl", "RSL", related=["robots.txt"])

    async def check(app, pilot):
        from textual.widgets import Static, Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        robots_node = tree.root.children[-2].children[0]
        assert robots_node.data["kind"] == "pack-ref"

        app._tree_node_selected(Tree.NodeSelected(robots_node))
        await pilot.pause()

        from llmsx.concepts_tui import FilePreviewScreen

        assert isinstance(app.screen, FilePreviewScreen)
        assert "robots.txt" in app.screen._meta         # the pack's own metadata
        assert "# robots.txt" in app.screen._body        # llms.txt's actual content
        status = app.query_one("#packs-status", Static)
        assert "previewing llms.txt" in str(status.content)

    _run(check, tmp_path)


def test_preview_pack_primary_file_prefers_llms_txt_over_other_files(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={"llms-facts.txt": 2, "llms.txt": 5})

    async def check(app, pilot):
        from textual.widgets import Static

        entry = app._entry("rsl")
        status = app.query_one("#packs-status", Static)
        app._preview_pack_primary_file(entry, status)
        await pilot.pause()

        assert app._current_file == (entry, "llms.txt")

    _run(check, tmp_path)


def test_preview_pack_primary_file_falls_back_when_no_llms_txt(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={"llms-facts.txt": 2})

    async def check(app, pilot):
        from textual.widgets import Static

        entry = app._entry("rsl")
        status = app.query_one("#packs-status", Static)
        app._preview_pack_primary_file(entry, status)
        await pilot.pause()

        assert app._current_file == (entry, "llms-facts.txt")

    _run(check, tmp_path)


def test_preview_pack_primary_file_with_no_files_reports_status(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")   # no files kwarg -> empty files dict

    async def check(app, pilot):
        from textual.widgets import Static

        entry = app._entry("rsl")
        status = app.query_one("#packs-status", Static)
        app._preview_pack_primary_file(entry, status)
        assert "no files to preview" in str(status.content)

    _run(check, tmp_path)


def test_right_arrow_expands_the_cursor_node_when_the_tree_has_focus(tmp_path):
    _write_pack(tmp_path, "robots", "robots.txt")
    _write_pack(tmp_path, "rsl", "RSL", related=["robots.txt"])

    async def check(app, pilot):
        from textual.widgets import Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        concepts_branch = tree.root.children[-2]
        robots_node = concepts_branch.children[0]
        assert not concepts_branch.is_expanded
        assert not robots_node.is_expanded

        tree.focus()
        await pilot.pause()
        tree.cursor_line = concepts_branch.line     # only visible (non -1) line to start
        app.action_expand_node()                    # right arrow: reveal robots_node
        await pilot.pause()
        assert concepts_branch.is_expanded
        assert robots_node.line != -1

        tree.cursor_line = robots_node.line
        app.action_expand_node()                    # right arrow again: expand it
        await pilot.pause()

        assert robots_node.is_expanded
        assert robots_node.data["_populated"] is True   # NodeExpanded fired too

    _run(check, tmp_path)


def test_left_arrow_collapses_the_cursor_node_when_the_tree_has_focus(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL", files={"llms.txt": 1})

    async def check(app, pilot):
        from textual.widgets import Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        assert tree.root.is_expanded

        tree.focus()
        tree.cursor_line = tree.root.line
        await pilot.pause()
        app.action_collapse_node()
        await pilot.pause()

        assert not tree.root.is_expanded

    _run(check, tmp_path)


def test_arrow_actions_are_a_no_op_when_the_tree_is_not_focused(tmp_path):
    """The filter Input owns left/right for text-cursor movement — the
    tree's own expand/collapse actions must not fire while it has focus."""
    _write_pack(tmp_path, "robots", "robots.txt")
    _write_pack(tmp_path, "rsl", "RSL", related=["robots.txt"])

    async def check(app, pilot):
        from textual.widgets import Input, Tree

        app._populate_tree(app._entry("rsl"))
        tree = app.query_one("#packs-tree", Tree)
        concepts_branch = tree.root.children[-2]     # collapsed, but a visible line
        await pilot.pause()                          # let the tree compute line numbers
        assert concepts_branch.line != -1
        assert not concepts_branch.is_expanded

        app.query_one("#packs-filter", Input).focus()
        await pilot.pause()
        tree.cursor_line = concepts_branch.line
        app.action_expand_node()
        await pilot.pause()

        assert not concepts_branch.is_expanded        # unchanged: Input had focus, not the tree

    _run(check, tmp_path)


def test_index_all_button_delegates_hub_wide_to_the_librarian(tmp_path):
    _write_pack(tmp_path, "rsl", "RSL")

    async def check(app, pilot):
        calls = []
        app._run_claude_skill = lambda prompt, status: calls.append(prompt)
        app._index_all_button(None)
        assert len(calls) == 1
        prompt = calls[0].lower()
        assert "librarian" in prompt
        assert "semantic" in prompt and "keyword" in prompt

    _run(check, tmp_path)

