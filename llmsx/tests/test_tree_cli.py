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

# --- load() validates shape ---------------------------------------------- #

def test_load_rejects_nodes_that_is_not_an_object(tmp_path):
    import pytest

    p = tmp_path / "tree.json"
    p.write_text(json.dumps({"nodes": ["not", "an", "object"]}))
    with pytest.raises(ValueError, match="nodes"):
        tree.load(p)


def test_load_rejects_a_non_list_roots(tmp_path):
    import pytest

    p = tmp_path / "tree.json"
    p.write_text(json.dumps({"nodes": {}, "roots": "root"}))
    with pytest.raises(ValueError, match="roots"):
        tree.load(p)


def test_load_reports_the_path_on_bad_json(tmp_path):
    import pytest

    p = tmp_path / "tree.json"
    p.write_text("{not valid json")
    with pytest.raises(ValueError, match=str(p)):
        tree.load(p)


# --- walk() is DAG-safe, not just cycle-safe ------------------------------ #

DAG = {"generated": "x", "roots": ["a", "c"], "edges": [], "frontier": [],
       "nodes": {
           "a": {"slug": "a", "concept": "A", "state": "researched",
                 "children": [{"concept": "Shared", "slug": "shared", "state": "researched"}]},
           "c": {"slug": "c", "concept": "C", "state": "researched",
                 "children": [{"concept": "Shared", "slug": "shared", "state": "researched"}]},
           "shared": {"slug": "shared", "concept": "Shared", "state": "researched",
                      "children": []},
       }}


def test_walk_emits_a_multi_parent_child_under_every_parent():
    """A node reachable from two different roots is a DAG, not a cycle — it
    must render under both, not only the first parent walk() happens to
    reach."""
    seen = [(concept, level) for concept, level, _state, slug in tree.walk(DAG) if slug == "shared"]
    assert seen == [("Shared", 1), ("Shared", 1)]


TRUE_CYCLE = {"generated": "x", "roots": ["a"], "edges": [], "frontier": [],
              "nodes": {
                  "a": {"slug": "a", "concept": "A", "state": "researched",
                        "children": [{"concept": "B", "slug": "b", "state": "researched"}]},
                  "b": {"slug": "b", "concept": "B", "state": "researched",
                        "children": [{"concept": "A", "slug": "a", "state": "researched"}]},
              }}


def test_walk_still_breaks_a_true_self_referential_cycle():
    slugs = [slug for _c, _l, _s, slug in tree.walk(TRUE_CYCLE)]
    assert slugs == ["a", "b"]      # "a" is not re-emitted under "b"


# --- defensive coercion on malformed node fields -------------------------- #

def test_search_does_not_crash_on_a_null_concept():
    data = {"nodes": {"a": {"slug": "a", "concept": None, "aliases": [None]}},
            "roots": [], "frontier": [], "edges": []}
    assert tree.search(data, "x") == []


def test_resolve_does_not_crash_on_a_null_concept():
    data = {"nodes": {"a": {"slug": "a", "concept": None}},
            "roots": [], "frontier": [], "edges": []}
    assert tree.resolve(data, "a") is not None
    assert tree.resolve(data, "nope") is None

def test_walk_is_bounded_against_pathological_diamond_fanout():
    """A `tree.json` with deep multi-level diamond fan-in — the same slug
    shared by many parents, whose own descendants are shared again — makes
    a DAG-correct walk (see test_walk_emits_a_multi_parent_child_under_every_
    parent) genuinely re-expand the shared subtree once per path to it. That
    is correct for a handful of levels but must not be allowed to grow
    without bound: this asserts the total emitted count never exceeds
    tree.MAX_WALK_NODES regardless of how deep or wide the fan-in is."""
    def make_diamond(width, depth):
        nodes = {}
        def mk(level):
            slug = f"L{level}"
            if slug in nodes:
                return slug
            children = []
            if level < depth:
                for _ in range(width):
                    child = mk(level + 1)
                    children.append({"concept": f"C{level + 1}", "slug": child,
                                     "state": "researched"})
            nodes[slug] = {"slug": slug, "concept": f"C{level}", "state": "researched",
                           "children": children}
            return slug
        roots = []
        for r in range(width):
            rslug = f"R{r}"
            child = mk(1)
            nodes[rslug] = {"slug": rslug, "concept": f"Root{r}", "state": "researched",
                            "children": [{"concept": "C1", "slug": child, "state": "researched"}]}
            roots.append(rslug)
        return {"nodes": nodes, "roots": roots, "frontier": [], "edges": []}

    data = make_diamond(width=3, depth=20)
    count = sum(1 for _ in tree.walk(data))
    assert count <= tree.MAX_WALK_NODES

def test_walk_handles_a_deep_linear_chain_without_recursion_error():
    """A long but ordinary chain (no fan-in at all) is a legitimate shape
    for a tree that has grown deep over time — it must not blow Python's
    call-stack recursion limit the way the old recursive implementation
    did well before MAX_WALK_NODES would ever engage."""
    n = 5000
    nodes = {}
    for i in range(n):
        slug = f"n{i}"
        children = ([{"concept": f"C{i + 1}", "slug": f"n{i + 1}", "state": "researched"}]
                    if i < n - 1 else [])
        nodes[slug] = {"slug": slug, "concept": f"C{i}", "state": "researched",
                       "children": children}
    data = {"nodes": nodes, "roots": ["n0"], "frontier": [], "edges": []}
    count = sum(1 for _ in tree.walk(data))
    assert count == n



# --- llmsx.tui's own tree-building must be DAG-safe too ------------------ #

def test_tui_renders_a_multi_parent_node_under_every_parent(tmp_path):
    """`llmsx.tui.ConceptBrowser`'s widget-building recursion had its own,
    independent copy of the "one shared `seen` set" bug tree.walk() was
    fixed to no longer have — it must not silently drop a node shared by
    two parents the way tree.walk() no longer does."""
    import asyncio
    import json

    import pytest

    pytest.importorskip("textual")
    from llmsx.tui import ConceptBrowser

    dag = {"generated": "x", "roots": ["a", "c"], "edges": [], "frontier": [],
           "nodes": {
               "a": {"slug": "a", "concept": "A", "state": "researched",
                     "children": [{"concept": "Shared", "slug": "shared", "state": "researched"}]},
               "c": {"slug": "c", "concept": "C", "state": "researched",
                     "children": [{"concept": "Shared", "slug": "shared", "state": "researched"}]},
               "shared": {"slug": "shared", "concept": "Shared", "state": "researched",
                          "children": []},
           }}
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(dag))

    async def go():
        app = ConceptBrowser(str(p))
        async with app.run_test(size=(100, 40)):
            widget = app.query_one("#concept-tree")
            a_kids = [str(n.label) for n in widget.root.children[0].children]
            c_kids = [str(n.label) for n in widget.root.children[1].children]
            assert any("Shared" in k for k in a_kids)
            assert any("Shared" in k for k in c_kids)

    asyncio.run(go())
