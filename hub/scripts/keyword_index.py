#!/usr/bin/env python3
"""
keyword_index.py — BM25 keyword index (SQLite FTS5) over the files in hub.db.

Every file row in hub.db has an embedding; this adds a files_fts row beside
it so exact identifiers, error strings and flags are findable without an
embedding call. The table lives in hub.db (see hub_sqlite.init_fts); the
idle-indexer and hub-daemon keep it current once they run this code.

Usage:
  keyword_index.py backfill [--limit N] [--batch 500] [--force]
  keyword_index.py reindex --path PATH [--path PATH ...]
  keyword_index.py prune
  keyword_index.py stats
  keyword_index.py query "<terms>" [--prefix PATH] [--top 10]
                         [--mode any|all|phrase|raw] [--json]

backfill walks the `files` table (not the disk), skips rows whose file is
gone, skips rows that fail today's extension/excluded-dir rules, and skips
rows whose keyword entry is already fresh (size + mtime) unless --force.
It commits every --batch files so live daemons are never locked out long.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import hub_lib
import hub_sqlite

HOME = os.path.expanduser("~")


WATCH_DIRS_FILE = os.path.join(hub_lib.HUB_DIR, "watch_dirs.txt")


def _watch_roots():
    try:
        with open(WATCH_DIRS_FILE) as f:
            roots = [ln.strip().rstrip(os.sep) for ln in f if ln.strip()]
    except OSError:
        roots = []
    return sorted(roots, key=len, reverse=True)  # longest (most specific) first


def _permitted(path, cfg, roots=None):
    """Same filters the embedder applies today (a row may predate a rule,
    e.g. the `[redacted]` exclusion).

    Like idle-indexer's os.walk, only directories BELOW the enclosing watch
    root are checked: ~/.claude is itself a watch root although `.claude`
    is in excluded_dirs, and 120k+ of its files are legitimately indexed."""
    if not hub_lib.is_allowed_file(path, cfg):
        return False
    if roots is None:
        roots = _watch_roots()
    rel = path
    for r in roots:
        if path.startswith(r + os.sep):
            rel = path[len(r) + 1:]
            break
    parts = rel.split(os.sep)[:-1]
    return not any(hub_lib.is_excluded_dir(p, cfg) for p in parts if p)


def backfill(limit=None, batch=500, force=False, log=print):
    cfg = hub_lib.load_config()
    hub_sqlite.init_db()
    with hub_sqlite.get_conn() as conn:
        paths = [r[0] for r in conn.execute("SELECT path FROM files ORDER BY path")]
    fresh = {} if force else hub_sqlite.load_fts_index()
    roots = _watch_roots()
    counts = {"files_rows": len(paths), "indexed": 0, "already_fresh": 0,
              "missing_on_disk": 0, "filtered": 0, "unreadable": 0}
    if limit:
        paths = paths[:limit]
    t0 = time.time()
    pending = []

    def flush():
        if not pending:
            return
        with hub_sqlite.get_conn() as c:
            for p in pending:
                if hub_lib.index_keywords(p, conn=c):
                    counts["indexed"] += 1
                else:
                    counts["unreadable"] += 1
        pending.clear()

    for i, p in enumerate(paths, 1):
        try:
            st = os.stat(p)
        except OSError:
            counts["missing_on_disk"] += 1
            continue
        if not _permitted(p, cfg, roots):
            counts["filtered"] += 1
            continue
        if hub_sqlite.fts_is_fresh(fresh.get(p), st.st_size, st.st_mtime):
            counts["already_fresh"] += 1
            continue
        pending.append(p)
        if len(pending) >= batch:
            flush()
        if i % 10000 == 0:
            log(f"  {i}/{len(paths)} scanned, {counts['indexed']} indexed, "
                f"{time.time() - t0:.0f}s")
    flush()
    counts["seconds"] = round(time.time() - t0, 1)
    return counts


def reindex(paths):
    out = {}
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            with hub_sqlite.get_conn() as c:
                hub_sqlite.init_fts(c)
                out[ap] = "deleted" if hub_sqlite.fts_delete(c, ap) else "missing"
            continue
        out[ap] = "indexed" if hub_lib.index_keywords(ap) else "unreadable"
    return out


def _snippet(path, query, width=160):
    """Best matching line: the whole query as a phrase if any line has it,
    else the first line holding the most query terms. files_fts is
    contentless, so the context comes from the file itself."""
    phrase = query.strip().strip('"').lower()
    terms = [t.strip('"').lower() for t in query.split() if t.strip('"')]
    terms = [t for t in terms if t.upper() not in ("OR", "AND", "NOT")]
    best, best_hits = None, 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                low = line.lower()
                if phrase and phrase in low:
                    return f"L{n}: {line.strip()[:width]}"
                hits = sum(t in low for t in terms)
                if hits > best_hits:
                    best, best_hits = (n, line.strip()), hits
                if n > 20000:
                    break
    except OSError:
        pass
    return f"L{best[0]}: {best[1][:width]}" if best else ""


def query(q, prefix=None, top=10, mode="any", snippets=True):
    if prefix:
        prefix = os.path.abspath(os.path.expanduser(prefix))
    hits = hub_sqlite.fts_query(q, top=top, prefix=prefix, mode=mode)
    if snippets:
        for h in hits:
            h["snippet"] = _snippet(h["path"], q)
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backfill", help="index every hub.db file row that exists on disk")
    b.add_argument("--limit", type=int)
    b.add_argument("--batch", type=int, default=500)
    b.add_argument("--force", action="store_true", help="rewrite rows even when fresh")
    r = sub.add_parser("reindex", help="(re)index specific paths; deletes rows for gone paths")
    r.add_argument("--path", action="append", required=True)
    sub.add_parser("prune", help="drop keyword rows whose file no longer exists")
    sub.add_parser("stats", help="row counts")
    q = sub.add_parser("query", help="BM25-ranked paths")
    q.add_argument("terms")
    q.add_argument("--prefix")
    q.add_argument("--top", type=int, default=10)
    q.add_argument("--mode", choices=("any", "all", "phrase", "raw"), default="any")
    q.add_argument("--json", action="store_true")
    q.add_argument("--no-snippet", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "backfill":
        print(json.dumps(backfill(a.limit, a.batch, a.force), indent=2))
    elif a.cmd == "reindex":
        print(json.dumps(reindex(a.path), indent=2))
    elif a.cmd == "prune":
        print(json.dumps({"pruned": hub_sqlite.fts_prune()}))
    elif a.cmd == "stats":
        print(json.dumps(hub_sqlite.fts_stats(), indent=2))
    elif a.cmd == "query":
        hits = query(a.terms, a.prefix, a.top, a.mode, snippets=not a.no_snippet)
        if a.json:
            print(json.dumps(hits, indent=2))
            return 0
        print(f"\n{'BM25':>8}  File")
        print(f"{'─'*8}  {'─'*60}")
        for h in hits:
            print(f"{h['score']:8.3f}  {h['path'].replace(HOME, '~')}")
            if h.get("snippet"):
                print(f"{'':8}    {h['snippet']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
