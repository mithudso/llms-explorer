# site/tests/test_context_page.py — /context/ and /context.md list what the build serves.
#
# The page and the twin are both rendered from src/data/context.json; the
# downloads they link are written by gen_downloads.py and gen_concept_facts.py
# in `prebuild`. A row that links a file the build does not carry is exactly the
# broken promise the site's own rubric grades other sites down for.
# ruff: noqa: E501
import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
CONTEXT = SITE / "src" / "data" / "context.json"
HREF_RE = re.compile(r'href="(/downloads/[^"]+)"')
MD_LINK_RE = re.compile(r"\]\((https?://[^)]+/downloads/[^)]+)\)")


@pytest.fixture(scope="module")
def built():
    if not (DIST / "context" / "index.html").is_file():
        pytest.skip("no built /context/ — run `npm run build` first")
    return json.loads(CONTEXT.read_text(encoding="utf-8"))


def _rows(data: dict) -> list[str]:
    return [f["download"] for r in data["roots"] for f in r["files"]] + \
           [c["download"] for r in data["roots"] for c in r["concepts"]]


def test_the_page_links_every_row_and_every_row_is_built(built):
    html = (DIST / "context" / "index.html").read_text(encoding="utf-8")
    linked = set(HREF_RE.findall(html))
    rows = _rows(built)
    assert rows, "context.json lists nothing"
    missing_link = [r for r in rows if r not in linked]
    assert not missing_link, missing_link[:5]
    missing_file = [r for r in rows if not (DIST / r.lstrip("/")).is_file()]
    assert not missing_file, missing_file[:5]


def test_the_twin_is_advertised_built_and_absolute(built):
    html = (DIST / "context" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="alternate" type="text/markdown" href="/context.md"' in html
    twin = (DIST / "context.md").read_text(encoding="utf-8")
    assert twin.startswith("<!-- llms-explorer twin of ")
    urls = MD_LINK_RE.findall(twin)
    assert len(urls) == len(_rows(built)), "the twin must list every row, once"
    assert all(u.startswith("http") for u in urls), "an agent needs absolute URLs"


def test_a_facts_file_keeps_its_sources(built):
    c = next(c for r in built["roots"] for c in r["concepts"] if c["facts"] > 0)
    text = (DIST / c["download"].lstrip("/")).read_text(encoding="utf-8")
    assert text.startswith("<!-- llms-explorer concept facts · ")
    assert "tokens -->" in text.split("\n", 1)[0]
    assert f"# {c['concept']}" in text
    assert "[source](" in text or "source: `" in text


def test_the_node_page_offers_its_facts_file(built):
    c = next(c for r in built["roots"] for c in r["concepts"])
    html = (DIST / "tree" / c["slug"] / "index.html").read_text(encoding="utf-8")
    assert f'href="{c["download"]}"' in html
    assert 'rel="alternate"' not in html, "the node page stays twin-less (usage.md §2)"


def test_the_home_page_leads_with_skills_and_context():
    home = DIST / "index.html"
    if not home.is_file():
        pytest.skip("no built site")
    html = home.read_text(encoding="utf-8")
    for href in ("/skills/", "/context/", "/context.md", "/tree/", "/downloads/"):
        assert f'href="{href}"' in html, href
    assert "A research hub for agents" in html
