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
    return removed
