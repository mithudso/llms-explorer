"""docsets.py — thin wrapper over docset_indexer's CLI for the TUI.

Shells out to the hub venv python so ChromaDB stays in the interpreter it was
installed in; the TUI itself only needs the text results.

Semantic search goes through that subprocess (it needs the embedding pool and
the vector store). Fuzzy and regex search do NOT: they scan the docset's
source mirror file directly here, which needs no model and no Chroma import.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from . import core, settings

SEARCH_MODES = ("semantic", "fuzzy", "regex")

# Mirror files run to hundreds of MB; a scan must stay bounded so a stray
# regex on the biggest docset cannot hang the worker thread indefinitely.
MAX_SCAN_LINES = 400_000
_SNIPPET_CHARS = 300

_BANNER_RE = re.compile(r"^={10,}\s*$")
_URL_RE = re.compile(r"^URL:\s*(\S+)\s*$")


def _run(argv: list[str], timeout: int = 120) -> tuple[bool, str]:
    try:
        out = subprocess.run(
            [core.python_for_hub(), str(core.INDEXER_SCRIPT), *argv],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, **settings.stage_env()})
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except OSError as exc:
        return False, str(exc)
    text = (out.stdout + ("\n" + out.stderr if out.stderr.strip() else "")).strip()
    return out.returncode == 0, text


def list_docsets() -> tuple[bool, str]:
    return _run(["list"], timeout=60)


def query(docset: str, question: str, top: int = 5) -> tuple[bool, str]:
    return _run(["query", docset, question, "--top", str(top)], timeout=180)


def delete(docset: str) -> tuple[bool, str]:
    """Drop a docset (vectors + pages + registry row) via the indexer CLI.
    Returncode 1 there means "no such docset", which reads as failure here —
    the tab only offers rows it just listed, so that is a real surprise."""
    return _run(["delete", docset], timeout=120)


def index_argv(source_path: str, docset: str) -> list[str]:
    """argv that re-embeds a docset from its source mirror under the SAME
    key. `--name` pins the key: the default is derived from the mirror's
    first URL + file stem, which normally matches, but a mirror whose first
    page moved host would otherwise index as a second docset and leave the
    stale one behind."""
    return [core.python_for_hub(), str(core.INDEXER_SCRIPT), "index",
            source_path, "--name", docset]


def refresh_argvs(source_path: str, docset: str, polish: bool = False) -> list[list[str]]:
    """The refresh chain for one docset, run in order, each only after the
    previous exited 0: refine (clean/extract/LLM units/render), raw index
    from the clean mirror, facts index from all_units.jsonl. `polish=True`
    runs docset_refine's claude -p pass instead of the full chain and then
    re-indexes just the facts layer."""
    py = core.python_for_hub()
    mirror = Path(source_path).expanduser()
    ref = reference_dir_for(mirror)
    facts = [py, str(core.INDEXER_SCRIPT), "index", str(ref / "all_units.jsonl"),
             "--units", "--name", docset]
    if polish:
        return [[py, "-m", "docset_refine", "polish", str(mirror)],
                [py, "-m", "docset_refine", "render", str(mirror)], facts]
    clean = mirror.parent / f"{mirror.stem}.clean.md"
    return [[py, "-m", "docset_refine", "all", str(mirror)],
            [py, str(core.INDEXER_SCRIPT), "index", str(clean), "--name", docset],
            facts]


def _host_slug(host: str) -> str:
    """Mirror of docset_indexer._slug for the host part of a key, kept local
    so the TUI never imports the indexer (which drags in the embed pool)."""
    slug = re.sub(r"[^\w\s-]", "", host.lower()).strip()
    return re.sub(r"[\s_-]+", "-", slug)


def queue_url_for(entry: dict, items) -> str | None:
    """The pipeline-queue URL a docset was built from, or None.

    Two joins, in order of confidence: the queue item's recorded mirror path
    equals the docset's source_path (exact provenance), else the docset key's
    host slug matches the URL's host (the key is `<host-slug>__<stem>` and the
    pipeline names mirrors `<host>.md`, so this is how the key was minted).
    `items` are hub_manager.queue_model.QueueItem-shaped (url, mirror).
    """
    src = str(entry.get("source_path") or "")
    if src:
        want = str(Path(src).expanduser())
        for it in items:
            if it.mirror and str(Path(it.mirror).expanduser()) == want:
                return it.url
    key = str(entry.get("docset") or "")
    host_part = key.split("__", 1)[0] if "__" in key else ""
    if not host_part:
        return None
    for it in items:
        m = re.match(r"https?://([^/]+)", it.url)
        if m and _host_slug(m.group(1)) == host_part:
            return it.url
    return None


def docset_detail(entry: dict) -> str:
    """Rich-markup detail block for one docset row, rendered in the pane below
    the table when a row is clicked.

    The source path is emitted as an OSC-8 file:// hyperlink — terminals that
    support it (iTerm2, kitty, WezTerm, Ghostty) open the mirror on click;
    the rest just show the full path, which is the point either way.
    """
    key = str(entry.get("docset", "?"))
    raw = str(entry.get("source_path") or "")
    lines = [
        f"[b]{key}[/b]",
        f"  pages    {entry.get('pages', '?')}",
        f"  chunks   {entry.get('chunks', '?')}",
        f"  model    {entry.get('model', '?')} ({entry.get('backend', '?')})",
        f"  updated  {entry.get('updated_at') or '-'}",
    ]
    facts = entry.get("facts")
    lines.append(f"  facts    {facts} units (indexed as {key}__facts)" if facts
                 else "  facts    [dim]none — press e to build the fact layer[/dim]")
    if not raw:
        lines.append("  source   [red]not recorded — reindex to capture it[/red]")
        return "\n".join(lines)

    src = Path(raw).expanduser()
    lines.append(f"  source   [link=file://{src}]{src}[/link]")
    try:
        st = src.stat()
        lines.append(
            f"           {st.st_size / 1_048_576:.1f} MB · modified "
            + time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)))
    except OSError as exc:
        lines.append(f"           [red]unreadable: {exc}[/red]")
    lines.extend(reference_lines(src))
    return "\n".join(lines)


def reference_dir_for(mirror: Path) -> Path:
    return mirror.parent / f"{mirror.stem}.reference"


def reference_lines(mirror: Path) -> list[str]:
    """Detail lines for the docset's fact layer on disk (docset_refine's
    summary.json + reference.md), empty when refine has not run."""
    ref = reference_dir_for(mirror)
    summary = ref / "summary.json"
    if not summary.is_file():
        return []
    try:
        sm = json.loads(summary.read_text())
    except (OSError, json.JSONDecodeError):
        return [f"  reference [red]summary.json unreadable[/red] ({ref})"]
    by = sm.get("units_by_origin", {})
    out = [f"  reference {sm.get('units', 0)} units on disk — "
           + ", ".join(f"{k} {v}" for k, v in sorted(by.items()))]
    md = ref / "reference.md"
    if md.is_file():
        out.append(f"           [link=file://{md}]{md}[/link]")
    return out


def _fuzzy_scorer(query: str):
    """Token-gated fuzzy match.

    A line must share at least one query token before difflib runs on it —
    an unconditional ratio() over a multi-hundred-MB source is far too slow.
    Score = token coverage + closeness, so a line that carries every token
    and reads like the query outranks one that merely mentions a word.
    """
    ql = query.lower()
    tokens = [t for t in re.split(r"\s+", ql) if t]

    def score(line: str) -> float:
        low = line.lower()
        hit = [t for t in tokens if t in low]
        if not hit:
            return 0.0
        return len(hit) / len(tokens) + difflib.SequenceMatcher(None, ql, low).ratio()
    return score


def _make_scorer(query: str, mode: str):
    """(score_fn, error). One scorer feeds both the mirror scan and the
    chunk scan so the two paths can never drift in how they rank."""
    if mode not in ("fuzzy", "regex"):
        return None, f"unsupported search mode: {mode!r} (fuzzy|regex)"
    if not query:
        return None, "empty query"
    if mode == "regex":
        try:
            rx = re.compile(query, re.IGNORECASE)
        except re.error as exc:
            return None, f"bad regex: {exc}"
        return (lambda line: 1.0 if rx.search(line) else 0.0), ""
    return _fuzzy_scorer(query), ""


def _rank(lines, score) -> tuple[list[tuple[float, int, str, str, str]], bool]:
    """Score an iterable of (locator, url, text) under MAX_SCAN_LINES.

    The scan ordinal rides along so equal-scoring hits break the tie in source
    order — locators are strings, and sorting those puts line 100 before 9.
    """
    hits: list[tuple[float, int, str, str, str]] = []
    for n, (locator, url, text) in enumerate(lines, 1):
        if n > MAX_SCAN_LINES:
            return hits, True
        if not text.strip():
            continue
        s = score(text)
        if s:
            hits.append((s, n, locator, url, text.strip()[:_SNIPPET_CHARS]))
    return hits, False


def _render(hits, truncated: bool, mode: str, query: str,
            origin: str, top: int) -> str:
    tail = f" (scan stopped at {MAX_SCAN_LINES} lines)" if truncated else ""
    if not hits:
        return f"no {mode} matches for {query!r} in {origin}{tail}"
    hits.sort(key=lambda h: (-h[0], h[1]))
    shown = hits[:max(1, top)]
    out = [f"{len(hits)} {mode} match(es) in {origin} — showing {len(shown)}{tail}"]
    for _s, _n, locator, url, text in shown:
        out.append(f"  {locator}  {url or '-'}")
        out.append(f"    {text}")
    return "\n".join(out)


def _mirror_lines(src: Path):
    """Yield (locator, page url, line) from a web-text-mirror file, carrying
    the URL of the `==== / URL: / ====` banner each line falls under."""
    url = ""
    prev_banner = False
    with src.open("r", encoding="utf-8", errors="replace") as fh:
        for n, raw_line in enumerate(fh, 1):
            line = raw_line.rstrip("\n")
            if prev_banner:
                m = _URL_RE.match(line)
                if m:
                    url = m.group(1)
            prev_banner = bool(_BANNER_RE.match(line))
            yield f"{src.name}:{n}", url, line


def search_file(path: str, query: str, mode: str, top: int = 20) -> tuple[bool, str]:
    """Fuzzy or regex line search over a docset's source mirror file.

    Returns (ok, rendered text) to match list_docsets()/query(). Hits carry
    the page URL of the banner they fall under, so a match is traceable back
    to the page it came from and not just a line number.
    """
    q = query.strip()
    score, err = _make_scorer(q, mode)
    if err:
        return False, err
    if not path:
        return False, "this docset has no recorded source path"
    src = Path(path).expanduser()
    if not src.is_file():
        return False, f"source file missing: {src}"
    try:
        hits, truncated = _rank(_mirror_lines(src), score)
    except OSError as exc:
        return False, f"could not read {src}: {exc}"
    return True, _render(hits, truncated, mode, q, src.name, top)


def _index_lines(docset: str, timeout: int):
    """Yield (locator, page url, line) from `docset_indexer dump` JSONL.

    The dump emits raw PAGES when the docset stored them (full fidelity) and
    falls back to chunks otherwise; the `kind` field says which, and the
    locator carries it so a hit reads `page 12.4` or `chunk 12.4`.

    Streamed, not captured: a large docset's text runs to tens of MB and the
    scan is capped anyway, so it must not be buffered whole.
    """
    proc = subprocess.Popen(
        [core.python_for_hub(), str(core.INDEXER_SCRIPT), "dump", docset],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env={**os.environ, **settings.stage_env()})
    try:
        for raw in proc.stdout:
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue  # a stray non-JSON line must not abort the scan
            url, seq = row.get("url", ""), row.get("seq", "?")
            kind = row.get("kind", "chunk")
            for i, line in enumerate(str(row.get("text", "")).splitlines()):
                yield f"{kind} {seq}.{i}", url, line
    finally:
        # The scan usually stops at its cap long before the dump ends; killing
        # the producer is what turns that into a BrokenPipe it exits cleanly on.
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
        for stream in (proc.stdout, proc.stderr):
            if stream:
                stream.close()


def search_index(docset: str, query: str, mode: str, top: int = 20,
                 timeout: int = 180) -> tuple[bool, str]:
    """Fuzzy or regex search over a docset's STORED TEXT.

    The path for a docset whose source mirror is not on this box — a
    replicated `.chroma-docsets/` carries the text but not the file it came
    from. Docsets indexed since raw pages were stored are full fidelity here;
    older ones fall back to chunks, which lose fragments under 40 chars and
    overlap the rest, so they are a near-miss rather than an equal. Either way
    matches are located by page/chunk index instead of file line.
    """
    q = query.strip()
    score, err = _make_scorer(q, mode)
    if err:
        return False, err
    try:
        hits, truncated = _rank(_index_lines(docset, timeout), score)
    except OSError as exc:
        return False, f"could not dump docset {docset!r}: {exc}"
    return True, _render(hits, truncated, mode, q,
                         f"{docset} (stored text)", top)


def search_docset(docset: str, path: str, query: str, mode: str,
                  top: int = 20) -> tuple[bool, str]:
    """Fuzzy/regex search, preferring the source mirror and falling back to
    the indexed chunks when it is not on this box.

    The mirror wins whenever it is present — real file line numbers, and no
    dependence on what the indexer chose to store. The stored-text scan keeps
    replicated docsets searchable instead of erroring out.
    """
    if path and Path(path).expanduser().is_file():
        return search_file(path, query, mode, top=top)
    reason = ("no source path recorded" if not path
              else "source mirror not on this box")
    ok, text = search_index(docset, query, mode, top=top)
    if not ok:
        return ok, text
    return ok, f"[{reason} — searched the docset's stored text instead]\n{text}"
