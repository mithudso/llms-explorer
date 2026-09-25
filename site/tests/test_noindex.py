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


def test_mirrored_pages_are_noindex():
    for section in ("sources", "directory"):
        route = _first(section)
        assert NOINDEX.search(_html(route)), f"{route} is indexable"


def test_the_sites_own_pages_stay_indexable():
    for route in ("/", "/directory/", _first("tree"), _first("blog"), _first("reference")):
        assert not NOINDEX.search(_html(route)), f"{route} was dropped from the index"


def test_noindex_pages_leave_the_sitemap():
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    assert "/sources/" not in sitemap
    assert re.search(r"/directory/[^<]+/</loc>", sitemap) is None
    assert "/tree/" in sitemap and "/blog/" in sitemap


def test_downloads_carry_the_noindex_header():
    twins.write_headers(DIST)
    edge = json.loads((DIST / twins.EDGE_HEADERS_FILE).read_text(encoding="utf-8"))
    rules = {r["pattern"]: [tuple(h) for h in r["headers"]] for r in edge["rules"]}
    assert ("X-Robots-Tag", "noindex") in rules["/downloads/*"]
