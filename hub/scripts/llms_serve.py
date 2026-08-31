#!/usr/bin/env python3
"""llms_serve.py — serve the hub's llms.txt surface over HTTP so an agent can be
pointed at a URL (the one consumer path the log studies show working).

Two sources, one root index (spec v2: H1, blockquote, H2 link lists):

  /llms.txt                     root index: every hub docset export + every mirrored
                                llms-full.txt (grouped by directory category)
  /index.json                   the same, as data
  /d/<stem>/llms.txt            a docset exported by `docset_refine export`
  /d/<stem>/llms-full.txt       (also llms-small.txt, llms-facts.txt, manifest.json)
  /d/<stem>/<section>/…/llms.txt  a section (any depth) of a split (hub-and-spoke) index
  /m/<key>/llms-full.txt        a file mirrored by llms_full_catalog.py
  /m/<key>/llms.txt             an index GENERATED from that file's pages (title + Source)
  /t/<slug>/llms.txt            a topical file (docset_refine topical): facts by concept
  /t/<slug>/llms-facts.txt      (also llms-vocabulary.txt, manifest.json)
  /c/<slug>/llms.txt            a concept pack (llms-concept-abstractor, /lca): one concept
  /c/<slug>/llms-full.txt       abstracted out of many sources (also llms-small.txt,
                                llms-facts.txt, llms-vocabulary.txt, concept-graph.json, manifest.json)
  /m/<key>/pages/<n>.md         one page of it
  /health                       liveness

Every markdown response carries `Content-Type: text/markdown; charset=utf-8`,
`X-Markdown-Tokens` (chars/4, the same estimator manifest.json uses) and a
`Link: <…/llms.txt>; rel="describedby"` header pointing at the index that
covers it — the spec-v2 discovery relations. Read-only, no network.

Trust model matches the MCP server: binds 127.0.0.1 by default. `--host
0.0.0.0` exposes it on the LAN for the other boxes; there is no auth, so do
not expose it further.

Usage:
  .venv/bin/python scripts/llms_serve.py [--host 127.0.0.1] [--port 8788]
  HUB_LLMS_PORT / HUB_LLMS_HOST override the defaults; launchd agent
  com.global-ai-hub.llms-serve keeps it running (scripts/launchd/).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_acquire  # noqa: E402
import llms_full_catalog  # noqa: E402
from hub_manager import core  # noqa: E402

DEFAULT_PORT = int(os.environ.get("HUB_LLMS_PORT", "8788"))
DEFAULT_HOST = os.environ.get("HUB_LLMS_HOST", "127.0.0.1")
CHARS_PER_TOKEN = 4
EXPORT_FILES = ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "manifest.json")
TOPICAL_FILES = ("llms.txt", "llms-facts.txt", "llms-vocabulary.txt", "manifest.json")
TOPICAL_DIR = Path(os.environ.get("HUB_LLMS_TOPICAL_DIR", core.HUB_DIR / "llms-topical"))
CONCEPT_FILES = ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
                 "llms-vocabulary.txt", "concept-graph.json", "manifest.json")
CONCEPT_DIR = Path(os.environ.get("HUB_LLMS_CONCEPT_DIR", core.HUB_DIR / "llms-concepts"))
_SAFE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")
_INDEX_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_LOCK = threading.Lock()


def _tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #


def hub_exports(mirror_dir: Path | None = None) -> list[dict]:
    """Every `<stem>.llms/manifest.json` under the text-mirror dir."""
    root = Path(mirror_dir or core.MIRROR_OUT_DIR)
    out = []
    for d in sorted(root.glob("*.llms")):
        man = d / "manifest.json"
        if not man.is_file():
            continue
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        stem = d.name[: -len(".llms")]
        if not _SAFE_RE.match(stem):
            continue
        m["stem"] = stem
        m["dir"] = str(d)
        out.append(m)
    return out


def topical_exports(topical_dir: Path | None = None) -> list[dict]:
    """Every `<slug>.llms/manifest.json` under llms-topical/."""
    root = Path(topical_dir or TOPICAL_DIR)
    out = []
    for d in sorted(root.glob("*.llms")):
        man = d / "manifest.json"
        if not man.is_file():
            continue
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        slug = d.name[: -len(".llms")]
        if not _SAFE_RE.match(slug):
            continue
        m["slug"] = slug
        m["dir"] = str(d)
        out.append(m)
    return out


def concept_exports(concept_dir: Path | None = None) -> list[dict]:
    """Every `<slug>.llms/manifest.json` under llms-concepts/ (kind == "concept")."""
    root = Path(concept_dir or CONCEPT_DIR)
    out = []
    for d in sorted(root.glob("*.llms")):
        man = d / "manifest.json"
        if not man.is_file():
            continue
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        slug = d.name[: -len(".llms")]
        if not _SAFE_RE.match(slug):
            continue
        m["slug"] = slug
        m["dir"] = str(d)
        out.append(m)
    return out


def mirror_entries() -> list[dict]:
    try:
        return llms_full_catalog.list_entries(status="ok", min_pages=1)
    except Exception:  # noqa: BLE001 — a broken manifest must not take the server down
        return []


def mirror_pages(entry: dict) -> list[dict]:
    """Split a mirrored file into pages, cached by (key, mtime)."""
    path = Path(entry.get("file") or "")
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return []
    with _CACHE_LOCK:
        hit = _INDEX_CACHE.get(entry["key"])
        if hit and hit[0] == mtime:
            return hit[1]
    text = path.read_text(encoding="utf-8", errors="replace")
    pages = llms_acquire.split_llms_full(text)
    with _CACHE_LOCK:
        _INDEX_CACHE[entry["key"]] = (mtime, pages)
    return pages


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def _first_sentence(text: str, limit: int = 160) -> str:
    body = re.sub(r"^#.*$", "", text, flags=re.M)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    for para in re.split(r"\n\s*\n", body):
        p = re.sub(r"\s+", " ", para).strip()
        if len(p) >= 30 and not p.startswith(("|", "-", "*", ">", "<", "[")):
            s = re.split(r"(?<=[.!?])\s+", p)[0]
            return s if len(s) <= limit else s[:limit].rsplit(" ", 1)[0] + "…"
    return ""


def render_mirror_index(entry: dict, pages: list[dict], base: str) -> str:
    name = entry.get("name") or entry["key"]
    out = [
        f"# {name}",
        "",
        f"> Index generated by the hub from {entry['url']} ({len(pages)} pages, "
        f"{entry.get('bytes', 0)} bytes). Links point at the publisher's pages; the full "
        f"text is served at {base}/m/{entry['key']}/llms-full.txt.",
        "",
        "## Pages",
        "",
    ]
    for n, p in enumerate(pages, 1):
        desc = _first_sentence(p.get("text", ""))
        line = f"- [{p.get('title') or p['url']}]({p['url']})"
        out.append(line + (f": {desc}" if desc else ""))
    out += [
        "",
        "## Optional",
        "",
        f"- [Whole file]({base}/m/{entry['key']}/llms-full.txt): all pages in one markdown "
        f"file (~{int(entry.get('bytes', 0)) // CHARS_PER_TOKEN} tokens)",
    ]
    return "\n".join(out) + "\n"


def render_root(exports: list[dict], mirrors: list[dict], base: str,  # noqa: PLR0913
                topics: list[dict] | None = None, concepts: list[dict] | None = None) -> str:
    topics = topics or []
    out = [
        "# Global AI Hub — llms.txt",
        "",
        f"> Every documentation set this hub can hand an agent as markdown: {len(exports)} "
        f"docsets refined by the hub (index, full text, a small subset, and an extracted fact "
        f"layer each) and {len(mirrors)} llms-full.txt files mirrored from sites that publish "
        "one. Each link below is itself an llms.txt; follow it, then follow its page links.",
        "",
        "Files under /d/ carry a `manifest.json` with byte and token counts per file; every "
        "markdown response carries an `X-Markdown-Tokens` header.",
        "",
    ]
    if topics:
        out += ["## Topics", "",
                "Concept-organised files: facts from every source, filed under the concept "
                "tree's children of one subject.", ""]
        for t in topics:
            f = t.get("files", {})
            out.append(
                f"- [{t.get('title') or t['slug']}]({base}/t/{t['slug']}/llms.txt): "
                f"{t.get('units', 0)} facts from {t.get('sources', 0)} sources, "
                f"{len(t.get('sections', {}))} sections, "
                f"~{f.get('llms-facts.txt', {}).get('tokens', 0)} tokens facts"
            )
        out.append("")
    if concepts:
        out += ["## Concepts", "",
                "Concept packs: everything the scanned sources say about ONE concept, "
                "grouped by facet, every line source-anchored (llms-concept-abstractor).", ""]
        for c in concepts:
            f = c.get("files", {})
            kids = len(c.get("children") or {})
            out.append(
                f"- [{c.get('concept') or c['slug']}]({base}/c/{c['slug']}/llms.txt): "
                f"{c.get('kept_units', 0)} units from {len(c.get('sources') or {})} sources, "
                f"{len(c.get('facets') or {})} facets, ~{f.get('llms-small.txt', {}).get('tokens', 0)} tokens small"
                + (f", {kids} child packs" if kids else "")
            )
        out.append("")
    if exports:
        out += ["## Hub docsets", ""]
        for m in exports:
            f = m.get("files", {})
            line = (
                f"- [{m.get('title') or m['stem']}]({base}/d/{m['stem']}/llms.txt): "
                f"{m.get('pages', 0)} pages, ~{f.get('llms.txt', {}).get('tokens', 0)} tokens index"
            )
            if "llms-full.txt" in f:
                line += f", ~{f['llms-full.txt']['tokens']} tokens full"
            if "llms-facts.txt" in f:
                line += f", {m.get('units', 0)} facts"
            out.append(line)
        out.append("")
    if mirrors:
        by_cat: dict[str, list[dict]] = {}
        for e in mirrors:
            by_cat.setdefault((e.get("category") or "uncategorised").strip().lower(), []).append(e)
        for cat in sorted(by_cat):
            out += [f"## Mirrored: {cat}", ""]
            for e in sorted(by_cat[cat], key=lambda x: (x.get("name") or x["key"]).lower()):
                out.append(
                    f"- [{e.get('name') or e['key']}]({base}/m/{e['key']}/llms.txt): "
                    f"{e.get('site') or e['url']} — {e.get('pages', 0)} pages, "
                    f"~{int(e.get('bytes', 0)) // CHARS_PER_TOKEN} tokens full"
                )
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def index_json(exports: list[dict], mirrors: list[dict], base: str,
               concepts: list[dict] | None = None) -> dict:
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "concepts": [
            {
                "slug": c["slug"],
                "concept": c.get("concept"),
                "units": c.get("kept_units"),
                "sources": len(c.get("sources") or {}),
                "files": c.get("files"),
                "children": sorted((c.get("children") or {}).keys()),
                "llms_txt": f"{base}/c/{c['slug']}/llms.txt",
            }
            for c in (concepts or [])
        ],
        "docsets": [
            {
                "stem": m["stem"],
                "title": m.get("title"),
                "pages": m.get("pages"),
                "units": m.get("units"),
                "files": m.get("files"),
                "llms_txt": f"{base}/d/{m['stem']}/llms.txt",
            }
            for m in exports
        ],
        "mirrors": [
            {
                "key": e["key"],
                "name": e.get("name"),
                "site": e.get("site"),
                "category": e.get("category"),
                "pages": e.get("pages"),
                "bytes": e.get("bytes"),
                "llms_txt": f"{base}/m/{e['key']}/llms.txt",
                "llms_full_txt": f"{base}/m/{e['key']}/llms-full.txt",
            }
            for e in mirrors
        ],
    }


# --------------------------------------------------------------------------- #
# handler
# --------------------------------------------------------------------------- #


class Handler(BaseHTTPRequestHandler):
    server_version = "hub-llms/1.0"
    mirror_dir: Path | None = None  # overridable for tests
    topical_dir: Path | None = None
    concept_dir: Path | None = None

    def log_message(self, fmt, *args):  # noqa: D401 — quiet by default
        if os.environ.get("HUB_LLMS_LOG"):
            super().log_message(fmt, *args)

    def _base(self) -> str:
        host = self.headers.get("Host") or f"{DEFAULT_HOST}:{DEFAULT_PORT}"
        return f"http://{host}"

    def _send(
        self,
        body: str | bytes,
        ctype: str = "text/markdown; charset=utf-8",
        describedby: str | None = None,
        status: int = 200,
    ) -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        if ctype.startswith("text/markdown"):
            self.send_header("X-Markdown-Tokens", str(len(data) // CHARS_PER_TOKEN))
        if describedby:
            self.send_header("Link", f'<{describedby}>; rel="describedby"')
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _error(self, status: HTTPStatus, msg: str) -> None:
        self._send(f"{status.value} {msg}\n", "text/plain; charset=utf-8", status=status.value)

    def do_HEAD(self):  # noqa: N802
        self.do_GET()

    def do_GET(self):  # noqa: N802
        path = unquote(urlsplit(self.path).path)
        base = self._base()
        parts = [p for p in path.split("/") if p]
        try:
            if path in ("/", "/llms.txt"):
                return self._send(render_root(hub_exports(self.mirror_dir), mirror_entries(), base,
                                              topical_exports(self.topical_dir),
                                              concept_exports(self.concept_dir)))
            if path == "/index.json":
                return self._send(
                    json.dumps(
                        index_json(hub_exports(self.mirror_dir), mirror_entries(), base,
                                   concept_exports(self.concept_dir)), indent=1
                    ),
                    "application/json; charset=utf-8",
                )
            if path == "/health":
                return self._send("ok\n", "text/plain; charset=utf-8")
            if len(parts) == 3 and parts[0] == "d":
                return self._docset(parts[1], parts[2], base)
            if len(parts) >= 4 and parts[0] == "d" and parts[-1] == "llms.txt":
                # a section (any depth) of a split index — export_llms.build_split_index
                return self._docset(parts[1], "/".join(parts[2:]), base)
            if len(parts) >= 3 and parts[0] == "m":
                return self._mirror(parts[1], parts[2:], base)
            if len(parts) == 3 and parts[0] == "t":
                return self._topical(parts[1], parts[2], base)
            if len(parts) == 3 and parts[0] == "c":
                return self._concept(parts[1], parts[2], base)
        except Exception as e:  # noqa: BLE001 — one bad file must not kill the listener
            return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"{type(e).__name__}: {e}")
        return self._error(HTTPStatus.NOT_FOUND, "not found")

    def _docset(self, stem: str, fname: str, base: str) -> None:
        section = fname.endswith("/llms.txt") and all(
            _SAFE_RE.match(seg) for seg in fname[: -len("/llms.txt")].split("/"))
        if not _SAFE_RE.match(stem) or not (fname in EXPORT_FILES or section):
            return self._error(HTTPStatus.NOT_FOUND, "no such docset file")
        root = Path(self.mirror_dir or core.MIRROR_OUT_DIR)
        f = root / f"{stem}.llms" / fname
        if not f.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "no such docset file")
        data = f.read_bytes()
        if fname.endswith(".json"):
            return self._send(data, "application/json; charset=utf-8")
        return self._send(data, describedby=f"{base}/d/{stem}/llms.txt")

    def _topical(self, slug: str, fname: str, base: str) -> None:
        if not _SAFE_RE.match(slug) or fname not in TOPICAL_FILES:
            return self._error(HTTPStatus.NOT_FOUND, "no such topical file")
        f = Path(self.topical_dir or TOPICAL_DIR) / f"{slug}.llms" / fname
        if not f.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "no such topical file")
        data = f.read_bytes()
        if fname.endswith(".json"):
            return self._send(data, "application/json; charset=utf-8")
        return self._send(data, describedby=f"{base}/t/{slug}/llms.txt")

    def _concept(self, slug: str, fname: str, base: str) -> None:
        if not _SAFE_RE.match(slug) or fname not in CONCEPT_FILES:
            return self._error(HTTPStatus.NOT_FOUND, "no such concept pack file")
        f = Path(self.concept_dir or CONCEPT_DIR) / f"{slug}.llms" / fname
        if not f.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "no such concept pack file")
        data = f.read_bytes()
        if fname.endswith(".json"):
            return self._send(data, "application/json; charset=utf-8")
        return self._send(data, describedby=f"{base}/c/{slug}/llms.txt")

    def _mirror(self, key: str, rest: list[str], base: str) -> None:
        if not _SAFE_RE.match(key):
            return self._error(HTTPStatus.NOT_FOUND, "bad key")
        entry = next((e for e in mirror_entries() if e["key"] == key), None)
        if entry is None:
            return self._error(HTTPStatus.NOT_FOUND, "unknown mirror key")
        describedby = f"{base}/m/{key}/llms.txt"
        if rest == ["llms-full.txt"]:
            return self._send(Path(entry["file"]).read_bytes(), describedby=describedby)
        if rest == ["llms.txt"]:
            return self._send(render_mirror_index(entry, mirror_pages(entry), base))
        if len(rest) == 2 and rest[0] == "pages" and re.fullmatch(r"\d+\.md", rest[1]):
            n = int(rest[1][:-3])
            pages = mirror_pages(entry)
            if not 1 <= n <= len(pages):
                return self._error(HTTPStatus.NOT_FOUND, f"page out of range (1..{len(pages)})")
            p = pages[n - 1]
            body = f"# {p.get('title') or p['url']}\nSource: {p['url']}\n\n{p.get('text', '')}\n"
            return self._send(body, describedby=describedby)
        return self._error(HTTPStatus.NOT_FOUND, "no such mirror file")


def serve(
    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, mirror_dir: Path | None = None,
    topical_dir: Path | None = None,
    concept_dir: Path | None = None,
) -> ThreadingHTTPServer:
    Handler.mirror_dir = mirror_dir
    Handler.topical_dir = topical_dir
    Handler.concept_dir = concept_dir
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    return srv


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    a = ap.parse_args(argv)
    srv = serve(a.host, a.port)
    print(
        f"hub llms.txt server on http://{a.host}:{a.port}/llms.txt "
        f"({len(hub_exports())} docsets, {len(mirror_entries())} mirrors)",
        flush=True,
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
