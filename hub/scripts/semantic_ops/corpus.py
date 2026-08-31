"""Uniform Corpus adapters over the hub's semantic indexes.

Each adapter exposes `search(query, top_k) -> list[Hit]` and degrades to an
empty result (never raises) when its backing index or the embedding pool is
unavailable — federated callers fan out over many corpora and one broken
source must not kill the query.
"""
from __future__ import annotations

import os
import re
import subprocess
import threading
from typing import Protocol

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops.fuse import Hit

SNIPPET_CHARS = 400
NAPMEM_AGENT = os.path.expanduser("~/dev/llm-memory-pyramid/napmem_retrieval_agent.py")
NAPMEM_PYRAMID = os.path.expanduser("~/dev/llm-memory-pyramid/napmem_pyramid.json")

_log = hub_lib.get_logger("semantic_ops")


class Corpus(Protocol):
    name: str

    def search(self, query: str, top_k: int = 10) -> list[Hit]: ...


# Every corpus type (docsets, logs, git, symbols, ...) embeds the SAME query
# string once per federated ask -- retrieve() fans them out concurrently via
# ThreadPoolExecutor, so a plain @lru_cache doesn't help: N threads all miss
# the cache in the same instant (nothing cached yet) and all fire their own
# request at the contended pool -- a thundering herd, not a dedup. This
# coalesces concurrent identical queries: the first caller does the real
# embed; everyone else waits on it and reads the same result.
_query_vec_lock = threading.Lock()
_query_vec_cache: dict[str, tuple[float, ...] | None] = {}
_query_vec_inflight: dict[str, threading.Event] = {}


def _query_vec(query: str) -> tuple[float, ...] | None:
    with _query_vec_lock:
        if query in _query_vec_cache:
            return _query_vec_cache[query]
        event = _query_vec_inflight.get(query)
        owner = event is None
        if owner:
            event = threading.Event()
            _query_vec_inflight[query] = event
    if not owner:
        event.wait()
        with _query_vec_lock:
            return _query_vec_cache.get(query)
    try:
        result: tuple[float, ...] | None
        try:
            result = tuple(embed_core.embed_texts([query])[0])
        except embed_core.EmbeddingUnavailable as e:
            _log.warning("semantic query degraded (embed pool down): %s", e)
            result = None
        with _query_vec_lock:
            _query_vec_cache[query] = result
        return result
    finally:
        event.set()
        with _query_vec_lock:
            _query_vec_inflight.pop(query, None)


class HubCorpus:
    """File-level vectors in hub.db (one embedding per indexed file).

    Queries embed via hub_lib.fetch_embedding — hub_lib's OWN config model —
    because hub.db was built with it (e.g. nomic-embed-text, 768d). Using the
    embed_core pool model here would dimension-mismatch every stored vector
    (verified live: mxbai-embed-large 1024d vs 768d → zero results)."""

    name = "codebase"

    def search(self, query: str, top_k: int = 10) -> list[Hit]:
        qvec = hub_lib.fetch_embedding(query)
        if not qvec:
            _log.warning("codebase search degraded: hub_lib embedding "
                         "unavailable (is Ollama up on hub_lib's ollama_url?)")
            return []
        scored: list[tuple[float, str]] = []
        for path, entry in hub_lib.load_embeddings().items():
            vec = entry.get("embedding")
            if not vec or len(vec) != len(qvec):
                continue  # missing or different-model vector — cosine meaningless
            scored.append((cosine_similarity(qvec, vec), path))
        scored.sort(reverse=True)
        hits = []
        for score, path in scored[:top_k]:
            snippet = (hub_lib.get_text_content(path, max_chars=SNIPPET_CHARS)
                       or "")[:SNIPPET_CHARS]
            hits.append(Hit(self.name, path, round(score, 4), snippet))
        return hits


class DocsetCorpus:
    """One indexed web-text-mirror docset via docset_indexer's store."""

    def __init__(self, key: str, store):
        self.key = key
        self.store = store
        self.name = f"docset:{key}"

    def search(self, query: str, top_k: int = 10) -> list[Hit]:
        qvec = _query_vec(query)
        if qvec is None:
            return []
        try:
            rows = self.store.query(self.key, list(qvec), top_k)
        except Exception as e:  # model mismatch, backend skew, missing collection
            _log.warning("docset '%s' query degraded: %s", self.key, e)
            return []
        return [
            Hit(self.name, r["url"], float(r["score"]),
                (r.get("text") or "")[:SNIPPET_CHARS], {"seq": r.get("seq")})
            for r in rows
        ]


_NAPMEM_SCORE = re.compile(r"\b(0\.\d{1,4}|1\.0{1,4})\b")


class NapmemCorpus:
    """llm-memory-pyramid retrieval agent, subprocess-isolated."""

    name = "napmem"

    def __init__(self, agent: str | None = None, pyramid: str | None = None,
                 timeout: int = 30):
        # Late-bound defaults: the module globals are the seam tests (and any
        # future env override) patch, so read them at construction time.
        self.agent = agent or NAPMEM_AGENT
        self.pyramid = pyramid or NAPMEM_PYRAMID
        self.timeout = timeout

    def available(self) -> bool:
        return os.path.exists(self.agent) and os.path.exists(self.pyramid)

    def search(self, query: str, top_k: int = 10) -> list[Hit]:
        if not self.available():
            return []
        cmd = ["python3", self.agent, "--pyramid", self.pyramid,
               "--query", query, "--semantic"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=self.timeout)
        except (OSError, subprocess.SubprocessError) as e:
            _log.warning("napmem agent failed: %s", e)
            return []
        if proc.returncode != 0:
            _log.warning("napmem agent rc=%s: %s", proc.returncode,
                         proc.stderr.strip()[:200])
            return []
        return _parse_napmem(proc.stdout, top_k)


def _parse_napmem(stdout: str, top_k: int) -> list[Hit]:
    """Tolerant parse of the agent's human-oriented output: one Hit per
    non-empty line; similarity lifted from a leading '[..., 0.74]'-style
    score when present, else rank-decayed."""
    hits: list[Hit] = []
    for line in stdout.splitlines():
        line = line.strip().lstrip("-").strip()
        if not line or line.startswith(("===", "___")) or set(line) <= {"=", "-"}:
            continue  # banner / separator lines from the agent's report
        if "Semantic Search Results" in line or "Search Results for" in line:
            continue
        m = _NAPMEM_SCORE.search(line[:40])
        score = float(m.group(1)) if m else 1.0 / (len(hits) + 1)
        hits.append(Hit("napmem", f"record-{len(hits)}", score, line[:SNIPPET_CHARS]))
        if len(hits) >= top_k:
            break
    return hits


def default_corpora(include_docsets: bool = True,
                    include_napmem: bool = True,
                    include_logs: bool = True,
                    include_git: bool = True,
                    include_symbols: bool = True) -> list[Corpus]:
    """Every currently-available corpus; broken sources are skipped, never fatal."""
    corpora: list[Corpus] = [HubCorpus()]
    if include_docsets:
        try:
            import docset_indexer
            store = docset_indexer.get_store()
            for row in store.list_docsets():
                corpora.append(DocsetCorpus(row["docset"], store))
        except Exception as e:  # chroma missing, db locked, registry corrupt
            _log.warning("docsets unavailable: %s", e)
    if include_logs:
        from semantic_ops.logs_corpus import LogsCorpus
        logs = LogsCorpus()
        if logs.available():
            corpora.append(logs)
    if include_git:
        from semantic_ops.git_corpus import GitCorpus
        git = GitCorpus()
        if git.available():
            corpora.append(git)
    if include_symbols:
        from semantic_ops.symbols import SymbolsCorpus
        syms = SymbolsCorpus()
        if syms.available():
            corpora.append(syms)
    if include_napmem:
        nap = NapmemCorpus()
        if nap.available():
            corpora.append(nap)
    return corpora
