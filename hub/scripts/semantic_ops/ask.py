"""Federated `hub ask` (idea #1): fan out one query over every corpus,
RRF-fuse, embed-rerank, then answer with the pooled LLM citing sources.

Retrieval always works even with the LLM down — `ask()` degrades to
("", hits). Every query is appended to HUB_ASK_HISTORY (jsonl) so the
coverage map (idea #14) can find weak spots later.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import hub_lib

from semantic_ops import llm
from semantic_ops.corpus import default_corpora
from semantic_ops.fuse import Hit, rrf
from semantic_ops.logs_corpus import hub_dir
from semantic_ops.rerank import rerank

CONTEXT_CHARS = 6000
PER_HIT_CHARS = 700
_log = hub_lib.get_logger("semantic_ops")

ANSWER_PROMPT = """You are the local hub oracle. Answer the question using ONLY \
the numbered context snippets. Cite snippet numbers like [1][3] after each claim. \
If the context is insufficient, say exactly what is missing.

Question: {query}

Context:
{context}

Answer:"""


def ask_topk() -> int:
    try:
        return int(os.environ.get("HUB_ASK_TOPK", "8"))
    except ValueError:
        return 8


def rerank_n() -> int:
    try:
        return int(os.environ.get("HUB_RERANK_N", "50"))
    except ValueError:
        return 50


def history_path() -> Path:
    return Path(os.environ.get("HUB_ASK_HISTORY", str(hub_dir() / "ask_history.jsonl")))


def retrieve(query: str, corpora=None, top_k: int | None = None) -> list[Hit]:
    """Parallel fan-out over corpora -> rrf -> rerank -> top_k."""
    corpora = corpora if corpora is not None else default_corpora()
    top_k = top_k if top_k is not None else ask_topk()

    def one(c) -> list[Hit]:
        try:
            return c.search(query, top_k=10)
        except Exception as e:  # one broken corpus must not kill the query
            _log.warning("corpus '%s' failed: %s", getattr(c, "name", "?"), e)
            return []

    # One worker per corpus (uncapped): every corpus is I/O-bound (network
    # embed call or a subprocess) and the identical-query embed is now
    # coalesced (semantic_ops.corpus._query_vec), so there's no thundering-
    # herd risk left -- a low cap here just serializes into waves, letting
    # one slow corpus (napmem's subprocess, a cold embed-pool host) gate
    # everything queued behind it for no reason.
    with ThreadPoolExecutor(max_workers=max(8, len(corpora))) as ex:
        ranklists = list(ex.map(one, corpora))
    fused = rrf([r for r in ranklists if r])
    return rerank(query, fused[:rerank_n()], top_n=top_k)


def _context_block(hits: list[Hit]) -> str:
    parts: list[str] = []
    used = 0
    for i, h in enumerate(hits, 1):
        snippet = h.snippet[:PER_HIT_CHARS].strip()
        entry = f"[{i}] {h.source} {h.ref}\n{snippet}\n"
        if used + len(entry) > CONTEXT_CHARS:
            break
        parts.append(entry)
        used += len(entry)
    return "\n".join(parts)


def ask(query: str, corpora=None) -> tuple[str, list[Hit]]:
    """(answer_with_citations, hits); answer is "" when the LLM pool is down."""
    hits = retrieve(query, corpora=corpora)
    if not hits:
        return "", []
    prompt = ANSWER_PROMPT.format(query=query, context=_context_block(hits))
    try:
        answer = llm.generate(prompt)
    except llm.LLMUnavailable as e:
        _log.warning("ask degraded to retrieval only (LLM down): %s", e)
        return "", hits
    return answer, hits


def log_query(query: str, hits: list[Hit]) -> None:
    """Best-effort jsonl append for the coverage map; never raises."""
    try:
        rec = {"ts": time.time(), "query": query,
               "top": [{"source": h.source, "ref": h.ref, "score": h.score}
                       for h in hits[:10]]}
        path = history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError as e:
        _log.warning("ask history append failed: %s", e)


def _print_hits(hits: list[Hit]) -> None:
    for i, h in enumerate(hits, 1):
        first = h.snippet.splitlines()[0][:80] if h.snippet else ""
        print(f"[{i}] {h.score:7.4f}  {h.source:<18} {h.ref}  {first}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ask the local hub oracle")
    ap.add_argument("query")
    ap.add_argument("--retrieve-only", action="store_true",
                    help="skip the LLM answer, print ranked sources only")
    ap.add_argument("--corpora", default="",
                    help="comma list filter, e.g. codebase,logs,git")
    ap.add_argument("--top", type=int, default=None)
    args = ap.parse_args(argv)

    corpora = default_corpora()
    if args.corpora:
        wanted = {w.strip() for w in args.corpora.split(",") if w.strip()}
        corpora = [c for c in corpora
                   if c.name in wanted or c.name.split(":", 1)[0] in wanted]

    if args.retrieve_only:
        hits = retrieve(args.query, corpora=corpora, top_k=args.top)
        log_query(args.query, hits)
        _print_hits(hits)
        if not hits:
            print("no hits (indexes built? embed pool up?)")
        return 0

    answer, hits = ask(args.query, corpora=corpora)
    log_query(args.query, hits)
    if answer:
        print(answer.strip())
        print("\nsources:")
    else:
        print("(LLM unavailable — retrieval only)\n")
    _print_hits(hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
