#!/usr/bin/env python3
"""twins — .md twins for every built page + the Cloudflare _headers file.
Usage: twins.py [--content src/content] [--dist dist] [--site-url URL]"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
from pathlib import Path

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
DEFAULT_SITE_URL = "https://llms-explorer.pages.dev"
# Cloudflare Pages: "A _headers file can have a maximum of 100 header rules."
MAX_HEADER_RULES = 100
CHARS_PER_TOKEN = 4                       # the estimator the family declares
_SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)


def default_site_url() -> str:
    """CI and Cloudflare Pages both set SITE_URL (astro.config.mjs reads it too);
    a custom domain must not leave the twins pointing at pages.dev."""
    return os.environ.get("SITE_URL", "").strip().rstrip("/") or DEFAULT_SITE_URL


def _title(fm: str) -> str:
    m = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else "Untitled"


def _description(fm: str) -> str:
    m = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else ""


def _slug(segment: str) -> str:
    """Astro's content slug per path segment (github-slugger): lowercase, drop
    punctuation, spaces to dashes."""
    return _SLUG_STRIP_RE.sub("", segment.strip().lower()).replace(" ", "-")


def route_of(rel: Path) -> str:
    """The route Astro builds for `src/content/<rel>` — segments slugified and a
    trailing `/index` dropped, so `blog/foo/index.md` is `/blog/foo/`, not
    `/blog/foo/index/`."""
    segs = [_slug(s) for s in rel.with_suffix("").parts]
    if segs and segs[-1] == "index":
        segs.pop()
    return "/" + "".join(f"{s}/" for s in segs)


def write_twins(content_dir: Path, dist_dir: Path, site_url: str) -> list[Path]:
    out = []
    stamp = datetime.datetime.now(datetime.UTC).date().isoformat()
    for src in sorted(content_dir.rglob("*.md")):
        rel = src.relative_to(content_dir)                      # essays/a.md
        route = route_of(rel)
        text = src.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        fm, body = (m.group(1), text[m.end():]) if m else ("", text)
        # the twin lives at the route with `.md` appended, which is what
        # Base.astro links and what the mirror maps back to a URL
        twin = dist_dir / (route.strip("/") + ".md" if route != "/" else "index.md")
        twin.parent.mkdir(parents=True, exist_ok=True)
        # the authored `description:` leads the body: the mirror keeps it, so the
        # index entry for this page is the description its author wrote rather
        # than whatever sentence happens to open the prose
        lede = f"{_description(fm)}\n\n" if _description(fm) else ""
        twin.write_text(f"<!-- llms-explorer twin of {site_url}{route} · generated {stamp} -->\n\n"
                        f"# {_title(fm)}\n\n{lede}{body.lstrip()}", encoding="utf-8")
        out.append(twin)
    return out


def _tokens(path: Path, manifest: dict) -> int:
    """The published token count. For a family file the manifest is the source of
    truth (one number per file, H8); anything else is the declared estimator."""
    entry = manifest.get("files", {}).get(path.name)
    if isinstance(entry, dict) and isinstance(entry.get("tokens"), int):
        return entry["tokens"]
    return len(path.read_text(encoding="utf-8")) // CHARS_PER_TOKEN


def write_headers(dist_dir: Path) -> Path:
    man = dist_dir / "manifest.json"
    manifest: dict = {}
    if man.exists():
        try:
            manifest = json.loads(man.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    md = "  Content-Type: text/markdown; charset=utf-8"
    describedby = '  Link: </llms.txt>; rel="describedby"'
    lines = ["/*.md", md, describedby, "/llms*.txt", md, describedby]
    rules = 2
    for f in sorted(dist_dir.rglob("*.md")):
        lines += [f"/{f.relative_to(dist_dir).as_posix()}",
                  f"  X-Markdown-Tokens: {_tokens(f, manifest)}"]
        rules += 1
    for f in sorted(dist_dir.glob("llms*.txt")):
        lines += [f"/{f.name}", f"  X-Markdown-Tokens: {_tokens(f, manifest)}"]
        rules += 1
    if rules > MAX_HEADER_RULES:
        raise ValueError(
            f"_headers would carry {rules} rules; Cloudflare Pages allows "
            f"{MAX_HEADER_RULES}. Serve X-Markdown-Tokens from a Pages Function "
            "or drop the per-file rules before adding more pages.")
    dest = dist_dir / "_headers"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--content", default="src/content")
    p.add_argument("--dist", default="dist")
    p.add_argument("--site-url", default=None, help="default: $SITE_URL, else " + DEFAULT_SITE_URL)
    a = p.parse_args(argv)
    here = Path(__file__).resolve().parents[1]
    site_url = (a.site_url or default_site_url()).rstrip("/")
    n = len(write_twins(here / a.content, here / a.dist, site_url))
    write_headers(here / a.dist)
    print(f"{n} twins, _headers written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
