#!/usr/bin/env python3
"""llms_full_catalog.py — catalog + local mirror of the web's `llms-full.txt` files.

`llms-full.txt` is a site's whole docset as one markdown file (the llms.txt
proposal). This module keeps a catalog of every site known to publish one,
downloads the reachable ones into `llms-full/`, and records what landed so
the MCP server (`hub_llms_full_list` / `hub_llms_full_read`) can serve the
directory without touching the network.

Layout (all under HUB_LLMS_FULL_DIR, default ~/.global-ai-hub/llms-full/):
  catalog.json   every candidate: name, site, category, url, sources (who listed it)
  manifest.json  per-catalog-entry download status: ok | rejected | failed, bytes,
                 pages (via llms_acquire.split_llms_full), sha256, fetched_at
  files/<key>.txt  the downloaded file; key = host[__path-slug]

Sources for `compile`:
  - github.com/thedaviddias/llms-txt-hub README (name, site, description, category)
  - llmstxt.site directory table (name, site)
  - directory.llmstxt.cloud (URL sweep)
  - this hub's own docslist.textmirror probe (docset_rollout.json, method=llms-full)
  - extra seed URLs from HUB_LLMS_FULL_SEEDS (comma-separated) or --seed

Usage:
  llms_full_catalog.py compile [--seed URL ...] [--offline FILE ...]
  llms_full_catalog.py download [--jobs N] [--max-bytes N] [--only SUBSTR] [--retry-failed]
  llms_full_catalog.py list [--status ok|rejected|failed|all] [--query S] [--min-pages N] [--json]
  llms_full_catalog.py delete KEY                     drop the file + manifest row
  llms_full_catalog.py export-mirror KEY OUT.md       banner-format copy for docset_indexer

Stdlib only (urllib, concurrent.futures) so the hub venv is not required.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_acquire  # noqa: E402

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub"))
BASE_DIR = Path(os.environ.get("HUB_LLMS_FULL_DIR", HUB_DIR / "llms-full"))
UA = "global-ai-hub-llms-full/1.0 (+https://github.com/mitchhudson/global-ai-hub)"
DEFAULT_MAX_BYTES = 200 * 1024 * 1024  # a docset bigger than this is not a docset
DEFAULT_JOBS = 12
FETCH_TIMEOUT = 90
MIN_BYTES = llms_acquire.MIN_FULL_BYTES

HUB_README = "https://raw.githubusercontent.com/thedaviddias/llms-txt-hub/main/README.md"
LLMSTXT_SITE = "https://llmstxt.site/"
DIRECTORY_CLOUD = "https://directory.llmstxt.cloud/"

_FULL_URL_RE = re.compile(r"https?://[^\s\"'<>()\]]*llms-full\.txt")
# thedaviddias README line: **[Name](site)** - desc <sub>[llms.txt](u) • [llms-full.txt](u)</sub>
_README_ROW_RE = re.compile(
    r"\*\*\[(?P<name>[^\]]+)\]\((?P<site>[^)]+)\)\*\*\s*-\s*(?P<desc>.*?)\s*<sub>(?P<links>.*?)</sub>")
_README_FULL_RE = re.compile(r"\[llms-full\.txt\]\((?P<url>[^)]+)\)")
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_HREF_RE = re.compile(r'href="([^"]+)"')
_TAG_RE = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------- #
# paths + persistence
# --------------------------------------------------------------------------- #


def _base(base: Path | None) -> Path:
    """Resolve at call time so BASE_DIR can be repointed after import."""
    return Path(base) if base is not None else BASE_DIR


def catalog_path(base: Path | None = None) -> Path:
    return _base(base) / "catalog.json"


def manifest_path(base: Path | None = None) -> Path:
    return _base(base) / "manifest.json"


def files_dir(base: Path | None = None) -> Path:
    return _base(base) / "files"


def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_catalog(base: Path | None = None) -> list[dict]:
    return _load(catalog_path(base), [])


def load_manifest(base: Path | None = None) -> dict:
    return _load(manifest_path(base), {})


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# keys
# --------------------------------------------------------------------------- #


def key_for(url: str) -> str:
    """Filesystem-safe id: host, plus a slug of any path above the file so
    `angular.dev/context/llm-files/llms-full.txt` and a hypothetical
    `angular.dev/llms-full.txt` never collide. `www.` is dropped."""
    p = urlparse(url)
    host = (p.netloc or "").lower().split("@")[-1].split(":")[0]
    host = host.removeprefix("www.")
    segs = [s for s in (p.path or "").split("/") if s and s != "llms-full.txt"]
    slug = "-".join(re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") for s in segs)
    slug = re.sub(r"-+", "-", slug).strip("-")
    key = host + (f"__{slug}" if slug else "")
    return re.sub(r"[^a-z0-9._-]+", "-", key)


def _norm_url(url: str) -> str:
    url = html.unescape(url.strip()).rstrip(".,;)")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    return url


# --------------------------------------------------------------------------- #
# source parsers (pure: text in, rows out)
# --------------------------------------------------------------------------- #


def _row(url: str, name: str = "", site: str = "", category: str = "",
         description: str = "", source: str = "") -> dict:
    url = _norm_url(url)
    return {"key": key_for(url), "url": url, "name": name.strip(), "site": site.strip(),
            "category": category.strip(), "description": description.strip(),
            "sources": [source] if source else []}


def parse_hub_readme(text: str) -> list[dict]:
    """Rows from thedaviddias/llms-txt-hub's README: entries live under
    `### <emoji> category` headers, one bullet per site."""
    rows, category = [], ""
    for line in text.splitlines():
        if line.startswith("### "):
            category = re.sub(r"^[^\w]+", "", line[4:].strip())  # drop the emoji
            continue
        m = _README_ROW_RE.search(line)
        if not m:
            continue
        f = _README_FULL_RE.search(m.group("links"))
        if not f:
            continue
        rows.append(_row(f.group("url"), m.group("name"), m.group("site"), category,
                         m.group("desc"), "llms-txt-hub"))
    return rows


def parse_llmstxt_site(page: str) -> list[dict]:
    """Rows from llmstxt.site's directory table: Product | Website | llms.txt
    | tokens | llms-full.txt | tokens. Only rows with a full-file link count."""
    rows = []
    for tr in _TR_RE.findall(page):
        tds = _TD_RE.findall(tr)
        if len(tds) < 5:
            continue
        full = _HREF_RE.search(tds[4])
        if not full or "llms-full.txt" not in full.group(1):
            continue
        name = html.unescape(_TAG_RE.sub("", tds[0])).strip()
        site_m = _HREF_RE.search(tds[1])
        site = site_m.group(1) if site_m else ""
        rows.append(_row(full.group(1), name, site, "", "", "llmstxt.site"))
    return rows


def parse_url_sweep(text: str, source: str) -> list[dict]:
    """Any llms-full.txt URL in a page/file — the fallback for directories
    that render client-side (directory.llmstxt.cloud) and plain seed lists."""
    seen, rows = set(), []
    for u in _FULL_URL_RE.findall(text):
        u = _norm_url(u)
        if u not in seen:
            seen.add(u)
            rows.append(_row(u, source=source))
    return rows


def parse_rollout(rollout: list[dict]) -> list[dict]:
    """The hub's own probe results (docset_rollout.py probe)."""
    rows = []
    for r in rollout:
        if r.get("method") == "llms-full" and r.get("source"):
            site = r.get("url", "")
            name = urlparse(site).netloc.removeprefix("www.")
            rows.append(_row(r["source"], name, site, "hub docslist", "", "docslist.textmirror"))
    return rows


def merge_rows(*groups: list[dict], existing: list[dict] | None = None) -> list[dict]:
    """Union by url; the first non-empty name/site/category/description wins
    (the hub README is the richest source, so pass it first). Sources
    accumulate. Existing catalog rows keep their metadata."""
    by_url: dict[str, dict] = {}
    for r in existing or []:
        by_url[r["url"]] = dict(r, sources=list(r.get("sources") or []))
    for group in groups:
        for r in group:
            cur = by_url.get(r["url"])
            if cur is None:
                by_url[r["url"]] = dict(r, sources=list(r["sources"]))
                continue
            for k in ("name", "site", "category", "description"):
                if not cur.get(k) and r.get(k):
                    cur[k] = r[k]
            for s in r["sources"]:
                if s not in cur["sources"]:
                    cur["sources"].append(s)
    rows = sorted(by_url.values(), key=lambda r: r["key"])
    # two catalog rows must never share a file key
    seen: dict[str, int] = {}
    for r in rows:
        n = seen.get(r["key"], 0)
        seen[r["key"]] = n + 1
        if n:
            r["key"] = f"{r['key']}-{n + 1}"
    return rows


# --------------------------------------------------------------------------- #
# network
# --------------------------------------------------------------------------- #


def _get(url: str, timeout: int = FETCH_TIMEOUT, max_bytes: int = DEFAULT_MAX_BYTES,
         attempts: int = 2) -> tuple[bytes | None, str, str]:
    """(body, content_type, error). body None on any failure. Streams so an
    oversized answer is cut off at max_bytes instead of filling memory."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/plain, */*"})
    err = ""
    for n in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                ctype = r.headers.get("Content-Type", "")
                clen = r.headers.get("Content-Length")
                if clen and clen.isdigit() and int(clen) > max_bytes:
                    return None, ctype, f"too large: {clen} bytes"
                chunks, total = [], 0
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        return None, ctype, f"too large: >{max_bytes} bytes"
                    chunks.append(chunk)
                return b"".join(chunks), ctype, ""
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code in (401, 403, 404, 410, 451):
                break  # a retry cannot change these
        except (urllib.error.URLError, OSError, ValueError) as e:
            err = f"{type(e).__name__}: {str(e)[:120]}"
        if n + 1 < attempts:
            time.sleep(2)
    return None, "", err


def _fetch_text(url: str) -> str | None:
    body, _, _ = _get(url, max_bytes=50 * 1024 * 1024)
    return body.decode("utf-8", errors="replace") if body is not None else None


def validate(body: bytes, ctype: str) -> tuple[str, int, str]:
    """(status, pages, reason). `ok` only for a real llms-full.txt: not HTML,
    above the stub floor, and (advisory) splittable into `# Title` + `Source:`
    pages — a file without Source: lines is still markdown docs, so it is kept
    with pages=0 rather than rejected."""
    if "html" in ctype.lower():
        return "rejected", 0, "HTML content-type (soft 404)"
    if len(body) < MIN_BYTES:
        return "rejected", 0, f"stub: {len(body)} bytes"
    head = body[:2048].lstrip().lower()
    if head.startswith((b"<!doctype html", b"<html")):
        return "rejected", 0, "HTML body (soft 404)"
    text = body.decode("utf-8", errors="replace")
    return "ok", len(llms_acquire.split_llms_full(text)), ""


def download_one(row: dict, base: Path | None = None, max_bytes: int = DEFAULT_MAX_BYTES,
                 get=_get) -> dict:
    body, ctype, err = get(row["url"], max_bytes=max_bytes)
    entry = {"key": row["key"], "url": row["url"], "name": row.get("name", ""),
             "site": row.get("site", ""), "category": row.get("category", ""),
             "fetched_at": _now()}
    if body is None:
        entry.update(status="failed", reason=err, bytes=0, pages=0)
        return entry
    status, pages, reason = validate(body, ctype)
    entry.update(status=status, reason=reason, bytes=len(body), pages=pages)
    if status == "ok":
        out = files_dir(base) / f"{row['key']}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        entry["file"] = str(out)
        entry["sha256"] = hashlib.sha256(body).hexdigest()
    return entry


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #


def compile_catalog(base: Path | None = None, seeds: list[str] | None = None,
                    offline: list[Path] | None = None, fetch=_fetch_text,
                    log=print) -> list[dict]:
    """Rebuild catalog.json from every source (network unless `offline`
    files are given, in which case only those + seeds + the rollout probe)."""
    groups: list[list[dict]] = []
    if offline:
        for f in offline:
            text = Path(f).read_text(encoding="utf-8", errors="replace")
            if "<sub>" in text and "llms-full.txt" in text:
                groups.append(parse_hub_readme(text))
            elif "<tr" in text:
                groups.append(parse_llmstxt_site(text))
            groups.append(parse_url_sweep(text, f"file:{Path(f).name}"))
    else:
        for name, url, parser in (("llms-txt-hub", HUB_README, parse_hub_readme),
                                  ("llmstxt.site", LLMSTXT_SITE, parse_llmstxt_site),
                                  ("directory.llmstxt.cloud", DIRECTORY_CLOUD, None)):
            text = fetch(url)
            if text is None:
                log(f"source unreachable: {name}")
                continue
            rows = parser(text) if parser else []
            sweep = parse_url_sweep(text, name)
            log(f"{name}: {len(rows)} rows, {len(sweep)} urls in sweep")
            groups.append(rows)
            groups.append(sweep)
    rollout = _load(HUB_DIR / "docset_rollout.json", [])
    groups.append(parse_rollout(rollout))
    seed_list = list(seeds or [])
    env_seeds = os.environ.get("HUB_LLMS_FULL_SEEDS", "")
    seed_list += [s.strip() for s in env_seeds.split(",") if s.strip()]
    groups.append([_row(s, source="seed") for s in seed_list])
    rows = merge_rows(*groups, existing=load_catalog(base))
    _save(catalog_path(base), rows)
    log(f"catalog: {len(rows)} llms-full.txt candidates -> {catalog_path(base)}")
    return rows


def download_all(base: Path | None = None, jobs: int = DEFAULT_JOBS,
                 max_bytes: int = DEFAULT_MAX_BYTES, only: str = "",
                 retry_failed: bool = False, refresh: bool = False,
                 get=_get, log=print) -> dict:
    """Fetch every catalog entry not yet in the manifest (plus failed ones
    with --retry-failed, or everything with --refresh). The manifest is
    saved after every completion, so a killed run resumes where it stopped."""
    catalog = load_catalog(base)
    manifest = load_manifest(base)
    todo = []
    for row in catalog:
        if only and only not in row["url"] and only not in row.get("name", ""):
            continue
        prev = manifest.get(row["key"])
        if prev and not refresh and not (retry_failed and prev["status"] != "ok"):
            continue
        todo.append(row)
    log(f"downloading {len(todo)} of {len(catalog)} (jobs={jobs})")
    counts = {"ok": 0, "rejected": 0, "failed": 0}
    with cf.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        futs = {ex.submit(download_one, row, base, max_bytes, get): row for row in todo}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            entry = fut.result()
            manifest[entry["key"]] = entry
            counts[entry["status"]] += 1
            if i % 25 == 0 or i == len(todo):
                _save(manifest_path(base), manifest)
                log(f"  {i}/{len(todo)}  ok={counts['ok']} rejected={counts['rejected']} "
                    f"failed={counts['failed']}")
    _save(manifest_path(base), manifest)
    return counts


def list_entries(base: Path | None = None, status: str = "ok", query: str = "",
                 min_pages: int = 0) -> list[dict]:
    """Manifest rows (sorted by key), filtered by status and a substring over
    key/name/site/url/category. `min_pages` drops downloaded files with fewer
    `# Title`/`Source:` pages — the directories are open submission, and a
    marketing blob with 0 pages is the common noise; real docsets have
    dozens to thousands. Downloaded files that vanished are reported with
    status `missing` so the caller never gets a dead path."""
    q = query.lower()
    out = []
    for e in sorted(load_manifest(base).values(), key=lambda e: e["key"]):
        e = dict(e)
        if e["status"] == "ok" and not Path(e.get("file", "")).exists():
            e["status"] = "missing"
        if status != "all" and e["status"] != status:
            continue
        if e["status"] == "ok" and int(e.get("pages") or 0) < min_pages:
            continue
        hay = " ".join(str(e.get(k, "")) for k in ("key", "name", "site", "url", "category"))
        if q and q not in hay.lower():
            continue
        out.append(e)
    return out


def read_entry(key: str, base: Path | None = None, offset: int = 0, limit: int = 20_000,
               page: str = "") -> dict:
    """A slice of one downloaded file. `page` selects one `# Title`/`Source:`
    page by exact source URL or case-insensitive title substring; otherwise
    `offset`/`limit` slice the raw characters."""
    entry = load_manifest(base).get(key)
    if not entry:
        return {"error": f"unknown key: {key}"}
    if entry["status"] != "ok":
        return {"error": f"{key} not downloaded: {entry['status']} ({entry.get('reason', '')})"}
    path = Path(entry.get("file", ""))
    if not path.exists():
        return {"error": f"{key} file missing on disk: {path}"}
    text = path.read_text(encoding="utf-8", errors="replace")
    if page:
        pages = llms_acquire.split_llms_full(text)
        pl = page.lower()
        hit = next((p for p in pages if p["url"] == page), None) or \
            next((p for p in pages if pl in p["title"].lower()), None)
        if hit is None:
            titles = [p["title"] for p in pages][:50]
            return {"error": f"no page matching {page!r}", "pages": len(pages),
                    "titles": titles}
        body = hit["text"][:limit]
        return {"key": key, "url": entry["url"], "page_title": hit["title"],
                "page_url": hit["url"], "total_chars": len(hit["text"]),
                "truncated": len(hit["text"]) > limit, "text": body}
    offset = max(0, offset)
    body = text[offset:offset + limit]
    return {"key": key, "url": entry["url"], "offset": offset, "total_chars": len(text),
            "next_offset": offset + len(body) if offset + len(body) < len(text) else None,
            "text": body}


def delete_entry(key: str, base: Path | None = None) -> dict:
    """Drop one mirrored file and its manifest row. The catalog row stays, so
    the next `download` fetches it again unless the catalog is edited too;
    `--retry-failed`/`--refresh` semantics are unchanged."""
    manifest = load_manifest(base)
    entry = manifest.pop(key, None)
    if entry is None:
        return {"key": key, "deleted": False, "error": "unknown key"}
    removed = False
    path = Path(entry.get("file") or "")
    if entry.get("file") and path.exists():
        path.unlink()
        removed = True
    _save(manifest_path(base), manifest)
    return {"key": key, "deleted": True, "file_removed": removed}


def mirror_path_for(key: str, out_dir: Path) -> Path:
    return Path(out_dir) / f"{key}.llms-full.md"


def export_mirror(key: str, out_path: Path, base: Path | None = None,
                  max_pages: int = 0) -> dict:
    """Write a mirrored llms-full.txt as a web-text-mirror banner file so
    `docset_indexer index` / the refine pipeline can consume it unchanged.
    A file with no `Source:` pages becomes one page under its own URL."""
    entry = load_manifest(base).get(key)
    if not entry or entry.get("status") != "ok":
        return {"key": key, "pages": 0, "error": f"{key} is not downloaded"}
    path = Path(entry.get("file") or "")
    if not path.exists():
        return {"key": key, "pages": 0, "error": f"file missing: {path}"}
    text = path.read_text(encoding="utf-8", errors="replace")
    pages = llms_acquire.split_llms_full(text) or [
        {"title": entry.get("name") or key, "url": entry["url"], "text": text}]
    n = llms_acquire.write_mirror(pages, str(out_path), max_pages)
    return {"key": key, "pages": n, "mirror": str(out_path)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile", help="rebuild catalog.json from the public directories")
    c.add_argument("--seed", action="append", default=[], help="extra llms-full.txt URL")
    c.add_argument("--offline", action="append", default=[], type=Path,
                   help="parse this saved directory page/file instead of the network")
    d = sub.add_parser("download", help="fetch catalog entries into files/")
    d.add_argument("--jobs", type=int, default=DEFAULT_JOBS)
    d.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    d.add_argument("--only", default="", help="substring filter on url/name")
    d.add_argument("--retry-failed", action="store_true")
    d.add_argument("--refresh", action="store_true", help="re-fetch everything")
    ls = sub.add_parser("list", help="show the manifest")
    ls.add_argument("--status", default="ok",
                    choices=("ok", "rejected", "failed", "missing", "all"))
    ls.add_argument("--query", default="")
    ls.add_argument("--min-pages", type=int, default=0,
                    help="hide downloaded files with fewer Source: pages (0 = show all)")
    ls.add_argument("--json", action="store_true")
    de = sub.add_parser("delete", help="drop one mirrored file + its manifest row")
    de.add_argument("key")
    ex = sub.add_parser("export-mirror",
                        help="write a mirrored file as a web-text-mirror banner file")
    ex.add_argument("key")
    ex.add_argument("out", type=Path)
    ex.add_argument("--max-pages", type=int, default=0)
    a = ap.parse_args(argv)

    if a.cmd == "compile":
        compile_catalog(seeds=a.seed, offline=a.offline or None)
    elif a.cmd == "download":
        counts = download_all(jobs=a.jobs, max_bytes=a.max_bytes, only=a.only,
                              retry_failed=a.retry_failed, refresh=a.refresh)
        print(json.dumps(counts))
    elif a.cmd == "delete":
        out = delete_entry(a.key)
        print(json.dumps(out))
        return 0 if out.get("deleted") else 1
    elif a.cmd == "export-mirror":
        out = export_mirror(a.key, a.out, max_pages=a.max_pages)
        print(json.dumps(out))
        return 0 if not out.get("error") else 1
    elif a.cmd == "list":
        rows = list_entries(status=a.status, query=a.query, min_pages=a.min_pages)
        if a.json:
            print(json.dumps(rows, indent=1, ensure_ascii=False))
        else:
            for e in rows:
                print(f"{e['status']:8} {e['bytes']:>10} {e['pages']:>5}p  {e['key']:45} "
                      f"{e.get('name', '')[:40]}")
            print(f"{len(rows)} entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
