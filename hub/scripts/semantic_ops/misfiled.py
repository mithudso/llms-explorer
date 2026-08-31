"""Misfiled-file detector (idea #9).

Every indexed directory has a centroid — the average of its files' vectors.
A file that sits much closer to a different directory's centroid than to its
own is probably in the wrong folder. Uses only vectors already in hub.db, so
it costs no embedding calls.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import hub_lib
from search import cosine_similarity

from semantic_ops.fuse import Hit

MIN_FILES = 4
MARGIN = 0.10
# Fallback-only guard: the pure-Python path is O(files x dirs x dims), which is
# hopeless on the real corpus (measured: 49k files x 4.8k dirs x 768 dims).
# With numpy present we do the whole thing as a chunked matmul instead.
FALLBACK_MAX_DIRS = 200
CHUNK = 2048

_log = hub_lib.get_logger("semantic_ops")


def directory_centroids(min_files: int = MIN_FILES) -> dict[str, list[float]]:
    """Average vector per parent directory with at least min_files entries."""
    groups: dict[str, list[list[float]]] = {}
    for path, entry in hub_lib.load_embeddings().items():
        vec = entry.get("embedding")
        if not vec:
            continue
        groups.setdefault(str(Path(path).parent), []).append(vec)
    out: dict[str, list[float]] = {}
    for d, vecs in groups.items():
        dims = {len(v) for v in vecs}
        if len(vecs) < min_files or len(dims) != 1:
            continue  # too small, or mixed embedding models
        n = len(vecs)
        out[d] = [sum(col) / n for col in zip(*vecs, strict=True)]
    return out


def _hit(path: str, own: str, own_sim: float, best_dir: str,
         best_sim: float) -> Hit:
    return Hit("misfiled", path, round(best_sim - own_sim, 4), "",
               {"own_dir": own, "suggested_dir": best_dir,
                "own_similarity": round(own_sim, 4),
                "suggested_similarity": round(best_sim, 4)})


def _outliers_numpy(cents: dict[str, list[float]], vectors: dict,
                    margin: float) -> list[Hit]:
    import numpy as np

    dirs = list(cents)
    dim = len(cents[dirs[0]])
    idx_of = {d: i for i, d in enumerate(dirs)}
    cmat = np.asarray([cents[d] for d in dirs], dtype=np.float32)
    cmat /= np.maximum(np.linalg.norm(cmat, axis=1, keepdims=True), 1e-9)

    items = [(p, e["embedding"], str(Path(p).parent))
             for p, e in vectors.items()
             if e.get("embedding") and len(e["embedding"]) == dim
             and str(Path(p).parent) in cents]
    hits: list[Hit] = []
    for start in range(0, len(items), CHUNK):
        block = items[start:start + CHUNK]
        fmat = np.asarray([v for _p, v, _d in block], dtype=np.float32)
        fmat /= np.maximum(np.linalg.norm(fmat, axis=1, keepdims=True), 1e-9)
        sims = fmat @ cmat.T                       # (chunk, n_dirs)
        own_cols = np.asarray([idx_of[d] for _p, _v, d in block])
        rows = np.arange(len(block))
        own_sims = sims[rows, own_cols]
        sims[rows, own_cols] = -np.inf             # exclude the file's own dir
        best_cols = sims.argmax(axis=1)
        best_sims = sims[rows, best_cols]
        for i, (path, _v, own) in enumerate(block):
            if best_sims[i] - own_sims[i] > margin:
                hits.append(_hit(path, own, float(own_sims[i]),
                                 dirs[int(best_cols[i])], float(best_sims[i])))
    return hits


def _outliers_python(cents: dict[str, list[float]], vectors: dict,
                     margin: float) -> list[Hit]:
    """numpy-free fallback: compares against the largest directories only."""
    dirs = list(cents)
    if len(dirs) > FALLBACK_MAX_DIRS:
        dirs = dirs[:FALLBACK_MAX_DIRS]
        _log.warning("misfiled: numpy unavailable — comparing against the first "
                     "%d of %d directories only (install numpy for the full scan)",
                     FALLBACK_MAX_DIRS, len(cents))
    hits: list[Hit] = []
    for path, entry in vectors.items():
        vec = entry.get("embedding")
        own = str(Path(path).parent)
        if not vec or own not in cents or len(vec) != len(cents[own]):
            continue
        own_sim = cosine_similarity(vec, cents[own])
        best_dir, best_sim = None, -1.0
        for d in dirs:
            c = cents[d]
            if d == own or len(c) != len(vec):
                continue
            sim = cosine_similarity(vec, c)
            if sim > best_sim:
                best_dir, best_sim = d, sim
        if best_dir and best_sim - own_sim > margin:
            hits.append(_hit(path, own, own_sim, best_dir, best_sim))
    return hits


def outliers(min_files: int = MIN_FILES, margin: float = MARGIN) -> list[Hit]:
    """Files whose best foreign directory beats their own by > margin."""
    cents = directory_centroids(min_files=min_files)
    if len(cents) < 2:
        return []
    vectors = hub_lib.load_embeddings()
    try:
        import numpy  # noqa: F401
        hits = _outliers_numpy(cents, vectors, margin)
    except ImportError:
        hits = _outliers_python(cents, vectors, margin)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Flag indexed files that look like they're in the wrong folder")
    ap.add_argument("--margin", type=float, default=MARGIN)
    ap.add_argument("--min-files", type=int, default=MIN_FILES)
    args = ap.parse_args(argv)
    hits = outliers(min_files=args.min_files, margin=args.margin)
    if not hits:
        print("no misfiled files detected")
        return 0
    for h in hits:
        print(f"{h.score:6.3f}  {h.ref}\n         fits {h.meta['suggested_dir']} "
              f"better than {h.meta['own_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
