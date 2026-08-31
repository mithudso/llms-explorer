# llmsx/tests/test_tree_cli.py
# ruff: noqa: E501  -- the fixture mirrors real tree.json rows
import json

from llmsx import tree

DATA = {"generated": "2026-08-31", "roots": ["root"], "edges": [["root", "kid"]],
        "frontier": [{"concept": "Ghost", "parent": "Root", "parent_slug": "root"}],
        "nodes": {"root": {"slug": "root", "concept": "Root", "parent": None, "parent_slug": None,
                           "children": [{"concept": "Kid", "slug": "kid", "state": "researched"},
                                        {"concept": "Ghost", "slug": "ghost", "state": "frontier"}],
                           "aliases": ["Roots"], "researchedAt": "2026-08-01", "sourcesCount": 3,
                           "conceptsCount": 9, "skillId": "s", "state": "researched"},
                  "kid": {"slug": "kid", "concept": "Kid", "parent": "Root", "parent_slug": "root",
                          "children": [], "aliases": [], "researchedAt": "2026-08-02",
                          "sourcesCount": 1, "conceptsCount": 2, "skillId": None, "state": "researched"}}}


def test_render_ascii_marks_frontier(tmp_path):
    out = tree.render_ascii(DATA)
    assert "Root" in out and "Kid" in out
    assert "Ghost" in out and "·" in out          # frontier marker
    assert out.index("Root") < out.index("Kid")


def test_search_matches_alias_not_just_concept():
    assert [n["slug"] for n in tree.search(DATA, "roots")] == ["root"]
    assert [n["slug"] for n in tree.search(DATA, "kid")] == ["kid"]
    assert tree.search(DATA, "zzz") == []


def test_load_reads_the_generated_file(tmp_path):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(DATA))
    assert tree.load(p)["roots"] == ["root"]


# --- CLI surface ------------------------------------------------------- #

def _tree_file(tmp_path):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(DATA))
    return p


def test_cli_show_and_search_read_the_data_flag(tmp_path, capsys):
    from llmsx.__main__ import main

    assert main(["--data", str(_tree_file(tmp_path)), "tree", "show"]) == 0
    out = capsys.readouterr().out
    assert "▪ Root" in out and "· Ghost" in out

    assert main(["--data", str(_tree_file(tmp_path)), "tree", "search", "roots"]) == 0
    assert "Root" in capsys.readouterr().out


def test_cli_reports_a_missing_tree_instead_of_a_traceback(capsys):
    from llmsx.__main__ import main

    assert main(["--data", "/nope/tree.json", "tree", "show"]) == 2
    assert "no concept tree" in capsys.readouterr().err


def test_detail_adds_siblings_and_frontier_children():
    d = tree.detail(DATA, "kid")
    assert d["siblings"] == []          # Ghost is frontier, not a sibling node
    assert tree.detail(DATA, "root")["frontierChildren"] == ["Ghost"]


# --- TUI parity (needs the `tui` extra) -------------------------------- #

def _run_tui(coro_factory, data_path):
    import asyncio

    from llmsx.tui import ConceptBrowser

    async def go():
        app = ConceptBrowser(str(data_path))
        async with app.run_test(size=(100, 40)) as pilot:
            await coro_factory(app, pilot)

    asyncio.run(go())


def test_tui_greys_frontier_and_filters_to_matching_branches(tmp_path):
    import pytest

    pytest.importorskip("textual")
    path = _tree_file(tmp_path)

    async def check(app, pilot):
        widget = app.query_one("#concept-tree")
        labels = [str(n.label) for n in widget.root.children]
        assert labels == ["Root"]
        kids = [str(n.label) for n in widget.root.children[0].children]
        assert "Kid" in kids
        assert any("Ghost" in k and "frontier" in k for k in kids)
        app.query_one("#concept-filter").value = "kid"
        await pilot.pause()
        # the parent survives because a descendant matches
        assert [str(n.label) for n in widget.root.children] == ["Root"]
        app.query_one("#concept-filter").value = "zzz"
        await pilot.pause()
        assert list(widget.root.children) == []

    _run_tui(check, path)
