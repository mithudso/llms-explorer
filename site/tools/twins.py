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
DEFAULT_SITE_URL = "https://llms-explorer.com"
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


# Routes that are Astro pages rather than content entries: the data sections
# (tree, directory, demo) render from src/data/*.json, so there is no markdown
# to walk — but the site's own llms.txt has to list them or its index hides its
# largest sections. The twin publishes what the ROUTE holds — its own lede, the
# date of the data it renders, a link to the page that explains it, and a
# generated inventory. It must never republish the explainer's body: that prose
# has one canonical URL, and copying it here put every line in llms-full.txt
# twice under two `Source:` URLs.
#
# `title` is the page's own <title> (`const title` in the .astro file) — the
# index name and the page name have to be the same string, and
# test_twins.py::test_section_titles_match_the_astro_pages holds them together.
PAGE_SECTIONS = [
    {"route": "/tree/", "title": "The concept tree",
     "page": "src/pages/tree/index.astro",
     "description": "Every researched concept in the hub's tree, one page each, "
                    "with its parent, its children and the frontier names below it.",
     "explains": "reference/concept-tree.md", "data": "tree.json", "dated": "generated",
     "index": lambda d: [(n["concept"], f"/tree/{n['slug']}/") for n in
                         sorted(d["nodes"].values(), key=lambda n: n["concept"])]},
    {"route": "/directory/", "title": "The directory of known llms files",
     "page": "src/pages/directory/index.astro",
     "description": "Every mirrored llms-full.txt that splits into pages, scored "
                    "against the attribute rubric by llms_lint and graded A–F.",
     "explains": "reference/directory.md", "data": "directory.json", "dated": "scored",
     "index": lambda d: [(f"{s['name'] or s['key']} — grade {s['grade']}, {s['pages']} pages",
                          f"/directory/{s['key']}/") for s in d["sites"]]},
    {"route": "/demo/", "title": "Semantic indexing, recorded",
     "page": "src/pages/demo.astro",
     "description": "One question set run three ways against one indexed docset — keyword "
                    "(BM25), vector, and the fusion of both — hits and timings as recorded.",
     "explains": "essays/semantic-indexing.md", "data": "demo.json", "dated": "recorded",
     "index": lambda d: [(q["q"], "/demo/") for q in d["questions"]]},
]


def _section_twin(spec: dict, content_dir: Path, data_dir: Path, dist_dir: Path,
                  site_url: str, stamp: str) -> Path | None:
    """A twin for a route whose page is generated, not authored.

    Carries only what is unique to the section: the route's own lede, the date
    of the data it renders (in the body, so it survives comment stripping), a
    link to the explainer, and the inventory. The explainer's prose stays at its
    own URL — see PAGE_SECTIONS.
    """
    prose = content_dir / spec["explains"]
    data_file = data_dir / spec["data"]
    if not prose.is_file() or not data_file.is_file():
        return None
    m = FM_RE.match(prose.read_text(encoding="utf-8"))
    explains_title = _title(m.group(1)) if m else spec["explains"]
    explains_url = f"{site_url}{route_of(Path(spec['explains']))}"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    recorded = str(data.get("generated") or "").strip()
    rows = spec["index"](data)
    listing = "\n".join(f"- [{name}]({site_url}{href})" for name, href in rows)
    dated = (f"Data {spec['dated']} {recorded}; twin built {stamp}." if recorded
             else f"Data undated; twin built {stamp}.")
    twin = dist_dir / (spec["route"].strip("/") + ".md")
    twin.parent.mkdir(parents=True, exist_ok=True)
    twin.write_text(
        f"<!-- llms-explorer twin of {site_url}{spec['route']} · data {spec['dated']} "
        f"{recorded or 'undated'} · twin built {stamp} -->\n\n"
        f"# {spec['title']}\n\n{spec['description']}\n\n{dated}\n\n"
        f"What this section is and how it is built: "
        f"[{explains_title}]({explains_url}).\n\n"
        f"## What this section holds ({len(rows)})\n\n{listing}\n", encoding="utf-8")
    return twin


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
    data_dir = content_dir.parent / "data"
    for spec in PAGE_SECTIONS:
        twin = _section_twin(spec, content_dir, data_dir, dist_dir, site_url, stamp)
        if twin is not None:
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
    # `/llms*.txt` is a path PREFIX, so it misses `/blog/llms.txt`: the section
    # indexes the root index sends readers to need a rule of their own, or they
    # are served without the content type and the describedby link this site's
    # own recipe-09 tells readers to follow.
    lines = ["/*.md", md, describedby, "/llms*.txt", md, describedby,
             "/*/llms.txt", md, describedby]
    rules = 3
    for f in sorted(dist_dir.rglob("*.md")):
        lines += [f"/{f.relative_to(dist_dir).as_posix()}",
                  f"  X-Markdown-Tokens: {_tokens(f, manifest)}"]
        rules += 1
    for f in sorted(dist_dir.rglob("llms*.txt")):     # rglob: the spokes too
        lines += [f"/{f.relative_to(dist_dir).as_posix()}",
                  f"  X-Markdown-Tokens: {_tokens(f, manifest)}"]
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
