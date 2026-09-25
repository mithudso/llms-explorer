#!/usr/bin/env python3
"""
hub_sqlite.py — SQLite data access layer for Global AI Hub
Replaces the old JSON-based UNIVERSAL-INDEX/EMBEDDINGS with a concurrent WAL-mode SQLite DB.
"""

import contextlib
import sqlite3
import os
import json
import time

HUB_DIR = os.path.expanduser("~/.global-ai-hub")
DB_FILE = os.path.join(HUB_DIR, "hub.db")

@contextlib.contextmanager
def get_conn():
    """Context manager yielding a connection that is always CLOSED on exit.

    The previous version returned a bare connection: `with conn:` only ends
    the transaction, so every call leaked one fd. Under the high-rate
    indexing endpoints the daemon hit the 256-fd launchd limit within
    minutes ("unable to open database file", reset connections). Commit/
    rollback semantics match the old transaction context manager exactly.
    """
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                hash TEXT,
                size INTEGER,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                hash TEXT PRIMARY KEY,
                model TEXT,
                vector TEXT
            );
            CREATE TABLE IF NOT EXISTS concepts (
                file_path TEXT,
                concept TEXT,
                group_name TEXT,
                PRIMARY KEY (file_path, concept)
            );
            CREATE TABLE IF NOT EXISTS tier_links (
                session_id TEXT,
                concept TEXT,
                embedding_hash TEXT,
                PRIMARY KEY (session_id, concept, embedding_hash)
            );
            CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
        """)
        init_fts(conn)

def load_embeddings():
    """Return dictionary of {path: {'hash': hash, 'embedding': vector}} for compatibility."""
    init_db()
    with get_conn() as conn:
        files = conn.execute("SELECT path, hash FROM files").fetchall()
        h2p = {r["hash"]: r["path"] for r in files}
        
        rows = conn.execute("SELECT hash, vector FROM embeddings").fetchall()
        result = {}
        for r in rows:
            path = h2p.get(r["hash"])
            if path:
                result[path] = {"hash": r["hash"], "embedding": json.loads(r["vector"])}
        return result

def load_index():
    """Return dictionary of {path: {"hash": hash, "size": size}} for idle-indexer check."""
    init_db()
    with get_conn() as conn:
        rows = conn.execute("SELECT path, hash, size FROM files").fetchall()
        return {r["path"]: {"hash": r["hash"], "size": r["size"]} for r in rows}

def upsert_file(path, content_hash, size, embedding_vector, model):
    """Insert or update a file and its embedding."""
    init_db()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    vector_str = json.dumps(embedding_vector)
    
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO files (path, hash, size, updated_at) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET 
                hash=excluded.hash, 
                size=excluded.size, 
                updated_at=excluded.updated_at
        """, (path, content_hash, size, now))
        
        conn.execute("""
            INSERT OR IGNORE INTO embeddings (hash, model, vector)
            VALUES (?, ?, ?)
        """, (content_hash, model, vector_str))

def gc_stale_entries():
    """Remove files that no longer exist on disk. Return number of removed rows."""
    init_db()
    removed = 0
    with get_conn() as conn:
        rows = conn.execute("SELECT path FROM files").fetchall()
        for row in rows:
            path = row["path"]
            if not os.path.exists(path):
                conn.execute("DELETE FROM files WHERE path = ?", (path,))
                removed += 1

        # Cleanup orphan embeddings (hash not in files table)
        conn.execute("""
            DELETE FROM embeddings
            WHERE hash NOT IN (SELECT hash FROM files)
        """)
    fts_prune()
    return removed


# ---------------------------------------------------------------------------
# Keyword layer (FTS5 / BM25) beside the embeddings
# ---------------------------------------------------------------------------
# files_fts is CONTENTLESS (content=''): 263k files are ~17 GB on disk, so
# storing a second copy of the text in hub.db is not an option. The price is
# that snippet()/highlight() return nothing; callers read the file itself for
# context (see keyword_index.py). contentless_delete=1 (SQLite >= 3.43) makes
# DELETE and INSERT OR REPLACE work on a contentless table.
#
# files_fts_map owns the rowid. The files table's implicit rowid is not
# stable (VACUUM may renumber it), so the FTS rowid is keyed off this map.
# size + mtime decide freshness: the embedding hash covers only the first
# max_content_chars, so it cannot tell whether the tail of a file changed.
#
# Tokenizer: unicode61 splits on `_`, `-` and `.`, the same choice as the
# docset keyword layer (docset_indexer.py). fts_match() double-quotes each
# term, so `upsert_file` or `hub_sqlite.get_conn` still match as exact
# phrases, and `upsert` alone also finds `upsert_file`. porter adds stemming
# so prose queries (`indexing` ~ `index`) recall more.

FTS_TOKENIZE = "porter unicode61 remove_diacritics 2"


def init_fts(conn):
    conn.executescript(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
            body, content='', contentless_delete=1,
            tokenize='{FTS_TOKENIZE}'
        );
        CREATE TABLE IF NOT EXISTS files_fts_map (
            rowid INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            size INTEGER,
            mtime REAL,
            chars INTEGER,
            indexed_at TEXT
        );
    """)


def fts_match(query, mode="any"):
    """User query -> FTS5 MATCH expression (same rules as docset_indexer).

    Every term is double-quoted so `--append-system-prompt` becomes a phrase
    of its sub-tokens instead of FTS5 operators. mode: any (OR, default),
    all (AND), phrase (exact sequence), raw (caller-written MATCH syntax)."""
    if mode == "raw":
        return query
    q = query.replace('"', '""').strip()
    if mode == "phrase":
        return f'"{q}"'
    terms = [f'"{w}"' for w in q.split() if w]
    if not terms:
        return '""'
    return (" AND " if mode == "all" else " OR ").join(terms)


def fts_upsert(conn, path, text, size, mtime):
    """Insert or replace one file's keyword row inside the caller's transaction."""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Savepoint: a batch caller shares one transaction across hundreds of
    # files; a failure here must not leave a map row without its fts row.
    conn.execute("SAVEPOINT fts_upsert")
    try:
        row = conn.execute("SELECT rowid FROM files_fts_map WHERE path=?", (path,)).fetchone()
        if row:
            rid = row[0]
            conn.execute("DELETE FROM files_fts WHERE rowid=?", (rid,))
            conn.execute("UPDATE files_fts_map SET size=?, mtime=?, chars=?, indexed_at=?"
                         " WHERE rowid=?", (size, mtime, len(text), now, rid))
        else:
            rid = conn.execute(
                "INSERT INTO files_fts_map (path, size, mtime, chars, indexed_at)"
                " VALUES (?,?,?,?,?)",
                (path, size, mtime, len(text), now)).lastrowid
        conn.execute("INSERT INTO files_fts (rowid, body) VALUES (?, ?)", (rid, text))
    except Exception:
        conn.execute("ROLLBACK TO fts_upsert")
        conn.execute("RELEASE fts_upsert")
        raise
    conn.execute("RELEASE fts_upsert")


def fts_delete(conn, path):
    row = conn.execute("SELECT rowid FROM files_fts_map WHERE path=?", (path,)).fetchone()
    if not row:
        return False
    conn.execute("DELETE FROM files_fts WHERE rowid=?", (row[0],))
    conn.execute("DELETE FROM files_fts_map WHERE rowid=?", (row[0],))
    return True


def load_fts_index():
    """{path: (size, mtime)} for every path that has a keyword row."""
    init_db()
    with get_conn() as conn:
        init_fts(conn)
        return {r[0]: (r[1], r[2]) for r in
                conn.execute("SELECT path, size, mtime FROM files_fts_map")}


def fts_is_fresh(entry, size, mtime):
    """entry is a (size, mtime) pair from files_fts_map, or None."""
    return (bool(entry) and entry[0] == size and entry[1] is not None
            and abs(entry[1] - mtime) < 1e-3)


def fts_prune(exists=os.path.exists):
    """Drop keyword rows whose file is gone from disk. Returns the count."""
    init_db()
    removed = 0
    with get_conn() as conn:
        init_fts(conn)
        rows = conn.execute("SELECT rowid, path FROM files_fts_map").fetchall()
        for rid, path in rows:
            if not exists(path):
                conn.execute("DELETE FROM files_fts WHERE rowid=?", (rid,))
                conn.execute("DELETE FROM files_fts_map WHERE rowid=?", (rid,))
                removed += 1
    return removed


def fts_query(query, top=10, prefix=None, mode="any"):
    """BM25-ranked [{"score", "path"}]; higher score = better match."""
    init_db()
    match = fts_match(query, mode)
    sql = ("SELECT m.path, bm25(files_fts) AS s FROM files_fts"
           " JOIN files_fts_map m ON m.rowid = files_fts.rowid"
           " WHERE files_fts MATCH ?")
    args = [match]
    if prefix:
        # A directory prefix means that directory: ~/dev/repo must not
        # also match the sibling ~/dev/repo-main.
        esc = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        if prefix.endswith(os.sep):
            sql += " AND m.path LIKE ? ESCAPE '\\'"
            args.append(esc + "%")
        else:
            # Exact path, or anything inside it as a directory; never a sibling
            # like ~/dev/repo-main. No filesystem probe on a caller-supplied path.
            sql += " AND (m.path = ? OR m.path LIKE ? ESCAPE '\\')"
            args.extend([prefix, esc + os.sep + "%"])
    sql += " ORDER BY s LIMIT ?"
    args.append(int(top))
    with get_conn() as conn:
        init_fts(conn)
        rows = conn.execute(sql, args).fetchall()
    return [{"score": round(-r[1], 4), "path": r[0]} for r in rows]


def fts_stats():
    init_db()
    with get_conn() as conn:
        init_fts(conn)
        def c(q):
            return conn.execute(q).fetchone()[0]
        return {
            "files_rows": c("SELECT COUNT(*) FROM files"),
            "fts_rows": c("SELECT COUNT(*) FROM files_fts_map"),
            "fts_files_covered": c("SELECT COUNT(*) FROM files f"
                                   " JOIN files_fts_map m ON m.path = f.path"),
            "fts_chars": c("SELECT COALESCE(SUM(chars), 0) FROM files_fts_map"),
            "fts_only_rows": c("SELECT COUNT(*) FROM files_fts_map m"
                               " WHERE NOT EXISTS (SELECT 1 FROM files f WHERE f.path = m.path)"),
            "last_indexed_at": c("SELECT MAX(indexed_at) FROM files_fts_map"),
        }
