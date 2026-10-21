#!/usr/bin/env python3
"""llms_acquire.py — fetch a docset as the clean markdown a site already publishes.

Many docs hosts (Mintlify, Fern, Docusaurus, GitBook) serve `llms-full.txt`
(the whole docset in one file), `llms.txt` (an index) and a `.md` twin of
every page. Those keep the code blocks, tables and admonitions that
trafilatura drops. This module writes them in the web-text-mirror banner
format so every downstream tool is unchanged.

Stdlib only apart from the llms-txt library, which splits llms-full files
(imported lazily: text_mirror.py imports this module on boxes with no hub venv,
and only the split path needs the library).

Usage:
  python3 scripts/llms_acquire.py SEED_URL OUT.md [MAX_PAGES]
    -> prints {"method": "llms-full"|"llms"|null, "pages": n, "failed": n}
  from text_mirror.py: the --prefer-llms path (default on) calls acquire().
"""

from __future__ import annotations

import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = "trafilatura-text-mirror/1.0 (+public-archive)"
MIN_FULL_BYTES = 1024  # a "llms-full.txt" smaller than this is a stub or a soft-404
BANNER = "=" * 90
_LINK_RE = re.compile(r"^\s*[-*]\s*\[[^\]]*\]\((https?://[^)\s]+)\)")


def _fetch(url: str, timeout: int = 60, attempts: int = 2) -> str | None:
    """GET as text; None for HTML (a 200 HTML page is a soft-404 for these
    files), errors, or timeouts. One retry: docs CDNs rate-limit bursts, and a
    single flaky answer must not flip a docset onto the crawl path."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for n in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if "html" in r.headers.get("Content-Type", ""):
                    return None
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError, ValueError):
            if n + 1 < attempts:
                time.sleep(2)
    return None


def _roots(seed: str) -> list[str]:
    """Candidate directories, most specific first: the seed treated as a
    directory (`https://host/docs` → `/docs/`), then every ancestor up to the
    site root. Mintlify-style sites keep llms.txt under the docs subtree,
    others at the root; a 404 is cheap, guessing wrong is not."""
    p = urlparse(seed)
    origin = f"{p.scheme}://{p.netloc}"
    segs = [x for x in (p.path or "").split("/") if x]
    roots = []
    for n in range(len(segs), -1, -1):
        roots.append(origin + "/" + "/".join(segs[:n]) + ("/" if n else ""))
    return roots


def probe(seed: str, fetch=_fetch) -> dict:
    """{"llms_full": url|None, "llms": url|None} — the first root that has
    either wins, so a docs subtree's own files beat a site-wide index.

    llms-full.txt counts only when it actually holds pages (`# Title` +
    `Source:` blocks): some hosts redirect it to their llms.txt index, and
    size alone cannot tell the two apart."""
    out = {"llms_full": None, "llms": None}
    for root in _roots(seed):
        for key, name in (("llms_full", "llms-full.txt"), ("llms", "llms.txt")):
            url = urljoin(root, name)
            text = fetch(url)
            if not text:
                continue
            if key == "llms_full" and (
                len(text.encode("utf-8")) < MIN_FULL_BYTES or not split_llms_full(text)
            ):
                continue
            out[key] = url
        if out["llms_full"] or out["llms"]:
            break
    return out


def _split_lib():
    """The llms-txt splitter, imported on first use so that `import llms_acquire` (and the
    fetch/probe-free helpers) still work on a box without the library."""
    try:
        import llms_txt.split as mod
    except ImportError as exc:
        raise ImportError(
            "llms_acquire needs the llms-txt library to split llms-full files "
            "(pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt')"
        ) from exc
    return mod


def strip_index_blockquote(text: str) -> str:
    """Mintlify prepends `> ## Documentation Index …` to every .md twin and
    llms-full page and Cloudflare emits `> Documentation Index …` plus a
    `[Skip to content]` link; all navigation, not content. (llms_txt.split)"""
    return _split_lib().strip_index_blockquote(text)


def split_llms_full(text: str) -> list[dict]:
    """Split an llms-full.txt into pages across the grammars seen in the wild
    (Mintlify, YAML frontmatter / Cloudflare, Firecrawl delimiters). Implemented by
    `llms_txt.split.split_llms_full`; this wrapper keeps the historical return shape,
    a list of `{"title", "url", "text"[, "description"]}` dicts."""
    return [s.as_dict() for s in _split_lib().split_llms_full(text)]


def parse_llms_index(text: str) -> list[str]:
    urls: list[str] = []
    for line in text.splitlines():
        m = _LINK_RE.match(line)
        if m and m.group(1) not in urls:
            urls.append(m.group(1))
    return urls


def write_mirror(pages: list[dict], out_path: str, max_pages: int = 0) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for pg in pages:
            if max_pages and n >= max_pages:
                break
            body = pg.get("text") or "[no extractable text]"
            title = pg.get("title") or ""
            if title and not body.lstrip().startswith("# "):
                body = f"# {title}\n\n{body}"
            fh.write(f"\n\n{BANNER}\nURL: {pg['url']}\n{BANNER}\n\n{body}\n")
            n += 1
    return n


def _page_url(md_url: str) -> str:
    return md_url[:-3] if md_url.endswith(".md") else md_url


def acquire(seed: str, out_path: str, max_pages: int = 0, fetch=_fetch, log=print) -> dict:
    """Write the docset at `seed` to `out_path` from the site's own markdown.
    {"method": "llms-full"|"llms"|None, "pages": n, "failed": n}. A failing
    page on the index path is skipped and counted, never fatal for the site."""
    found = probe(seed, fetch)
    if found["llms_full"]:
        pages = split_llms_full(fetch(found["llms_full"]) or "")
        if pages:
            n = write_mirror(pages, out_path, max_pages)
            log(f"llms-full: {n} pages from {found['llms_full']}")
            return {"method": "llms-full", "pages": n, "failed": 0}
    if found["llms"]:
        urls = parse_llms_index(fetch(found["llms"]) or "")
        pages, failed = [], 0
        for u in urls:
            if max_pages and len(pages) >= max_pages:
                break
            text = fetch(u)
            if text is None:
                failed += 1
                log(f"llms page failed: {u}")
                continue
            pages.append({"url": _page_url(u), "title": "", "text": text})
        if pages:
            n = write_mirror(pages, out_path, max_pages)
            log(f"llms index: {n} pages, {failed} failed, from {found['llms']}")
            return {"method": "llms", "pages": n, "failed": failed}
    log("no llms.txt / llms-full.txt — falling back to crawl")
    return {"method": None, "pages": 0, "failed": 0}


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 3:
        sys.exit("usage: llms_acquire.py SEED_URL OUT.md [MAX_PAGES]")
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    print(json.dumps(acquire(sys.argv[1], sys.argv[2], cap)))
