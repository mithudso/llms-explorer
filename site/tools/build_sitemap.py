#!/usr/bin/env python3
"""Generate sitemap.xml and robots.txt from the public pages in an Astro build."""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

from twins import default_site_url

NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
ACCOUNT_ROUTES = {"/login/", "/account/", "/keys/", "/usage/"}
MAX_URLS = 50_000
MAX_BYTES = 52_428_800
CONTENT_SIGNALS = "ai-train=no, search=yes, ai-input=no"


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.excluded = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in (attrs.get("rel") or "").lower().split():
            self.canonical = attrs.get("href")
        if tag == "meta":
            name = (attrs.get("name") or "").lower()
            directives = re.split(r"[\s,]+", (attrs.get("content") or "").lower())
            if name in {"robots", "googlebot"} and {"noindex", "none"}.intersection(directives):
                self.excluded = True
            if (attrs.get("http-equiv") or "").lower() == "refresh":
                self.excluded = True


def build(dist: Path, site_url: str) -> list[str]:
    site_url = site_url.rstrip("/")
    origin = urlsplit(site_url)
    if (origin.scheme not in {"http", "https"} or not origin.netloc
            or origin.query or origin.fragment):
        raise ValueError("SITE_URL must be an absolute HTTP(S) URL without a query or fragment")
    if not (dist / "index.html").is_file():
        raise ValueError("Build the Astro site before generating its sitemap: missing index.html")
    urls = set()
    for page in sorted(dist.rglob("index.html")):
        parts = page.parent.relative_to(dist).parts
        route = "/" + "/".join(parts) + ("/" if parts else "")
        if route in ACCOUNT_ROUTES:
            continue
        metadata = PageMetadata()
        metadata.feed(page.read_text(encoding="utf-8"))
        if metadata.excluded:
            continue
        url = site_url + quote(route, safe="/")
        # Aliases and cross-origin canonicals must not enter this site's sitemap.
        if metadata.canonical and urljoin(url, metadata.canonical) != url:
            continue
        if len(url) >= 2048:
            raise ValueError(f"Sitemap URL must be shorter than 2,048 characters: {page}")
        urls.add(url)
    if not urls or len(urls) > MAX_URLS:
        raise ValueError("A sitemap must contain 1–50,000 public URLs; split larger sites")
    root = ET.Element("urlset", {"xmlns": NAMESPACE})
    for url in sorted(urls):
        ET.SubElement(ET.SubElement(root, "url"), "loc").text = url
    ET.indent(root)
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    if len(xml) > MAX_BYTES:
        raise ValueError("Sitemap exceeds the 50 MB protocol limit; split it before publishing")
    (dist / "sitemap.xml").write_bytes(xml)
    (dist / "robots.txt").write_text(
        f"User-agent: *\nContent-Signal: {CONTENT_SIGNALS}\nAllow: /\n\n"
        f"Sitemap: {site_url}/sitemap.xml\n", encoding="utf-8")
    return sorted(urls)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--site-url", default=None, help="default: $SITE_URL or production URL")
    args = parser.parse_args(argv)
    site = Path(__file__).resolve().parents[1]
    urls = build(site / args.dist, args.site_url or default_site_url())
    print(f"sitemap.xml: {len(urls)} public URLs; robots.txt written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
