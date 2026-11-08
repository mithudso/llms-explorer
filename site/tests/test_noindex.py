"""Mirrored material stays out of the search index; the site's own writing stays in.

AdSense and search both judge a site by what it indexes. The hub's docs under
/sources/, the per-file /directory/<key>/ grade cards and the raw /downloads/
copies are mirrors or near-identical templates, so they carry `noindex`."""
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
sys.path.insert(0, str(SITE / "tools"))
import twins  # noqa: E402

NOINDEX = re.compile(r'<meta name="robots" content="noindex, follow"\s*/?>')


def _html(route: str) -> str:
    return (DIST / route.strip("/") / "index.html").read_text(encoding="utf-8")


def _first(section: str) -> str:
    pages = sorted((DIST / section).rglob("index.html"))
    page = next(p for p in pages if p.parent != DIST / section)
    return "/" + page.parent.relative_to(DIST).as_posix() + "/"


def test_mirrored_pages_are_absent():
    for section in ("sources", "directory"):
        assert not (DIST / section).exists()


def _curated_and_generated():
    """One editor's pick from research-tasks.json and one generated pack that no task picks."""
    tasks = json.loads((SITE / "src" / "data" / "research-tasks.json").read_text(encoding="utf-8"))
    picked = {slug for task in tasks["tasks"] for slug in task["references"]}
    tree = json.loads((SITE / "src" / "data" / "tree.json").read_text(encoding="utf-8"))
    packs = {p.stem for p in (SITE / "src" / "data" / "concepts").glob("*.json")}
    generated = sorted(n["slug"] for n in tree["nodes"].values()
                       if n["slug"] in packs and n["slug"] not in picked and n["state"] != "domain")
    return f"/tree/{sorted(picked & packs)[0]}/", f"/tree/{generated[0]}/"


def test_the_sites_own_pages_stay_indexable():
    curated, _ = _curated_and_generated()
    for route in ("/", "/tree/", curated, "/tree/ai-llm-engineering/",
                  _first("blog"), _first("reference")):
        assert not NOINDEX.search(_html(route)), f"{route} was dropped from the index"


def test_generated_concept_pages_and_utility_pages_stay_out_of_search():
    """AdSense rejected the site as "low value content" (2026-11-07) when 94% of
    its sitemap was generated concept pages. Only topic groups and editor's picks
    are indexable; the rest stay published for readers and agents (KNOW-1220)."""
    _, generated = _curated_and_generated()
    for route in (generated, "/queue/", "/moderate/", "/proposals/", "/donate/", "/contribute/"):
        assert NOINDEX.search(_html(route)), f"{route} should carry noindex"


def test_noindex_pages_leave_the_sitemap():
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    assert "/sources/" not in sitemap
    assert re.search(r"/directory/[^<]+/</loc>", sitemap) is None
    assert "/tree/" in sitemap and "/blog/" in sitemap
    curated, generated = _curated_and_generated()
    assert curated in sitemap and generated not in sitemap
    for route in ("/queue/", "/moderate/", "/proposals/"):
        assert f"{route}</loc>" not in sitemap
    tree_urls = re.findall(r"<loc>[^<]*/tree/[^<]*</loc>", sitemap)
    assert len(tree_urls) < 100, \
        f"{len(tree_urls)} concept pages in the sitemap; curate, do not bulk-index"


def test_concept_pages_never_link_a_local_research_path():
    """19,513 facts cite a research note on the build machine (~/.global-ai-hub/...).
    Linking one publishes a private path and a 404 (KNOW-1221)."""
    for page in (DIST / "tree").glob("*/index.html"):
        html = page.read_text(encoding="utf-8")
        assert 'href="~' not in html and 'href="/Users/' not in html, page


def test_downloads_carry_the_noindex_header():
    twins.write_headers(DIST)
    edge = json.loads((DIST / twins.EDGE_HEADERS_FILE).read_text(encoding="utf-8"))
    rules = {r["pattern"]: [tuple(h) for h in r["headers"]] for r in edge["rules"]}
    assert ("X-Robots-Tag", "noindex") in rules["/downloads/*"]
