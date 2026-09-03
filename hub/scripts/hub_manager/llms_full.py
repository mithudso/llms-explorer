"""llms_full.py — the LLMs-full tab's model: the local llms-full.txt mirror.

Reads llms_full_catalog's catalog + manifest in-process (both are small
JSON files; no subprocess, no model). Mutations that take time — compile,
download, index — are handed back as argv lists for the app's job runner,
the same way docsets.py does for the Docsets tab. Fuzzy/regex search scans
the downloaded file directly, tracking the `Source:` line each hit falls
under so a match traces back to its page.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import core, docsets

import llms_acquire  # noqa: E402  (core put scripts/ on sys.path)
import llms_full_catalog as catalog  # noqa: E402

STATUSES = ("ok", "all", "failed", "rejected", "missing")
SORTS = ("key", "pages", "bytes", "fetched", "name")
SEARCH_MODES = ("fuzzy", "regex")
CATALOG_SCRIPT = core.SCRIPTS_DIR / "llms_full_catalog.py"
_SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$")
_PREVIEW_BYTES = 5 * 1024 * 1024  # titles preview reads at most this much
_PREVIEW_TITLES = 40


def _repo_mirror_base() -> Path | None:
    """The repo's vendored llms-full mirror — `outputs/llms-full/`, or a bare
    `llms-full/` — the same one `site/tools/gen_directory.py` scores into
    the site's Directory. Fallback only: used when the live hub directory
    (`~/.global-ai-hub/llms-full/`) has no manifest yet because nobody has
    run `download` on this box, so the tab is never empty just because of
    that — it shows the same data the public Directory page shows."""
    repo_root = core.SCRIPTS_DIR.parent.parent
    for rel in ("llms-full", "outputs/llms-full"):
        cand = repo_root / rel
        if (cand / "manifest.json").is_file():
            return cand
    return None


def using_repo_mirror() -> bool:
    """True when `rows()` is about to fall back to the repo-vendored mirror
    rather than the live hub directory — the tab uses this to say so."""
    return not catalog.manifest_path().is_file() and _repo_mirror_base() is not None


def _mirror_rows(base: Path, status: str, query: str, min_pages: int) -> list[dict]:
    """Like `catalog.list_entries()`, but safe for a mirror checked out on a
    different machine than the one that ran `download`: the manifest's
    `file` field is an absolute path from *that* machine, so
    `list_entries()`'s existence check would call every row `missing` here.
    Rebind `file` to this mirror's own `files/<key>.txt` by key instead —
    the same fix `gen_directory.py`'s `entries()` already applies for the
    site build."""
    manifest = catalog.load_manifest(base)
    cat = {c["key"]: c for c in catalog.load_catalog(base) if c.get("key")}
    q = query.lower()
    out = []
    for key, raw in sorted(manifest.items()):
        e = dict(raw, key=raw.get("key", key))
        local = base / "files" / f"{e['key']}.txt"
        e["file"] = str(local)
        if e.get("status") == "ok" and not local.is_file():
            e["status"] = "missing"
        if status != "all" and e.get("status") != status:
            continue
        if e.get("status") == "ok" and int(e.get("pages") or 0) < min_pages:
            continue
        merged = dict(cat.get(e["key"], {}))
        merged.update(e)
        hay = " ".join(str(merged.get(k, "")) for k in
                       ("key", "name", "site", "url", "category"))
        if q and q not in hay.lower():
            continue
        out.append(merged)
    return out


def rows(status: str = "ok", query: str = "", min_pages: int = 0) -> list[dict]:
    """Manifest rows for the table, joined with the catalog's name/category/
    description/sources (the manifest carries only what download saw).
    Falls back to the repo's vendored mirror — see `_repo_mirror_base` —
    when the live hub mirror has no manifest yet."""
    if not catalog.manifest_path().is_file():
        mirror_base = _repo_mirror_base()
        if mirror_base is not None:
            return _mirror_rows(mirror_base, status, query, min_pages)
    cat = {r["key"]: r for r in catalog.load_catalog()}
    out = []
    for e in catalog.list_entries(status=status, query=query, min_pages=min_pages):
        c = cat.get(e["key"], {})
        merged = dict(c)
        merged.update(e)
        for k in ("name", "category"):
            if not merged.get(k) and c.get(k):
                merged[k] = c[k]
        out.append(merged)
    return out


def sort_rows(entries: list[dict], key: str, reverse: bool = False) -> list[dict]:
    if key in ("pages", "bytes"):
        entries = sorted(entries, key=lambda e: int(e.get(key) or 0))
    elif key == "fetched":
        entries = sorted(entries, key=lambda e: str(e.get("fetched_at") or ""))
    elif key == "name":
        entries = sorted(entries, key=lambda e: str(e.get("name") or e["key"]).lower())
    else:
        entries = sorted(entries, key=lambda e: e["key"])
    return list(reversed(entries)) if reverse else entries


def size_str(n: int) -> str:
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


def _titles(path: Path) -> tuple[list[str], int]:
    """(first page titles, total pages seen) from the head of the file."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(_PREVIEW_BYTES)
    except OSError:
        return [], 0
    pages = llms_acquire.split_llms_full(head)
    return [p["title"] for p in pages[:_PREVIEW_TITLES]], len(pages)


def detail(entry: dict) -> str:
    """Rich-markup block for the pane below the table."""
    lines = [f"[b]{entry['key']}[/b]  {entry.get('name') or ''}"]
    if entry.get("site"):
        lines.append(f"  site:        {entry['site']}")
    lines.append(f"  url:         {entry.get('url', '')}")
    if entry.get("category"):
        lines.append(f"  category:    {entry['category']}")
    if entry.get("description"):
        lines.append(f"  about:       {entry['description']}")
    if entry.get("sources"):
        lines.append(f"  listed by:   {', '.join(entry['sources'])}")
    status = entry.get("status", "?")
    reason = f" — {entry['reason']}" if entry.get("reason") else ""
    lines.append(f"  status:      {status}{reason}")
    if status == "ok":
        lines.append(f"  size:        {size_str(entry.get('bytes'))} bytes · "
                     f"{entry.get('pages', 0)} Source: pages · "
                     f"fetched {entry.get('fetched_at', '')}")
        path = Path(entry.get("file") or "")
        if path.exists():
            lines.append(f"  file:        [link=file://{path}]{path}[/link]")
            titles, n = _titles(path)
            if titles:
                more = f" … (+{n - len(titles)} more in the first 5 MB)" if n > len(titles) else ""
                lines.append(f"  pages:       {' · '.join(titles)}{more}")
        else:
            lines.append(f"  file:        MISSING {path}")
        mirror = catalog.mirror_path_for(entry["key"], core.MIRROR_OUT_DIR)
        if mirror.exists():
            lines.append(f"  mirror:      [link=file://{mirror}]{mirror}[/link] "
                         "(exported for docset_indexer)")
    return "\n".join(lines)


def _file_lines(src: Path):
    """Yield (locator, page url, line), the URL being the last `Source:` seen."""
    url = ""
    with src.open("r", encoding="utf-8", errors="replace") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            m = _SOURCE_RE.match(line)
            if m:
                url = m.group(1)
            yield f"{src.name}:{n}", url, line


def search_file(path: str, query: str, mode: str, top: int = 20) -> tuple[bool, str]:
    """Fuzzy or regex line search over one mirrored file; hits carry the
    `Source:` URL they fall under. Same scorer/ranker as the Docsets tab."""
    q = query.strip()
    score, err = docsets._make_scorer(q, mode)
    if err:
        return False, err
    src = Path(path or "")
    if not path or not src.is_file():
        return False, f"file missing: {src}"
    try:
        hits, truncated = docsets._rank(_file_lines(src), score)
    except OSError as exc:
        return False, f"could not read {src}: {exc}"
    return True, docsets._render(hits, truncated, mode, q, src.name, top)


# -- mutations ---------------------------------------------------------------


def delete(key: str) -> dict:
    return catalog.delete_entry(key)


def _py() -> str:
    return core.python_for_hub()


def refresh_all_argvs() -> list[list[str]]:
    """Re-compile the catalog from the directories, then download what is
    new + retry the failures. Already-ok files are left alone."""
    return [[_py(), str(CATALOG_SCRIPT), "compile"],
            [_py(), str(CATALOG_SCRIPT), "download", "--retry-failed"]]


def redownload_argv(entry: dict) -> list[str]:
    """Force re-fetch of one entry (matched by its URL)."""
    return [_py(), str(CATALOG_SCRIPT), "download", "--refresh",
            "--only", entry["url"], "--jobs", "1"]


def add_argvs(urls: list[str]) -> list[list[str]]:
    """Seed one or more llms-full.txt URLs into the catalog, then fetch just
    those (--only matches the url substring; the host is unique enough)."""
    compile_cmd = [_py(), str(CATALOG_SCRIPT), "compile"]
    for u in urls:
        compile_cmd += ["--seed", u]
    downloads = [[_py(), str(CATALOG_SCRIPT), "download", "--only", u, "--jobs", "1"]
                 for u in urls]
    return [compile_cmd, *downloads]


def index_argvs(entry: dict) -> list[list[str]]:
    """Export the file in banner format under text-mirror/, then index it as
    docset <key> — after which the Docsets tab's e/p (refine/polish) apply."""
    mirror = catalog.mirror_path_for(entry["key"], core.MIRROR_OUT_DIR)
    return [[_py(), str(CATALOG_SCRIPT), "export-mirror", entry["key"], str(mirror)],
            docsets.index_argv(str(mirror), entry["key"])]


def editor_argv(path: str) -> list[str]:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    return [*editor.split(), path]
