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


# --- slug parity with the generators ----------------------------------- #

def _repo_root():
    from pathlib import Path

    for base in Path(__file__).resolve().parents:
        if (base / "site" / "tools" / "gen_tree.py").is_file():
            return base
    return None


def _load_gen_tree():
    import importlib.util

    root = _repo_root()
    if root is None:
        return None
    spec = importlib.util.spec_from_file_location(
        "_gen_tree_for_slug_parity", root / "site" / "tools" / "gen_tree.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_slugify_keeps_dotted_names_split_like_the_authorities():
    # `\w` would glue "llms.txt" into "llmstxt"; the authoritative rule splits it.
    assert tree.slugify("llms.txt specification v2") == "llms-txt-specification-v2"
    assert tree.slugify("llms-full.txt page grammars") == "llms-full-txt-page-grammars"
    assert tree.slugify("llms.txt and LLM-readable documentation") == \
        "llms-txt-and-llm-readable-documentation"
    assert tree.slugify("  Trailing & leading  ") == "trailing-leading"
    assert tree.slugify("!!!") == "concept"


def test_slugify_matches_the_generator_over_the_live_tree():
    import pytest

    gen = _load_gen_tree()
    if gen is None:
        pytest.skip("not running inside the llms-explorer checkout")
    root = _repo_root()
    data_path = root / "site" / "src" / "data" / "tree.json"
    if not data_path.is_file():
        pytest.skip(f"no generated tree at {data_path}")
    data = tree.load(data_path)

    names = set()
    for node in data["nodes"].values():
        names.add(node["concept"])
        # the node's own committed slug is the contract llmsx has to reproduce
        assert tree.slugify(node["concept"]) == node["slug"], node["concept"]
        for child in node.get("children") or []:
            names.add(child["concept"])
            assert tree.slugify(child["concept"]) == child["slug"], child["concept"]
    for entry in data.get("frontier") or []:
        names.add(entry["concept"])

    assert names, "the committed tree has no concepts to check"
    disagree = [n for n in sorted(names) if tree.slugify(n) != gen.slugify(n)]
    assert disagree == []
