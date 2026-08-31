"""Error→fix recall (idea #6): match a new failure against past incidents in
the log corpus and attach what happened next — the .remember session entries
and commits landed within a 6h window after each matched error."""
from __future__ import annotations

from pathlib import Path

import embed_core
import hub_lib

from semantic_ops.fuse import Hit
from semantic_ops.git_corpus import git_db_path
from semantic_ops.logs_corpus import SNIPPET_CHARS, logs_db_path
from semantic_ops.vecstore import VecStore

WINDOW_SECS = 6 * 3600
_log = hub_lib.get_logger("semantic_ops")


def nearest_fixes(error_text: str, top_k: int = 3,
                  logs_db: str | Path | None = None,
                  git_db: str | Path | None = None,
                  window_secs: float = WINDOW_SECS) -> list[Hit]:
    """Top past errors similar to error_text, each with fix_candidates meta:
    <=2 session entries and <=2 commits from the window after the error."""
    ldb = Path(logs_db) if logs_db else logs_db_path()
    if not ldb.exists():
        return []
    try:
        qvec = embed_core.embed_texts([error_text])[0]
    except embed_core.EmbeddingUnavailable as e:
        _log.warning("fix recall degraded (embed pool down): %s", e)
        return []

    store = VecStore(ldb)
    try:
        rows = store.query(qvec, top=top_k, kinds=("error",))
        windows = [(r, store.rows_between(r["ts"], r["ts"] + window_secs,
                                          kinds=("session",))[:2]) for r in rows]
    finally:
        store.close()

    gdb = Path(git_db) if git_db else git_db_path()
    commits_by_row: list[list[dict]] = [[] for _ in windows]
    if gdb.exists():
        gstore = VecStore(gdb)
        try:
            for i, (r, _sessions) in enumerate(windows):
                commits_by_row[i] = gstore.rows_between(
                    r["ts"], r["ts"] + window_secs, kinds=("commit",))[:2]
        finally:
            gstore.close()

    hits: list[Hit] = []
    for (r, sessions), commits in zip(windows, commits_by_row, strict=True):
        cands = [{"kind": c["kind"], "ref": c["ref"], "ts": c["ts"],
                  "text": c["text"][:200]} for c in sessions + commits]
        cands.sort(key=lambda c: c["ts"])
        hits.append(Hit("logs", r["ref"], r["score"], r["text"][:SNIPPET_CHARS],
                        {"ts": r["ts"], "kind": "error", "fix_candidates": cands}))
    return hits
