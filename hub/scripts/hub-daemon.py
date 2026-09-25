#!/usr/bin/env python3
"""
hub-daemon.py — Event bus and background indexer.
Listens on 127.0.0.1:8000 for file change events.
Also runs the idle-indexer loop in a background thread.

Usage:
  hub-daemon.py            # no arguments; runs until SIGTERM
Start detached from the hub-manager Health tab (t on the hub-daemon row);
logs to ~/.global-ai-hub/hub-daemon.log.

Endpoints:
  POST /index       {path}                  index one file (background)
  POST /index-tree  {root, max_files?}      index a repo/dir, freshest first
  POST /search      {query, prefix?, top?}  semantic file search
  POST /keyword     {query, prefix?, top?, mode?}  BM25 keyword file search
  GET  /health                              liveness + store counts
"""

import json
import math
import os
import sys
import threading
import time

from fastapi import FastAPI, BackgroundTasks
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))
import hub_lib
import hub_sqlite

log = hub_lib.get_logger("hub-daemon", os.path.join(hub_lib.HUB_DIR, "hub-daemon.log"))
cfg = hub_lib.load_config()

HOME = os.path.expanduser("~")
STARTED_AT = time.time()
# System/vendor trees must never be indexed: an earlier feeder once shoveled
# all of /Applications into the store. Every path written to the index must
# live under $HOME and outside these subtrees.
DENY_HOME_SUBTREES = ("Library", "Applications", ".Trash")
# Hidden top-level dirs under $HOME are vendor/cache trees (.vscode, .cargo,
# .npm, ...) except the knowledge homes the hub actually serves.
ALLOWED_HOME_DOTDIRS = {".global-ai-hub", ".claude", ".gemini", ".napmem", ".remember"}
# macOS firmlink alias for the data volume: normalize so guards and stored
# paths use the canonical /Users/... form.
FIRMLINK_PREFIX = "/System/Volumes/Data"
SEARCH_ROW_CAP = 8000
TREE_DEFAULT_MAX = 400


def _normalize(abs_path: str) -> str:
    if abs_path.startswith(FIRMLINK_PREFIX + "/"):
        return abs_path[len(FIRMLINK_PREFIX):]
    return abs_path


def _path_permitted(abs_path: str) -> bool:
    """Home-anchored guard applied to every path entering the index,
    regardless of which endpoint or loop submitted it."""
    if not abs_path.startswith(HOME + os.sep):
        return False
    rel = abs_path[len(HOME) + 1:]
    parts = rel.split(os.sep)
    if parts and parts[0] in DENY_HOME_SUBTREES:
        return False
    if parts and parts[0].startswith(".") and parts[0] not in ALLOWED_HOME_DOTDIRS:
        return False
    return not any(hub_lib.is_excluded_dir(p, cfg) for p in parts[:-1])


def process_file(abs_path):
    abs_path = _normalize(abs_path)
    if not _path_permitted(abs_path):
        return False
    if not hub_lib.is_allowed_file(abs_path, cfg):
        return False
    if not os.path.exists(abs_path):
        return False
    try:
        current_size = os.path.getsize(abs_path)
    except OSError:
        return False
    if current_size == 0:
        return False

    text = hub_lib.get_text_content(abs_path)
    if not text or not text.strip():
        return False
    content_hash = hub_lib.compute_hash(text)

    # Check if already embedded
    hub_sqlite.init_db()
    with hub_sqlite.get_conn() as conn:
        row = conn.execute("SELECT hash, size FROM files WHERE path=?", (abs_path,)).fetchone()
        kw = conn.execute("SELECT size, mtime FROM files_fts_map WHERE path=?", (abs_path,)).fetchone()
    try:
        kw_fresh = hub_sqlite.fts_is_fresh(tuple(kw) if kw else None,
                                           current_size, os.path.getmtime(abs_path))
    except OSError:
        return False
    if row and row["hash"] == content_hash and row["size"] == current_size:
        # Embedding up to date; keyword row may still be missing or stale.
        if not kw_fresh:
            hub_lib.index_keywords(abs_path)
        return False

    emb = hub_lib.fetch_embedding(text)
    if emb:
        hub_sqlite.upsert_file(abs_path, content_hash, current_size, emb, cfg["embed_model"])
        hub_lib.index_keywords(abs_path)
        return True
    return False

app = FastAPI()

@app.post("/index")
def api_index_file(payload: dict, background_tasks: BackgroundTasks):
    path = payload.get("path")
    if path:
        abs_path = _normalize(os.path.abspath(path))
        # Rejected paths are not logged: a misconfigured bulk feeder once
        # produced tens of thousands of these lines per pass.
        if not _path_permitted(abs_path):
            return {"status": "rejected", "path": abs_path}
        # Run in background so we don't block the API
        background_tasks.add_task(process_file_with_logging, abs_path)
        return {"status": "accepted", "path": abs_path}
    return {"status": "error", "message": "No path provided"}


@app.post("/index-tree")
def api_index_tree(payload: dict, background_tasks: BackgroundTasks):
    """Walk a directory and index every allowed file, freshest first.
    Budget-capped per call so one huge repo can't monopolize the daemon."""
    root = payload.get("root")
    if not root:
        return {"status": "error", "message": "No root provided"}
    root = os.path.realpath(os.path.expanduser(str(root)))
    # Inline home-anchor (also enforced by _path_permitted) so static analysis
    # sees the path is confined before it touches the filesystem.
    if not root.startswith(HOME + os.sep):
        return {"status": "error", "message": "root not permitted"}
    if not os.path.isdir(root) or not _path_permitted(os.path.join(root, "probe")):
        return {"status": "error", "message": f"root not permitted: {root}"}
    try:
        max_files = min(int(payload.get("max_files", TREE_DEFAULT_MAX)), 2000)
    except (TypeError, ValueError):
        max_files = TREE_DEFAULT_MAX

    candidates = []
    for walk_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not hub_lib.is_excluded_dir(d, cfg)]
        for f in files:
            fp = os.path.join(walk_root, f)
            if hub_lib.is_allowed_file(fp, cfg) and _path_permitted(fp):
                try:
                    candidates.append((os.path.getmtime(fp), fp))
                except OSError:
                    continue
    candidates.sort(reverse=True)
    batch = [fp for _, fp in candidates[:max_files]]
    background_tasks.add_task(process_tree_with_logging, root, batch)
    return {"status": "accepted", "root": root,
            "queued": len(batch), "found": len(candidates)}


@app.post("/search")
def api_search(payload: dict):
    """Semantic file search: embed the query, cosine against stored vectors.
    `prefix` (a path prefix, e.g. a repo root) bounds the candidate set so
    per-prompt hooks stay fast even with a large store."""
    query = (payload.get("query") or "").strip()
    if not query:
        return {"status": "error", "message": "No query provided"}
    try:
        top = min(int(payload.get("top", 5)), 25)
    except (TypeError, ValueError):
        top = 5
    prefix = payload.get("prefix") or HOME
    prefix = os.path.abspath(os.path.expanduser(prefix))

    qvec = hub_lib.fetch_embedding(query)
    if not qvec:
        return {"status": "error", "message": "query embedding unavailable"}

    hub_sqlite.init_db()
    with hub_sqlite.get_conn() as conn:
        rows = conn.execute(
            "SELECT f.path, e.vector FROM files f JOIN embeddings e ON f.hash = e.hash "
            "WHERE f.path LIKE ? LIMIT ?",
            (prefix + "%", SEARCH_ROW_CAP),
        ).fetchall()

    qn = math.sqrt(sum(x * x for x in qvec)) or 1.0
    scored = []
    for row in rows:
        try:
            vec = json.loads(row["vector"])
        except (TypeError, ValueError):
            continue
        if len(vec) != len(qvec):
            continue  # row from a different embedding-model generation
        dot = sum(a * b for a, b in zip(qvec, vec))
        vn = math.sqrt(sum(x * x for x in vec)) or 1.0
        scored.append((dot / (qn * vn), row["path"]))
    scored.sort(reverse=True)
    return {"status": "ok", "query": query, "prefix": prefix,
            "candidates": len(rows),
            "matches": [{"score": round(s, 4), "path": p} for s, p in scored[:top]]}


@app.post("/keyword")
def api_keyword(payload: dict):
    """BM25 keyword file search over files_fts (no embedding call).
    mode: any (default) | all | phrase | raw FTS5 MATCH syntax."""
    query = (payload.get("query") or "").strip()
    if not query:
        return {"status": "error", "message": "No query provided"}
    try:
        top = min(int(payload.get("top", 10)), 50)
    except (TypeError, ValueError):
        top = 10
    mode = payload.get("mode") or "any"
    if mode not in ("any", "all", "phrase", "raw"):
        return {"status": "error", "message": "mode must be any, all, phrase or raw"}
    prefix = payload.get("prefix") or HOME
    prefix = os.path.abspath(os.path.expanduser(prefix))
    try:
        matches = hub_sqlite.fts_query(query, top=top, prefix=prefix, mode=mode)
    except Exception:  # malformed raw MATCH syntax; detail stays out of the response
        return {"status": "error", "message": "query could not be executed (check mode/syntax)"}
    return {"status": "ok", "query": query, "prefix": prefix, "mode": mode,
            "matches": matches}


@app.get("/health")
def api_health():
    hub_sqlite.init_db()
    with hub_sqlite.get_conn() as conn:
        n_files = conn.execute("SELECT COUNT(*) c FROM files").fetchone()["c"]
        n_vecs = conn.execute("SELECT COUNT(*) c FROM embeddings").fetchone()["c"]
        n_kw = conn.execute("SELECT COUNT(*) c FROM files_fts_map").fetchone()["c"]
    return {"status": "ok", "files": n_files, "embeddings": n_vecs, "keyword_rows": n_kw,
            "model": cfg.get("embed_model"),
            "uptime_s": int(time.time() - STARTED_AT)}


def process_file_with_logging(abs_path):
    if process_file(abs_path):
        log.info(f"Updated index for {abs_path}")


def process_tree_with_logging(root, batch):
    done = 0
    for fp in batch:
        try:
            if process_file(fp):
                done += 1
        except Exception as exc:
            log.warning(f"index-tree: {fp}: {exc}")
    log.info(f"index-tree {root}: {done}/{len(batch)} files (re)indexed")


def fastapi_server_loop():
    log.info("Starting FastAPI server on 127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)

def idle_indexer_loop():
    sleep_between = cfg.get("sleep_between_files", 2.0)
    sleep_idle = cfg.get("sleep_idle_check", 60.0)
    gc_interval = 10
    pass_count = 0

    def is_system_idle():
        try:
            load1, _, _ = os.getloadavg()
            return load1 < cfg.get("idle_threshold", 2.0)
        except Exception:
            return True

    def get_watch_dirs():
        wfile = os.path.join(hub_lib.HUB_DIR, "watch_dirs.txt")
        if not os.path.exists(wfile):
            return [os.path.expanduser("~/dev")]
        with open(wfile, "r") as f:
            return [line.strip() for line in f if line.strip() and os.path.isdir(line.strip())]

    while True:
        if not is_system_idle():
            time.sleep(sleep_idle)
            continue

        log.info("System idle, starting background pass...")
        watch_dirs = get_watch_dirs()
        for wdir in watch_dirs:
            for root, dirs, files in os.walk(wdir):
                dirs[:] = [d for d in dirs if not hub_lib.is_excluded_dir(d, cfg)]
                for f in files:
                    filepath = os.path.join(root, f)
                    if not is_system_idle():
                        break
                    if process_file(os.path.abspath(filepath)):
                        time.sleep(sleep_between)
                else:
                    continue
                break
        pass_count += 1
        if pass_count % gc_interval == 0:
            removed = hub_lib.gc_stale_entries()
            if removed:
                log.info(f"GC removed {removed} stale entries.")
        time.sleep(sleep_idle * 5)

def main():
    hub_sqlite.init_db()
    t1 = threading.Thread(target=fastapi_server_loop, daemon=True)
    t2 = threading.Thread(target=idle_indexer_loop, daemon=True)
    t1.start()
    t2.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        log.info("Daemon shutting down.")

if __name__ == "__main__":
    main()
