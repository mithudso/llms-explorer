# site/tests/test_tree_pages.py
# ruff: noqa: E501
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
TREE = json.loads((SITE / "src/data/tree.json").read_text())


def test_a_page_exists_for_every_node():
    missing = [s for s in TREE["nodes"] if not (DIST / "tree" / s / "index.html").is_file()]
    assert not missing, missing[:5]
    assert (DIST / "tree" / "index.html").is_file()


def test_node_page_shows_state_and_links_its_parent():
    kid = next(n for n in TREE["nodes"].values() if n["parent_slug"])
    html = (DIST / "tree" / kid["slug"] / "index.html").read_text()
    assert kid["concept"] in html
    assert f'/tree/{kid["parent_slug"]}/' in html
    assert str(kid["sourcesCount"]) in html


def test_frontier_children_are_marked_and_not_linked():
    node = next((n for n in TREE["nodes"].values()
                 if any(c["state"] == "frontier" for c in n["children"])), None)
    if node is None:
        return  # a fully-researched tree is a valid state
    html = (DIST / "tree" / node["slug"] / "index.html").read_text()
    ghost = next(c for c in node["children"] if c["state"] == "frontier")
    assert ghost["concept"] in html
    assert f'href="/tree/{ghost["slug"]}/"' not in html
    assert "frontier" in html.lower()


def test_tree_index_carries_the_data_for_the_island():
    html = (DIST / "tree" / "index.html").read_text()
    assert "tree-data" in html and TREE["roots"][0] in html
