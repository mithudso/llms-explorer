"""Sitemap protocol, publication lifecycle, and built-page coverage."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import build_sitemap
import twins


def page(dist, route, head=""):
    target = dist / route.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"<!doctype html><html><head>{head}</head><body>Page</body></html>")
    return target


def locations(dist):
    root = ET.parse(dist / "sitemap.xml").getroot()
    assert root.tag == f"{{{build_sitemap.NAMESPACE}}}urlset"
    return [url.find(f"{{{build_sitemap.NAMESPACE}}}loc").text for url in root]


def test_public_pages_are_canonical_and_xml_is_utf8(tmp_path):
    for route in ("/", "/blog/published/", "/tree/node/", "/directory/example/", "/café & tea/"):
        page(tmp_path, route)
    page(tmp_path, "/alias/", '<link rel="canonical" href="/blog/published/">')
    page(tmp_path, "/external/", '<link rel="canonical" href="https://elsewhere.test/">')
    page(tmp_path, "/draft/", '<meta name="robots" content="follow, NOINDEX">')
    page(tmp_path, "/hidden/", '<meta name="googlebot" content="none">')
    page(tmp_path, "/old/", '<meta http-equiv="refresh" content="0;url=/">')
    for route in build_sitemap.ACCOUNT_ROUTES:
        page(tmp_path, route)
    (tmp_path / "index.md").write_text("# Markdown twin")
    (tmp_path / "404.html").write_text("Not found")
    # Scheduled content outside dist cannot become an entry before publication.
    scheduled = tmp_path / "scheduled-posts.md"
    scheduled.write_text("# Future post")
    build_sitemap.build(tmp_path, "https://preview.example.test/")
    assert locations(tmp_path) == sorted([
        "https://preview.example.test/",
        "https://preview.example.test/blog/published/",
        "https://preview.example.test/tree/node/",
        "https://preview.example.test/directory/example/",
        "https://preview.example.test/caf%C3%A9%20%26%20tea/",
    ])
    xml = (tmp_path / "sitemap.xml").read_bytes()
    assert xml.startswith(b"<?xml version='1.0' encoding='utf-8'?>")
    assert (tmp_path / "robots.txt").read_text() == (
        "User-agent: *\nContent-Signal: ai-train=no, search=yes, ai-input=no\nAllow: /\n\n"
        "Sitemap: https://preview.example.test/sitemap.xml\n")


def test_rebuild_tracks_publication_and_removal(tmp_path):
    page(tmp_path, "/")
    build_sitemap.build(tmp_path, "https://example.test")
    published = page(tmp_path, "/blog/new/")
    build_sitemap.build(tmp_path, "https://example.test")
    assert "https://example.test/blog/new/" in locations(tmp_path)
    published.unlink()
    build_sitemap.build(tmp_path, "https://example.test")
    assert locations(tmp_path) == ["https://example.test/"]
    previous = (tmp_path / "sitemap.xml").read_bytes()
    build_sitemap.build(tmp_path, "https://example.test")
    assert (tmp_path / "sitemap.xml").read_bytes() == previous


def test_environment_controls_canonical_origin_and_robots(tmp_path, monkeypatch):
    page(tmp_path, "/", '<link rel="canonical" href="https://configured.test/">')
    monkeypatch.setenv("SITE_URL", "https://configured.test/")
    assert build_sitemap.main(["--dist", str(tmp_path)]) == 0
    assert locations(tmp_path) == ["https://configured.test/"]
    assert "Sitemap: https://configured.test/sitemap.xml" in (tmp_path / "robots.txt").read_text()


@pytest.mark.parametrize("origin", ["example.test", "ftp://example.test", "https://x.test/?x=1"])
def test_invalid_origin_fails(tmp_path, origin):
    page(tmp_path, "/")
    with pytest.raises(ValueError, match="absolute HTTP"):
        build_sitemap.build(tmp_path, origin)


def test_missing_build_and_protocol_limits_fail(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="missing index.html"):
        build_sitemap.build(tmp_path, "https://example.test")
    page(tmp_path, "/")
    page(tmp_path, "/blog/post/")
    monkeypatch.setattr(build_sitemap, "MAX_URLS", 1)
    with pytest.raises(ValueError, match="50,000"):
        build_sitemap.build(tmp_path, "https://example.test")
    monkeypatch.setattr(build_sitemap, "MAX_URLS", 50_000)
    monkeypatch.setattr(build_sitemap, "MAX_BYTES", 1)
    with pytest.raises(ValueError, match="50 MB"):
        build_sitemap.build(tmp_path, "https://example.test")


def test_pages_headers_declare_xml_and_plain_text(tmp_path):
    twins.write_headers(tmp_path)
    headers = (tmp_path / "_headers").read_text()
    assert "/sitemap.xml\n  Content-Type: application/xml; charset=utf-8\n" in headers
    assert "/robots.txt\n  Content-Type: text/plain; charset=utf-8\n" in headers


def test_built_sitemap_covers_all_public_page_canonicals():
    dist = SITE / "dist"
    expected = []
    for target in dist.rglob("index.html"):
        parts = target.parent.relative_to(dist).parts
        route = "/" + "/".join(parts) + ("/" if parts else "")
        metadata = build_sitemap.PageMetadata()
        metadata.feed(target.read_text(encoding="utf-8"))
        assert metadata.canonical, f"{route} has no canonical link"
        assert metadata.canonical.endswith(quote(route, safe="/"))
        if route not in build_sitemap.ACCOUNT_ROUTES and not metadata.excluded:
            expected.append(metadata.canonical)
    assert expected, "run npm run build before testing the site"
    assert locations(dist) == sorted(expected)
    assert len(expected) == len(set(expected)), "duplicate page canonicals"
