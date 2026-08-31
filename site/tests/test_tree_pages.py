# site/tests/test_tree_pages.py
# ruff: noqa: E501
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
TREE = json.loads((SITE / "src/data/tree.json").read_text())
TREE_DATA_RE = re.compile(
    r'<script type="application/json" id="tree-data">(.*?)</script>', re.DOTALL)

sys.path.insert(0, str(SITE / "tools"))
import gen_tree  # noqa: E402

# A tree the committed one does not contain: one frontier child, and a concept name
# carrying `</script>`, so the frontier rendering path and the escaping of the inlined
# payload are both exercised by a real build rather than surveyed on live data.
FIXTURE = [
    {"concept": "Root", "parentConcept": None, "slug": "root", "aliases": [],
     "childConcepts": ["Kid", "Ghost </script><script>alert(1)</script>"],
     "researchedAt": "2026-08-01", "sourcesCount": 3, "conceptsCount": 9},
    {"concept": "Kid", "parentConcept": "Root", "slug": "kid", "aliases": [],
     "childConcepts": [], "researchedAt": "2026-08-02", "sourcesCount": 1, "conceptsCount": 2},
]
GHOST = FIXTURE[0]["childConcepts"][1]


@pytest.fixture(scope="module")
def fixture_dist(tmp_path_factory) -> Path:
    """Build the real pages against a fixture tree, in a throwaway root.

    The site's own `src/data/tree.json` is never touched: src/ is copied, node_modules
    symlinked, and only the copy's tree.json is replaced — so this can run beside
    another build without either seeing the other's data.
    """
    if shutil.which("npx") is None or not (SITE / "node_modules" / "astro").is_dir():
        pytest.skip("needs node + `npm ci` in site/ to build a fixture tree")
    root = tmp_path_factory.mktemp("fixroot")
    for item in ("src", "public", "astro.config.mjs", "tsconfig.json", "package.json"):
        src = SITE / item
        if not src.exists():
            continue
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, root / item)
    os.symlink(SITE / "node_modules", root / "node_modules")
    repo = root / "fixture-repo"
    (repo / "concept-tree").mkdir(parents=True)
    (repo / "concept-tree" / "tree.json").write_text(json.dumps(FIXTURE))
    (root / "src" / "data" / "tree.json").write_text(json.dumps(gen_tree.build(repo)))
    out = root / "dist"
    r = subprocess.run(["npx", "astro", "build", "--outDir", str(out)],
                       cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


def test_a_page_exists_for_every_node():
    missing = [s for s in TREE["nodes"] if not (DIST / "tree" / s / "index.html").is_file()]
    assert not missing, missing[:5]
    assert (DIST / "tree" / "index.html").is_file()


def test_every_node_page_is_the_node_it_claims():
    """A static route resolves before the dynamic one, so `/tree/3d/` would answer for a
    concept slugging to `3d` and the file-exists check above would still pass. Assert the
    page carries its own concept, so a shadowed route fails instead."""
    wrong = []
    for slug, node in TREE["nodes"].items():
        html = (DIST / "tree" / slug / "index.html").read_text()
        if f"<h1>{node['concept']}</h1>" not in html:
            wrong.append(slug)
    assert not wrong, wrong[:5]


def test_reserved_and_duplicate_slugs_fail_the_build(tmp_path):
    """The guard in [slug].astro's getStaticPaths, read as source: a concept slugging to
    a static route (`3d`) or colliding with another must stop the build, not vanish."""
    src = (SITE / "src/pages/tree/[slug].astro").read_text()
    assert '"3d"' in src and "throw new Error" in src
    assert "slug alike" in src, "duplicate slugs must be rejected too"
    # and the collision the guard exists for is real: `/tree/3d/` is a built static page
    assert (DIST / "tree" / "3d" / "index.html").is_file()
    assert "3d" not in TREE["nodes"], "a node already occupies the reserved slug"


def test_node_page_shows_state_and_links_its_parent():
    kid = next(n for n in TREE["nodes"].values() if n["parent_slug"])
    html = (DIST / "tree" / kid["slug"] / "index.html").read_text()
    assert kid["concept"] in html
    assert f'/tree/{kid["parent_slug"]}/' in html
    assert str(kid["sourcesCount"]) in html


def test_frontier_children_are_marked_and_not_linked(fixture_dist):
    """The rendering path, exercised end to end: the fixture tree has one frontier child,
    so the `<span class="frontier">` branch of [slug].astro is really built."""
    html = (fixture_dist / "tree" / "root" / "index.html").read_text()
    assert '<span class="frontier"' in html
    assert 'href="/tree/ghost' not in html, "a frontier child has no page to link"
    assert 'href="/tree/kid/"' in html, "a researched child still links"
    assert "Frontier under this node" in html
    index = (fixture_dist / "tree" / "index.html").read_text()
    assert '<li class="frontier"' in index
    assert "1 frontier" in index


def test_the_live_tree_frontier_is_rendered_too():
    """The same check against the committed tree. Reported as a skip rather than a silent
    pass when the tree happens to be fully researched."""
    node = next((n for n in TREE["nodes"].values()
                 if any(c["state"] == "frontier" for c in n["children"])), None)
    if node is None:
        pytest.skip("the committed tree currently has no frontier child")
    html = (DIST / "tree" / node["slug"] / "index.html").read_text()
    ghost = next(c for c in node["children"] if c["state"] == "frontier")
    assert ghost["concept"] in html
    assert f'href="/tree/{ghost["slug"]}/"' not in html
    assert "frontier" in html.lower()


def test_tree_index_carries_the_data_for_the_island():
    html = (DIST / "tree" / "index.html").read_text()
    assert "tree-data" in html and TREE["roots"][0] in html


def test_inlined_tree_data_cannot_close_its_own_script(fixture_dist):
    """Concept names are text a person or a research run wrote: `</script>` in one must
    not terminate the block. Same escape as Tree3D and DirectoryTable."""
    html = (fixture_dist / "tree" / "index.html").read_text()
    m = TREE_DATA_RE.search(html)
    assert m, "the tree island must inline its data as application/json"
    assert "</script>" not in m.group(1)
    assert "\\u003c/script>" in m.group(1)
    assert json.loads(m.group(1))["nodes"]["root"]["children"][1]["concept"] == GHOST


def test_the_frontier_definition_the_site_publishes_matches_what_it_computes():
    """/tree/ counts frontier from `childConcepts` only. The hub also treats unchecked
    research-queue rows as frontier, and the snapshot does not carry that queue — so the
    page and the reference must name the narrower rule rather than claim the hub's."""
    page = (SITE / "src/pages/tree/index.astro").read_text()
    assert "childConcepts" in page and "research queue" in page.lower()
    ref = (SITE / "src/content/reference/concept-tree.md").read_text()
    assert "RESEARCH_QUEUE.md" in ref and "research-queue" in ref
    assert 'no way to mark a concept "frontier" by hand' not in ref
    assert not (SITE.parent / "concept-tree" / "RESEARCH_QUEUE.md").exists(), \
        "the snapshot now carries the queue — gen_tree must read it before the page may count it"


def test_tree_section_advertises_its_published_twin():
    html = (DIST / "tree" / "index.html").read_text()
    assert '<link rel="alternate" type="text/markdown" href="/tree.md"' in html
    assert (DIST / "tree.md").is_file()
    # the per-node pages have no twin, and must not advertise one
    slug = next(iter(TREE["nodes"]))
    assert 'rel="alternate"' not in (DIST / "tree" / slug / "index.html").read_text()


def test_the_home_page_links_the_tree():
    home = (DIST / "index.html").read_text()
    assert 'href="/tree/"' in home, "/tree/ must be one hop from the home page"
