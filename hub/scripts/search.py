#!/usr/bin/env python3
"""
search.py — Semantic search CLI for the Global AI Hub.

Usage:
    python ~/.global-ai-hub/scripts/search.py "your query here"
    python ~/.global-ai-hub/scripts/search.py "tiered memory" --top 10
    python ~/.global-ai-hub/scripts/search.py "upsert_file" --mode keyword [--prefix ~/dev]

Semantic mode (default) embeds the query and ranks hub.db vectors by cosine
similarity. Keyword mode ranks the files_fts BM25 index (keyword_index.py)
and needs no Ollama.
"""

import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(__file__))
import hub_lib


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search(query, top_n=5, use_rerank=False):
    """Search the universal embeddings for the most similar files."""
    query_emb = hub_lib.fetch_embedding(query)
    if not query_emb:
        print("ERROR: Could not generate query embedding. Is Ollama running?", file=sys.stderr)
        sys.exit(1)

    vectors = hub_lib.load_embeddings()
    if not vectors:
        print("No embeddings found. Run the indexer first.")
        sys.exit(0)

    results = []
    for path, entry in vectors.items():
        vec = entry.get("embedding")
        if not vec:
            continue
        score = cosine_similarity(query_emb, vec)
        results.append((score, path))

    results.sort(key=lambda x: x[0], reverse=True)
    top = results[:top_n]

    if use_rerank:
        # Precision pass: re-score the candidate pool on snippet content
        # (semantic_ops.rerank). Falls back to the plain order on any failure.
        try:
            from semantic_ops import rerank as _rr
            from semantic_ops.fuse import Hit
            cands = [Hit("codebase", path, score,
                         (hub_lib.get_text_content(path, max_chars=400) or ""))
                     for score, path in results[:max(top_n * 4, top_n)]]
            top = [(h.score, h.ref) for h in _rr.rerank(query, cands, top_n=top_n)]
        except Exception as e:
            print(f"(rerank unavailable: {e})", file=sys.stderr)

    print(f"\n{'Score':>7}  File")
    print(f"{'─'*7}  {'─'*60}")
    for score, path in top:
        # Shorten home dir for display
        display = path.replace(os.path.expanduser("~"), "~")
        print(f"{score:7.4f}  {display}")
    print()


def keyword_search(query, top_n=5, prefix=None):
    """BM25 search over the files_fts keyword index."""
    import keyword_index
    hits = keyword_index.query(query, prefix=prefix, top=top_n)
    if not hits:
        print("No keyword matches (is the index built? keyword_index.py stats).")
        return
    print(f"\n{'BM25':>7}  File")
    print(f"{'─'*7}  {'─'*60}")
    for h in hits:
        print(f"{h['score']:7.3f}  {h['path'].replace(os.path.expanduser('~'), '~')}")
        if h.get("snippet"):
            print(f"{'':7}    {h['snippet']}")
    print()


def _opt(name):
    if name in sys.argv:
        idx = sys.argv.index(name)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: search.py <query> [--top N] [--rerank] [--mode semantic|keyword] [--prefix PATH]")
        sys.exit(1)

    query = sys.argv[1]
    top_n = 5

    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        if idx + 1 < len(sys.argv):
            try:
                top_n = int(sys.argv[idx + 1])
            except ValueError:
                pass

    mode = _opt("--mode") or ("keyword" if "--keyword" in sys.argv else "semantic")
    if mode == "keyword":
        keyword_search(query, top_n, prefix=_opt("--prefix"))
        return
    if mode != "semantic":
        print("ERROR: --mode must be semantic or keyword", file=sys.stderr)
        sys.exit(1)
    search(query, top_n, use_rerank="--rerank" in sys.argv)


if __name__ == "__main__":
    main()
