#!/usr/bin/env python3
"""twins — .md twins for every built page + the Cloudflare _headers file.
Usage: twins.py [--content src/content] [--dist dist] [--site-url URL]"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import os
import re
from pathlib import Path

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
DEFAULT_SITE_URL = "https://llms-explorer.com"
# The API the account islands call. Same default as AccountNav.astro, same
# build-time env var: `connect-src` has to name whatever origin the pages were
# built to talk to, or every signed-in fetch is blocked by our own policy.
DEFAULT_API_URL = "https://api.llms-explorer.com"
# Cloudflare Pages: "A _headers file can have a maximum of 100 header rules."
MAX_HEADER_RULES = 100
CHARS_PER_TOKEN = 4                       # the estimator the family declares
_SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)


def default_api_url() -> str:
    """The account islands' API origin (AccountNav.astro reads the same var)."""
    return os.environ.get("PUBLIC_API_URL", "").strip().rstrip("/") or DEFAULT_API_URL


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
     "explains": "blog/semantic-indexing.md", "data": "demo.json", "dated": "recorded",
     "index": lambda d: [(q["q"], "/demo/") for q in d["questions"]]},
]


# Routes whose Astro page has nothing behind it at build time: the account
# surface. Its four pages are islands — the markup ships an empty mount and a
# signed-out fallback, and every byte of user data arrives later from the API —
# so there is no page body to mirror. Without a twin they would be the only
# built pages this site's own llms.txt does not list, and an agent reading the
# index would not learn that the account surface exists or what it is for. The
# twin therefore publishes what the ROUTE is for, never a rendering of it.
#
# `title` and `description` are the page's own `const title` / `const
# description`; test_account_pages.py holds the two together so the index cannot
# describe a page under a name the page does not use.
STATIC_PAGES = [
    {"route": "/downloads/", "title": "Downloads",
     "page": "src/pages/downloads.astro",
     "description": "Everything installable: the agent skills via npx, the llmsx Python "
                    "library and CLI, the llmsx-skills npm package, and the terminal "
                    "browser that ships inside llmsx today.",
     "body": "Four installable surfaces, described as they are today rather than at GA: the "
             "agent skills, which are prompts and need no runtime; `llmsx`, a Python library "
             "and CLI; `llmsx-skills`, the same reading surface for JavaScript; and the "
             "terminal browser over the concept tree.\n\n"
             "## What is on it\n\n"
             "The `npx skills add` lines for the skills, install-from-source commands for "
             "both packages — neither is on a registry yet, so no `pip install llmsx` or "
             "`npm install llmsx-skills` is advertised — and a note that the TUI ships "
             "inside `llmsx` as `llmsx tui`, with the standalone build still designed and "
             "not implemented.\n"},
    {"route": "/family/", "title": "This site's llms family",
     "page": "src/pages/family.astro",
     "description": "The five files an agent reads, what each one is for, and the index "
                    "rendered as clickable links rather than the raw text/markdown a "
                    "browser cannot follow.",
     "body": "The family is served as `text/markdown`, which is right for the agents it is "
             "written for and unreadable in a browser: the links inside arrive as text. This "
             "route is the reader for it, and it renders the file it links rather than a "
             "second copy of the index — there is only one llms.txt, and it is the one the "
             "lint gates.\n\n"
             "## What is on it\n\n"
             "A table of the five members and what each is for, the index fetched and "
             "rendered with its links clickable, and a note on the `.md` twin every content "
             "page publishes beside itself.\n"},
    {"route": "/login/", "title": "Sign in", "page": "src/pages/login.astro",
     "description": "Sign in with a passkey, GitHub or Google; the API sets an HttpOnly "
                    "session cookie that the account, keys and usage pages send back on "
                    "every call.",
     "body": "The ceremony belongs to the API: passkey registration and assertion, and "
             "the two OAuth redirects. Signed out, the route is four buttons and a "
             "paragraph.\n\n"
             "## Why an account exists\n\n"
             "Only the metered surfaces need one — your own docsets, the hosted MCP "
             "endpoint, and private forks of the concept tree. Every published page, "
             "including the whole llms family, stays readable and unmetered without it.\n"},
    {"route": "/account/", "title": "Your account", "page": "src/pages/account.astro",
     "description": "Who you are signed in as, which plan you are on, and the sign-in "
                    "methods and private tree forks attached to the account — all fetched "
                    "in the browser.",
     "body": "The address, the plan and the attached sign-in methods are one visitor's, so "
             "they are requested from the API after the page loads rather than built into "
             "it.\n\n"
             "## What the account holds\n\n"
             "Three things the public site has no place for: the plan and its quotas, the "
             "API keys that authenticate the hosted MCP endpoint, and the private tree "
             "forks whose changes are proposed back rather than published. Deleting the "
             "account revokes every key with it.\n"},
    {"route": "/keys/", "title": "API keys", "page": "src/pages/keys.astro",
     "description": "Create, list and revoke the scoped keys that authenticate the hosted "
                    "MCP endpoint; the plaintext is shown once, at creation, and stored "
                    "only as a hash.",
     "body": "A key carries scopes — read for the hub\u2019s read tools, run for jobs that "
             "spend credits, publish for your own artifacts. A key with only the scopes it "
             "needs is the difference between a leaked token that reads and one that "
             "spends.\n\n"
             "## Shown once, stored hashed\n\n"
             "What the API keeps is a non-secret lookup prefix and an Argon2id hash of the "
             "rest, so a key can be listed and revoked forever but never displayed twice. "
             "Losing one means issuing another and revoking the old, not recovering it.\n"},
    {"route": "/usage/", "title": "Usage and credits", "page": "src/pages/usage.astro",
     "description": "The metered work on your account this period — jobs, tokens and "
                    "embeddings, each row priced from the append-only ledger — and the "
                    "credit balance left against your quota.",
     "body": "Totals and rows come from the API already priced; the page performs no "
             "arithmetic of its own, so a number on screen is a number in the ledger.\n\n"
             "## What metering counts\n\n"
             "Model tokens on the refine and vocabulary passes, embedding calls on "
             "indexing, and the wall time of a job holding a worker. Querying an "
             "already-built index is not metered. A correction is a new ledger row, never "
             "an edited one.\n"},
    {"route": "/billing/", "title": "Pricing", "page": "src/pages/billing.astro",
     "description": "Reference, blog, the public tree and every served llms file stay "
                    "free; a plan pays for lint model passes, semantic search, indexing "
                    "a docset, and publishing to the catalogue.",
     "body": "The three plans and the price on each come straight from "
             "`api/explorer_api/plans.py` (`src/data/plans.json`, `tools/gen_plans.py`) — "
             "this page never hand-transcribes a number the API itself might change.\n\n"
             "## What is on it\n\n"
             "Free, Starter ($9/mo) and Pro ($39/mo), each with a sign-in link; a "
             "feature-by-feature table below covering everything a request can spend — "
             "lint model passes, keyword and semantic queries, indexing, storage, corpus "
             "synthesis, private trees, publishing, and overage — reading every row "
             "straight from the same plan table the API enforces.\n"},
]


def _static_twin(spec: dict, dist_dir: Path, site_url: str, stamp: str) -> Path | None:
    """A twin for an account route: what the route is for, not a rendering of it.

    These pages are islands, so a mirror of their built markup would carry only
    the signed-out fallback — which is why the prose lives here, beside the
    route, rather than being scraped out of HTML that deliberately holds nothing.

    Written only when the page is in this build: a twin for a route that was not
    built is a `.md` the family would index and the site would 404.
    """
    if not (dist_dir / spec["route"].strip("/") / "index.html").is_file():
        return None
    twin = dist_dir / (spec["route"].strip("/") + ".md")
    twin.parent.mkdir(parents=True, exist_ok=True)
    twin.write_text(
        f"<!-- llms-explorer twin of {site_url}{spec['route']} · generated {stamp} -->\n\n"
        f"# {spec['title']}\n\n{spec['description']}\n\n{spec['body'].strip()}\n",
        encoding="utf-8")
    return twin


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
        rel = src.relative_to(content_dir)                      # reference/a.md
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
    for spec in STATIC_PAGES:
        twin = _static_twin(spec, dist_dir, site_url, stamp)
        if twin is not None:
            out.append(twin)
    return out


def _tokens(path: Path, manifest: dict, dist_dir: Path | None = None) -> int:
    """The published token count. For a family file the manifest is the source of
    truth (one number per file, H8); anything else is the declared estimator.

    Keyed by the path RELATIVE TO dist, not the basename: after the index split
    there is an `llms.txt` in every section directory, and they would all match
    the root's manifest entry and publish its token count."""
    rel = path.relative_to(dist_dir).as_posix() if dist_dir else path.name
    files = manifest.get("files", {})
    entry = files.get(rel) if rel in files else (files.get(path.name) if "/" not in rel else None)
    if isinstance(entry, dict) and isinstance(entry.get("tokens"), int):
        return entry["tokens"]
    return len(path.read_text(encoding="utf-8")) // CHARS_PER_TOKEN


# Every `<script>` that is not `src=`d: Astro inlines the small island modules
# straight into the HTML, so a `script-src 'self'` with no allowance for them
# would blank the four account pages. Hashing each one keeps the pages working
# while still refusing anything an injector adds, which `'unsafe-inline'` would
# not: an XSS on this origin can read the one-time key `/keys/` paints into the
# DOM and drive `/api/*` with the session cookie.
_INLINE_SCRIPT_RE = re.compile(rb"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>",
                               re.DOTALL | re.IGNORECASE)


def inline_script_hashes(dist_dir: Path) -> list[str]:
    """`'sha256-...'` source expressions for every inline script in the build.

    The digest is over the exact bytes between the tags, which is what the CSP
    hash algorithm specifies — trimming or re-encoding here silently produces a
    hash that matches nothing and takes the page down."""
    seen = set()
    for f in sorted(dist_dir.rglob("*.html")):
        for body in _INLINE_SCRIPT_RE.findall(f.read_bytes()):
            digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
            seen.add(f"'sha256-{digest}'")
    return sorted(seen)


def content_security_policy(dist_dir: Path, api_url: str | None = None) -> str:
    """The site's CSP. `frame-ancestors 'none'` is the one that matters most:
    without it `/keys/` can be framed and clickjacked into a Create or a Revoke.

    `style-src` keeps `'unsafe-inline'` — Astro emits inline `<style>` blocks and
    a few `style=` attributes, neither of which a hash can cover, and CSS cannot
    read the DOM. Scripts get no such latitude."""
    api = (api_url or default_api_url()).rstrip("/")
    return "; ".join([
        "default-src 'self'",
        " ".join(["script-src 'self'", *inline_script_hashes(dist_dir)]).rstrip(),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        f"connect-src 'self' {api}",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
        "object-src 'none'",
    ])


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
    # One `/*` rule, not one per account route: Pages caps the file at
    # MAX_HEADER_RULES, and the per-file token-count rules below already spend
    # most of it. Every route on this origin gets the same policy, so the
    # wildcard is also the honest description of it.
    lines = ["/*",
             f"  Content-Security-Policy: {content_security_policy(dist_dir)}",
             "  Referrer-Policy: no-referrer",
             "  X-Content-Type-Options: nosniff",
             "  X-Frame-Options: DENY",
             "  Strict-Transport-Security: max-age=31536000; includeSubDomains",
             "/*.md", md, describedby, "/llms*.txt", md, describedby,
             "/*/llms.txt", md, describedby]
    rules = 4
    # Pages applies EVERY matching rule and concatenates repeated header names,
    # so a per-file rule that repeats Content-Type sends it twice. The wildcards
    # above already cover type and link for `*.md` and every `llms*.txt`
    # (including the section indexes, via `/*/llms.txt`), so a per-file rule
    # carries only the one header no wildcard can know: this file's token count.
    for f in sorted(dist_dir.rglob("*.md")):
        lines += [f"/{f.relative_to(dist_dir).as_posix()}",
                  f"  X-Markdown-Tokens: {_tokens(f, manifest, dist_dir)}"]
        rules += 1
    for f in sorted(dist_dir.rglob("llms*.txt")):     # rglob: the spokes too
        lines += [f"/{f.relative_to(dist_dir).as_posix()}",
                  f"  X-Markdown-Tokens: {_tokens(f, manifest, dist_dir)}"]
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
