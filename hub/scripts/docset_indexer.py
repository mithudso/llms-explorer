#!/usr/bin/env python3
"""docset_indexer.py — index web-text-mirror docsets for semantic query.

Pipeline position: web-text-mirror produces one markdown file per docset
(pages delimited by `==== / URL: <url> / ====` banners). This tool chunks
each page, embeds the chunks via the hub's Ollama pool (embed_core), and
stores them in a per-docset collection so consuming skills query one shared
index instead of re-embedding.

Storage adapter: ChromaDB when importable (the hub venv installs it), else a
SQLite fallback mirroring the hub's proven hub_sqlite pattern (vectors as
JSON text, cosine in Python). Same CLI either way; backend recorded per
docset in the registry table.

Docset identity: <source hostname>__<mirror filename stem>, slugified —
deterministic, so re-indexing the same mirror updates one collection.

CLI:
  docset_indexer.py index  <mirror.md> [--model M] [--max-fail-pct 5]
  docset_indexer.py query  <docset> "question" [--top 5]
  docset_indexer.py dump   <docset> [--kind auto|pages|chunks]   # JSONL text
  docset_indexer.py list
Env: HUB_OLLAMA_URLS, HUB_EMBED_MODEL (see embed_core);
     HUB_DOCSET_DB overrides the SQLite registry/fallback path only (default
     <HUB_DIR>/.chroma-docsets/docsets.db, alongside the vectors it
     describes — the Chroma dir itself is always <HUB_DIR>/.chroma-docsets);
     HUB_DOCSET_BACKEND forces "chroma" or "sqlite" (default: chroma when importable).
Bannerless input (no URL banners) is indexed as one synthetic page.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embed_core  # noqa: E402

# expanduser: env blocks from launchd/MCP-client JSON pass literal '~' through
HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()
CHROMA_DIR = HUB_DIR / ".chroma-docsets"
SQLITE_PATH = Path(os.environ.get("HUB_DOCSET_DB", CHROMA_DIR / "docsets.db")).expanduser()

CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200

# ---------------------------------------------------------------------------
# mirror parsing (canonical implementation: distillers/distill_offline.py —
# kept in sync; duplicated here so the hub has no cross-repo import)
# ---------------------------------------------------------------------------

_BANNER_RE = re.compile(r"^={10,}\s*$")
_URL_RE = re.compile(r"^URL:\s*(\S+)\s*$")


def parse_mirror(text: str) -> list[dict] | None:
    lines = text.splitlines()
    starts = []
    for i in range(len(lines) - 2):
        if _BANNER_RE.match(lines[i]) and _BANNER_RE.match(lines[i + 2]):
            m = _URL_RE.match(lines[i + 1])
            if m:
                starts.append((i, m.group(1)))
    if not starts:
        return None  # single-page mirrors are valid input for indexing
    pages = []
    for n, (i, url) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        pages.append({"url": url, "text": "\n".join(lines[i + 3:end]).strip("\n")})
    return pages


def _slug(text: str) -> str:
    raw = text or ""
    slug = re.sub(r"[^\w\s-]", "", raw.lower()).strip()
    slug = re.sub(r"[\s_-]+", "-", slug)
    # Truncation or total-fallback can collide two unrelated inputs — pin
    # identity with a short hash of the untruncated source when that happens.
    if len(slug) > 80 or not slug:
        suffix = hashlib.sha1(raw.encode()).hexdigest()[:8]
        slug = f"{slug[:80] or 'docset'}-{suffix}"
    return slug


def docset_key(pages: list[dict], path: str) -> str:
    m = re.match(r"https?://([^/]+)", pages[0]["url"]) if pages else None
    host = m.group(1) if m else "unknown-host"
    return f"{_slug(host)}__{_slug(Path(path).stem)}"


FACTS_SUFFIX = "__facts"


def facts_key(key: str) -> str:
    return key if key.endswith(FACTS_SUFFIX) else key + FACTS_SUFFIX


def base_key(key: str) -> str:
    return key[:-len(FACTS_SUFFIX)] if key.endswith(FACTS_SUFFIX) else key


def load_units(path: Path) -> list[dict]:
    """A docset_refine all_units.jsonl -> index rows (no vectors yet). A
    snippet embeds as its caption plus the code body so a query for a
    command hits the block that contains it; url carries the anchor."""
    rows = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                u = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = str(u.get("text", "")).strip()
            code = u.get("code") or {}
            if code.get("body"):
                # snippet text is "<caption>: <first code line>" — embed the
                # caption plus the whole body once, not the first line twice
                caption = text.split(": ", 1)[0] if ": " in text else text
                text = f"{caption}\n{code['body']}"
            if len(text) < 20:
                continue
            uid = str(u.get("id") or f"u{n:06d}")
            if uid in seen:  # a stale all_units.jsonl from before render re-id'd
                uid = f"{uid}-{n}"
            seen.add(uid)
            rows.append({"id": uid,
                         "url": f"{u.get('source_url', '')}{u.get('anchor', '')}",
                         "seq": n, "text": text,
                         "unit_type": u.get("type", ""), "origin": u.get("origin", "")})
    return rows


def chunk_page(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Paragraph-aware sliding window: pack whole paragraphs up to `size`
    chars; fall back to a hard window inside oversized paragraphs."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > size:
            if buf:
                chunks.append(buf)
                buf = ""
            step = max(1, size - overlap)  # guard: overlap >= size would zero/negate the stride
            for i in range(0, len(p), step):
                chunks.append(p[i:i + size])
            continue
        if buf and len(buf) + len(p) + 2 > size:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return [c for c in chunks if len(c) >= 40]


# ---------------------------------------------------------------------------
# storage adapters
# ---------------------------------------------------------------------------

def _hit(score, url, seq, text, unit_type=None, origin=None) -> dict:
    hit = {"score": round(score, 4), "url": url, "seq": seq, "text": text}
    if unit_type:
        hit["unit_type"] = unit_type
    if origin:
        hit["origin"] = origin
    return hit


def fts_match(query: str, mode: str = "any") -> str:
    """Turn a user query into an FTS5 MATCH expression.

    Every term is double-quoted so tokens like `--append-system-prompt` or
    `X-Markdown-Tokens` become phrases of their sub-tokens instead of FTS5
    operators; `raw` passes the caller's own MATCH syntax through."""
    if mode == "raw":
        return query
    q = query.replace('"', '""').strip()
    if mode == "phrase":
        return f'"{q}"'
    terms = [f'"{w}"' for w in q.split() if w]
    if not terms:
        return '""'
    return (" AND " if mode == "all" else " OR ").join(terms)


class SqliteStore:
    """Fallback mirroring hub_sqlite's convention: vectors as JSON text.

    Thread-safety: the MCP server caches ONE store and mcp 2.0 dispatches
    concurrent tool calls on different worker threads, so the connection is
    opened with check_same_thread=False and every db operation holds _lock
    (sqlite connections are not safe for concurrent multi-thread use even
    with the flag off)."""

    backend = "sqlite"

    def __init__(self):
        import sqlite3
        self._lock = threading.Lock()
        self.db = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            " docset TEXT, chunk_id TEXT, url TEXT, seq INTEGER,"
            " text TEXT, vector TEXT, model TEXT,"
            " PRIMARY KEY (docset, chunk_id))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS docsets ("
            " docset TEXT PRIMARY KEY, source_path TEXT, pages INTEGER,"
            " chunks INTEGER, model TEXT, backend TEXT, updated_at TEXT)"
        )
        # Raw page text, kept under BOTH backends (chroma stores its chunks in
        # the collection, but this rides in docsets.db, which replicate_docsets
        # copies). Chunking drops fragments under 40 chars and overlaps the
        # rest, so chunks are not a faithful copy of the source -- this is what
        # lets a box without the mirror still do a full-fidelity text search.
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS pages ("
            " docset TEXT, idx INTEGER, url TEXT, text TEXT,"
            " PRIMARY KEY (docset, idx))"
        )
        # Facts rows carry their unit type/origin; older databases gain the
        # columns in place (ALTER is idempotent via the check).
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(chunks)").fetchall()}
        for col in ("unit_type", "origin"):
            if col not in cols:
                self.db.execute(f"ALTER TABLE chunks ADD COLUMN {col} TEXT")

    # ---- keyword layer (FTS5 / BM25) --------------------------------------
    # One virtual table for every docset and layer, keyed by the same
    # `<key>` / `<key>__facts` names as the vector collections, so a caller
    # resolves the layer once and asks either index. unicode61 splits on
    # `-`, `_` and `.`, which is what makes `CLAUDE_CODE_SYNC_SKILLS` or
    # `--append-system-prompt` findable as a phrase without the caller
    # knowing the tokenizer; keyword_query() quotes terms accordingly.
    def _ensure_kw(self):
        self.db.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS kw USING fts5("
            " docset UNINDEXED, url UNINDEXED, seq UNINDEXED, text,"
            " tokenize='unicode61 remove_diacritics 2')"
        )

    def keyword_replace(self, key, rows) -> int:
        """Rebuild the keyword index for `key` from {url, seq, text} rows.

        Rows are materialised BEFORE the lock is taken: callers pass
        dump_chunks(), a generator that takes the same non-reentrant lock,
        and draining it under the lock deadlocks the store."""
        rows = list(rows)
        with self._lock, self.db:
            self._ensure_kw()
            self.db.execute("DELETE FROM kw WHERE docset=?", (key,))
            n = 0
            for r in rows:
                self.db.execute("INSERT INTO kw (docset, url, seq, text) VALUES (?,?,?,?)",
                                (key, r.get("url", ""), r.get("seq", 0), r.get("text", "")))
                n += 1
        return n

    def keyword_count(self, key) -> int:
        with self._lock:
            self._ensure_kw()
            return self.db.execute("SELECT count(*) FROM kw WHERE docset=?", (key,)).fetchone()[0]

    def keyword_query(self, key, query: str, top: int = 5, mode: str = "any") -> list[dict]:
        """BM25-ranked hits. mode: any (OR of terms, default), all (AND),
        phrase (exact sequence), raw (caller-written FTS5 MATCH syntax)."""
        match = fts_match(query, mode)
        with self._lock:
            self._ensure_kw()
            rows = self.db.execute(
                "SELECT url, seq, snippet(kw, 3, '[', ']', ' … ', 24), bm25(kw)"
                " FROM kw WHERE docset=? AND kw MATCH ? ORDER BY bm25(kw) LIMIT ?",
                (key, match, top)).fetchall()
        return [{"score": round(-s, 4), "url": u, "seq": q, "snippet": sn}
                for u, q, sn, s in rows]

    def replace_docset(self, key, rows, meta, pages=None):
        with self._lock, self.db:
            self.db.execute("DELETE FROM chunks WHERE docset=?", (key,))
            self.db.executemany(
                "INSERT OR REPLACE INTO chunks"
                " (docset, chunk_id, url, seq, text, vector, model, unit_type, origin)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                [(key, r["id"], r["url"], r["seq"], r["text"],
                  json.dumps(r["vector"]), r["model"], r.get("unit_type"), r.get("origin"))
                 for r in rows],
            )
            self._write_meta(key, meta, len(rows), self.backend)
            self._write_pages(key, pages)

    def _write_meta(self, key, meta, chunk_count, backend):
        """Registry row. Caller holds _lock and the transaction."""
        self.db.execute(
            "INSERT OR REPLACE INTO docsets VALUES (?,?,?,?,?,?,datetime('now'))",
            (key, meta["source_path"], meta["pages"], chunk_count,
             meta["model"], backend),
        )

    def _write_pages(self, key, pages):
        """Raw page text. `pages=None` leaves whatever is stored alone, so an
        older caller cannot silently wipe it; `[]` clears it deliberately."""
        if pages is None:
            return
        self.db.execute("DELETE FROM pages WHERE docset=?", (key,))
        self.db.executemany(
            "INSERT OR REPLACE INTO pages VALUES (?,?,?,?)",
            [(key, i, pg.get("url", ""), pg.get("text", ""))
             for i, pg in enumerate(pages)],
        )

    def record_pages(self, key, meta, chunk_count, backend, pages):
        """Registry row + page text in one transaction, for a store whose
        vectors live elsewhere (ChromaStore)."""
        with self._lock, self.db:
            self._write_meta(key, meta, chunk_count, backend)
            self._write_pages(key, pages)

    def delete_docset(self, key):
        """Drop a docset entirely: registry row, chunks, raw pages. Returns
        True when a registry row existed. Deleting a key that is not present
        is a no-op rather than an error, so a retry after a half-failed
        delete converges instead of tripping."""
        with self._lock, self.db:
            existed = self.db.execute(
                "SELECT 1 FROM docsets WHERE docset=?", (key,)).fetchone() is not None
            for table in ("chunks", "pages", "docsets"):
                self.db.execute(f"DELETE FROM {table} WHERE docset=?", (key,))
        return existed

    def query(self, key, qvec, top):
        self._check_backend(key)
        with self._lock:
            rows = self.db.execute(
                "SELECT url, seq, text, vector, unit_type, origin FROM chunks WHERE docset=?",
                (key,)).fetchall()
        qmag = math.sqrt(sum(x * x for x in qvec)) or 1.0
        scored = []
        mismatched = 0
        for url, seq, text, vec_json, unit_type, origin in rows:
            v = json.loads(vec_json)
            if len(v) != len(qvec):
                mismatched += 1  # different embedding model — cosine meaningless
                continue
            mag = math.sqrt(sum(x * x for x in v)) or 1.0
            sim = sum(a * b for a, b in zip(qvec, v)) / (qmag * mag)
            scored.append((sim, url, seq, text, unit_type, origin))
        if mismatched and not scored:
            raise ValueError(
                f"embedding model mismatch: all {mismatched} stored vectors have a "
                "different dimension than the query — re-index or query with the "
                "docset's recorded model")
        scored.sort(reverse=True)
        return [_hit(s, u, q, t, ut, o) for s, u, q, t, ut, o in scored[:top]]

    def docset_model(self, key):
        with self._lock:
            row = self.db.execute(
                "SELECT model FROM docsets WHERE docset=?", (key,)).fetchone()
        return row[0] if row else None

    def _check_backend(self, key):
        """A docset indexed under one backend is invisible to the other —
        without this check a backend flip returns silent empty results."""
        with self._lock:
            row = self.db.execute(
                "SELECT backend FROM docsets WHERE docset=?", (key,)).fetchone()
        if row and row[0] != self.backend:
            raise ValueError(
                f"docset '{key}' was indexed with backend={row[0]}, but this "
                f"process is using backend={self.backend} (HUB_DOCSET_BACKEND)")

    def close(self):
        with self._lock:
            self.db.close()

    def dump_pages(self, key):
        """Yield the raw source pages as {url, seq, text}, newest write wins.

        Empty for docsets indexed before pages were stored — the caller falls
        back to dump_chunks() rather than reporting the docset as empty."""
        with self._lock:
            rows = self.db.execute(
                "SELECT url, idx, text FROM pages WHERE docset=? ORDER BY idx",
                (key,)).fetchall()
        for url, idx, text in rows:
            yield {"url": url, "seq": idx, "text": text}

    def dump_chunks(self, key):
        """Yield every stored chunk as {url, seq, text}, no vectors.

        Consumers that need the docset's TEXT (literal/regex search when the
        source mirror is not on this box) must not have to load embeddings."""
        with self._lock:
            rows = self.db.execute(
                "SELECT url, seq, text FROM chunks WHERE docset=? ORDER BY seq",
                (key,)).fetchall()
        for url, seq, text in rows:
            yield {"url": url, "seq": seq, "text": text}

    def list_docsets(self, include_facts: bool = False):
        """Docsets with their `<key>__facts` twin folded into a `facts` count
        (None when there is no fact layer yet). include_facts=True lists the
        twins as their own rows instead — replicate/delete want the raw view."""
        with self._lock:
            rows = self.db.execute(
                "SELECT docset, pages, chunks, model, backend, updated_at,"
                " source_path FROM docsets").fetchall()
        # source_path rides along so callers (hub-manager's Docsets tab) can
        # link straight to the mirror file a docset was built from.
        entries = [dict(zip(("docset", "pages", "chunks", "model", "backend",
                             "updated_at", "source_path"), row))
                   for row in rows]
        if include_facts:
            return entries
        facts = {e["docset"]: e for e in entries if e["docset"].endswith(FACTS_SUFFIX)}
        out = []
        for e in entries:
            if e["docset"].endswith(FACTS_SUFFIX):
                continue
            twin = facts.pop(facts_key(e["docset"]), None)
            e["facts"] = twin["chunks"] if twin else None
            e["facts_path"] = twin["source_path"] if twin else None
            out.append(e)
        for twin in facts.values():  # a facts layer whose raw twin is gone
            twin["facts"], twin["facts_path"] = twin["chunks"], twin["source_path"]
            out.append(twin)
        return out


class ChromaStore:
    backend = "chroma"

    def __init__(self):
        import chromadb
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        # Registry rides in SQLite either way so `list` needs no Chroma scan.
        self.registry = SqliteStore()

    def keyword_replace(self, key, rows):
        return self.registry.keyword_replace(key, rows)

    def keyword_count(self, key):
        return self.registry.keyword_count(key)

    def keyword_query(self, key, query, top=5, mode="any"):
        return self.registry.keyword_query(key, query, top, mode)

    def replace_docset(self, key, rows, meta, pages=None):
        # Stage-then-swap: populate a staging collection fully BEFORE touching
        # the existing one, so a mid-write failure never destroys the last
        # good index (the previous version stays queryable throughout).
        staging = f"{key}__staging"
        try:
            self.client.delete_collection(staging)
        except Exception:
            pass
        col = self.client.create_collection(staging, metadata={"hnsw:space": "cosine"})
        try:
            for i in range(0, len(rows), 500):
                batch = rows[i:i + 500]
                col.add(
                    ids=[r["id"] for r in batch],
                    embeddings=[r["vector"] for r in batch],
                    documents=[r["text"] for r in batch],
                    metadatas=[{"url": r["url"], "seq": r["seq"],
                                "unit_type": r.get("unit_type") or "",
                                "origin": r.get("origin") or ""} for r in batch],
                )
        except Exception:
            try:
                self.client.delete_collection(staging)
            except Exception:
                pass
            raise
        # All batches landed — swap: drop old, rename staging into place.
        try:
            self.client.delete_collection(key)
        except Exception:
            pass
        col.modify(name=key)
        # Registry row AND raw page text land in docsets.db — the vectors stay
        # in Chroma, but the text has to ride in the file replicate_docsets
        # actually copies.
        self.registry.record_pages(key, dict(meta), len(rows), self.backend,
                                   pages)

    def query(self, key, qvec, top):
        row_backend = None
        with self.registry._lock:
            row = self.registry.db.execute(
                "SELECT backend FROM docsets WHERE docset=?", (key,)).fetchone()
        row_backend = row[0] if row else None
        if row_backend and row_backend != self.backend:
            raise ValueError(
                f"docset '{key}' was indexed with backend={row_backend}, but this "
                f"process is using backend={self.backend} (HUB_DOCSET_BACKEND)")
        col = self.client.get_collection(key)
        res = col.query(query_embeddings=[qvec], n_results=top,
                        include=["documents", "metadatas", "distances"])
        out = []
        for doc, md, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            out.append(_hit(1.0 - dist, md["url"], md["seq"], doc,
                            md.get("unit_type"), md.get("origin")))
        return out

    def delete_docset(self, key):
        """Drop the collection (and any staging leftover from an interrupted
        index) plus the registry row + pages in docsets.db. The registry
        write is what replicate_docsets ships, so it must go too or the other
        boxes keep listing a docset whose vectors are gone."""
        found = False
        for name in (key, f"{key}__staging"):
            try:
                self.client.delete_collection(name)
                found = found or name == key
            except Exception:  # noqa: BLE001 — absent collection is fine
                pass
        return self.registry.delete_docset(key) or found

    def dump_pages(self, key):
        return self.registry.dump_pages(key)

    def dump_chunks(self, key):
        """Paged .get over the collection — documents + metadata only, so a
        big docset never materialises its vectors just to be text-searched."""
        col = self.client.get_collection(key)
        offset, page = 0, 1000
        while True:
            res = col.get(include=["documents", "metadatas"],
                          limit=page, offset=offset)
            docs = res.get("documents") or []
            if not docs:
                return
            for doc, md in zip(docs, res.get("metadatas") or []):
                md = md or {}
                yield {"url": md.get("url", ""), "seq": md.get("seq", 0),
                       "text": doc}
            if len(docs) < page:
                return
            offset += page

    def list_docsets(self, include_facts: bool = False):
        return self.registry.list_docsets(include_facts=include_facts)

    def docset_model(self, key):
        return self.registry.docset_model(key)

    def close(self):
        self.registry.close()


def get_store():
    forced = os.environ.get("HUB_DOCSET_BACKEND", "").lower()
    if forced == "sqlite":
        return SqliteStore()
    try:
        import chromadb  # noqa: F401
        return ChromaStore()
    except ImportError:
        if forced == "chroma":
            raise
        return SqliteStore()


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_index_units(args) -> int:
    """Embed a docset_refine all_units.jsonl as `<name>__facts`: one row per
    unit, metadata carrying unit type / origin, no raw pages (the facts
    layer has none — `dump` falls back to its chunks, which ARE the units)."""
    src = Path(args.mirror).expanduser()
    if not args.name:
        print("ERROR: --units requires --name <docset key> (the facts twin is <key>__facts)",
              file=sys.stderr)
        return 2
    key = facts_key(args.name)
    model = args.model or embed_core.embed_model()
    units = load_units(src)
    if not units:
        print(f"ERROR: no units in {src}", file=sys.stderr)
        return 2
    rows, failed = [], 0
    batch = 64
    for i in range(0, len(units), batch):
        chunk = units[i:i + batch]
        try:
            vecs = embed_core.embed_texts([u["text"] for u in chunk], model=model)
        except embed_core.EmbeddingUnavailable as e:
            failed += len(chunk)
            print(f"WARN units {i}-{i + len(chunk)}: {e}", file=sys.stderr)
            continue
        for u, vec in zip(chunk, vecs):
            rows.append({**u, "vector": vec, "model": model})
        if (i // batch) % 10 == 9:
            print(f"  embedded {len(rows)}/{len(units)} units", file=sys.stderr, flush=True)
    total = len(rows) + failed
    fail_pct = 100.0 * failed / total if total else 0.0
    if fail_pct > args.max_fail_pct:
        print(f"ERROR: {failed}/{total} units failed to embed ({fail_pct:.1f}% > "
              f"{args.max_fail_pct}%) — index NOT written.", file=sys.stderr)
        return 3
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    store.replace_docset(key, rows, {"source_path": str(src), "pages": 0, "model": model},
                         pages=[])
    print(json.dumps({"docset": key, "backend": store.backend, "units": len(rows),
                      "failed_units": failed, "fail_pct": round(fail_pct, 2),
                      "model": model}, indent=2))
    return 0


def cmd_index(args) -> int:
    if getattr(args, "units", False):
        return cmd_index_units(args)
    src = Path(args.mirror).expanduser()
    text = src.read_text(errors="ignore")
    pages = parse_mirror(text)
    if not pages:
        # Bannerless input is still indexable — treat the whole file as one
        # synthetic page anchored to its local path.
        print("NOTE: no URL banners found — indexing as a single synthetic page",
              file=sys.stderr)
        pages = [{"url": f"file://{src.resolve()}", "text": text}]
    key = args.name or docset_key(pages, args.mirror)
    model = args.model or embed_core.embed_model()

    rows, failed = [], 0
    for pi, pg in enumerate(pages):
        chunks = chunk_page(pg["text"])
        if not chunks:
            continue
        try:
            vecs = embed_core.embed_texts(chunks, model=model)
        except embed_core.EmbeddingUnavailable as e:
            failed += len(chunks)
            print(f"WARN page {pg['url']}: {e}", file=sys.stderr)
            continue
        for ci, (chunk, vec) in enumerate(zip(chunks, vecs)):
            rows.append({
                "id": f"p{pi:03d}c{ci:03d}", "url": pg["url"], "seq": ci,
                "text": chunk, "vector": vec, "model": model,
            })
        if (pi + 1) % 20 == 0:
            # stderr: stdout is reserved for the single final JSON payload
            # (the MCP server returns raw stdout as the tool result).
            print(f"  embedded {pi + 1}/{len(pages)} pages "
                  f"({len(rows)} chunks)", file=sys.stderr, flush=True)

    total = len(rows) + failed
    if total == 0:
        print(f"ERROR: no chunks >= 40 chars produced from {len(pages)} page(s) — "
              "nothing to index", file=sys.stderr)
        return 2
    fail_pct = 100.0 * failed / total
    if fail_pct > args.max_fail_pct:
        print(f"ERROR: {failed}/{total} chunks failed to embed "
              f"({fail_pct:.1f}% > {args.max_fail_pct}%) — index NOT written. "
              "See kickoff verification threshold.", file=sys.stderr)
        return 3

    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    store.replace_docset(key, rows, {
        "source_path": str(Path(args.mirror).expanduser()),
        "pages": len(pages), "model": model,
    }, pages=pages)
    print(json.dumps({
        "docset": key, "backend": store.backend, "pages": len(pages),
        "chunks": len(rows), "failed_chunks": failed,
        "fail_pct": round(fail_pct, 2), "model": model,
    }, indent=2))
    return 0


def cmd_query(args) -> int:
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    args.top = max(1, min(int(args.top), 50))  # backend-consistent clamp
    key, layer = resolve_layer(store, args.docset, getattr(args, "layer", "auto"))
    # Embed the query with the MODEL THE DOCSET WAS INDEXED WITH — a different
    # model puts the query in a different embedding space (wrong or no results).
    model = store.docset_model(key) or embed_core.embed_model()
    try:
        qvec = embed_core.embed_texts([args.question], model=model)[0]
    except embed_core.EmbeddingUnavailable as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    try:
        hits = store.query(key, qvec, args.top)
    except Exception as e:
        print(f"ERROR: query failed for docset '{key}': {e}", file=sys.stderr)
        return 2
    print(json.dumps({"docset": args.docset, "layer": layer, "queried": key,
                      "question": args.question, "results": hits},
                     indent=2, ensure_ascii=False))
    return 0


def cmd_keyword_index(args) -> int:
    """Build the FTS5 keyword index for a docset layer from its stored text
    (chunks under either backend), so exact-token lookups never need an
    embedding call. Re-run after `index`; `--layer` picks the twin."""
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    key, layer = resolve_layer(store, args.docset, getattr(args, "layer", "auto"))
    if store.docset_model(key) is None:
        print(f"ERROR: docset '{key}' is not indexed", file=sys.stderr)
        return 2
    try:
        n = store.keyword_replace(key, store.dump_chunks(key))
    except Exception as e:
        print(f"ERROR: keyword index failed for '{key}': {e}", file=sys.stderr)
        return 2
    print(json.dumps({"docset": args.docset, "layer": layer, "indexed": key, "rows": n}))
    return 0


def cmd_keyword(args) -> int:
    """BM25 keyword query — the cheap path beside `query` (vector)."""
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    args.top = max(1, min(int(args.top), 50))
    key, layer = resolve_layer(store, args.docset, getattr(args, "layer", "auto"))
    if store.keyword_count(key) == 0:
        print(f"ERROR: no keyword index for '{key}' — run: docset_indexer.py keyword-index "
              f"{args.docset} --layer {layer}", file=sys.stderr)
        return 2
    try:
        hits = store.keyword_query(key, args.question, args.top, args.mode)
    except Exception as e:
        print(f"ERROR: keyword query failed for '{key}': {e}", file=sys.stderr)
        return 2
    print(json.dumps({"docset": args.docset, "layer": layer, "queried": key,
                      "question": args.question, "mode": args.mode, "results": hits},
                     indent=2, ensure_ascii=False))
    return 0


def resolve_layer(store, docset: str, layer: str = "auto") -> tuple[str, str]:
    """(key to query, layer name). auto -> facts when `<docset>__facts`
    exists, else raw. An explicit `__facts` key is honored as facts."""
    if docset.endswith(FACTS_SUFFIX):
        return docset, "facts"
    if layer == "raw":
        return docset, "raw"
    twin = facts_key(docset)
    has_twin = store.docset_model(twin) is not None
    if layer == "facts":
        return twin, "facts"
    return (twin, "facts") if has_twin else (docset, "raw")


def cmd_dump(args) -> int:
    """Stream a docset's text as JSONL — one {kind, url, seq, text} per line.

    Raw pages when they were stored (full fidelity: every line, nothing
    dropped by chunking), else the indexed chunks, so a docset written before
    pages existed still dumps instead of coming back empty. --kind forces one.

    JSONL, not a JSON array, so a consumer can scan a multi-hundred-MB docset
    line by line instead of holding the whole thing in memory."""
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2

    def emit(kind, rows) -> int:
        n = 0
        for row in rows:
            print(json.dumps({"kind": kind, **row}, ensure_ascii=False))
            n += 1
        return n

    try:
        want = getattr(args, "kind", "auto")
        if want != "chunks":
            # Pages are a generator: nothing is written until one is produced,
            # so an empty pages table falls through having printed nothing.
            if emit("page", store.dump_pages(args.docset)) or want == "pages":
                return 0
        emit("chunk", store.dump_chunks(args.docset))
    except BrokenPipeError:
        return 0  # consumer stopped early (hit its cap) -- not an error
    except Exception as e:
        print(f"ERROR: dump failed for docset '{args.docset}': {e}", file=sys.stderr)
        return 2
    return 0


def cmd_delete(args) -> int:
    """Remove a docset from the store. Exit 1 when nothing by that key exists,
    so a caller can tell "deleted" from "never there"."""
    try:
        store = get_store()
    except Exception as e:
        print(f"ERROR: storage backend unavailable: {e}", file=sys.stderr)
        return 2
    try:
        existed = store.delete_docset(args.docset)
        # the facts twin has no life without its raw docset
        twin = facts_key(args.docset) if not args.docset.endswith(FACTS_SUFFIX) else None
        twin_existed = store.delete_docset(twin) if twin else False
    except Exception as e:
        print(f"ERROR: delete failed: {e}", file=sys.stderr)
        return 2
    finally:
        store.close()
    print(json.dumps({"docset": args.docset, "backend": store.backend,
                      "deleted": bool(existed), "facts_deleted": bool(twin_existed)}))
    if not existed:
        print(f"no docset named {args.docset!r}", file=sys.stderr)
        return 1
    return 0


def cmd_list(args) -> int:
    try:
        print(json.dumps(get_store().list_docsets(
            include_facts=getattr(args, "all", False)), indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Semantic docset indexer (web-text-mirror -> Ollama -> vector store)")
    sub = p.add_subparsers(dest="cmd", required=True)

    ix = sub.add_parser("index", help="chunk+embed a mirror file into a docset collection")
    ix.add_argument("mirror", help="web-text-mirror .md file")
    ix.add_argument("--name", help="override docset key (default: <host>__<stem>)")
    ix.add_argument("--model", help="embedding model (default: HUB_EMBED_MODEL)")
    ix.add_argument("--max-fail-pct", type=float, default=5.0,
                    help="abort if more than this %% of chunks fail to embed (default 5)")
    ix.add_argument("--units", action="store_true",
                    help="MIRROR is a docset_refine all_units.jsonl; index it as <name>__facts")
    ix.set_defaults(func=cmd_index)

    q = sub.add_parser("query", help="semantic query against a docset")
    q.add_argument("docset")
    q.add_argument("question")
    q.add_argument("--top", type=int, default=5)
    q.add_argument("--layer", choices=("auto", "facts", "raw"), default="auto",
                   help="auto (default): the facts layer when the docset has one, else raw")
    q.set_defaults(func=cmd_query)

    ki = sub.add_parser("keyword-index", help="build the FTS5 keyword index for a docset layer")
    ki.add_argument("docset")
    ki.add_argument("--layer", choices=("auto", "facts", "raw"), default="auto")
    ki.set_defaults(func=cmd_keyword_index)

    kq = sub.add_parser("keyword", help="BM25 keyword query against a docset (no embedding)")
    kq.add_argument("docset")
    kq.add_argument("question")
    kq.add_argument("--top", type=int, default=5)
    kq.add_argument("--layer", choices=("auto", "facts", "raw"), default="auto")
    kq.add_argument("--mode", choices=("any", "all", "phrase", "raw"), default="any",
                    help="any: OR of terms (default); all: AND; phrase: exact; raw: FTS5 syntax")
    kq.set_defaults(func=cmd_keyword)

    dp = sub.add_parser("dump", help="stream a docset's text as JSONL (kind, url, seq, text)")
    dp.add_argument("docset")
    dp.add_argument("--kind", choices=("auto", "pages", "chunks"), default="auto",
                    help="auto (default): raw pages if stored, else chunks")
    dp.set_defaults(func=cmd_dump)

    ls = sub.add_parser("list", help="list indexed docsets (facts twins folded in)")
    ls.add_argument("--all", action="store_true", help="list <key>__facts docsets as rows too")
    ls.set_defaults(func=cmd_list)

    rm = sub.add_parser("delete", help="remove a docset (vectors, pages, registry row)")
    rm.add_argument("docset")
    rm.set_defaults(func=cmd_delete)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
