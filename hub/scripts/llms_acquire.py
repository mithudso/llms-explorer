#!/usr/bin/env python3
"""llms_acquire.py — fetch a docset as the clean markdown a site already publishes.

Many docs hosts (Mintlify, Fern, Docusaurus, GitBook) serve `llms-full.txt`
(the whole docset in one file), `llms.txt` (an index) and a `.md` twin of
every page. Those keep the code blocks, tables and admonitions that
trafilatura drops. This module writes them in the web-text-mirror banner
format so every downstream tool is unchanged.

Stdlib only: text_mirror.py imports it, and that script runs on boxes that
have no hub venv.

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
_SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$")
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


_YAML_KEY_RE = re.compile(r"^(title|url|source|description):\s*(.*?)\s*$")
_VIEW_MD_RE = re.compile(r"\[View as Markdown\]\((https?://[^)\s]+)\)")
_FIRECRAWL_DELIM_RE = re.compile(r"^<\|firecrawl-page-(\d+)-lllmstxt\|>\s*$")
_DOC_INDEX_BLOCKQUOTE_RE = re.compile(
    r"^> (?:## )?Documentation Index[^\n]*\n(?:>[^\n]*\n?)*\n*", re.M
)
_SKIP_LINK_RE = re.compile(r"^\[Skip to content\]\([^)]*\)\s*\n*", re.M)


def strip_index_blockquote(text: str) -> str:
    """Mintlify prepends `> ## Documentation Index …` to every .md twin and
    llms-full page and Cloudflare emits `> Documentation Index …` plus a
    `[Skip to content]` link; all navigation, not content."""
    text = _SKIP_LINK_RE.sub("", text)
    return _DOC_INDEX_BLOCKQUOTE_RE.sub("", text, count=1).lstrip("\n")


def _yaml_block(lines: list[str], i: int) -> tuple[dict, int] | None:
    """A `---` … `---` block starting at lines[i] → (fields, index after)."""
    if lines[i].strip() != "---":
        return None
    fields: dict = {}
    j = i + 1
    while j < len(lines) and lines[j].strip() != "---":
        m = _YAML_KEY_RE.match(lines[j])
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("\"'")
        j += 1
    if j >= len(lines):
        return None
    return fields, j + 1


def split_llms_full(text: str) -> list[dict]:
    """Split an llms-full.txt into pages across the grammars seen in the wild.

    (a) Mintlify: `# Title` whose next non-blank line is `Source: <url>`.
    (b) YAML block: `---` … `title:` / `url:` … `---` (Anthropic platform docs,
        Cloudflare frontmatter — Cloudflare's URL is only in a later
        `[View as Markdown](…/index.md)` line, so it is picked up from the body).
    (c) Firecrawl delimiters `<|firecrawl-page-N-lllmstxt|>` (no URL; a
        synthetic `page-N` url keeps the page addressable).
    Lines inside fenced code never start a page; a page ABOUT this format
    cannot split itself. A bare `# ` line never starts a page on its own —
    pages contain H1s of their own."""
    lines = text.splitlines()
    pages: list[dict] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            if line.startswith("# "):  # (a)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                m = _SOURCE_RE.match(lines[j]) if j < len(lines) else None
                if m:
                    pages.append({"title": line[2:].strip(), "url": m.group(1), "lines": []})
                    i = j + 1
                    continue
            yb = _yaml_block(lines, i)  # (b)
            if yb and ("url" in yb[0] or "source" in yb[0] or "title" in yb[0]):
                fields, nxt = yb
                pages.append(
                    {
                        "title": fields.get("title", ""),
                        "url": fields.get("url") or fields.get("source") or "",
                        "description": fields.get("description", ""),
                        "lines": [],
                    }
                )
                i = nxt
                continue
            fm = _FIRECRAWL_DELIM_RE.match(line)  # (c)
            if fm:
                pages.append({"title": "", "url": f"page-{fm.group(1)}", "lines": []})
                i += 1
                continue
            if pages and not pages[-1]["url"]:
                vm = _VIEW_MD_RE.search(line)
                if vm:
                    pages[-1]["url"] = (
                        vm.group(1).rsplit("/index.md", 1)[0] + "/"
                        if vm.group(1).endswith("/index.md")
                        else vm.group(1)[:-3]
                        if vm.group(1).endswith(".md")
                        else vm.group(1)
                    )
        if pages:
            pages[-1]["lines"].append(line)
        i += 1
    out = []
    for p in pages:
        body = strip_index_blockquote("\n".join(p.pop("lines")).strip("\n"))
        if not p["title"]:
            hm = re.search(r"^# (.+)$", body, re.M)
            p["title"] = hm.group(1).strip() if hm else p["url"]
        if not p["url"]:
            continue  # a block we cannot address is useless to a consumer
        p["text"] = body
        out.append(p)
    return out


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
