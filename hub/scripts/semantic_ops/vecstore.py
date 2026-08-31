"""Minimal SQLite vector store shared by semantic_ops corpora (logs, git, …).

Mirrors docset_indexer.SqliteStore conventions: WAL, JSON-encoded vectors,
one lock around every db operation, dimension-mismatched vectors skipped at
query time (different embedding model — cosine meaningless).
"""
from __future__ import annotations

import json
import math
import sqlite3
import threading
from pathlib import Path


class VecStore:
    def __init__(self, path: str | Path):
        self._lock = threading.Lock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            " id TEXT PRIMARY KEY, ref TEXT, ts REAL, kind TEXT,"
            " text TEXT, vector TEXT, model TEXT, meta TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS marks (source TEXT PRIMARY KEY, mark TEXT)"
        )

    def existing_ids(self, ids: list[str]) -> set[str]:
        out: set[str] = set()
        with self._lock:
            for i in range(0, len(ids), 500):
                batch = ids[i:i + 500]
                ph = ",".join("?" * len(batch))
                out.update(r[0] for r in self.db.execute(
                    f"SELECT id FROM chunks WHERE id IN ({ph})", batch))  # noqa: S608
        return out

    def upsert(self, rows: list[dict]) -> int:
        """Insert-or-replace rows; returns how many ids were NEW."""
        ids = [r["id"] for r in rows]
        existing = self.existing_ids(ids)
        with self._lock, self.db:
            self.db.executemany(
                "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?)",
                [(r["id"], r["ref"], float(r["ts"]), r["kind"], r["text"],
                  json.dumps(r["vector"]), r["model"],
                  json.dumps(r.get("meta") or {})) for r in rows],
            )
        return len(set(ids) - existing)

    def query(self, qvec: list[float], top: int = 10,
              kinds: tuple[str, ...] | None = None) -> list[dict]:
        sql = "SELECT id, ref, ts, kind, text, vector, meta FROM chunks"
        params: tuple = ()
        if kinds:
            sql += f" WHERE kind IN ({','.join('?' * len(kinds))})"
            params = tuple(kinds)
        with self._lock:
            rows = self.db.execute(sql, params).fetchall()
        qmag = math.sqrt(sum(x * x for x in qvec)) or 1.0
        scored = []
        for id_, ref, ts, kind, text, vec_json, meta_json in rows:
            v = json.loads(vec_json)
            if len(v) != len(qvec):
                continue
            mag = math.sqrt(sum(x * x for x in v)) or 1.0
            sim = sum(a * b for a, b in zip(qvec, v, strict=True)) / (qmag * mag)
            scored.append((sim, id_, ref, ts, kind, text, meta_json))
        scored.sort(reverse=True)
        return [{"score": round(s, 4), "id": i, "ref": r, "ts": t, "kind": k,
                 "text": x, "meta": json.loads(mj)}
                for s, i, r, t, k, x, mj in scored[:top]]

    def rows_between(self, ts0: float, ts1: float,
                     kinds: tuple[str, ...] | None = None) -> list[dict]:
        sql = "SELECT id, ref, ts, kind, text, meta FROM chunks WHERE ts > ? AND ts <= ?"
        params: list = [ts0, ts1]
        if kinds:
            sql += f" AND kind IN ({','.join('?' * len(kinds))})"
            params += list(kinds)
        sql += " ORDER BY ts"
        with self._lock:
            rows = self.db.execute(sql, params).fetchall()
        return [{"id": i, "ref": r, "ts": t, "kind": k, "text": x,
                 "meta": json.loads(mj)} for i, r, t, k, x, mj in rows]

    def delete_ref_prefix(self, prefix: str) -> int:
        """Remove rows whose ref starts with prefix (e.g. a re-chunked file)."""
        with self._lock, self.db:
            cur = self.db.execute(
                "DELETE FROM chunks WHERE ref LIKE ? || '%'", (prefix,))
        return cur.rowcount

    def get_mark(self, source: str) -> str | None:
        with self._lock:
            row = self.db.execute(
                "SELECT mark FROM marks WHERE source=?", (source,)).fetchone()
        return row[0] if row else None

    def set_mark(self, source: str, mark: str) -> None:
        with self._lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO marks VALUES (?,?)", (source, mark))

    def count(self) -> int:
        with self._lock:
            return self.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self.db.close()
