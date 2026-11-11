"""A shared, compact float32 view of the file vectors in a hub SQLite index.

Refresh fingerprints stored values and decodes only new or changed vectors.
Content hashes can be reused after garbage collection, even between queries.
Comparing fingerprints within the read snapshot prevents stale hash reuse.
No configuration, model client or background indexing job is loaded here.

Usage (library, no CLI):
    from embedding_matrix import shared_matrix
    hits = shared_matrix("/path/to/hub.db").search([1.0, 0.0], top_k=10)
"""
from __future__ import annotations

import heapq
import hashlib
import json
import os
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

import numpy as np

CHUNK = 500
MIN_COMPACT_ROWS = 1000
COMPACT_FRACTION = 0.25


def _vector(value) -> np.ndarray | None:
    try:
        raw = np.asarray(value)
        if raw.ndim != 1 or not raw.size or raw.dtype.kind not in "iuf":
            return None
        with np.errstate(over="ignore", invalid="ignore"):
            vector = raw.astype(np.float32)
        return vector if np.isfinite(vector).all() else None
    except (TypeError, ValueError, OverflowError):
        return None


def parse_vector(text: str) -> np.ndarray | None:
    """Parse a nonempty JSON numeric array; reject malformed/nonfinite values."""
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, (int, float)) for item in value
    ):
        return None
    return _vector(value)


def _normalized(vector: np.ndarray) -> np.ndarray:
    # Compute the norm in float64 so finite float32 extremes do not overflow.
    wide = vector.astype(np.float64)
    return (wide / (float(np.linalg.norm(wide)) or 1.0)).astype(np.float32)


def _fingerprint(model, text) -> bytes:
    if isinstance(text, str):
        payload = b"s" + text.encode()
    elif isinstance(text, bytes):
        payload = b"b" + text
    else:
        payload = b"o" + repr(text).encode()
    return hashlib.sha256(repr(model).encode() + b"\0" + payload).digest()


class _Block:
    def __init__(self, dim: int):
        self.n = 0
        self.mat = np.empty((64, dim), dtype=np.float32)
        self.hashes: list[str | None] = []
        self.paths: list[str | None] = []
        self.live = np.zeros(0, dtype=bool)

    def append(self, hashes: list[str], vectors: list[np.ndarray]) -> None:
        need = self.n + len(vectors)
        if need > len(self.mat):
            grown = np.empty((max(need, len(self.mat) * 2), self.mat.shape[1]), dtype=np.float32)
            grown[:self.n] = self.mat[:self.n]
            self.mat = grown
        for index, vector in enumerate(vectors, self.n):
            self.mat[index] = _normalized(vector)
        self.n = need
        self.hashes.extend(hashes)

    def relabel(self, paths: dict[str, str]) -> int:
        # Retire orphan rows permanently. A later reinsert of that hash must
        # reload its vector rather than resurrecting a row removed by GC.
        self.hashes = [h if h in paths else None for h in self.hashes]
        self.paths = [paths.get(h) for h in self.hashes]
        self.live = np.fromiter((p is not None for p in self.paths), bool, count=self.n)
        return self.n - int(self.live.sum())

    def retire(self, hashes: set[str]) -> None:
        self.hashes = [None if h in hashes else h for h in self.hashes]


class EmbeddingMatrix:
    def __init__(self, db_path: str | os.PathLike):
        self.db_path = os.path.abspath(os.path.expanduser(os.fspath(db_path)))
        self._lock = threading.Lock()
        self._reset()

    def _reset(self) -> None:
        self._blocks: dict[int, _Block] = {}
        self._known: dict[str, bytes] = {}
        self._signature: tuple | None = None

    def _db_signature(self) -> tuple:
        signature = []
        for suffix in ("", "-wal"):
            try:
                stat = os.stat(self.db_path + suffix)
                signature.append((stat.st_dev, stat.st_ino, stat.st_mtime_ns,
                                  stat.st_ctime_ns, stat.st_size))
            except FileNotFoundError:
                signature.append(None)
        return tuple(signature)

    def refresh(self, force: bool = False) -> None:
        """Observe database/WAL writes; force reloads even unchanged values."""
        with self._lock:
            self._refresh_locked(force)

    def _refresh_locked(self, force: bool = False) -> None:
        signature = self._db_signature()
        if signature[0] is None:
            self._reset()
            return
        if not force and signature == self._signature:
            return
        if force or (self._signature and signature[0][:2] != self._signature[0][:2]):
            self._reset()
        # Read only: a missing database must never be created by a search.
        uri = Path(self.db_path).as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=30.0)) as conn:
            conn.execute("BEGIN")  # files and vectors come from one SQLite snapshot
            paths = {h: path for path, h in conn.execute("SELECT path, hash FROM files")}
            # A hash/model/rowid can all be reused after GC between queries.
            # Verify stored values on each changed snapshot without decoding
            # cached vectors. This scan trades read I/O for correct invalidation.
            fingerprints = {
                h: _fingerprint(model, text)
                for h, model, text in conn.execute("SELECT hash, model, vector FROM embeddings")
                if h in paths
            }
            stale = {h for h, value in self._known.items() if fingerprints.get(h) != value}
            for block in self._blocks.values():
                block.retire(stale)
            for h in stale:
                del self._known[h]
            fresh = [h for h in paths if h not in self._known]
            for offset in range(0, len(fresh), CHUNK):
                self._load_chunk(conn, fresh[offset:offset + CHUNK])
        orphans = sum(block.relabel(paths) for block in self._blocks.values())
        total = sum(block.n for block in self._blocks.values())
        if orphans >= MIN_COMPACT_ROWS and orphans > COMPACT_FRACTION * total:
            self._reset()
            self._refresh_locked()
            return
        self._signature = signature

    def _load_chunk(self, conn: sqlite3.Connection, hashes: list[str]) -> None:
        marks = ",".join("?" * len(hashes))
        by_dim: dict[int, tuple[list[str], list[np.ndarray]]] = {}
        for content_hash, model, text in conn.execute(
            f"SELECT hash, model, vector FROM embeddings WHERE hash IN ({marks})", hashes
        ):
            self._known[content_hash] = _fingerprint(model, text)
            vector = parse_vector(text)
            if vector is not None:
                keys, vectors = by_dim.setdefault(int(vector.size), ([], []))
                keys.append(content_hash)
                vectors.append(vector)
        for dim, (keys, vectors) in by_dim.items():
            self._blocks.setdefault(dim, _Block(dim)).append(keys, vectors)
        # Missing embedding rows remain unseen and are retried on a later write.

    def search(self, qvec, top_k: int = 10) -> list[tuple[float, str]]:
        """Return cosine/path pairs, descending by score then descending path.

        Float32 arithmetic can differ from Python double cosine near a tie.
        Exact ties, including the selection boundary, retain the old path order.
        Empty, malformed or nonfinite queries and nonpositive limits return [].
        """
        if top_k <= 0:
            return []
        query = _vector(qvec)
        if query is None:
            return []
        with self._lock:
            self._refresh_locked()
            block = self._blocks.get(int(query.size))
            if block is None:
                return []
            k = min(top_k, int(block.live.sum()))
            if not k:
                return []
            scores = block.mat[:block.n] @ _normalized(query)
            scores[~block.live] = -np.inf
            # argpartition is unstable. Include the entire boundary tie before
            # applying the original descending (score, path) tuple ordering.
            threshold = np.partition(scores, len(scores) - k)[len(scores) - k]
            candidates = np.flatnonzero(scores >= threshold)
            return heapq.nlargest(k, ((float(scores[i]), block.paths[i]) for i in candidates))

    def stats(self) -> dict:
        """Report allocated vectors, dimensions and matrix bytes without I/O."""
        with self._lock:
            return {"vectors": sum(block.n for block in self._blocks.values()),
                    "dims": sorted(self._blocks),
                    "bytes": sum(block.mat.nbytes for block in self._blocks.values())}


_shared: dict[str, EmbeddingMatrix] = {}
_shared_lock = threading.Lock()


def shared_matrix(db_path: str | os.PathLike) -> EmbeddingMatrix:
    """One thread-safe matrix per normalized absolute database path per process."""
    key = os.path.abspath(os.path.expanduser(os.fspath(db_path)))
    with _shared_lock:
        if key not in _shared:
            _shared[key] = EmbeddingMatrix(key)
        return _shared[key]
