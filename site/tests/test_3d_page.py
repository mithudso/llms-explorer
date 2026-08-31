# site/tests/test_3d_page.py — Task 3: the 3D view
# ruff: noqa: E501
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
TREE = json.loads((SITE / "src/data/tree.json").read_text())

DATA_RE = re.compile(
    r'<script type="application/json" id="concept-tree-3d-data">(.*?)</script>', re.DOTALL
)


def _page() -> str:
    return (DIST / "tree" / "3d" / "index.html").read_text()


def test_3d_page_is_self_contained():
    html = _page()
    assert "/vendor/concept-tree-3d.bundle.js" in html
    assert "concept-tree-3d-data" in html            # the inlined DATA
    assert "http://" not in html.split("<body")[1]   # no third-party CDN in the body
    assert (DIST / "vendor" / "concept-tree-3d.bundle.js").is_file()


def test_inlined_graph_covers_the_whole_tree():
    m = DATA_RE.search(_page())
    assert m, "the page must inline its graph as application/json"
    data = json.loads(m.group(1))
    # every researched node plus every derived frontier child gets a node,
    # every edge plus every frontier attachment gets a link
    assert len(data["nodes"]) == len(TREE["nodes"]) + len(TREE["frontier"])
    assert len(data["links"]) == len(TREE["edges"]) + len(TREE["frontier"])
    ids = {n["id"] for n in data["nodes"]}
    assert len(ids) == len(data["nodes"]), "node ids must be unique"
    assert all(link["source"] in ids and link["target"] in ids for link in data["links"])
    node = data["nodes"][0]
    assert {"id", "name", "group", "color", "val"} <= set(node)


def test_page_degrades_without_javascript():
    html = _page()
    assert "<noscript" in html
    assert 'href="/tree/"' in html


def test_vendored_bundle_records_its_provenance():
    v = (SITE / "VENDOR.md").read_text()
    assert "json-3d-renderer" in v and "commit" in v.lower()
